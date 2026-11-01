#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Exercise actual imported ANS1 functions with host mailbox/DMA stubs.

ANS1 implementation: Nick Chan / Hoolock m1n1, SPDX MIT. This harness
tests command admission and geometry only, not firmware or DMA execution.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import resource
import subprocess
import tempfile

IMPORT='boot/m1n1/patches/hoolock/0032-Add-ANS1-storage.patch'
IMPORT_SHA='9522985e68957b0906d8ef1b7b0fb224ec54cb4e7132ab2bb6cad110b7548b40'
PRELUDE=r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef uint8_t u8; typedef uint16_t u16; typedef uint32_t u32; typedef uint64_t u64;
#define PACKED __attribute__((packed))
#define static_assert _Static_assert
#define BIT(n) (1ULL << (n))
#define GENMASK(h,l) ((~0ULL << (l)) & (~0ULL >> (63-(h))))
#define FIELD_PREP(mask,value) (((u64)(value) << __builtin_ctzll(mask)) & (mask))
#define SZ_4K 4096
'''
STUBS=r'''
typedef int rtkit_dev_t;
struct rtkit_message {u64 msg; unsigned ep;};
static struct ans1_cmd_hdr *cmd;
static rtkit_dev_t dummy, *ans1_rtkit=&dummy;
static unsigned ans1_ep=0x20, sends, barriers, cases;
static bool ans1_initialized, ans1_geometry_valid, send_ok, wait_ok;
static u32 ans1_total_lbas;
static struct asp_identify identity;
static void dma_wmb(void) {barriers++;}
static void dma_rmb(void) {barriers++;}
static bool rtkit_send(rtkit_dev_t *dev, struct rtkit_message *message) {
    assert(dev==ans1_rtkit && message->ep==ans1_ep);sends++;
    if(cmd->op==ANS1_CMD_OP_IDENTIFY) memcpy(cmd+1,&identity,sizeof(identity));
    return send_ok;
}
static bool ans1_wait_for_tag(rtkit_dev_t *dev, u8 tag) {
    assert(dev==ans1_rtkit && tag==0);return wait_ok;
}
static void reset(void) {
    memset(cmd,0,ANS1_CMD_SIZE);memset(&identity,0,sizeof(identity));
    ans1_initialized=true;ans1_geometry_valid=true;ans1_total_lbas=100;
    send_ok=true;wait_ok=true;sends=0;barriers=0;
    identity.util_formatted=true;identity.lba_size=4096;identity.num_lba_formatted=100;
}
'''
MAIN=r'''
int main(void) {
    cmd=aligned_alloc(4096,4096);assert(cmd);
#ifndef CANDIDATE
    reset();cmd->op=ANS1_CMD_OP_WRITE_UNLOCK;
    assert(!ans1_exec_command() && "baseline accepted write-unlock");
#else
    for(unsigned op=0;op<256;op++) {
        reset();cmd->op=op;
        if(op==ANS1_CMD_OP_READ_USERAREA) {cmd->flags=8;cmd->length=1;}
        bool allowed=op==ANS1_CMD_OP_IDENTIFY || op==ANS1_CMD_OP_READ_USERAREA;
        assert(ans1_exec_command()==allowed);assert(sends==(allowed?1U:0U));cases++;
    }
    for(unsigned i=0;i<3;i++) {
        reset();cmd->op=ANS1_CMD_OP_IDENTIFY;
        if(i==0)cmd->flags=8;if(i==1)cmd->slba=1;if(i==2)cmd->length=1;
        assert(!ans1_exec_command() && sends==0 && barriers==0);cases++;
    }
    for(unsigned i=0;i<5;i++) {
        reset();cmd->op=ANS1_CMD_OP_READ_USERAREA;cmd->flags=8;cmd->length=1;
        if(i==0)cmd->tag=1;if(i==1)cmd->flags=0;if(i==2)cmd->length=2;
        if(i==3)cmd->slba=100;if(i==4)ans1_geometry_valid=false;
        assert(!ans1_exec_command() && sends==0 && barriers==0);cases++;
    }
    u64 bad_lbas[]={100,0x100000000ULL,UINT64_MAX};
    for(unsigned i=0;i<3;i++) {
        reset();assert(!ans1_read_main_storage(bad_lbas[i],(void*)0x1000));
        assert(sends==0 && barriers==0);cases++;
    }
    u64 bad_buffers[]={0,0x1001,1ULL<<44};
    for(unsigned i=0;i<3;i++) {
        reset();assert(!ans1_read_main_storage(0,(void*)(uintptr_t)bad_buffers[i]));
        assert(sends==0 && barriers==0);cases++;
    }
    for(unsigned i=0;i<2;i++) {
        reset();if(i==0)ans1_initialized=false;else ans1_geometry_valid=false;
        assert(!ans1_read_main_storage(0,(void*)0x1000) && sends==0);cases++;
    }
    reset();assert(ans1_read_main_storage(99,(void*)0x1000));
    assert(sends==1 && cmd->slba==99 && cmd->length==1);cases++;
    reset();assert(ans1_read_main_storage(0,(void*)(uintptr_t)(0xffffffffULL<<12)));
    assert(((struct ans1_io*)(cmd+1))->sgl[0]==0xffffffffU);cases++;
    for(unsigned i=0;i<5;i++) {
        reset();
        if(i==0)identity.num_lba_formatted=0;
        if(i==1)identity.lba_size=512;
        if(i==2)identity.util_formatted=false;
        if(i==3)send_ok=false;
        if(i==4)wait_ok=false;
        assert(!ans1_read_geometry() && !ans1_geometry_valid && ans1_total_lbas==0);cases++;
    }
    reset();assert(ans1_read_geometry());
    assert(ans1_geometry_valid && ans1_total_lbas==100 && sends==1);cases++;
    printf("cases=%u\n",cases);
#endif
    free(cmd);return 0;
}
'''

def function(text,name):
    pattern=r'^(?:static )?bool '+name+r'\([^\n]*\)\n\{.*?^\}'
    match=re.search(pattern,text,re.S|re.M)
    if not match:raise ValueError('Missing actual function '+name)
    return match.group()+'\n'

def no_core():resource.setrlimit(resource.RLIMIT_CORE,(0,0))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--orchard-tree',type=Path,required=True)
    p.add_argument('--patches',type=Path,default=Path(__file__).resolve().parent)
    args=p.parse_args();data=(args.orchard_tree/IMPORT).read_bytes()
    if hashlib.sha256(data).hexdigest()!=IMPORT_SHA:p.error('Upstream ANS1 import changed; re-audit required')
    part=data.decode().split('diff --git a/src/ans1.c b/src/ans1.c\n',1)[1].split('\ndiff --git ',1)[0]
    source='\n'.join(x[1:] for x in part.splitlines() if x.startswith('+') and not x.startswith('+++'))+'\n'
    with tempfile.TemporaryDirectory(prefix='j72-ans1-read-') as temp:
        root=Path(temp);(root/'src').mkdir();target=root/'src/ans1.c';target.write_text(source)
        for name in ['0001-ans1-Avoid-freeing-the-command-buffer-twice.patch','0002-ans1-Validate-read-only-commands-and-measured-geometry.patch']:
            subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str((args.patches/name).resolve())],cwd=root,check=True,capture_output=True,timeout=10)
        patched=target.read_text();count=None
        for label,text in [('imported',source),('candidate',patched)]:
            constants=text[text.index('/* based on syslog'):text.index('static struct ans1_cmd_hdr *cmd;')]
            functions=function(text,'ans1_exec_command')+function(text,'ans1_read_main_storage')
            if label=='candidate':functions+=function(text,'ans1_read_geometry')
            file=root/(label+'.c');file.write_text(PRELUDE+constants+STUBS+functions+MAIN)
            binary=root/label
            command=['cc','-std=c11','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-variable','-Wno-misleading-indentation','-fsanitize=undefined','-fno-sanitize-recover=all']
            if label=='candidate':command+=['-DCANDIDATE=1']
            subprocess.run(command+[str(file),'-o',str(binary)],check=True,capture_output=True,timeout=30)
            result=subprocess.run([str(binary)],capture_output=True,timeout=5,preexec_fn=no_core)
            if label=='imported':
                assert result.returncode==-6 and b'baseline accepted write-unlock' in result.stderr
            else:
                assert result.returncode==0,result.stderr.decode()
                count=int(re.search(rb'cases=(\d+)',result.stdout)[1])
    print(json.dumps({'baseline_missing_command_allowlist_reproduced':True,'candidate_actual_source_cases':count,
                      'invalid_commands_blocked_before_dma_or_mailbox':True,'read_geometry_and_narrowing_checks':True,
                      'ubsan_pass':True,'full_loader_built':False,'hardware_tested':False},indent=2))

if __name__=='__main__':main()
