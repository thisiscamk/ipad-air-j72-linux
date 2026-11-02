#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Prepare an exact-J72 RAM-only Pongo recovery handoff. Never access USB."""
import hashlib, importlib.util, json, os, plistlib, struct, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'private/j72-platform/power-storage-20261102/recovery-prep'
WORK=BASE/'pongo-route/handoff-v1'
IMPORTS={'_alloc_static','_command_puts','_command_register','_dt_alloc_memmap','_dt_check$64',
 '_dt_find','_dt_parse$64','_dt_prop$64','_gBootArgs','_gDeviceTree','_gEntryPoint',
 '_gTopOfKernelData','_loader_xfer_recv_count','_loader_xfer_recv_data','_memcmp','_memcpy',
 '_ramdisk_buf','_ramdisk_size','_socnum','_task_yield'}
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def records(raw):
 assert len(raw)>=24 and struct.unpack_from('<I',raw)[0]==1
 n=struct.unpack_from('<I',raw,20)[0];assert 0<n<=10000 and len(raw)==24+22*n
 entries=[raw[24+i*22:46+i*22] for i in range(n)]
 assert entries==sorted(entries)
 seen={}
 for entry in entries:
  if entry[:20] in seen:assert seen[entry[:20]]==entry,'conflicting duplicate CDhash metadata'
  else:seen[entry[:20]]=entry
 assert all(e[20] in (1,2,3,4) for e in entries)
 return entries
