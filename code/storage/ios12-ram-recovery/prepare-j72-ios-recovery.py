#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build/check a private exact-J72 iOS12 RAM recovery capsule. No USB calls."""
import argparse, hashlib, io, json, os, plistlib, shutil, struct, subprocess, tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'private/j72-platform/power-storage-20261102/recovery-prep'
FW=WORK/'firmware/16H81__iPad4,2'
BOOTARGS='rd=md0 debug=0x2014e -v wdt=-1'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args,**kw):
 r=subprocess.run([str(x) for x in args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,**kw)
 if r.returncode:raise RuntimeError(f'{args[0]} {args[2:]} failed {r.returncode}: '+r.stderr.decode(errors='replace')[-2000:])
 return r
def be32(b,o):return struct.unpack_from('>I',b,o)[0]
def cdh(b):
 """Parse and verify embedded CodeDirectory pages; return (cdhash,type,flags)."""
 if len(b)<32:return []
 magic=b[:4]
 if magic in (b'\xca\xfe\xba\xbe',b'\xca\xfe\xba\xbf'):
  count=be32(b,4);assert 0<count<=8
  result=[];stride=32 if magic[-1]==0xbf else 20
  for i in range(count):
   o=8+i*stride;assert o+stride<=len(b)
   cpu=be32(b,o)
   off,size=struct.unpack_from('>QQ' if stride==32 else '>II',b,o+8)
   assert off<=len(b) and 0<size<=len(b)-off
   if cpu==0x100000c:result+=cdh(b[off:off+size])
  return result
 if magic!=b'\xcf\xfa\xed\xfe':return []
 assert struct.unpack_from('<I',b,4)[0]==0x100000c,'non-ARM64 Mach-O'
 count,cmdbytes=struct.unpack_from('<II',b,16);assert count<=128 and 32+cmdbytes<=len(b)
 at=32;cs=None
 for _ in range(count):
  cmd,n=struct.unpack_from('<II',b,at);assert n>=8 and at+n<=32+cmdbytes
  if cmd==0x1d:
   assert n==16;cs=struct.unpack_from('<II',b,at+8)
  at+=n
 assert at==32+cmdbytes and cs is not None,'missing code signature'
 off,size=cs;assert off<=len(b) and 12<=size<=len(b)-off
 blob=b[off:off+size];assert be32(blob,0)==0xfade0cc0
 length,num=be32(blob,4),be32(blob,8);assert 12+num*8<=length<=len(blob) and num<=32
 result=[]
 for i in range(num):
  typ,pos=struct.unpack_from('>II',blob,12+8*i);assert pos+8<=length
  if typ!=0 and not 0x1000<=typ<0x1005:continue
  ln=be32(blob,pos+4);assert 44<=ln<=length-pos
  cd=blob[pos:pos+ln];assert be32(cd,0)==0xfade0c02
  ho,special,slots,limit=struct.unpack_from('>IIII',cd,16)[0],be32(cd,24),be32(cd,28),be32(cd,32)
  hs,ht,platform,pg=cd[36:40];assert ht in (1,2,3,4) and pg in (12,14)
  digest={1:'sha1',2:'sha256',3:'sha256',4:'sha384'}[ht]
  assert hs=={1:20,2:32,3:20,4:48}[ht]
  assert limit<=off and slots==(limit+(1<<pg)-1)//(1<<pg)
  assert special*hs<=ho and ho+slots*hs<=len(cd)
  for j in range(slots):
   assert hashlib.new(digest,b[j*(1<<pg):min((j+1)*(1<<pg),limit)]).digest()[:hs]==cd[ho+j*hs:ho+(j+1)*hs], 'CodeDirectory page hash mismatch'
  result.append((hashlib.new(digest,cd).digest()[:20],ht,0))
 assert result,'no CodeDirectory';return result

def firmware():
 m=plistlib.loads((FW/'BuildManifest.plist').read_bytes())
 choices=[x for x in m['BuildIdentities'] if x['Info']['DeviceClass']=='j72ap' and x['Info']['RestoreBehavior']=='Erase']
 assert len(choices)==1;i=choices[0]
 assert int(i['ApChipID'],16)==0x8960 and int(i['ApBoardID'],16)==0x12
 out={}
 for label in ['KernelCache','RestoreRamDisk','RestoreTrustCache','iBSS','iBEC','DeviceTree']:
  ent=i['Manifest'][label];p=FW/ent['Info']['Path']
  if label=='RestoreRamDisk':p=ROOT/'private/firmware/j72-ios1257/16H81__iPad4,2'/p.name
  b=p.read_bytes()
  if label=='RestoreTrustCache':
   assert b.count(b'trst')==1;b=b.replace(b'trst',b'rtsc',1)
  assert hashlib.sha1(b).digest()==ent['Digest'],label+' Apple BuildManifest digest mismatch'
  out[label]=p
 return out

def adr_refs(b,target):
 found=[]
 for o in range(0,len(b)-3,4):
  ins=struct.unpack_from('<I',b,o)[0]
  if ins&0x9f000000!=0x10000000:continue
  delta=((ins>>5)&0x7ffff)<<2|((ins>>29)&3)
  if delta&(1<<20):delta-=1<<21
  if o+delta==target:found.append(o)
 return found

def bootloaders():
 a=(WORK/'iBEC12.5.7.patched').read_bytes();b=BOOTARGS.encode()+b'\0'
 assert a.count(b)==1;off=a.index(b);refs=adr_refs(a,off);assert len(refs)>=1
 for label in ['iBSS','iBEC']:
  p=WORK/(label+'12.5.7.patched');original=WORK/(label+'12.5.7.dec')
  assert p.stat().st_size==original.stat().st_size and p.read_bytes()!=original.read_bytes()
 return {'active_bootargs':BOOTARGS,'bootargs_offset':off,'adr_references':refs,'nvram_unlock_requested':False}

def filtered_tar(stage):
 archive=WORK/'legacy-ssh64.tar.gz';assert hashlib.sha1(archive.read_bytes()).hexdigest()=='61975423c096d5f21fd9f8a48042fffd3828708b'
 keepbin={'bash','sh'}
 selected={}
 with tarfile.open(archive) as src:
  for m in src.getmembers():
   n=m.name.removeprefix('./');assert not n.startswith('/') and '..' not in Path(n).parts
   allowed=(n.startswith('bin/') and Path(n).name in keepbin) or n=='usr/local/bin/dropbear'
   if not allowed:continue
   if m.isdir():continue
   assert m.isfile() or m.issym() or m.islnk(),n
   selected[n]=(m,src.extractfile(m).read() if m.isfile() else None)
 # Extract only into our fresh private stage with Python's data filter.
 temp=stage.parent/'filtered-ssh.tar'
 with tarfile.open(temp,'w',format=tarfile.USTAR_FORMAT) as tar:
  for n,(m,b) in selected.items():
   m.name=n;m.uid=m.gid=0;m.uname=m.gname='root'
   tar.addfile(m,io.BytesIO(b) if b is not None else None)
 with tarfile.open(temp) as tar:tar.extractall(stage,filter='data')
 assert (stage/'usr/local/bin/dropbear').is_file()
 assert b'ssh-rsa' in (stage/'usr/local/bin/dropbear').read_bytes(),'client key algorithm unavailable'
 return len(selected)

def build(out):
 assert not out.exists(),'refuse an existing capsule output';out.mkdir(mode=0o700)
 f=firmware();bl=bootloaders();stage=out/'stage';stage.mkdir()
 count=filtered_tar(stage)
 def add(src,rel,mode):
  p=stage/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,p);p.chmod(mode)
 add(WORK/'readonly-service/j72-usb-recovery','usr/local/bin/j72-usb-recovery',0o755)
 add(WORK/'readonly-service/j72-recovery-inspect','usr/local/bin/j72-recovery-inspect',0o755)
 add(WORK/'readonly-service/j72-usb-recovery','usr/local/bin/restored_external',0o755)
 add(WORK/'keys/dropbear_rsa_host_key','private/etc/dropbear/dropbear_rsa_host_key',0o600)
 auth=stage/'private/var/root/.ssh/authorized_keys';auth.parent.mkdir(parents=True);auth.parent.chmod(0o700)
 pub=(WORK/'keys/client_rsa_key.pub').read_text().split();assert pub[0]=='ssh-rsa'
 auth.write_text('no-port-forwarding,no-agent-forwarding,no-X11-forwarding,no-pty,command="/usr/local/bin/j72-recovery-inspect" '+' '.join(pub[:2])+'\n');auth.chmod(0o600)
 p=stage/'private/etc/profile';p.parent.mkdir(parents=True,exist_ok=True);p.write_text('export PATH=/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin\nexport LC_ALL=C\n')
 p=stage/'System/Library/LaunchDaemons/com.apple.restored_external.plist';p.parent.mkdir(parents=True)
 p.write_bytes(plistlib.dumps({'Label':'dev.j72.usb-recovery','ProgramArguments':['/usr/local/bin/j72-usb-recovery'],'RunAtLoad':True,'KeepAlive':True,'POSIXSpawnType':'Interactive','StandardErrorPath':'/dev/console','StandardOutPath':'/dev/console','ThrottleInterval':5}))
 # Disable the other stock jobs in place: catalog deletion is broken in this HFS tool.
 for job in ['com.apple.PurpleReverseProxy.ramdisk','com.apple.ReportCrash.restored','com.apple.syslogd']:
  (p.parent/(job+'.plist')).write_bytes(plistlib.dumps({'Label':job,'Disabled':True,'RunAtLoad':False,'ProgramArguments':['/usr/local/bin/j72-recovery-inspect']}))
 # All startup mutation helpers are omitted; restored_external is replaced by our guarded service.
 for bad in ['usr/bin/mount_filesystems','usr/bin/snaputil','usr/bin/trollstoreinstaller','usr/bin/binbag','sbin/apfs_deletefs']:
  assert not (stage/bad).exists(),bad
 # Keep the original Apple recovery cache, then add every staged ARM64 CodeDirectory.
 raw=(WORK/'restore12.5.7.stock-trustcache').read_bytes();version,n=struct.unpack_from('<I16xI',raw);assert version==1 and len(raw)==24+22*n
 entries={raw[24+i*22:24+(i+1)*22] for i in range(n)};machos=0
 for p in stage.rglob('*'):
  if p.is_symlink() or not p.is_file():continue
  hashes=cdh(p.read_bytes())
  if hashes:machos+=1
  entries.update(h+bytes((t,fl)) for h,t,fl in hashes)
 entries=sorted(entries);body=b''.join(entries);uuid=hashlib.sha256(body).digest()[:16]
 tc=out/'recovery.trustcache';tc.write_bytes(struct.pack('<I',1)+uuid+struct.pack('<I',len(entries))+body)
 ram=out/'ramdisk.hfs';shutil.copyfile(WORK/'restore12.5.7.original.hfs',ram)
 hfs=WORK/'host/hfsplus';run([hfs,ram,'grow','130000000'])
 # Directory-only tar never removes catalog entries. Existing regular files are
 # replaced via add_hfs -> writeToHFSFile, not untar's removeFile path.
 overlay=out/'overlay-dirs.tar'
 with tarfile.open(overlay,'w',format=tarfile.USTAR_FORMAT) as t:
  for p in sorted(stage.rglob('*')):
   if not p.is_dir():continue
   info=t.gettarinfo(str(p),arcname=str(p.relative_to(stage)));info.uid=info.gid=0;info.uname=info.gname='root';t.addfile(info)
 run([hfs,ram,'untar',overlay])
 verified={}
 for p in sorted(stage.rglob('*')):
  if p.is_dir():continue
  assert p.is_file() and not p.is_symlink()
  rel=str(p.relative_to(stage));run([hfs,ram,'add',p,'/'+rel]);run([hfs,ram,'chmod',oct(p.stat().st_mode&0o777)[2:],'/'+rel])
  dest=out/'readback'/rel;dest.parent.mkdir(parents=True,exist_ok=True)
  run([hfs,ram,'extract','/'+rel,dest]);assert dest.read_bytes()==p.read_bytes(),rel
  verified[rel]=sha(dest)
 listing=run([hfs,ram,'ls','/System/Library/LaunchDaemons']).stdout.decode()
 (out/'launchdaemons.txt').write_text(listing)
 enabled=[]
 for p in (out/'readback/System/Library/LaunchDaemons').glob('*.plist'):
  d=plistlib.loads(p.read_bytes())
  if not d.get('Disabled',False):enabled.append(d)
 assert len(enabled)==1 and enabled[0]['Label']=='dev.j72.usb-recovery'
 # Package the UNMODIFIED Apple kernel, plus our RAM-only image and cache.
 ipsw=ROOT/'tools/host/aarch64/bin/ipsw';ticket=WORK/'IM4M7'
 commands={
  'iBSS.img4':['--input',WORK/'iBSS12.5.7.patched','--type','ibss'],
  'iBEC.img4':['--input',WORK/'iBEC12.5.7.patched','--type','ibec'],
  'kernel.img4':['--im4p',f['KernelCache'],'--type','rkrn'],
  'devicetree.img4':['--im4p',f['DeviceTree'],'--type','rdtr'],
  'ramdisk.img4':['--input',ram,'--type','rdsk'],
  'trustcache.img4':['--input',tc,'--type','rtsc']}
 for name,args in commands.items():run([ipsw,'img4','create',*args,'--im4m',ticket,'--output',out/name])
 manifest={'profile':'j72-ios12-ram-recovery-v1','product':'iPad4,2','cpid':0x8960,'bdid':0x12,'ios_build':'16H81','boot':bl,'apple_kernel_patched':False,'automatic_internal_mounts':False,'automatic_storage_writes':False,'ssh_password_auth':False,'ssh_forced_commands':['inspect','reboot'],'staged_files':count,'ramdisk_readback_files':verified,'enabled_launch_jobs':1,'new_macho_files':machos,'trustcache_version':1,'trustcache_entries':len(entries),'runtime_tested':False,'files':{n:sha(out/n) for n in commands},'source_files':{str(p.relative_to(ROOT)):sha(p) for p in (WORK/'readonly-service').rglob('*') if p.suffix in ('.c','.h','.tbd','.plist')},'inputs':{str(p.relative_to(ROOT)):sha(p) for p in [*f.values(),WORK/'IM4M7',WORK/'legacy-ssh64.tar.gz',WORK/'iBSS12.5.7.patched',WORK/'iBEC12.5.7.patched']}}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');check(out);print(json.dumps({'status':'OFFLINE_BUILD_PASS','output':str(out),'trustcache_entries':len(entries),'new_macho_files':machos}))

def check(out):
 m=json.loads((out/'manifest.json').read_text());assert m['profile']=='j72-ios12-ram-recovery-v1'
 assert m['boot']['active_bootargs']==BOOTARGS and not m['apple_kernel_patched'] and not m['automatic_internal_mounts'] and not m['automatic_storage_writes'] and not m['ssh_password_auth']
 for group,base in [('files',out),('inputs',ROOT),('source_files',ROOT)]:
  for f,h in m[group].items():assert sha(base/f)==h,f
 assert firmware() and bootloaders()==m['boot']
 return m

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['build','check']);p.add_argument('--output',type=Path,default=WORK/'capsule-v1');a=p.parse_args()
 if a.action=='build':build(a.output.resolve())
 else:check(a.output.resolve());print('PASS exact-J72 private recovery inputs, bootargs, component and source hashes; no USB access')
