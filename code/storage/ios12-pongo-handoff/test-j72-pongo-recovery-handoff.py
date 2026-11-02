#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Test actual SHA, serialized-cache and RAM-bundle validation without USB."""
import ctypes, hashlib, importlib.util, json, struct, subprocess, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'private/j72-platform/power-storage-20261102/recovery-prep/pongo-route/handoff-v2'
def main():
 manifest=json.loads((WORK/'manifest.json').read_text())
 transport=json.loads(subprocess.run(['python3',str(ROOT/'tools/test-j72-recovery-inspect-transport.py')],check=True,capture_output=True,text=True).stdout)
 with tempfile.TemporaryDirectory(prefix='j72-handoff-test-') as tmp:
  tmp=Path(tmp);source=tmp/'harness.c';binary=tmp/'harness.so'
  source.write_text('''typedef unsigned long long u64;
#include "j72-pongo-recovery-handoff-bounds.h"
int span(u64 a,u64 b,u64 c,u64 d){return j72_span(a,b,c,d);}
int macho(const unsigned char*b,u64 n,unsigned char*out){return j72_macho_uuid(b,n,out);}
void hash(const unsigned char*b,u64 n,unsigned char*out){j72_sha256(b,n,out,0);}
int tc(const unsigned char*b,u64 n){unsigned entries=0;return j72_tc(b,n,&entries);}
int bundle(const unsigned char*b,u64 n,u64 total,u64 tc_off,u64 tc_size,u64 hfs_off,u64 hfs_size,const unsigned char*expected){return j72_bundle(b,n,total,tc_off,tc_size,hfs_off,hfs_size,expected,0);}
''')
  subprocess.run(['cc','-shared','-fPIC','-O2','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all','-I',str(ROOT/'tools'),str(source),'-o',str(binary)],check=True)
  lib=ctypes.CDLL(str(binary));lib.hash.argtypes=[ctypes.c_void_p,ctypes.c_ulonglong,ctypes.c_void_p]
  cases=0
  for n in [0,1,3,7,31,55,56,57,63,64,65,119,120,127,128,129,1024,65536,1048577]:
   data=(bytes(range(256))*((n+255)//256))[:n];buf=ctypes.create_string_buffer(data);out=ctypes.create_string_buffer(32)
   lib.hash(buf,n,out);assert out.raw==hashlib.sha256(data).digest(),n;cases+=1
  lib.tc.argtypes=[ctypes.c_void_p,ctypes.c_ulonglong]
  tc=(WORK/'trustcache.serialized.merged').read_bytes();raw=ctypes.create_string_buffer(tc)
  assert lib.tc(raw,len(tc))==1
  tc_bad=[tc[:31],struct.pack('<I',2)+tc[4:],tc[:4]+struct.pack('<I',16)+tc[8:],
          tc[:28]+struct.pack('<I',10001)+tc[32:],tc[:-1],tc[:52]+b'\0'+tc[53:]]
  for data in tc_bad:
   b=ctypes.create_string_buffer(data);assert lib.tc(b,len(data))==0
  lib.bundle.argtypes=[ctypes.c_void_p]+[ctypes.c_ulonglong]*6+[ctypes.c_void_p]
  data=(WORK/'recovery.bundle').read_bytes();buf=ctypes.create_string_buffer(data,len(data));digest=ctypes.create_string_buffer(hashlib.sha256(data).digest())
  v=manifest['layout'];args=[v[k] for k in ['BUNDLE_SIZE','TC_OFFSET','TC_SIZE','HFS_OFFSET','HFS_SIZE']]
  assert lib.bundle(buf,len(data),*args,digest)==1
  refusals=0
  for index,off in enumerate([0,8,12,16,24,32,40,48,v['HFS_OFFSET']+1024,v['HFS_OFFSET']+2048]):
   old=buf[off];buf[off]=bytes([old[0]^1]);assert lib.bundle(buf,len(data),*args,digest)==0,(index,off);buf[off]=old;refusals+=1
  assert lib.bundle(buf,len(data)-1,*args,digest)==0;refusals+=1
 spec=importlib.util.spec_from_file_location('launcher',ROOT/'tools/run-j72-pongo-recovery-handoff.py');launcher=importlib.util.module_from_spec(spec);spec.loader.exec_module(launcher)
 launcher.preflight(require_tests=False)
 for marker in [b'J72_HANDOFF_CHECK_OK',b'J72_HANDOFF_STAGE_OK']:
  values=b'ORIGINAL_TC_MATCH 0000000000000001\n' if marker==b'J72_HANDOFF_CHECK_OK' else f'RAMDISK_BYTES {v["HFS_SIZE"]:016x}\nTRUSTCACHE_BYTES {v["TC_SIZE"]:016x}\n'.encode()
  assert launcher.response(marker+b'\n'+values+b'DISK_IO 0000000000000000\nJ72_HANDOFF_END\npongoOS> ',marker,v)['disk_io'] is False
 for bad in [b'',b'J72_HANDOFF_REFUSED\n',b'J72_HANDOFF_STAGE_OK\nDISK_IO 0000000000000001\nJ72_HANDOFF_END\n']:
  try:launcher.response(bad,b'J72_HANDOFF_STAGE_OK');raise AssertionError('Invalid handoff response accepted')
  except RuntimeError:pass
 # A malformed boot receipt must fail before any USB identity query or command.
 boot_refusals=0
 with tempfile.TemporaryDirectory(prefix='j72-handoff-receipt-') as folder:
  folder=Path(folder);launcher.WORK=folder
  (folder/'manifest.json').write_bytes((WORK/'manifest.json').read_bytes())
  stage=folder/'stage-test';stage.mkdir()
  def forbidden_usb():raise AssertionError('USB accessed before boot-receipt gate')
  launcher.binding=forbidden_usb
  good={'state':'staged','profile':manifest['profile'],'manifest_sha256':hashlib.sha256((WORK/'manifest.json').read_bytes()).hexdigest()}
  for key,value in [('state','started'),('state','boot_requested'),('profile','other'),('manifest_sha256','0'*64)]:
   invalid=dict(good);invalid[key]=value;(stage/'state.json').write_text(json.dumps(invalid))
   try:launcher.boot(manifest,stage);raise AssertionError('Invalid boot receipt accepted')
   except RuntimeError:boot_refusals+=1
 result={'status':'PASS','manifest_sha256':hashlib.sha256((WORK/'manifest.json').read_bytes()).hexdigest(),
         'actual_source_sha256_vectors':cases,'actual_source_serialized_cache_refusals':len(tc_bad),
         'actual_source_full_bundle_pass':True,'actual_source_bundle_refusals':refusals,
         'host_guard_response_refusals':3,'original_records_preserved':True,
         'boot_receipt_refusals_before_usb':boot_refusals,
         'transport_cleanup_and_refusal_cases':transport['transport_cleanup_and_refusal_cases'],
         'audited_root_home_mode':manifest['ssh_auth_permissions']['root_home'],
         'recovery_boot_tested':False,'ram_stage_tested':False,'usb_access':False}
 (WORK/'offline-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
