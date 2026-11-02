#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Run actual inspector gates with native syscall stubs; never open a disk."""
import json, subprocess, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 with tempfile.TemporaryDirectory(prefix='j72-mount-guard-') as tmp:
  tmp=Path(tmp);c=tmp/'harness.c';exe=tmp/'harness'
  c.write_text(r'''
#define main inspector_main
#define sysctlbyname stub_sysctl
#define getuid stub_uid
#define getfsstat stub_mounts
#define stat64 stub_stat64
#define open stub_open
#define reboot stub_reboot
#include "j72-recovery-inspect-v3.c"
#undef main
static int scenario,opens,reboots;
extern int atoi(const char*);
static void copy(char*d,const char*s){while((*d++=*s++));}
unsigned stub_uid(void){return 0;}
int stub_sysctl(const char*key,void*out,size_t*n,void*x,size_t y){
 (void)x;(void)y;const char*s=same(key,"hw.machine")?"iPad4,2":same(key,"kern.osrelease")?"18.7.0":scenario==16?"rd=disk0s1":"rd=md0 debug=0x2014e -v wdt=-1";
 size_t len=0;while(s[len])len++;if(*n<len+1)return -1;copy(out,s);*n=len+1;return scenario==17&&same(key,"kern.bootargs")?-1:0;
}
int stub_mounts(void*out,int bytes,int flags){
 (void)bytes;(void)flags;if(scenario==9)return -1;if(scenario==10)return 17;
 if(!out)return scenario==6||scenario==7?2:1;
 if(scenario==11)return 0;
 struct fsrow*r=out;r[0]=(struct fsrow){0};copy(r[0].fstype,scenario==4?"apfs":"hfs");copy(r[0].on,scenario==8?"/other":"/");
 copy(r[0].from,scenario==0?"/dev/md0":scenario==1?"md0":scenario==2?"root_device":scenario==3?"disk0s1":"root_device");r[0].flags=scenario==5?0:0x4000;
 if(scenario==12)for(unsigned i=0;i<16;i++)r[0].fstype[i]='h';
 if(scenario==6||scenario==7){r[1]=(struct fsrow){0};copy(r[1].fstype,scenario==6?"apfs":"hfs");copy(r[1].on,scenario==6?"/private/var":"/");copy(r[1].from,"/dev/disk0s1");return 2;}
 return 1;
}
int stub_stat64(const char*path,struct statrow*out){
 *out=(struct statrow){0};if(same(path,"/")){out->dev=0x1000000;out->mode=0040755;return scenario==13?-1:0;}
 out->rdev=scenario==14?0x2000000:0x1000000;out->mode=scenario==15?0020600:0060600;return scenario==18?-1:0;
}
int stub_open(const char*path,int flags,...){(void)path;(void)flags;opens++;return -1;}
int stub_reboot(int how){(void)how;reboots++;return 0;}
int main(int argc,char**argv){if(argc!=2)return 99;scenario=atoi(argv[1]);int rc=inspector_main(0,0);printf("HARNESS %d %d %d\n",rc,opens,reboots);return 0;}
''')
  subprocess.run(['cc','-O2','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all','-I',str(ROOT/'tools'),str(c),'-ldl','-o',str(exe)],check=True)
  cases=0
  import os
  for scenario in range(19):
   env=dict(os.environ,SSH_ORIGINAL_COMMAND='inspect')
   r=subprocess.run([str(exe),str(scenario)],check=True,capture_output=True,text=True,env=env)
   rows=r.stdout.splitlines();diag=json.loads(next(x[len('J72_GUARD_JSON '):] for x in rows if x.startswith('J72_GUARD_JSON ')))
   status,opened,rebooted=map(int,next(x for x in rows if x.startswith('HARNESS ')).split()[1:])
   expected=scenario in (0,1,2)
   assert (status,opened,rebooted)==((8,1,0) if expected else (5,0,0)),(scenario,r.stdout)
   assert diag['raw_disk_opened'] is False and bool(diag['root_is_hfs_md0'])==(scenario<3 or scenario in (16,17))
   cases+=1
  for command in ['diagnose','reboot','sh','inspect; sh','']:
   r=subprocess.run([str(exe),'2'],check=True,capture_output=True,text=True,env=dict(os.environ,SSH_ORIGINAL_COMMAND=command))
   status,opened,rebooted=map(int,next(x for x in r.stdout.splitlines() if x.startswith('HARNESS ')).split()[1:])
   assert opened==0 and rebooted==int(command=='reboot')
   assert status==(0 if command in ('diagnose','reboot') else 7)
   cases+=1
  # Diagnose remains metadata-only even when an internal APFS mount is reported.
  r=subprocess.run([str(exe),'6'],check=True,capture_output=True,text=True,env=dict(os.environ,SSH_ORIGINAL_COMMAND='diagnose'))
  assert r.stdout.endswith('HARNESS 0 0 0\n');cases+=1
 print(json.dumps({'status':'PASS','actual_inspector_guard_and_command_cases':cases,'real_disk_opens':0,'usb_access':False}))
if __name__=='__main__':main()
