#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Compile the actual candidate's recovery branch with controlled health/clock I/O."""
import subprocess,tempfile,sys
from pathlib import Path
source=Path(sys.argv[1]);text=source.read_text()
start=text.index('  if(consecutive_bad>=3){')
end=text.index('  if(input_active &&',start)
branch=text[start:end]
preamble=r'''
#include <assert.h>
#include <stdbool.h>
#include <string.h>
#include <stdio.h>
#include "j72-recovery-window.h"
typedef unsigned char u8;
#define READ_ONCE(v) (v)
#define pr_info(...) ((void)0)
#define pr_err(...) ((void)0)
static unsigned input_recoveries,recovery_stop_reason,releases;
static bool continuous,info_ok=true,status_ok=true,gate_ok=true;
static unsigned long long now_ms;
static struct j72_recovery_window recovery_window;
static void release_touch_input(void){releases++;}
static bool read_device_info(void *dev){(void)dev;return info_ok;}
static bool short_report(void *dev,unsigned report,unsigned len,u8 *out){
 (void)dev;memset(out,0,len);
 if(report==0x7f)return status_ok;
 assert(report==0xc8 && len==1);*out=gate_ok?0x19:0;return true;
}
static void *memchr_inv(const void *p,int c,unsigned n){
 const u8 *b=p;for(unsigned i=0;i<n;i++)if(b[i]!=(u8)c)return (void *)(b+i);return 0;
}
static unsigned long long ktime_get_ns(void){return now_ms*1000000ULL;}
static bool recover(void){
 bool stopped=false,previous_success=true;
 unsigned consecutive_bad=3;void *dev=0;
 do {
'''
post=r'''
 }while(0);
 if(!stopped){assert(consecutive_bad==0);assert(!previous_success);}
 return !stopped;
}
static void reset(bool cont){
 continuous=cont;input_recoveries=recovery_stop_reason=releases=0;
 info_ok=status_ok=gate_ok=true;now_ms=0;
 recovery_window=(struct j72_recovery_window){0};
}
int main(void){
 reset(true);
 for(unsigned i=0;i<1000;i++){now_ms=60000ULL*i;assert(recover());}
 assert(input_recoveries==1000 && releases==1000);
 reset(true);
 for(unsigned i=0;i<6;i++)assert(recover());
 assert(!recover() && recovery_stop_reason==1 && input_recoveries==7);
 reset(false);
 for(unsigned i=0;i<6;i++){now_ms=60000ULL*i;assert(recover());}
 now_ms+=60000;assert(!recover() && recovery_stop_reason==1);
 reset(true);info_ok=false;assert(!recover() && recovery_stop_reason==2);
 reset(true);status_ok=false;assert(!recover() && recovery_stop_reason==3);
 reset(true);gate_ok=false;assert(!recover() && recovery_stop_reason==4);
 puts("PASS: actual recovery branch: continuous sparse/burst, finite budget, info/status/gate failure, release and re-prime");
}
'''
with tempfile.TemporaryDirectory(prefix='j72-touch-integration-') as directory:
 p=Path(directory);(p/'test.c').write_text(preamble+branch+post)
 subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=undefined,bounds','-fno-sanitize-recover=all','-I',str(source.parent),str(p/'test.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
