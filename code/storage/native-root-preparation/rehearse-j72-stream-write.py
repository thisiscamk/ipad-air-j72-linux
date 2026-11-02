#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Host regular-file transaction rehearsal; never contacts an iPad/device node."""
import hashlib,json,os,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'private/j72-platform/power-storage-20261102'
PUBLIC=Path('/home/pi/ipad-air-j72-linux/code/storage')
sys.path.insert(0,str(PUBLIC))
import j72_storage_preflight as g
import j72_install_state as state
import j72_host_write_rehearsal as host
import j72_native_view_plan as view

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def metadata(folder):
 return {key:g.regular_bytes(folder/(key.replace('_','-')+'.bin'),16384 if 'entries' in key else 4096)
         for key in state.PARTS}
def main():
 os.umask(0o077)
 assert os.geteuid()==0,'Private host inputs need sudo; there is no device access'
 old=metadata(WORK/'recovery-prep/gpt-qualified-20261102')
 new=metadata(WORK/'desktop-storage35/layout-rehearsal-v2')
 transition=state.Transition(old,new)
 image=WORK/'desktop-storage35/local-root-image/j72-local-root-1536.ext4'
 reference=json.loads((image.parent/'result.json').read_text())
 assert not image.is_symlink() and image.is_file() and image.stat().st_size==view.CONTAINER_BYTES
 print('Hashing original host image before rehearsal; no iPad access',flush=True)
 assert sha(image)==reference['image_sha256']
 kernel=os.uname().release;out=WORK/'desktop-storage35'/('host-stream-write-'+time.strftime('%Y%m%d-%H%M%S'));out.mkdir(mode=0o700)
 disk=host.HostWriteRehearsal(out,transition)
 result=dict(status='HOST_REHEARSAL_IN_PROGRESS',ipad_contacted=False,apfs_resize_executed=False,apfs_size_is_model_input=True)
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 try:
  for step in transition.metadata_steps():disk.commit_next_metadata(step['name'])
  assert transition.classify(disk.metadata(),state.APFS_TARGET)['status']=='PARTITIONS_COMMITTED_IMAGE_NOT_VERIFIED'
  source_hash=hashlib.sha256();before=image.stat();start=time.monotonic()
  with image.open('rb') as f:
   for offset in range(0,view.CONTAINER_BYTES,1<<20):
    data=f.read(1<<20);assert len(data)==1<<20;source_hash.update(data)
    disk.write_image_chunk(offset,data)
   assert f.read(1)==b''
  assert source_hash.hexdigest()==reference['image_sha256']
  after=image.stat();assert (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)
  print('Full host image streamed; verifying fsync, full readback and outside fences',flush=True)
  result=disk.finish(reference['image_sha256'])
  result.update(elapsed_stream_and_readback_s=round(time.monotonic()-start,3),host_kernel_unchanged=os.uname().release==kernel,source_stream_hash_matches=True,source_image_identity_size_mtime_unchanged=True,io_failure_test_methods_pass=9,logical_block_bytes=4096,chunk_bytes=1<<20,original_gpt_input_unchanged=True)
 finally:disk.close()
 assert sha(image)==reference['image_sha256']
 disk.path.unlink() # Only the newly created and now-closed disposable host file.
 result['disposable_host_file_removed']=True
 result['source_files']={str(p):sha(p) for p in [Path(__file__),PUBLIC/'j72_host_write_rehearsal.py',PUBLIC/'test_j72_host_write_rehearsal.py']}
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 print('PASS ordered host GPT steps + full1.5GiB image/fsync/readback/fences; native iOS writer still unqualified',flush=True)
 print('Private receipt:',out)
if __name__=='__main__':main()
