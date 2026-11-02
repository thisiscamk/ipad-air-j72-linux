#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build a separate audited RAM capsule with strict device-based root checks."""
import argparse, importlib.util, json, os, shutil, subprocess, types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'private/j72-platform/power-storage-20261102/recovery-prep'
DEFAULT=BASE/'capsule-v3'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def previous():return load('permissions_builder',ROOT/'tools/prepare-j72-ios-recovery-v2.py')
def check(folder):
 old=previous();m=old.original().check(folder)
 if m.get('capsule_revision')!=3 or m.get('ssh_auth_permissions')!=old.permissions(folder):raise RuntimeError('Wrong audited capsule revision')
 if m.get('root_identity_guard')!='hfs-root-flag-md0-device-match-no-apfs':raise RuntimeError('Missing strict RAM device identity guard')
 return m
def build(folder):
 if folder.exists():raise RuntimeError('Refuse existing revision3 output')
 os.umask(0o077);old=previous();image=old.original();builddir=BASE/'readonly-service-v3';builddir.mkdir(exist_ok=True)
 stub=builddir/'libSystem.tbd'
 stub.write_text((BASE/'readonly-service/libSystem.tbd').read_text().replace('_printf,','_printf, _stat64, _memcpy, _memset,'))
 binary=builddir/'j72-recovery-inspect';obj=builddir/'j72-recovery-inspect.o'
 env=os.environ.copy();env['LD_LIBRARY_PATH']=str(ROOT/'private/j72-touch/runtime/usr/lib/aarch64-linux-gnu')
 with (builddir/'build.log').open('wb') as log:
  commands=[['/usr/bin/clang','-target','arm64-apple-ios12.0','-O2','-ffreestanding','-fno-builtin','-fno-stack-protector','-Wall','-Wextra','-Werror','-c',str(ROOT/'tools/j72-recovery-inspect-v3.c'),'-o',str(obj)],
   [str(ROOT/'private/j72-touch/ld64-arm64'),'-arch','arm64','-platform_version','ios','12.0','12.0','-e','_main','-L',str(builddir),'-lSystem','-o',str(binary),str(obj)],
   [str(BASE/'ldid-src/ldid'),'-S'+str(BASE/'readonly-service/inspect-entitlements.plist'),str(binary)]]
  for args in commands:subprocess.run(args,stdout=log,stderr=log,check=True,env=env,timeout=45)
 assert image.cdh(binary.read_bytes()),'new inspector signature invalid'
 # Redirect only the one inspector payload. All firmware, service and original
 # builder inputs stay fixed; permission auditing uses the preceding builder.
 def copyfile(src,dst,*args,**kwargs):
  if Path(src)==BASE/'readonly-service/j72-recovery-inspect':src=binary
  return shutil.copyfile(src,dst,*args,**kwargs)
 image.shutil=types.SimpleNamespace(copyfile=copyfile);old.original=lambda:image
 old.build(folder)
 m=json.loads((folder/'manifest.json').read_text());m['capsule_revision']=3
 m['root_identity_guard']='hfs-root-flag-md0-device-match-no-apfs'
 m['ssh_forced_commands']=['inspect','diagnose','reboot']
 sources=[ROOT/'tools'/n for n in ['prepare-j72-ios-recovery-v3.py','j72-recovery-inspect-v3.c','j72-recovery-mount-guard.h','j72-recovery-guard.h','test-j72-recovery-mount-guard.py']]
 for p in sources+[binary,stub,ROOT/'private/j72-touch/ld64-arm64',BASE/'ldid-src/ldid']:
  m['source_files'][str(p.relative_to(ROOT))]=image.sha(p)
 (folder/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');check(folder)
 print('PASS capsule-v3: signed inspector, HFS readback, root/device guard and SSH permissions; no USB access')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['build','check']);p.add_argument('--output',type=Path,default=DEFAULT);a=p.parse_args()
 if a.action=='build':build(a.output.resolve())
 else:check(a.output.resolve());print('PASS revision3 capsule/source/permission pins; no USB access')