def main():
 os.umask(0o077);WORK.mkdir(exist_ok=True)
 capsule=BASE/'capsule-v1';image=load('image',ROOT/'tools/prepare-j72-ios-recovery.py');capsule_manifest=image.check(capsule)
 legacy=load('legacy',ROOT/'tools/run-j72-pongo-recovery-probe.py')
 compact=load('compact',ROOT/'tools/run-j72-pongo-recovery-compact.py');previous=compact.check()
 decoder=load('der',ROOT/'tools/test-j72-ios-recovery.py')
 stock_image=BASE/'static-trustcache/16H81__iPad4,2/038-87004-055.dmg.trustcache'
 apple=plistlib.loads((BASE/'firmware/16H81__iPad4,2/BuildManifest.plist').read_bytes())
 identity=[i for i in apple['BuildIdentities'] if i['Info']['DeviceClass']=='j72ap' and i['Info']['RestoreBehavior']=='Erase'][0]
 assert hashlib.sha1(stock_image.read_bytes()).digest()==identity['Manifest']['StaticTrustCache']['Digest']
 tag,body,end=decoder.der_value(stock_image.read_bytes());assert tag==48 and end==stock_image.stat().st_size
 children=list(decoder.der_children(body));assert children[0]==(22,b'IM4P') and children[1]==(22,b'trst') and children[3][0]==4
 stock=children[3][1];original=records(stock)
 live_header=BASE/'pongo-route/trustcache-live-header32.bin'
 assert live_header.read_bytes()==struct.pack('<II',1,8)+stock[:24]
 original_serialized=struct.pack('<II',1,8)+stock
 extra=(capsule/'recovery.trustcache').read_bytes();recovery=records(extra)
 seen={e[:20]:e for e in original};merged=list(original)
 for entry in recovery:
  if entry[:20] in seen:assert seen[entry[:20]]==entry,'conflicting CDhash metadata'
  else:seen[entry[:20]]=entry;merged.append(entry)
 merged.sort();assert set(original)<=set(merged) and set(recovery)<=set(merged)
 entries=b''.join(merged)
 tc=struct.pack('<III',1,8,1)+hashlib.sha256(entries).digest()[:16]+struct.pack('<I',len(merged))+entries
 (WORK/'trustcache.serialized.merged').write_bytes(tc)
 hfs=(capsule/'ramdisk.hfs').read_bytes()
 tag,body,end=decoder.der_value((capsule/'ramdisk.img4').read_bytes());assert tag==48
 im4p=list(decoder.der_children(list(decoder.der_children(body))[1][1]))
 assert im4p[1]==(22,b'rdsk') and im4p[3]==(4,hfs)
 tag,body,end=decoder.der_value((capsule/'trustcache.img4').read_bytes());assert tag==48
 im4p=list(decoder.der_children(list(decoder.der_children(body))[1][1]));assert im4p[3]==(4,extra)
 assert hfs[1024:1026] in (b'H+',b'HX') and len(hfs)==130000000
 tc_offset=512;hfs_offset=(tc_offset+len(tc)+0x3fff)&~0x3fff
 total=(hfs_offset+len(hfs)+511)&~511;assert total<=0x8000000
 bundle=bytearray(total);bundle[:48]=struct.pack('<8sIIQQQQ',b'J72RAM01',1,512,tc_offset,len(tc),hfs_offset,len(hfs))
 bundle[tc_offset:tc_offset+len(tc)]=tc;bundle[hfs_offset:hfs_offset+len(hfs)]=hfs
 bundle_path=WORK/'recovery.bundle';bundle_path.write_bytes(bundle)
 values={'BUNDLE_SIZE':total,'TC_OFFSET':tc_offset,'TC_SIZE':len(tc),'HFS_OFFSET':hfs_offset,'HFS_SIZE':len(hfs),'ORIGINAL_TC_USED':len(original_serialized)}
 config=WORK/'j72-pongo-recovery-handoff-private.h'
 text='/* Private generated hashes/UUID. Never publish this file. */\n'
 text+=''.join(f'#define {name} {value}ULL\n' for name,value in values.items())
 text+='#define RAM_BOOTARGS "'+image.BOOTARGS+'"\n'
 for name,data in [('expected_uuid',bytes.fromhex(previous['expected_kernel_uuid'])),('expected_original_tc_sha',hashlib.sha256(original_serialized).digest()),('expected_bundle_sha',hashlib.sha256(bundle).digest())]:
  text+='static const unsigned char '+name+'['+str(len(data))+']={'+','.join(hex(b) for b in data)+'};\n'
 config.write_text(text)
 obj=WORK/'j72-recovery-handoff.o';module=WORK/'j72-recovery-handoff.kext';linker=ROOT/'private/j72-touch/ld64-arm64'
 env=os.environ.copy();env['LD_LIBRARY_PATH']=str(ROOT/'private/j72-touch/runtime/usr/lib/aarch64-linux-gnu')
 with (WORK/'build.log').open('wb') as log:
  for args in [
   ['/usr/bin/clang','-target','arm64-apple-ios12.0','-O2','-ffreestanding','-fno-builtin','-fno-stack-protector','-Wall','-Wextra','-Werror','-I',str(WORK),'-c',str(ROOT/'tools/j72-pongo-recovery-handoff.c'),'-o',str(obj)],
   [str(linker),'-arch','arm64','-kext','-static','-ios_version_min','12.0','-o',str(module),str(obj)]]:
   subprocess.run(args,stdout=log,stderr=log,check=True,env=env,timeout=45)
 legacy.EXPECTED_IMPORTS=IMPORTS;imports=legacy.module_imports(module);pongo=legacy.PONGO.read_bytes()
 for name in imports:
  offset=pongo.find(name.encode()+b'\0');assert offset>=0
  pair=pongo.find(struct.pack('<Q',0x100000000+offset));assert pair>=0
  assert 0x100000000<=struct.unpack_from('<Q',pongo,pair+8)[0]<0x100100000
 files=dict(previous['files'])
 # Reuse only the pinned old launcher's restricted USB/SSH inspector path;
 # this candidate never calls its exploit or Apple bootloader upload methods.
 inspection_pins=BASE/'launcher-pins.json'
 for name,digest in json.loads(inspection_pins.read_text())['files'].items():
  assert sha(ROOT/name)==digest,name
  files[name]=digest
 files[str(inspection_pins.relative_to(ROOT))]=sha(inspection_pins)
 additions=[ROOT/'tools'/name for name in ['j72-pongo-recovery-handoff.c','j72-pongo-recovery-handoff-bounds.h','j72_sha256.h','prepare-j72-pongo-recovery-handoff.py','run-j72-pongo-recovery-handoff.py','test-j72-pongo-recovery-handoff.py']]
 additions += [stock_image,live_header,config,bundle_path,module,capsule/'manifest.json',capsule/'ramdisk.hfs',capsule/'recovery.trustcache']
 for p in additions:files[str(p.relative_to(ROOT))]=sha(p)
 manifest={'profile':'j72-pongo-ram-recovery-handoff-v1','files':files,'module_imports':imports,
   'expected_kernel_uuid':previous['expected_kernel_uuid'],'bootargs':image.BOOTARGS,
   'capsule_profile':capsule_manifest['profile'],'layout':values,
   'original_trustcache_entries':len(original),'recovery_trustcache_entries':len(recovery),'merged_trustcache_entries':len(merged),
   'original_trustcache_records_preserved':True,'kernel_patched':False,'automatic_internal_mounts':False,'internal_storage_write_interface':False,'runtime_tested':False}
 (WORK/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('PASS offline RAM handoff build; original cache records retained:',len(original),'merged:',len(merged),'bundle bytes:',total)
if __name__=='__main__':main()
