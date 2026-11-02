#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Offline preflight or single compact, read-only J72 Pongo inventory."""
import argparse, fcntl, hashlib, importlib.util, json, os, re, time
from pathlib import Path
from j72_pongo_control import PongoControl
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'private/j72-platform/power-storage-20261102/recovery-prep/pongo-route/compact-v2'
MODULE=WORK/'j72-recovery-compact.kext'
def old():
    s=importlib.util.spec_from_file_location('legacy_probe',ROOT/'tools/run-j72-pongo-recovery-probe.py')
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
FIELDS={'MODEL_OK','SOC','PHYS_BASE','MEM_SIZE','ENTRY_PHYS','ALLOCATOR_TOP',
        'BOOT_COMMAND_LINE_LENGTH','PROPERTIES','MAPS','METADATA','RESERVED_SLOTS',
        'EMPTY_SLOTS','TRUSTCACHE_PHYS','TRUSTCACHE_SIZE','KERNEL_HEADER_PHYS','KERNEL_TEXT_SIZE'}
def parse(raw,uuid):
    raw=raw.replace(b'\r',b'')
    begin=b'J72_COMPACT_BEGIN\n';end=b'J72_COMPACT_END\n'
    if len(raw)>=2048 or b'REFUSED' in raw or raw.count(begin)!=1 or raw.count(end)!=1:
        raise RuntimeError('Invalid compact frame')
    values={}
    for line in raw.split(begin,1)[1].split(end,1)[0].decode().splitlines():
        if not line:continue
        match=re.fullmatch(r'([A-Z_]+) ([0-9a-f]+)',line)
        if not match or match[1] in values:raise RuntimeError('Malformed or duplicate compact row')
        key,val=match.groups()
        if key=='KERNEL_UUID':
            if len(val)!=32:raise RuntimeError('Invalid kernel UUID')
            values[key]=val
        else:
            if key not in FIELDS or len(val)!=16:raise RuntimeError('Unknown compact scalar')
            values[key]=int(val,16)
    if set(values)!=FIELDS|{'KERNEL_UUID'}:raise RuntimeError('Incomplete compact response')
    if values['MODEL_OK']!=1 or values['SOC']!=0x8960 or values['KERNEL_UUID']!=uuid:
        raise RuntimeError('Compact platform or original kernel mismatch')
    base,size=values['PHYS_BASE'],values['MEM_SIZE']
    if base<0x800000000 or not 0x10000000<=size<=0x40000000 or base+size>2**64-1:
        raise RuntimeError('Invalid RAM geometry')
    for addr,count in [('ENTRY_PHYS',4),('ALLOCATOR_TOP',1),('TRUSTCACHE_PHYS',values['TRUSTCACHE_SIZE']),('KERNEL_HEADER_PHYS',values['KERNEL_TEXT_SIZE'])]:
        if not count or not base<=values[addr]<base+size or count>base+size-values[addr]:raise RuntimeError('Compact memory range outside RAM')
    if not 1<=values['RESERVED_SLOTS']==values['EMPTY_SLOTS']<=values['MAPS']<=128:
        raise RuntimeError('Invalid reserved slot inventory')
    if values['PROPERTIES']!=values['MAPS']+values['METADATA']+1 or values['PROPERTIES']>128 or values['BOOT_COMMAND_LINE_LENGTH']>=256:
        raise RuntimeError('Invalid compact property or argument counts')
    return {'status':'PASS','profile':'j72-pongo-readonly-recovery-compact-v2',
            'kernel_uuid_matches_original':True,'values':values,
            'raw_disk_opened':False,'guest_memory_patched':False,'boot_requested':False}
def check():
    m=json.loads((WORK/'manifest.json').read_text());legacy=old()
    if m['profile']!='j72-pongo-readonly-recovery-compact-v2':raise RuntimeError('Wrong compact profile')
    for name,digest in m['files'].items():
        if legacy.sha(ROOT/name)!=digest:raise RuntimeError('Compact input pin mismatch: '+name)
    legacy.module_imports(MODULE)
    if legacy.kernel_uuid(legacy.WORK/'kernel.original.dec')!=m['expected_kernel_uuid']:raise RuntimeError('Original kernel pin mismatch')
    print('PASS offline compact probe and native transport pins; no USB access',flush=True);return m
def target_binding():
    old().target()
    devices=[]
    for p in Path('/sys/bus/usb/devices').iterdir():
        try:
            if (p/'idVendor').read_text().strip()=='05ac':devices.append(p)
        except FileNotFoundError:pass
    assert len(devices)==1
    p=devices[0]
    from j72_usb_path import require_direct_pi
    require_direct_pi(p)
    return hashlib.sha256(b'\0'.join((p/n).read_bytes() for n in ['serial','busnum','devnum'])).hexdigest()
def capture(m):
    if os.geteuid()!=0:raise RuntimeError('Use sudo for Pongo USB')
    with (ROOT/'private/j72-usb.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);binding=target_binding()
        out=WORK/('capture-'+time.strftime('%Y%m%d-%H%M%S'));out.mkdir(mode=0o700)
        prior=WORK/('session-'+binding+'.json')
        if prior.exists():raise RuntimeError('Already attempted module upload in this Pongo boot')
        with (out/'console.log').open('wb') as log, PongoControl(log) as client:
            client.synchronize();listing=client.command(b'help',b'shows this help message')
            if b'j72rescueprobe' in listing or b'j72rescuecompact' in listing:raise RuntimeError('Existing recovery module: no replacement upload')
            prior.write_text(json.dumps({'state':'upload_started','module_sha256':old().sha(MODULE),'capture':out.name})+'\n')
            client.upload_module(MODULE.read_bytes())
            client.command(b'modload',b'Loaded module j72_recovery_compact')
            raw=client.command(b'j72rescuecompact',b'J72_COMPACT_END')
            result=parse(raw,m['expected_kernel_uuid']);(out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
            prior.write_text(json.dumps({'state':'probe_passed','module_sha256':old().sha(MODULE),'capture':out.name})+'\n')
            print('PASS compact J72 inventory; original kernel UUID matches. Private result:',out,flush=True)
            print('Pongo left running; no boot, kernel patch or disk access requested.',flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--capture',action='store_true');a=p.parse_args()
    os.umask(0o077);m=check()
    if a.capture:capture(m)
