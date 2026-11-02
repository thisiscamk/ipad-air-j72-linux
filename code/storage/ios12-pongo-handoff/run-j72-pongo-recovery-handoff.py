#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Preflight, stage RAM-only recovery, or boot a separately verified RAM stage."""
import argparse, ctypes as C, fcntl, hashlib, importlib.util, json, os, re, time
from pathlib import Path
from j72_pongo_control import PongoControl
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'private/j72-platform/power-storage-20261102/recovery-prep/pongo-route/handoff-v3'
def load(name,file):
 s=importlib.util.spec_from_file_location(name,file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def preflight(require_tests=True):
 manifest=json.loads((WORK/'manifest.json').read_text())
 if manifest['profile']!='j72-pongo-ram-recovery-handoff-v3' or manifest.get('capsule_revision')!=3 or manifest['kernel_patched'] or manifest['automatic_internal_mounts'] or manifest['internal_storage_write_interface']:raise RuntimeError('Unsafe handoff profile')
 if manifest.get('root_identity_guard')!='hfs-root-flag-md0-device-match-no-apfs':raise RuntimeError('Missing RAM device identity guard')
 if manifest.get('ssh_auth_permissions',{}).get('root_home')!=0o700:raise RuntimeError('Root SSH home permissions not audited')
 if manifest['bootargs']!='rd=md0 debug=0x2014e -v wdt=-1':raise RuntimeError('RAM-root boot-argument mismatch')
 for name,digest in manifest['files'].items():
  if sha(ROOT/name)!=digest:raise RuntimeError('RAM handoff input/source pin mismatch: '+name)
 if require_tests:
  result=json.loads((WORK/'offline-result.json').read_text())
  if result['status']!='PASS' or result['manifest_sha256']!=sha(WORK/'manifest.json'):raise RuntimeError('No matching completed offline checks')
 print('PASS offline: exact RAM capsule, original kernel, merged trust cache and handoff pins; no USB access',flush=True)
 return manifest
def response(raw,marker,layout=None):
 clean=raw.replace(b'\r',b'')
 if len(clean)>1024 or b'REFUSED' in clean or clean.count(marker)!=1 or clean.count(b'J72_HANDOFF_END')!=1 or b'DISK_IO 0000000000000000\n' not in clean:raise RuntimeError('RAM handoff guard/postcondition refused')
 fields={}
 for row in clean.split(marker+b'\n',1)[1].split(b'J72_HANDOFF_END',1)[0].splitlines():
  match=re.fullmatch(rb'([A-Z_]+) ([0-9a-f]{16})',row)
  if not match or match[1].decode() in fields:raise RuntimeError('Invalid or duplicate handoff scalar')
  fields[match[1].decode()]=int(match[2],16)
 required={'ORIGINAL_TC_MATCH','DISK_IO'} if marker==b'J72_HANDOFF_CHECK_OK' else {'RAMDISK_BYTES','TRUSTCACHE_BYTES','DISK_IO'}
 if set(fields)!=required or fields['DISK_IO']!=0:raise RuntimeError('Incomplete handoff response')
 if marker==b'J72_HANDOFF_CHECK_OK' and fields['ORIGINAL_TC_MATCH']!=1:raise RuntimeError('Original trust cache mismatch')
 if layout is not None and marker==b'J72_HANDOFF_STAGE_OK' and (fields['RAMDISK_BYTES']!=layout['HFS_SIZE'] or fields['TRUSTCACHE_BYTES']!=layout['TC_SIZE']):raise RuntimeError('Staged lengths differ from pinned image')
 return {'guard_marker':marker.decode(),'disk_io':False,'values':fields}
class HandoffClient(PongoControl):
 def handoff(self,line,marker):
  if line not in (b'j72rescuecheck',b'j72rescuestage',b'j72rescuestatus'):raise ValueError('Not a guarded handoff command')
  self.control(0x21,4,0)
  buf=C.create_string_buffer(line+b'\n')
  n=self.usb.libusb_control_transfer(self.handle,0x21,3,0,0,buf,len(line)+1,45000)
  if n!=len(line)+1:raise RuntimeError('Synchronous handoff command failed: '+str(n))
  data=self._drain(time.monotonic()+10)
  if b'pongoOS> ' not in data:raise RuntimeError('Handoff did not return to Pongo prompt')
  response(data,marker,json.loads((WORK/'manifest.json').read_text())['layout']);return data
 def bundle(self,data):
  if len(data)!=json.loads((WORK/'manifest.json').read_text())['layout']['BUNDLE_SIZE'] or not 0<len(data)<=0x8000000:raise RuntimeError('Wrong RAM bundle size')
  self.control(0x21,1,data=len(data).to_bytes(4,'little'))
  buf=C.create_string_buffer(data,len(data))
  for off in range(0,len(data),0x800000):
   size=min(0x800000,len(data)-off);done=C.c_int()
   result=self.usb.libusb_bulk_transfer(self.handle,2,C.byref(buf,off),size,C.byref(done),5000)
   if result or done.value!=size:raise RuntimeError('RAM bundle upload incomplete; no boot requested')
  time.sleep(.1)
def binding():
 compact=load('compact',ROOT/'tools/run-j72-pongo-recovery-compact.py')
 return compact.target_binding()
def stage(manifest):
 with (ROOT/'private/j72-usb.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);device=binding()
  once=WORK/('session-'+device+'.json')
  if once.exists():raise RuntimeError('RAM handoff already attempted in this USB session')
  out=WORK/('stage-'+time.strftime('%Y%m%d-%H%M%S'));out.mkdir(mode=0o700)
  receipt={'profile':manifest['profile'],'binding':device,'manifest_sha256':sha(WORK/'manifest.json'),'state':'started'}
  def save(state):receipt['state']=state;(out/'state.json').write_text(json.dumps(receipt,indent=2)+'\n');once.write_text(json.dumps(receipt)+'\n')
  with (out/'console.log').open('wb') as log,HandoffClient(log) as client:
   client.synchronize();listing=client.command(b'help',b'shows this help message')
   if b'j72rescue' in listing:raise RuntimeError('Fresh Pongo required; no replacement module upload')
   save('module_upload_started');client.upload_module((WORK/'j72-recovery-handoff.kext').read_bytes())
   client.command(b'modload',b'Loaded module j72_recovery_handoff')
   client.handoff(b'j72rescuecheck',b'J72_HANDOFF_CHECK_OK');save('guards_passed')
   print('PASS live original kernel/cache and RAM guards; uploading RAM recovery bundle.',flush=True)
   client.bundle((WORK/'recovery.bundle').read_bytes());save('bundle_uploaded')
   client.handoff(b'j72rescuestage',b'J72_HANDOFF_STAGE_OK')
   client.handoff(b'j72rescuestatus',b'J72_HANDOFF_STAGE_OK');save('staged')
  print('PASS RAM staging and independent postcondition read; no boot or disk I/O requested.',flush=True)
  print('Private staged receipt:',out,flush=True)
def boot(manifest,folder):
 folder=folder.resolve()
 if folder.parent!=WORK or not folder.name.startswith('stage-'):raise RuntimeError('Stage receipt outside this candidate')
 receipt=json.loads((folder/'state.json').read_text())
 if receipt.get('state')!='staged' or receipt.get('profile')!=manifest['profile'] or receipt.get('manifest_sha256')!=sha(WORK/'manifest.json'):raise RuntimeError('No valid staged RAM receipt')
 with (ROOT/'private/j72-usb.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  if binding()!=receipt['binding']:raise RuntimeError('Pongo USB session changed after staging')
  with (folder/'preboot.log').open('xb') as log,HandoffClient(log) as client:
   client.synchronize();client.handoff(b'j72rescuestatus',b'J72_HANDOFF_STAGE_OK')
   receipt['state']='boot_requested';(folder/'state.json').write_text(json.dumps(receipt,indent=2)+'\n')
   client.control(0x21,4,0xffff)
   try:client.control(0x21,3,data=b'bootux\n')
   except RuntimeError:pass # USB teardown is possible; only the recovery marker proves boot.
 # The inspection helper owns the same USB lock while temporarily running
 # usbmuxd without normal-iOS lockdownd preflight. Release this lock first.
 inspect=load('restricted_recovery_transport',ROOT/'tools/j72-recovery-inspect-live.py')
 inspect.inspect_live(folder)
 receipt['state']='recovery_inspected';(folder/'state.json').write_text(json.dumps(receipt,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);mode=p.add_mutually_exclusive_group();mode.add_argument('--stage',action='store_true');mode.add_argument('--boot-staged',type=Path);a=p.parse_args()
 os.umask(0o077);m=preflight()
 if a.stage or a.boot_staged:
  if os.geteuid()!=0:raise RuntimeError('Use sudo for the guarded hardware step')
  if a.stage:stage(m)
  else:boot(m,a.boot_staged)
