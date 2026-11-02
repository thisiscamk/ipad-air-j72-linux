#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Exercise actual native-query C with fake iOS ABI; never access a disk."""
import json
from pathlib import Path
import subprocess
import tempfile

SOURCE = Path(__file__).with_name('j72-ios-writer-capabilities.c')
STUB = r'''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define main query_main
#define open mock_open
#define close mock_close
#define ioctl mock_ioctl
#define getuid mock_getuid
#define alarm mock_alarm
#define dlopen mock_dlopen
#define dlsym mock_dlsym
#define dlclose mock_dlclose
#include "SOURCE"
#undef main
static int scenario, opened, queries, errors;
unsigned mock_getuid(void){return scenario==4?501:0;}
unsigned mock_alarm(unsigned x){if(x!=20)abort();return 0;}
int *__error(void){return &errors;}
int sysctlbyname(const char*k,void*out,size_t*n,void*set,size_t bytes){
 if(set||bytes)abort();
 const char*v=0;
 if(!strcmp(k,"hw.machine"))v=scenario==1?"iPad4,1":"iPad4,2";
 if(!strcmp(k,"kern.osversion"))v=scenario==2?"16H88":"16H81";
 if(!strcmp(k,"kern.osrelease"))v=scenario==3?"19.0.0":"18.7.0";
 if(!v||strlen(v)+1>*n)abort();
 memcpy(out,v,strlen(v)+1);*n=strlen(v)+1;return 0;
}
int mock_open(const char*p,int flags,...){if(strcmp(p,"/dev/rdisk0")||flags!=0x100)abort();opened++;return scenario==6?-1:3;}
int mock_close(int fd){if(fd!=3)abort();return 0;}
int mock_ioctl(int fd,unsigned long command,...){
 #define TAKE __builtin_va_list va;__builtin_va_start(va,command);void*p=__builtin_va_arg(va,void*);__builtin_va_end(va)
 TAKE;
 if(fd!=3)abort();
 queries++;
 /* Independent XNU _IOR derivation: direction OUT, sizeof argument, 'd', nr. */
 if(command==(0x40000000UL|(4UL<<16)|('d'<<8)|24)){*(u32*)p=scenario==7?512:4096;return 0;}
 if(command==(0x40000000UL|(8UL<<16)|('d'<<8)|25)){*(u64*)p=scenario==8?31249999:31250000;return 0;}
 const unsigned numbers[]={29,76,77,70,71};const unsigned sizes[]={4,4,4,8,8};
 for(unsigned i=0;i<5;i++)if(command==(0x40000000UL|((unsigned long)sizes[i]<<16)|('d'<<8)|numbers[i])){
  if(scenario==9){errors=25;return -1;}
  if(sizes[i]==4)*(u32*)p=i==0?1:i==1?2:4096;else *(u64*)p=1048576;
  if(scenario==14)((u64*)p)[1]=0;
  return 0;
 }
 abort(); /* No write, arbitrary ioctl or synchronize request is acceptable. */
}
static int minimum(const char*name,long*out){if(strcmp(name,"disk0s1"))abort();*out=scenario==12?0:126357602304L;if(scenario==13)((u64*)out)[1]=0;return scenario==12?37:0;}
void *mock_dlopen(const char*name,int flags){if(strcmp(name,"/System/Library/PrivateFrameworks/APFS.framework/APFS")||flags!=1)abort();return scenario==11?0:(void*)1;}
void *mock_dlsym(void*h,const char*name){if(h!=(void*)1||strcmp(name,"APFSContainerGetMinimalSize"))abort();return scenario==10?0:(void*)minimum;}
int mock_dlclose(void*h){if(h!=(void*)1)abort();return 0;}
int main(int argc,char**argv){if(argc!=2)return 99;scenario=atoi(argv[1]);int rc=query_main(scenario==5?2:1,argv);fprintf(stderr,"opened=%d queries=%d\n",opened,queries);return rc;}
'''


def main():
    with tempfile.TemporaryDirectory(prefix='j72-ios-query-test-') as folder:
        root = Path(folder); source = root / 'harness.c'; binary = root / 'harness'
        source.write_text(STUB.replace('SOURCE', str(SOURCE)))
        subprocess.run(['cc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                        '-fsanitize=undefined', '-fno-sanitize-recover=all', str(source), '-o', str(binary)], check=True)
        for scenario in range(15):
            r = subprocess.run([str(binary), str(scenario)], capture_output=True)
            expected = 2 if 1 <= scenario <= 5 else {6:3,7:4,8:4,13:6,14:5}.get(scenario,0)
            assert r.returncode == expected, (scenario,r.returncode,r.stderr.decode())
            if 1 <= scenario <= 5: assert r.stderr == b'opened=0 queries=0\n'
            if expected == 0:
                d = json.loads(r.stdout)
                assert d['read_only'] is True and d['storage_writes'] is False
                assert not d['resize_called'] and not d['flush_issued'] and not d['write_qualification_pass']
                assert len(d['queries']) == 5 and r.stderr == b'opened=1 queries=7\n'
                if scenario == 9: assert all(q['status']==-1 and q['errno']==25 for q in d['queries'].values())
                if scenario in (10,11): assert d['minimal_size']['available'] is False
                if scenario == 12: assert d['minimal_size']['status']==37
    print('PASS: 15 actual-C/UBSan query cases; only fixed O_RDONLY path and XNU-derived _IOR requests; no device access')


if __name__ == '__main__': main()
