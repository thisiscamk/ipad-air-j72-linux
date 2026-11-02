#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build the same guarded RAM capsule with audited SSH directory permissions."""
import argparse, importlib.util, json, os, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'private/j72-platform/power-storage-20261102/recovery-prep'
DEFAULT=BASE/'capsule-v2'
def original():
 s=importlib.util.spec_from_file_location('original_capsule',ROOT/'tools/prepare-j72-ios-recovery.py')
 m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def permissions(folder):
 image=original();hfs=BASE/'host/hfsplus';ram=folder/'ramdisk.hfs'
 checks=[('/private/var','root',0o40700),('/private/var/root','.ssh',0o40700),
         ('/private/var/root/.ssh','authorized_keys',0o100600),('/private/etc','dropbear',0o40700),
         ('/private/etc/dropbear','dropbear_rsa_host_key',0o100600)]
 for parent,name,mode in checks:
  listing=image.run([hfs,ram,'ls',parent]).stdout.decode()
  rows=[line.split() for line in listing.splitlines() if line.split() and line.split()[-1]==name]
  if len(rows)!=1 or int(rows[0][0],8)!=mode or rows[0][1:3]!=['0','0']:raise RuntimeError('SSH ownership/mode mismatch: '+parent+'/'+name)
 return {'root_home':0o700,'ssh_directory':0o700,'authorized_keys':0o600,'host_key_directory':0o700,'host_key':0o600,'owner_uid':0,'owner_gid':0}
def check(folder):
 m=original().check(folder)
 if m.get('capsule_revision')!=2 or m.get('ssh_auth_permissions')!=permissions(folder):raise RuntimeError('Missing audited SSH permission revision')
 return m
def build(folder):
 os.umask(0o077);image=original();extract=image.filtered_tar
 def secure_stage(stage):
  count=extract(stage)
  for rel,mode in [('private',0o755),('private/var',0o755),('private/etc',0o755),('private/var/root',0o700),('private/etc/dropbear',0o700)]:
   path=stage/rel;path.mkdir(parents=True,exist_ok=True);path.chmod(mode)
  return count
 image.filtered_tar=secure_stage;image.build(folder)
 m=json.loads((folder/'manifest.json').read_text());m['capsule_revision']=2;m['ssh_auth_permissions']=permissions(folder)
 m['source_files'][str(Path(__file__).resolve().relative_to(ROOT))]=image.sha(Path(__file__))
 (folder/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');check(folder)
 print('PASS capsule-v2: root home/.ssh/host-key directory0700; key files0600; owner0:0')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['build','check']);p.add_argument('--output',type=Path,default=DEFAULT);a=p.parse_args()
 if a.action=='build':build(a.output.resolve())
 else:check(a.output.resolve());print('PASS audited RAM SSH permissions and existing capsule pins; no USB access')
