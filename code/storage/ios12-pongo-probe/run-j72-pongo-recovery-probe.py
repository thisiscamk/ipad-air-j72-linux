#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Preflight or capture the read-only exact-J72 Pongo XNU handoff probe."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import pty
import re
import select
import signal
import struct
import subprocess
import time
import tty

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'private/j72-platform/power-storage-20261102/recovery-prep/pongo-route'
MODULE=WORK/'j72-recovery-probe.kext'
PONGO=ROOT/'research/upstream/hoolock-docs/binaries/Pongo.bin'
PONGOTERM=ROOT/'tools/host/aarch64/bin/pongoterm'
PARENT=ROOT/'tools/host/aarch64/bin/j72-parent-bound-exec'
EXPECTED_IMPORTS={'_command_puts','_command_register','_dt_check$64','_dt_find',
                  '_dt_parse$64','_dt_prop$64','_gBootArgs','_gDeviceTree',
                  '_gEntryPoint','_socnum'}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def commands(raw):
    assert len(raw)>=32 and struct.unpack_from('<II',raw)==(0xfeedfacf,0x100000c)
    count,size=struct.unpack_from('<II',raw,16);assert 0<count<=128 and 32+size<=len(raw)
    at=32
    for i in range(count):
        cmd,n=struct.unpack_from('<II',raw,at);assert n>=8 and n%8==0 and at+n<=32+size
        yield cmd,raw[at:at+n]
        at+=n
    assert at==32+size

def kernel_uuid(path):
    result=[data[8:24].hex() for cmd,data in commands(path.read_bytes()) if cmd==0x1b]
    assert len(result)==1 and len(result[0])==32
    return result[0]

def module_imports(path):
    raw=path.read_bytes();assert len(raw)>=0x4000 and struct.unpack_from('<I',raw,12)[0]==11
    sym=None;dysym=None;segments=[]
    for cmd,data in commands(raw):
        if cmd==2:sym=struct.unpack_from('<IIII',data,8)
        if cmd==0xb:dysym=struct.unpack_from('<18I',data,8)
        if cmd==0x19:
            vm,size,off,n=struct.unpack_from('<QQQQ',data,24)
            assert off+n<=len(raw) and n<=size
            segments.append((vm,size,off,n))
    assert sym and dysym and len(segments)>=2 and min(x[0] for x in segments)==0
    total=max(x[0]+x[1] for x in segments);assert 0<total<=0x40000
    off,nsyms,stroff,strsize=sym
    assert off+16*nsyms<=len(raw) and stroff+strsize<=len(raw)
    names=[]
    for i in range(nsyms):
        idx,typ,sect,desc,value=struct.unpack_from('<IBBHQ',raw,off+i*16)
        assert idx<strsize
        end=raw.find(b'\0',stroff+idx,stroff+strsize);assert end>=0
        names.append(raw[stroff+idx:end].decode())
    ext,n_ext,loc,n_loc=dysym[14:18]
    imports=set()
    for offset,count,isext in [(ext,n_ext,True),(loc,n_loc,False)]:
        assert offset+8*count<=len(raw)
        for i in range(count):
            addr,bits=struct.unpack_from('<II',raw,offset+i*8)
            assert addr+8<=total and (bits>>25)&3==3 and bits>>28==0
            assert bool((bits>>27)&1)==isext and not (bits>>24)&1
            if isext:
                index=bits&0xffffff;assert index<nsyms;imports.add(names[index])
    assert {'_module_entry','_module_name','_exported_symbols'}<=set(names)
    assert imports==EXPECTED_IMPORTS
    return sorted(imports)

def check():
    manifest=json.loads((WORK/'manifest.json').read_text())
    assert manifest['profile']=='j72-pongo-readonly-recovery-probe-v1'
    for name,digest in manifest['files'].items():assert sha(ROOT/name)==digest,name
    for name in manifest['host_elf']:
        raw=(ROOT/name).read_bytes()[:64]
        assert raw[:6]==b'\x7fELF\x02\x01' and struct.unpack_from('<H',raw,18)[0]==183
    imports=module_imports(MODULE)
    assert all(name.encode()+b'\0' in PONGO.read_bytes() for name in imports)
    assert kernel_uuid(WORK/'kernel.original.dec')==manifest['expected_kernel_uuid']
    print('PASS offline: exact-J72 read-only probe, module relocations/imports and native host pins; no USB access',flush=True)
    return manifest

def target():
    found=[]
    for p in Path('/sys/bus/usb/devices').iterdir():
        try:
            if (p/'idVendor').read_text().strip()=='05ac':found.append(p)
        except FileNotFoundError:pass
    if len(found)!=1 or (found[0]/'idProduct').read_text().strip()!='4141':
        raise RuntimeError('Expected exactly one Pongo USB device')
    if 'CPID:8960 BDID:12' not in (found[0]/'serial').read_text():
        raise RuntimeError('Pongo device is not the exact J72')

