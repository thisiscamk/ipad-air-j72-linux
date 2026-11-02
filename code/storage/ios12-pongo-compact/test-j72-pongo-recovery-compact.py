#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Test compact C inventory, frame refusals and idle-before-read transport offline."""
import ctypes, importlib.util, io, json, subprocess, tempfile, time
from pathlib import Path
from j72_pongo_control import PongoControl
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'private/j72-platform/power-storage-20261102/recovery-prep/pongo-route/compact-v2'
def main():
    s=importlib.util.spec_from_file_location('compact',ROOT/'tools/run-j72-pongo-recovery-compact.py')
    host=importlib.util.module_from_spec(s);s.loader.exec_module(host)
    with tempfile.TemporaryDirectory(prefix='j72-compact-test-') as tmp:
        tmp=Path(tmp);source=tmp/'harness.c';binary=tmp/'harness.so'
        source.write_text('''#include <string.h>
#include "j72-pongo-recovery-compact.c"
struct boot_args12 *gBootArgs;dt_node *gDeviceTree;void *gEntryPoint;u64 gTopOfKernelData;u32 socnum;
void command_puts(const char*s){(void)s;}
void command_register(const char*a,const char*b,void(*c)(const char*,char*)){(void)a;(void)b;(void)c;}
int dt_check(void*a,size_t b,size_t*c){(void)a;(void)b;(void)c;return 0;}
int dt_parse(dt_node*a,int b,size_t*c,int(*d)(void*,dt_node*,int),void*e,int(*f)(void*,dt_node*,int,const char*,void*,size_t),void*g){(void)a;(void)b;(void)c;(void)d;(void)e;(void)f;(void)g;return 0;}
void *dt_prop(dt_node*a,const char*b,size_t*c){(void)a;(void)b;(void)c;return 0;}
dt_node *dt_find(dt_node*a,const char*b){(void)a;(void)b;return 0;}
static struct inventory current;
void clear(void){memset(&current,0,sizeof(current));}
int row(const char*key,unsigned long len,unsigned long long address,unsigned long long size){u64 bytes[2]={address,size};return inspect(&current,0,0,key,bytes,len);}
unsigned long long field(int n){u64 *p=(void*)&current;return p[n];}
''')
        subprocess.run(['cc','-shared','-fPIC','-O1','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all','-I',str(ROOT/'tools'),str(source),'-o',str(binary)],check=True)
        lib=ctypes.CDLL(str(binary));lib.row.argtypes=[ctypes.c_char_p,ctypes.c_ulong,ctypes.c_ulonglong,ctypes.c_ulonglong];lib.field.argtypes=[ctypes.c_int];lib.field.restype=ctypes.c_ulonglong
        cases=0
        for key,length,addr,size,expected,field,val in [
            (b'AAPL,phandle',4,5,0,0,2,1),(b'kernel-only',0,0,0,0,2,1),
            (b'name',11,0,0,0,1,0),(b'MemoryMapReserved-14',16,0,0,0,4,1),
            (b'MemoryMapReserved-14',16,1,0,0,4,0),(b'MemoryMapReserved-14',4,0,0,-1,3,0),
            (b'TrustCache',16,0x800500000,4096,0,5,0x800500000),
            (b'Kernel-__TEXT',16,0x800600000,4096,0,7,0x800600000)]:
            lib.clear();assert lib.row(key,length,addr,size)==expected and lib.field(field)==val;cases+=1
        for key in [b'TrustCache',b'Kernel-__TEXT']:
            lib.clear();assert lib.row(key,16,1,1)==0 and lib.row(key,16,1,1)==-1;cases+=1
        lib.clear()
        for _ in range(128):assert lib.row(b'name',4,0,0)==0
        assert lib.row(b'name',4,0,0)==-1;cases+=1
    uuid='01'*16
    scalar={'MODEL_OK':1,'SOC':0x8960,'PHYS_BASE':0x800000000,'MEM_SIZE':0x40000000,
            'ENTRY_PHYS':0x800601000,'ALLOCATOR_TOP':0x801000000,'BOOT_COMMAND_LINE_LENGTH':1,
            'PROPERTIES':21,'MAPS':18,'METADATA':2,'RESERVED_SLOTS':16,'EMPTY_SLOTS':16,
            'TRUSTCACHE_PHYS':0x800500000,'TRUSTCACHE_SIZE':4096,
            'KERNEL_HEADER_PHYS':0x800600000,'KERNEL_TEXT_SIZE':8192}
    frame='J72_COMPACT_BEGIN\n'+''.join(f'{k} {v:016x}\n' for k,v in scalar.items())+'KERNEL_UUID '+uuid+'\nJ72_COMPACT_END\npongoOS> '
    assert host.parse(frame.encode(),uuid)['status']=='PASS' and len(frame)<1024
    bad=[frame+frame,frame.replace('J72_COMPACT_END','missing'),
         frame.replace('EMPTY_SLOTS 0000000000000010','EMPTY_SLOTS 000000000000000f'),
         frame.replace('PROPERTIES 0000000000000015','PROPERTIES 0000000000000081'),
         frame.replace('BOOT_COMMAND_LINE_LENGTH 0000000000000001','BOOT_COMMAND_LINE_LENGTH 0000000000000100'),
         frame.replace('TRUSTCACHE_SIZE 0000000000001000','TRUSTCACHE_SIZE ffffffffffffffff'),
         frame.replace('KERNEL_UUID '+uuid,'KERNEL_UUID '+'02'*16),
         frame.replace('MODEL_OK 0000000000000001','MODEL_OK 0000000000000000')]
    for raw in bad:
        try:host.parse(raw.encode(),uuid);raise AssertionError('Invalid frame accepted')
        except RuntimeError:pass
    class Fake(PongoControl):
        def __init__(self,response,statuses):self.log=io.BytesIO();self.response=response;self.statuses=list(statuses);self.active=True;self.reads=0;self.calls=0
        def control(self,kind,request,value=0,data=b'',size=0):
            self.calls+=1
            if kind==0xa1 and request==2:
                status=self.statuses.pop(0) if self.statuses else b'\0';self.active=status!=b'\0';return status
            if kind==0xa1 and request==1:
                assert not self.active,'stdout read while command active'
                assert size==4096
                # Match Pongo: fetching empties the ring, rather than behaving
                # like a stream; a short requested length loses leading bytes.
                self.reads+=1;out=self.response[-size:];self.response=b'';return out
            assert kind==0x21 and ((request==4 and value==0xffff) or (request==3 and data==b'j72rescuecompact\n'))
            return b''
    fake=Fake(frame.replace('\n','\r\n').encode(),[b'\1',b'\1',b'\0'])
    reply=fake.command(b'j72rescuecompact',b'J72_COMPACT_END')
    assert host.parse(reply,uuid)['status']=='PASS' and fake.reads>=2
    rejected=0
    for fake,line in [(Fake(b'',[b'\0']),b'bootux'),(Fake(b'X'*4095,[b'\0']),b'j72rescuecompact'),(Fake(b'',[b'\2']),b'j72rescuecompact'),(Fake(b'',[b'']),b'j72rescuecompact')]:
        try:fake.command(line,b'J72_COMPACT_END');raise AssertionError('Unsafe transport accepted')
        except (RuntimeError,ValueError):rejected+=1
    result={'status':'PASS','actual_source_inventory_cases':cases,'frame_refusal_cases':len(bad),
            'command_completed_before_stdout_read':'PASS','console_control_read_length':4096,
            'transport_refusal_cases':rejected,'fixture_response_bytes':len(frame),
            'existing_shared_bounds_cases':{'span':8,'macho':143},
            'usb_access':False,'revised_device_probe_tested':False,'recovery_boot_tested':False}
    (WORK/'offline-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
