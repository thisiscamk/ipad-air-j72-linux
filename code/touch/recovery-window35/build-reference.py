#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build a separate #35 touch recovery-window candidate; no device access."""
import hashlib,json,os,shutil,subprocess,difflib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'private/j72-platform/power-storage-20261102'
BASE=WORK/'desktop-storage35/modules/touch'
OUT=WORK/'touch-recovery-window35'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 os.umask(0o077)
 assert not OUT.exists(),'Refuse existing candidate'
 pins=json.loads((WORK/'desktop-storage35/module-inputs.json').read_text())['kernel_base_files']
 for p,h in pins.items():assert sha(ROOT/p)==h,p
 result=json.loads((WORK/'desktop-storage35/module-result.json').read_text())
 assert sha(BASE/'j72_touch_session.ko')==result['modules']['touch/j72_touch_session.ko']['sha256']
 OUT.mkdir();mod=OUT/'module';mod.mkdir()
 for p in BASE.iterdir():
  if p.suffix in ('.c','.h','.inc') and not p.name.endswith('.mod.c'):shutil.copyfile(p,mod/p.name)
 for p in (ROOT/'tools/touch-recovery-window35').iterdir():shutil.copyfile(p,mod/p.name)
 source=mod/'j72_touch_session.c';old=source.read_text();s=old
 s=s.replace('#include "j72-classic-contacts.h"','#include "j72-classic-contacts.h"\n#include "j72-recovery-window.h"',1)
 s=s.replace('module_param(cleanup_ok,bool,0400);','''module_param(cleanup_ok,bool,0400);
/* Report physical restoration separately without weakening cleanup_ok/state4. */
static bool hardware_cleanup_ok;
module_param(hardware_cleanup_ok,bool,0400);
static unsigned int recovery_stop_reason;
module_param(recovery_stop_reason,uint,0400);
MODULE_PARM_DESC(recovery_stop_reason,"0=none 1=budget 2=info 3=status 4=gate");''',1)
 s=s.replace('u64 start,last_wake=0;unsigned long end;','u64 start,last_wake=0;unsigned long end;\n struct j72_recovery_window recovery_window={0};',1)
 before='''   if(++input_recoveries>6 || !read_device_info(dev) ||
      !short_report(dev,0x7f,4,status) || memchr_inv(status,0,4) ||
      !short_report(dev,0xc8,1,&gate) || gate!=0x19){stopped=true;break;}'''
 after='''   input_recoveries++;
   /* Finite diagnostic runs retain their original cumulative limit.
    * Continuous input uses a bounded sliding window: sparse recovered
    * transients must not exhaust a lifetime quota. All health gates remain. */
   if((READ_ONCE(continuous) &&
       !j72_recovery_admit(&recovery_window,ktime_get_ns()/1000000ULL)) ||
      (!READ_ONCE(continuous) && input_recoveries>6))recovery_stop_reason=1;
   else if(!read_device_info(dev))recovery_stop_reason=2;
   else if(!short_report(dev,0x7f,4,status) || memchr_inv(status,0,4))recovery_stop_reason=3;
   else if(!short_report(dev,0xc8,1,&gate) || gate!=0x19)recovery_stop_reason=4;
   if(recovery_stop_reason){
    pr_err("j72_touch_session: INPUT_RECOVERY_STOP count=%u reason=%u window_ms=60000\\n",
           input_recoveries,recovery_stop_reason);
    stopped=true;break;
   }'''
 assert s.count(before)==1;s=s.replace(before,after,1)
 s=s.replace('attempted=false;cleanup_failed=false;cleanup_ok=false;','attempted=false;cleanup_failed=false;cleanup_ok=false;\n  hardware_cleanup_ok=false;recovery_stop_reason=0;',1)
 needle='  if(ret || !attempted || audit.done!=1 || !audit.info_end || cleanup_failed){'
 assert s.count(needle)==1;s=s.replace(needle,'  hardware_cleanup_ok=!ret && attempted && audit.info_end && !cleanup_failed;\n'+needle,1)
 source.write_text(s)
 (mod/'Makefile').write_text('obj-m := j72_touch_session.o\n')
 patch=''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='a/j72_touch_session.c',tofile='b/j72_touch_session.c'))
 (OUT/'recovery-window.patch').write_text(patch)
 with (OUT/'host-tests.log').open('wb') as log:
  subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=undefined,bounds','-fno-sanitize-recover=all',str(mod/'test-recovery-window.c'),'-o',str(OUT/'test-window')],check=True,stdout=log,stderr=subprocess.STDOUT)
  subprocess.run([str(OUT/'test-window')],check=True,stdout=log,stderr=subprocess.STDOUT)
  subprocess.run(['python3',str(ROOT/'tools/touch-recovery-window35/test-integration.py'),str(source)],check=True,stdout=log,stderr=subprocess.STDOUT)
 with (OUT/'build.log').open('wb') as log:
  subprocess.run(['make','-C',str(WORK/'storage-kernel/src'),'O='+str(WORK/'storage-kernel/out'),'ARCH=arm64','M='+str(mod),'-j2','W=1','modules'],check=True,stdout=log,stderr=subprocess.STDOUT)
 exports={l.split()[1] for l in (WORK/'storage-kernel/out/Module.symvers').read_text().splitlines() if l.split()[2]=='vmlinux'}
 imports={l.split()[1] for l in subprocess.check_output(['nm','-u',str(mod/'j72_touch_session.ko')],text=True).splitlines() if l.split()[0]=='U'}
 assert not imports-exports,imports-exports
 assert subprocess.check_output(['modinfo','-F','vermagic',str(mod/'j72_touch_session.ko')],text=True).strip()=='7.0.12-j72spi2 SMP preempt aarch64'
 for p,h in pins.items():assert sha(ROOT/p)==h,p
 m=dict(status='OFFLINE_BUILD_TESTS_IMPORTS_PASS_DEVICE_UNTESTED',uts_version='#35 SMP PREEMPT Mon Nov 2 07:00:00 +08 2026',module_sha256=sha(mod/'j72_touch_session.ko'),base_source_sha256=sha(BASE/'j72_touch_session.c'),source_sha256=sha(source),module_strong_imports=len(imports),kernel_files_unchanged=True,device_access=False,storage_writes=False,continuous_max_recoveries=6,continuous_window_ms=60000,finite_diagnostic_budget_unchanged=True,cleanup_api_failure_guard_unchanged=True,files={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'tools/touch-recovery-window35/j72-recovery-window.h',ROOT/'tools/touch-recovery-window35/test-recovery-window.c',ROOT/'tools/touch-recovery-window35/test-integration.py',ROOT/'tools/run-j72-touch-recovery35.py',source,mod/'j72-recovery-window.h',OUT/'recovery-window.patch']})
 (OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
 print('PASS: #35 candidate built; bounded-window host cases and import closure pass; original kernel/module untouched; device untested')
if __name__=='__main__':main()
