#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Measure a private compressed desktop root; no iPad access or installation."""
import fcntl, hashlib, json, os, subprocess, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'private/j72-platform/power-storage-20261102/compressed-root-prep'
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def main():
 if os.geteuid()!=0:raise RuntimeError('Use sudo for the private read-only host loop mount')
 os.umask(0o077)
 with (ROOT/'private/j72-image-build.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  baseline=json.loads((ROOT/'private/j72-touch/integrated-session/manifest.json').read_text())
  source=Path(baseline['desktop_image']);out=WORK/'desktop-capacity.squashfs';mnt=WORK/'source-ro'
  if out.exists():raise RuntimeError('Refuse existing capacity artifact')
  mnt.mkdir(mode=0o700,exist_ok=True)
  if list(mnt.iterdir()) or subprocess.run(['mountpoint','-q',str(mnt)]).returncode==0:raise RuntimeError('Host build mountpoint is occupied')
  mk=WORK/'host/root/usr/bin/mksquashfs';un=WORK/'host/root/usr/bin/unsquashfs'
  expected={'mksquashfs':'76f38d648a9c82b6866565cfa570e805d1ac66186427cf88601a9d3c78c864ff','unsquashfs':'6757568c8ff82e0496d48c23f2ded127f7d1dcb40ce7f544ddb1b5d73b3ef0f2'}
  for p in [mk,un]:
   if sha(p)!=expected[p.name]:raise RuntimeError('Native host-tool pin mismatch')
  print('Checking original desktop image pin before read-only mount.',flush=True)
  if sha(source)!=baseline['desktop_sha256']:raise RuntimeError('Desktop baseline image mismatch')
  started=time.monotonic();mounted=False;verified={}
  try:
   subprocess.run(['mount','-t','ext4','-o','loop,ro,noload,nodev,nosuid,noexec',str(source),str(mnt)],check=True,timeout=15);mounted=True
   rows=[r.split() for r in Path('/proc/self/mounts').read_text().splitlines() if r.split()[1]==str(mnt)]
   if len(rows)!=1 or rows[0][2]!='ext4' or 'ro' not in rows[0][3].split(','):raise RuntimeError('Source host mount is not read-only ext4')
   print('Building private gzip SquashFS from the read-only baseline; two workers, 256MiB cache.',flush=True)
   with (WORK/'build.log').open('wb') as log:
    subprocess.run([str(mk),str(mnt),str(out),'-comp','gzip','-b','262144','-processors','2','-mem','256M','-noappend','-no-progress','-mkfs-time','1793577600'],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=1800)
   subprocess.run([str(un),'-s',str(out)],stdout=subprocess.DEVNULL,check=True,timeout=15)
   for rel in ['usr/lib/os-release','usr/bin/bash','usr/bin/foot','usr/bin/labwc','usr/bin/quickshell']:
    original=mnt/rel
    if original.is_symlink() or not original.is_file():continue
    r=subprocess.run([str(un),'-cat',str(out),rel],capture_output=True,check=True,timeout=30)
    expected_sha=sha(original)
    if hashlib.sha256(r.stdout).hexdigest()!=expected_sha:raise RuntimeError('Compressed file readback mismatch: '+rel)
    verified[rel]=expected_sha
   if len(verified)<3:raise RuntimeError('Insufficient desktop executable readbacks')
  finally:
   if mounted:subprocess.run(['umount',str(mnt)],check=True,timeout=15)
  size=out.stat().st_size
  result={'status':'OFFLINE_CAPACITY_PASS','source_desktop_sha256':baseline['desktop_sha256'],'source_bytes':source.stat().st_size,'source_mounted_read_only':True,'compression':'gzip','block_bytes':262144,'compressed_bytes':size,'compressed_sha256':sha(out),'selected_files_read_back':verified,'fits_1536_mib_artifact_budget':size<1536*1024**2,'available_apfs_shrink_bytes':1642352640,'remaining_bytes_before_partition_and_overlay_overhead':1642352640-size,'elapsed_seconds':round(time.monotonic()-started,2),'device_access':False,'device_installed':False,'boot_tested':False,'runtime_overrides_integrated':False,'source_unmounted':True}
  (WORK/'result.json').write_text(json.dumps(result,indent=2)+'\n')
  print(json.dumps({k:v for k,v in result.items() if k not in ('source_desktop_sha256','compressed_sha256','selected_files_read_back')}),flush=True)
if __name__=='__main__':main()
