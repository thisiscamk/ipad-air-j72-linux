#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Exercise actual probe bounds/parser with synthetic data; never access USB."""
import ctypes
import importlib.util
import io
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import threading
import time

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'private/j72-platform/power-storage-20261102/recovery-prep/pongo-route'

def main():
    spec=importlib.util.spec_from_file_location('probe_host',ROOT/'tools/run-j72-pongo-recovery-probe.py')
    host=importlib.util.module_from_spec(spec);spec.loader.exec_module(host)
    with tempfile.TemporaryDirectory(prefix='j72-probe-test-') as tmp:
        tmp=Path(tmp);c=tmp/'harness.c';so=tmp/'harness.so'
        c.write_text('#include "j72-pongo-recovery-bounds.h"\n'
                     'int span(unsigned long long a,unsigned long long b,unsigned long long c,unsigned long long d){return j72_span(a,b,c,d);}\n'
                     'int macho(const unsigned char*a,unsigned long long b,unsigned char*c){return j72_macho_uuid(a,b,c);}\n')
        subprocess.run(['cc','-shared','-fPIC','-O1','-g','-Wall','-Wextra','-Werror',
                        '-fsanitize=undefined','-fno-sanitize-recover=all','-I',str(ROOT/'tools'),str(c),'-o',str(so)],check=True)
        lib=ctypes.CDLL(str(so));lib.span.argtypes=[ctypes.c_ulonglong]*4
        spans=[((0x800000000,4096,0x800000000,4096),1),((1,4096,4096,1),1),
               ((1,4096,4097,1),0),((1,4096,0,1),0),((1,4096,1,0),0),
               ((1,0,1,1),0),((2**64-1,1,2**64-1,1),0),((1,2**64-1,1,2**64-1),0)]
        for args,result in spans:assert lib.span(*args)==result,args
        lib.macho.argtypes=[ctypes.c_void_p,ctypes.c_ulonglong,ctypes.c_void_p]
        def accepts(data,available=None):
            raw=ctypes.create_string_buffer(bytes(data));uuid=ctypes.create_string_buffer(16)
            result=lib.macho(raw,len(data) if available is None else available,uuid)
            return result,uuid.raw.hex()
        b=bytearray(128);struct.pack_into('<8I',b,0,0xfeedfacf,0x100000c,0,2,2,96,0,0)
        struct.pack_into('<II16sQQQQIIII',b,32,0x19,72,b'__TEXT',0xfffffff007004000,4096,0,4096,5,5,0,0)
        struct.pack_into('<II16s',b,104,0x1b,24,bytes(range(1,17)))
        assert accepts(b)==(1,bytes(range(1,17)).hex())
        cases=1
        for n in range(len(b)):
            assert accepts(b,n)[0]==0,n;cases+=1
        mutations=[(0,'I',0),(4,'I',0),(12,'I',11),(16,'I',0),(16,'I',129),
                   (20,'I',0xffffffff),(36,'I',0),(36,'I',0xffffffff),
                   (64,'Q',1),(72,'Q',4096),(96,'I',65),(108,'I',16)]
        for off,fmt,value in mutations:
            x=bytearray(b);struct.pack_into('<'+fmt,x,off,value);assert not accepts(x)[0],(off,value);cases+=1
        x=bytearray(b);x[112:128]=bytes(16);assert not accepts(x)[0];cases+=1
        original=(WORK/'kernel.original.dec').read_bytes()
        assert accepts(original)==(1,host.kernel_uuid(WORK/'kernel.original.dec'));cases+=1
        # Exercise the real module callback against the two non-map properties
        # observed on device, without reading or modifying a device tree.
        callback=tmp/'callback.c';callback_so=tmp/'callback.so'
        callback.write_text('''#include <string.h>
#include "j72-pongo-recovery-probe.c"
struct boot_args12 *gBootArgs;dt_node *gDeviceTree;void *gEntryPoint;
u64 gTopOfKernelData;u32 socnum;
static char output[4096];
void command_puts(const char*s){strncat(output,s,sizeof(output)-strlen(output)-1);strncat(output,"\\n",sizeof(output)-strlen(output)-1);}
void command_register(const char*a,const char*b,void(*c)(const char*,char*)){(void)a;(void)b;(void)c;}
int dt_check(void*a,size_t b,size_t*c){(void)a;(void)b;(void)c;return 0;}
int dt_parse(dt_node*a,int b,size_t*c,int(*d)(void*,dt_node*,int),void*e,int(*f)(void*,dt_node*,int,const char*,void*,size_t),void*g){(void)a;(void)b;(void)c;(void)d;(void)e;(void)f;(void)g;return 0;}
void *dt_prop(dt_node*a,const char*b,size_t*c){(void)a;(void)b;(void)c;return 0;}
dt_node *dt_find(dt_node*a,const char*b){(void)a;(void)b;return 0;}
int row(const char*key,unsigned long len){unsigned char bytes[16]={0};output[0]=0;maps=reserved=0;return maprow(0,0,0,key,bytes,len);}
const char *row_output(void){return output;}
''')
        subprocess.run(['cc','-shared','-fPIC','-O1','-Wall','-Wextra','-Werror',
                        '-fsanitize=undefined','-fno-sanitize-recover=all','-I',str(ROOT/'tools'),
                        str(callback),'-o',str(callback_so)],check=True)
        cb=ctypes.CDLL(str(callback_so));cb.row.argtypes=[ctypes.c_char_p,ctypes.c_ulong]
        cb.row_output.restype=ctypes.c_char_p
        callback_cases=[(b'AAPL,phandle',4,0,b'LEN AAPL,phandle 0000000000000004'),
                        (b'kernel-only',0,0,b'LEN kernel-only 0000000000000000'),
                        (b'MemoryMapReserved-14',16,0,b'MAP MemoryMapReserved-14'),
                        (b'MemoryMapReserved-14',4,-1,b'J72_PROBE_REFUSED'),
                        (b'Kernel-__TEXT',16,0,b'MAP Kernel-__TEXT'),
                        (b'bad key',4,-1,b'')]
        for key,length,expected,marker in callback_cases:
            assert cb.row(key,length)==expected and marker in cb.row_output()
        uuid='01'*16
        scalar={'MODEL_OK':1,'SOC':0x8960,'BOOT_REVISION':2,'BOOT_VERSION':2,
                'PHYS_BASE':0x800000000,'MEM_SIZE':0x40000000,'TOP_KERNEL_DATA':0x800800000,
                'ENTRY_PHYS':0x800401000,'RESERVED_SLOTS':2,'KERNEL_HEADER_PHYS':0x800400000}
        scalar.update(ALLOCATOR_TOP=0x800800000,BOOT_COMMAND_LINE_LENGTH=0)
        text='J72_PONGO_PROBE_BEGIN\n'+''.join(f'{k} {v:016x}\n' for k,v in scalar.items())
        text+='MAP MemoryMapReserved-0 0000000000000000\nMAP_SIZE 0000000000000000\n'
        text+='MAP MemoryMapReserved-1 0000000000000000\nMAP_SIZE 0000000000000000\n'
        text+='MAP Kernel-__TEXT 0000000800400000\nMAP_SIZE 0000000000100000\n'
        text+='LEN AAPL,phandle 0000000000000004\nLEN kernel-only 0000000000000000\n'
        text+='KERNEL_UUID '+uuid+'\nJ72_PONGO_PROBE_END\n'
        result=host.parse(text.encode(),uuid);assert result['reserved_memory_map_slots']==2
        assert result['other_property_lengths']=={'AAPL,phandle':4,'kernel-only':0}
        assert host.parse(text.replace('\n','\n\n').encode(),uuid)['status']=='PASS'
        invalid=[text.replace('J72_PONGO_PROBE_END\n',''),text+text,
                 text.replace('MODEL_OK 0000000000000001','MODEL_OK 0000000000000000'),
                 text.replace('MEM_SIZE 0000000040000000','MEM_SIZE ffffffffffffffff'),
                 text.replace('RESERVED_SLOTS 0000000000000002','RESERVED_SLOTS 0000000000000003'),
                 text.replace('MAP_SIZE 0000000000000000\n','',1),
                 text.replace('KERNEL_UUID '+uuid,'KERNEL_UUID '+'02'*16),
                 text.replace('ENTRY_PHYS 0000000800401000','ENTRY_PHYS 0000000000000000'),
                 text.replace('LEN AAPL,phandle','LEN MemoryMapReserved-2'),
                 text.replace('LEN AAPL,phandle','LEN Kernel-__TEXT'),
                 text.replace('LEN AAPL,phandle 0000000000000004','LEN AAPL,phandle 0000000000100001'),
                 text.replace('BOOT_COMMAND_LINE_LENGTH 0000000000000000','BOOT_COMMAND_LINE_LENGTH 0000000000000100')]
        for frame in invalid:
            try:host.parse(frame.encode(),uuid);raise AssertionError('bad frame accepted')
            except RuntimeError:pass
        # Deliberately split CR/LF and the footer across transport reads.
        rd,wr=os.pipe();wire=text.replace('\n','\r\n').encode()
        def writer():
            try:
                for off in range(0,len(wire),7):os.write(wr,wire[off:off+7]);time.sleep(.001)
            finally:os.close(wr)
        thread=threading.Thread(target=writer);thread.start()
        try:raw=host.read_until(rd,io.BytesIO(),b'J72_PONGO_PROBE_END\n',3)
        finally:os.close(rd);thread.join()
        assert host.parse(raw,uuid)['status']=='PASS'
    result={'status':'PASS','actual_source_span_cases':len(spans),'actual_source_macho_cases':cases,
            'actual_source_property_cases':len(callback_cases),
            'captured_frame_refusal_cases':len(invalid),'fragmented_crlf_transport':'PASS',
            'native_module_imports':host.module_imports(host.MODULE),'usb_access':False,
            'device_probe_tested':False,'recovery_boot_tested':False}
    (WORK/'offline-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()