def read_until(fd,log,marker,timeout):
    data=bytearray();deadline=time.monotonic()+timeout
    while marker not in data.replace(b'\r',b''):
        wait=deadline-time.monotonic()
        if wait<=0 or not select.select([fd],[],[],wait)[0]:raise TimeoutError('Pongo response deadline')
        block=os.read(fd,4096)
        if not block:raise RuntimeError('Pongo console disconnected')
        log.write(block);log.flush();data.extend(block)
        if len(data)>32768:raise RuntimeError('Pongo response exceeds capture bound')
    return bytes(data)

def parse(raw,expected_uuid):
    raw=raw.replace(b'\r',b'')
    begin=b'J72_PONGO_PROBE_BEGIN\n';end=b'J72_PONGO_PROBE_END\n'
    if b'J72_PROBE_REFUSED' in raw or raw.count(begin)!=1 or raw.count(end)!=1:
        raise RuntimeError('Probe refused or response framing invalid')
    body=raw.split(begin,1)[1].split(end,1)[0];values={};maps={};pending=None
    allowed={'MODEL_OK','SOC','BOOT_REVISION','BOOT_VERSION','PHYS_BASE','MEM_SIZE',
             'TOP_KERNEL_DATA','ENTRY_PHYS','RESERVED_SLOTS','KERNEL_HEADER_PHYS'}
    for line in body.decode().splitlines():
        if line.startswith('MAP '):
            if pending is not None:raise RuntimeError('Incomplete map pair')
            match=re.fullmatch(r'MAP ([A-Za-z0-9_-]{1,31}) ([0-9a-f]{16})',line)
            if not match or match[1] in maps:raise RuntimeError('Invalid or duplicate map')
            pending=(match[1],int(match[2],16));continue
        key,sep,value=line.partition(' ')
        if key=='MAP_SIZE':
            if pending is None or not re.fullmatch('[0-9a-f]{16}',value):raise RuntimeError('Invalid map size')
            maps[pending[0]]={'address':pending[1],'size':int(value,16)};pending=None;continue
        if pending is not None or key in values:raise RuntimeError('Missing map size or duplicate scalar')
        if key=='KERNEL_UUID':
            if not re.fullmatch('[0-9a-f]{32}',value):raise RuntimeError('Invalid UUID')
            values[key]=value
        else:
            if key not in allowed or not re.fullmatch('[0-9a-f]{16}',value):raise RuntimeError('Unexpected probe scalar')
            values[key]=int(value,16)
    if pending is not None or set(values)!=allowed|{'KERNEL_UUID'} or len(maps)>128:
        raise RuntimeError('Incomplete probe inventory')
    if values['MODEL_OK']!=1 or values['SOC']!=0x8960 or values['KERNEL_UUID']!=expected_uuid:
        raise RuntimeError('Runtime model or original iOS kernel mismatch')
    base,size=values['PHYS_BASE'],values['MEM_SIZE']
    if not (0x800000000<=base and 0x10000000<=size<=0x40000000):raise RuntimeError('Runtime RAM geometry invalid')
    for key in ['ENTRY_PHYS','KERNEL_HEADER_PHYS']:
        if not base<=values[key]<base+size:raise RuntimeError('Kernel address outside RAM')
    reserved=sum(name.startswith('MemoryMapReserved-') for name in maps)
    if values['RESERVED_SLOTS']!=reserved:raise RuntimeError('Reserved-slot count mismatch')
    return {'profile':'j72-pongo-readonly-recovery-probe-v1','status':'PASS',
            'kernel_uuid_matches_original':True,'raw_disk_opened':False,
            'guest_memory_patched':False,'boot_requested':False,
            'reserved_memory_map_slots':reserved,'values':values,'memory_maps':maps}

def capture(manifest):
    if os.geteuid()!=0:raise RuntimeError('Use the task administrator terminal for Pongo USB')
    with (ROOT/'private/j72-usb.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);target()
        out=WORK/('probe-'+time.strftime('%Y%m%d-%H%M%S'));out.mkdir(mode=0o700)
        master,slave=pty.openpty();tty.setraw(slave);process=None
        with (out/'console.log').open('wb') as log:
            try:
                process=subprocess.Popen([str(PARENT),str(os.getpid()),str(PONGOTERM)],
                                         stdin=slave,stdout=slave,stderr=slave,start_new_session=True)
                os.close(slave);slave=-1
                os.write(master,b'\n');read_until(master,log,b'pongoOS> ',12)
                os.write(master,(' /send '+str(MODULE)+'\n').lstrip().encode())
                read_until(master,log,f'Uploaded {MODULE.stat().st_size} bytes'.encode(),15)
                os.write(master,b'modload\n');read_until(master,log,b'Loaded module j72_recovery_probe',10)
                os.write(master,b'j72rescueprobe\n')
                raw=read_until(master,log,b'J72_PONGO_PROBE_END\n',15)
                result=parse(raw,manifest['expected_kernel_uuid'])
                (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
                print('PASS J72 read-only XNU handoff inventory; original kernel UUID matches.',flush=True)
                print('Private result: '+str(out),flush=True)
                print('Pongo remains running; no boot, disk access or kernel patch requested.',flush=True)
            finally:
                if process is not None:
                    try:os.killpg(process.pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                    process.wait()
                if slave>=0:os.close(slave)
                os.close(master)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--capture',action='store_true')
    a=p.parse_args();os.umask(0o077);m=check()
    if a.capture:capture(m)
