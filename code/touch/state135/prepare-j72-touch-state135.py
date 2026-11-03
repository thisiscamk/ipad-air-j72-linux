#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build a separate state-1 inactive candidate; preserve sealed prior inputs."""
import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'private/j72-platform/power-storage-20261102'
BASE=WORK/'touch-data-resync35'
OUT=WORK/'touch-state135'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def replace(s,before,after):
    assert s.count(before)==1,before
    return s.replace(before,after,1)
def main():
    os.umask(0o077)
    assert not OUT.exists(),'Preserve existing candidate'
    pins=json.loads((BASE/'manifest.json').read_text())
    for name,digest in pins['files'].items():assert sha(ROOT/name)==digest,name
    assert sha(BASE/'module/j72_touch_session.ko')==pins['module_sha256']
    kernel=json.loads((WORK/'desktop-storage35/module-inputs.json').read_text())['kernel_base_files']
    for name,digest in kernel.items():assert sha(ROOT/name)==digest,name
    OUT.mkdir();mod=OUT/'module';mod.mkdir()
    for p in (BASE/'module').iterdir():
        if p.suffix in ('.c','.h','.inc') and not p.name.endswith('.mod.c'):shutil.copyfile(p,mod/p.name)
    header=mod/'j72-classic-contacts.h';original_header=header.read_text()
    header.write_text(replace(original_header,'c[1]!=0 && c[1]!=3','c[1]!=0 && c[1]!=1 && c[1]!=3'))
    source=mod/'j72_touch_session.c';before=source.read_text()
    s=replace(before,'static bool emit_touch_input(','''/* Captured checksum-valid J72 state 1: use upstream Z2 inactive semantics.
 * Only states 3/4 emit positions. Other unobserved states remain rejected. */
static unsigned int contact_state1_policy=1,contact_state1_frames;
module_param(contact_state1_policy,uint,0400);
module_param(contact_state1_frames,uint,0400);
static bool emit_touch_input(''')
    s=replace(s,' /* Parser validates the WHOLE report before any event can be emitted. */',''' /* Parser validates the WHOLE report before any event can be emitted. */
 for(i=0;i<count;i++)if(contacts[i].state==1){contact_state1_frames++;break;}''')
    s=replace(s,'  phase_resync_headers=phase_resync_frames=phase_resync_failures=0;','  phase_resync_headers=phase_resync_frames=phase_resync_failures=0;\n  contact_state1_frames=0;')
    assert 'bool active=c->state==3||c->state==4;' in s
    source.write_text(s)
    (mod/'Makefile').write_text('obj-m := j72_touch_session.o\n')
    (OUT/'state1.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),s.splitlines(True),fromfile='a/j72_touch_session.c',tofile='b/j72_touch_session.c'))+''.join(difflib.unified_diff(original_header.splitlines(True),header.read_text().splitlines(True),fromfile='a/j72-classic-contacts.h',tofile='b/j72-classic-contacts.h')))
    for p in (BASE/'module').iterdir():
        if p.suffix in ('.c','.h','.inc') and p.name not in ('j72_touch_session.c','j72-classic-contacts.h') and not p.name.endswith('.mod.c'):assert sha(mod/p.name)==sha(p)
    private_report=BASE/'failure-20261103-181432/rejected-body.bin'
    with (OUT/'host-tests.log').open('wb') as log:
        subprocess.run(['python3',str(ROOT/'tools/touch-state135/test-emitter.py'),str(source),str(private_report)],check=True,stdout=log,stderr=subprocess.STDOUT)
        for name in ('test-data-phase','test-recovery-window'):
            subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fsanitize=undefined,bounds','-fno-sanitize-recover=all',str(mod/(name+'.c')),'-o',str(OUT/name)],check=True,stdout=log,stderr=subprocess.STDOUT)
            subprocess.run([str(OUT/name)],check=True,stdout=log,stderr=subprocess.STDOUT)
        subprocess.run(['python3',str(ROOT/'tools/touch-recovery-window35/test-integration.py'),str(source)],check=True,stdout=log,stderr=subprocess.STDOUT)
    with (OUT/'build.log').open('wb') as log:
        subprocess.run(['make','-C',str(WORK/'storage-kernel/src'),'O='+str(WORK/'storage-kernel/out'),'ARCH=arm64','M='+str(mod),'-j2','W=1','modules'],check=True,stdout=log,stderr=subprocess.STDOUT)
    assert 'warning:' not in (OUT/'build.log').read_text().lower()
    exports={l.split()[1] for l in (WORK/'storage-kernel/out/Module.symvers').read_text().splitlines() if l.split()[2]=='vmlinux'}
    imports={l.split()[1] for l in subprocess.check_output(['nm','-u',str(mod/'j72_touch_session.ko')],text=True).splitlines() if l.split()[0]=='U'}
    assert not imports-exports
    assert subprocess.check_output(['modinfo','-F','vermagic',str(mod/'j72_touch_session.ko')],text=True).strip()=='7.0.12-j72spi2 SMP preempt aarch64'
    for name,digest in kernel.items():assert sha(ROOT/name)==digest,name
    for name,digest in pins['files'].items():assert sha(ROOT/name)==digest,name
    files=[Path(__file__),ROOT/'tools/run-j72-touch-state135.py',ROOT/'tools/touch-state135/test-emitter.py',source,header,mod/'Makefile',OUT/'state1.patch']
    (OUT/'manifest.json').write_text(json.dumps(dict(status='OFFLINE_STATE1_BUILD_TESTS_IMPORTS_PASS_DEVICE_UNTESTED',uts_version=pins['uts_version'],module_sha256=sha(mod/'j72_touch_session.ko'),base_module_sha256=pins['module_sha256'],kernel_files_unchanged=True,prior_candidate_unchanged=True,private_inputs_unchanged=True,active_states_unchanged=True,unknown_states_still_rejected=True,wire_checksums_and_layout_bounds_unchanged=True,data_phase_retry_unchanged=True,recovery_timeout_cleanup_unchanged=True,actual_emitter_exhaustive_state_tests=True,private_rejected_report_replay_pass=True,module_strong_imports=len(imports),device_tested=False,files={str(p.relative_to(ROOT)):sha(p) for p in files}),indent=2)+'\n')
    print('PASS: state-1 inactive candidate, actual emitter/private replay, W1/imports; device untested')
if __name__=='__main__':main()
