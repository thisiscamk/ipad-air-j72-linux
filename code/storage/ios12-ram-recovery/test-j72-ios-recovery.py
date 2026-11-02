#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Offline checks of actual guard, staged signatures/cache and image readback."""
import ctypes
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'private/j72-platform/power-storage-20261102/recovery-prep'

def der_value(b, offset=0):
    tag=b[offset];n=b[offset+1];at=offset+2
    if n&128:
        size=n&127;assert 0<size<=4
        n=int.from_bytes(b[at:at+size],'big');at+=size
    assert at+n<=len(b)
    return tag,b[at:at+n],at+n

def der_children(b):
    at=0
    while at<len(b):
        tag,value,at=der_value(b,at)
        yield tag,value

def main():
    source=WORK/'readonly-service'
    with tempfile.TemporaryDirectory(prefix='j72-guard-') as tmp:
        tmp=Path(tmp);c=tmp/'test.c';lib=tmp/'test.so'
        c.write_text('#include <stddef.h>\n#include "j72-recovery-guard.h"\n'
                     'int test(const char*s){return same(s,s)&&safe_args(s);}\n')
        subprocess.run(['cc','-shared','-fPIC','-Wall','-Werror','-I',str(source),str(c),'-o',str(lib)],check=True)
        dll=ctypes.CDLL(str(lib));dll.test.argtypes=[ctypes.c_char_p]
        yes=['rd=md0','rd=md0 debug=0x2014e -v wdt=-1',' -v rd=md0   wdt=-1 ']
        no=['','-v','rd=disk0s1','rd=md00','rd=md0 -restore','rd=md0 nand-enable-reformat=1',
            'rd=md0 rootdev=md0','rd=md0\n','rd=md0 -n','rd=md0 rd=disk0s1',
            'rd=md0 init=/bin/sh','rd=md0 debug=0x2014eX','rd=md0 TrollStore=Tips']
        for s in yes:assert dll.test(s.encode())==1,s
        for s in no:assert dll.test(s.encode())==0,s
        spec=importlib.util.spec_from_file_location('builder',ROOT/'tools/prepare-j72-ios-recovery.py')
        builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
        capsule=WORK/'capsule-v1';manifest=builder.check(capsule)
        expected_types={'iBSS.img4':b'ibss','iBEC.img4':b'ibec','kernel.img4':b'rkrn',
                        'devicetree.img4':b'rdtr','ramdisk.img4':b'rdsk','trustcache.img4':b'rtsc'}
        for file,kind in expected_types.items():
            raw=(capsule/file).read_bytes();tag,value,end=der_value(raw)
            assert tag==48 and end==len(raw)
            children=list(der_children(value));assert children[0]==(22,b'IMG4')
            im4p=list(der_children(children[1][1]));assert im4p[1]==(22,kind)
            if file=='kernel.img4':
                _,value,_=der_value(builder.firmware()['KernelCache'].read_bytes())
                assert im4p[3]==list(der_children(value))[3]
        tc=(capsule/'recovery.trustcache').read_bytes();v,n=struct.unpack_from('<I16xI',tc)
        assert v==1 and len(tc)==24+22*n
        entries=[tc[24+i*22:24+(i+1)*22] for i in range(n)]
        assert entries==sorted(set(entries))
        stock=(WORK/'restore12.5.7.stock-trustcache').read_bytes();sn=struct.unpack_from('<I',stock,20)[0]
        assert all(stock[24+i*22:24+(i+1)*22] in entries for i in range(sn))
        machos=0
        for p in (capsule/'stage').rglob('*'):
            if not p.is_file():continue
            hashes=builder.cdh(p.read_bytes());machos+=bool(hashes)
            for h,t,f in hashes:assert h+bytes((t,f)) in entries
        # The six imports below are supplied by the original same-build RAM image.
        unchanged=['/sbin/launchd','/usr/lib/dyld','/usr/lib/libSystem.B.dylib',
                   '/usr/lib/libz.1.dylib','/usr/lib/libiconv.2.dylib',
                   '/System/Library/Frameworks/IOKit.framework/Versions/A/IOKit',
                   '/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation']
        for i,rel in enumerate(unchanged):
            a=tmp/(str(i)+'-stock');b=tmp/(str(i)+'-built')
            for image,dest in [(WORK/'restore12.5.7.original.hfs',a),(capsule/'ramdisk.hfs',b)]:
                builder.run([WORK/'host/hfsplus',image,'extract',rel,dest])
            assert len(a.read_bytes())>32 and a.read_bytes()==b.read_bytes(),rel
    result=dict(status='PASS',actual_source_guard_cases=len(yes)+len(no),
                stock_trustcache_entries_retained=sn,merged_trustcache_entries=n,
                staged_macho_code_pages_and_cache_inclusion_verified=machos,
                enabled_launch_jobs=manifest['enabled_launch_jobs'],
                ram_image_files_read_back=len(manifest['ramdisk_readback_files']),
                unchanged_stock_loader_and_imports=len(unchanged),
                img4_component_types_verified=len(expected_types),
                original_compressed_kernel_unchanged=True,device_boot_tested=False)
    (WORK/'offline-result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':main()
