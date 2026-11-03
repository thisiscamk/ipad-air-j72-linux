#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build separate, bounded data-phase resync with original firmware/guards."""
import difflib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'private/j72-platform/power-storage-20261102'
BASE=WORK/'touch-recovery-window35'
OUT=WORK/'touch-data-resync35'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def replace(s,before,after):
    assert s.count(before)==1, before
    return s.replace(before,after,1)


def main():
    os.umask(0o077)
    assert not OUT.exists(), 'Preserve existing candidate'
    pins=json.loads((BASE/'manifest.json').read_text())
    for name,digest in pins['files'].items():assert sha(ROOT/name)==digest,name
    assert sha(BASE/'module/j72_touch_session.ko')==pins['module_sha256']
    kernel=json.loads((WORK/'desktop-storage35/module-inputs.json').read_text())['kernel_base_files']
    for name,digest in kernel.items():assert sha(ROOT/name)==digest,name
    OUT.mkdir();mod=OUT/'module';mod.mkdir()
    for p in (BASE/'module').iterdir():
        if p.suffix in ('.c','.h','.inc') and not p.name.endswith('.mod.c'):
            shutil.copyfile(p,mod/p.name)
    for p in (ROOT/'tools/touch-data-resync35').iterdir():shutil.copyfile(p,mod/p.name)
    shutil.copyfile(ROOT/'tools/touch-recovery-window35/test-integration.py',mod/'test-integration.py')
    source=mod/'j72_touch_session.c';before=source.read_text()
    s=replace(before,'#include "j72-recovery-window.h"','#include "j72-recovery-window.h"\n#include "j72-data-phase.h"')
    needle='static noinline void query_report_metadata(struct spi_device *dev,void __iomem *gpio)'
    addition='''/* Acquisition retries a validated data-phase E1 header exactly once.
 * Final frame checksums and the complete native contact decoder are unchanged. */
static unsigned int phase_resync_policy=1;
static unsigned int phase_resync_headers,phase_resync_frames,phase_resync_failures;
module_param(phase_resync_policy,uint,0400);
module_param(phase_resync_headers,uint,0400);
module_param(phase_resync_frames,uint,0400);
module_param(phase_resync_failures,uint,0400);
struct phase_context {struct spi_device *dev;u64 start;u32 flags;};
static int phase_xfer(void *arg,u8 *tx,u8 *rx,unsigned int wire)
{
 struct phase_context *ctx=arg;
 return checked_xfer(ctx->dev,tx,rx,wire);
}
static void phase_header(void *arg,const u8 *tx,const u8 *rx,unsigned int wire)
{
 struct phase_context *ctx=arg;
 phase_resync_headers++;audit.bad_frame++;
 audit_save(ctx->start,2,tx,rx,wire,ctx->flags|AUDIT_FRAME_BAD);
}

'''
    s=replace(s,needle,addition+needle)
    s=replace(s,'u8 tx[16]={0xeb},rx[16]={0};unsigned int length,wire,j;\n  u16 sum;bool success=false;u32 level,flags;',
                'u8 tx[16]={0xeb},rx[16]={0};unsigned int length,wire;\n  bool success=false;u32 level,flags;')
    old='''  wire=length+5;
  memset(report_data_tx,0,sizeof(report_data_tx));
  report_data_tx[0]=0xeb;report_data_tx[1]=seq;report_data_tx[2]=1;
  sum=0;for(j=0;j<14;j++)sum+=report_data_tx[j];
  report_data_tx[wire-2]=sum;report_data_tx[wire-1]=sum>>8;
  if(checked_xfer(dev,report_data_tx,report_data_rx,wire)){
   audit.xfer_errors++;stopped=true;break;
  }'''
    new='''  struct phase_context phase={dev,start,level?AUDIT_ATTN_HIGH:AUDIT_ATTN_LOW};
  struct j72_data_io data_io={&phase,phase_xfer,phase_header};
  struct j72_data_result data=j72_data_phase(&data_io,report_data_tx,
    report_data_rx,sizeof(report_data_tx),length,seq);
  wire=data.wire;
  if(data.error){audit.xfer_errors++;stopped=true;break;}'''
    s=replace(s,old,new)
    s=replace(s,'   if(!emit_touch_input(report_data_rx+5,wire-7))flags|=0x0800;',
                '   if(!emit_touch_input(report_data_rx+5,wire-7))flags|=0x0800;\n   else if(data.resynced)phase_resync_frames++;')
    s=replace(s,'  audit_save(start,2,report_data_tx,report_data_rx,wire,flags);',
                '  if(data.resynced && ((flags&AUDIT_FRAME_BAD)||(flags&0x0800)))phase_resync_failures++;\n  audit_save(start,2,report_data_tx,report_data_rx,wire,flags);')
    s=replace(s,'  input_frames=input_bad_layouts=input_timeouts=input_recoveries=0;',
                '  input_frames=input_bad_layouts=input_timeouts=input_recoveries=0;\n  phase_resync_headers=phase_resync_frames=phase_resync_failures=0;')
    # Verify unchanged decoder, packet validator and recovery/timeout branch.
    for begin,end in [('static bool audit_data_reply(', 'static DECLARE_WAIT_QUEUE_HEAD'),
                      ('static bool emit_touch_input(', 'static noinline void query_report_metadata(')]:
        a=before[before.index(begin):before.index(end,before.index(begin))]
        if begin.startswith('static bool emit'):
            assert s[s.index(begin):s.index('/* Acquisition retries',s.index(begin))]==a
        else:assert s[s.index(begin):s.index(end,s.index(begin))]==a
    a=before[before.index('  if(consecutive_bad>=3)'):before.index('  msleep(25);',before.index('  if(consecutive_bad>=3)'))]
    assert a in s
    source.write_text(s)
    (mod/'Makefile').write_text('obj-m := j72_touch_session.o\n')
    (OUT/'data-resync.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),s.splitlines(True),fromfile='a/j72_touch_session.c',tofile='b/j72_touch_session.c')))
    for name in ('j72-classic-contacts.h','j72-recovery-window.h'):
        assert sha(mod/name)==sha(BASE/'module'/name)
    for p in (BASE/'module').glob('*.inc'):assert sha(mod/p.name)==sha(p)
    with (OUT/'host-tests.log').open('wb') as log:
        for name in ('test-data-phase','test-recovery-window'):
            binary=OUT/name
            subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fsanitize=undefined,bounds','-fno-sanitize-recover=all',str(mod/(name+'.c')),'-o',str(binary)],check=True,stdout=log,stderr=subprocess.STDOUT)
            subprocess.run([str(binary)],check=True,stdout=log,stderr=subprocess.STDOUT)
        subprocess.run(['python3',str(mod/'test-integration.py'),str(source)],check=True,stdout=log,stderr=subprocess.STDOUT)
    with (OUT/'build.log').open('wb') as log:
        subprocess.run(['make','-C',str(WORK/'storage-kernel/src'),'O='+str(WORK/'storage-kernel/out'),'ARCH=arm64','M='+str(mod),'-j2','W=1','modules'],check=True,stdout=log,stderr=subprocess.STDOUT)
    assert 'warning:' not in (OUT/'build.log').read_text().lower()
    exports={l.split()[1] for l in (WORK/'storage-kernel/out/Module.symvers').read_text().splitlines() if l.split()[2]=='vmlinux'}
    imports={l.split()[1] for l in subprocess.check_output(['nm','-u',str(mod/'j72_touch_session.ko')],text=True).splitlines() if l.split()[0]=='U'}
    assert not imports-exports,imports-exports
    assert subprocess.check_output(['modinfo','-F','vermagic',str(mod/'j72_touch_session.ko')],text=True).strip()=='7.0.12-j72spi2 SMP preempt aarch64'
    for name,digest in kernel.items():assert sha(ROOT/name)==digest,name
    for name,digest in pins['files'].items():assert sha(ROOT/name)==digest,name
    files=[Path(__file__),ROOT/'tools/run-j72-touch-resync35.py',source,mod/'Makefile',OUT/'data-resync.patch',*(mod.glob('*.h')),*((ROOT/'tools/touch-data-resync35').glob('*'))]
    manifest=dict(status='OFFLINE_RESYNC_BUILD_TESTS_IMPORTS_PASS_DEVICE_UNTESTED',uts_version=pins['uts_version'],module_sha256=sha(mod/'j72_touch_session.ko'),base_source_sha256=sha(BASE/'module/j72_touch_session.c'),source_sha256=sha(source),kernel_files_unchanged=True,original_candidate_unchanged=True,cleanup_api_failure_guard_unchanged=True,finite_diagnostic_budget_unchanged=True,contact_decoder_unchanged=True,complete_wire_validation_unchanged=True,bounded_resync_extra_transfers=1,private_inputs_unchanged=True,module_strong_imports=len(imports),device_tested=False,layout_rejection_cause_known=False,files={str(p.relative_to(ROOT)):sha(p) for p in files})
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('PASS: bounded data-phase candidate builds warning-free; guards/decoder/private inputs unchanged; device untested')


if __name__=='__main__':main()
