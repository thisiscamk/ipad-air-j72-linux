#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""One exact-J72 RAM recovery attempt. Default is offline preflight only."""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import signal
import socket
import struct
import subprocess
import time
from j72_usb_path import require_direct_pi

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT/'private/j72-platform/power-storage-20261102/recovery-prep'
CAPSULE = WORK/'capsule-v1'
MARKER = 'J72_RO_RECOVERY_V1'

class CableCycleRequired(RuntimeError):
    pass

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    out = importlib.util.module_from_spec(spec)
    # Dataclasses need the module registered before executing its source.
    import sys
    sys.modules[name] = out
    spec.loader.exec_module(out)
    return out

def preflight():
    if platform.machine() not in ('aarch64', 'arm64'):
        raise RuntimeError('This candidate requires the native ARM64 Pi host')
    module(ROOT/'tools/prepare-j72-ios-recovery.py', 'recovery_builder').check(CAPSULE)
    pins = json.loads((WORK/'launcher-pins.json').read_text())
    for rel, expected in pins['files'].items():
        p = ROOT/rel
        if digest(p) != expected:
            raise RuntimeError('Recovery source/tool pin mismatch: '+rel)
        if rel in pins['native_elf']:
            b = p.read_bytes()[:64]
            if b[:6] != b'\x7fELF\x02\x01' or struct.unpack_from('<H', b, 18)[0] != 183:
                raise RuntimeError('Not a native ARM64 executable: '+rel)
    print('PASS offline: exact J72 image, sources, native tools and key pins; no USB access', flush=True)

def usb_devices():
    devices = []
    for p in Path('/sys/bus/usb/devices').iterdir():
        try:
            if (p/'idVendor').read_text().strip() == '05ac':
                devices.append((p, (p/'idProduct').read_text().strip()))
        except FileNotFoundError:
            pass
    return devices

class Attempt:
    def __init__(self, out):
        self.out = out
        self.ecid = None
        self.proxy = None
        self.parent_exec = ROOT/'tools/host/aarch64/bin/j72-parent-bound-exec'

    def save_state(self, stage):
        state={'profile':'j72-ios12-ram-recovery-v1','ecid':self.ecid,
               'capsule_manifest_sha256':digest(CAPSULE/'manifest.json'),
               'stage':stage,'image_upload_started':False}
        (self.out/'state.json').write_text(json.dumps(state,indent=2)+'\n')

    def exploit(self):
        """Line-buffered log; stop cleanly at gaster's A7 manual reconnect step."""
        path=self.out/'gaster-live.log'
        argv=[str(self.parent_exec),str(os.getpid()),'/usr/bin/stdbuf','-oL','-eL',
              str(WORK/'gaster-src/gaster'),'pwn']
        self.save_state('exploit_started')
        with path.open('wb') as log:
            child=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            deadline=time.monotonic()+120
            try:
                while child.poll() is None:
                    text=path.read_text(errors='replace')
                    marker='Unplug and replug the device now (at least 2 times)'
                    # PATCH has sent its payload. The native USB reset itself can wait
                    # for a physical reconnect on A7, so do not require its return.
                    at=text.find(marker)
                    if at>=0 and '\nret: true\n' in text[at+len(marker):]:
                        self.save_state('a7_cable_cycles_required')
                        raise CableCycleRequired('A7 PATCH reached its manual cable step; perform two cable cycles, then resume this exact attempt')
                    if time.monotonic()>=deadline:
                        self.save_state('exploit_timeout')
                        raise RuntimeError('gaster timed out; live stage log saved privately')
                    time.sleep(.1)
                if child.returncode:
                    raise RuntimeError('gaster failed; inspect private gaster-live.log')
            finally:
                try:
                    os.killpg(child.pid,signal.SIGKILL)
                except ProcessLookupError:
                    pass
                child.wait()

    def command(self, argv, timeout=15, accepted=(0,)):
        """Parent-bound process group; capture privately and reap on every path."""
        p = subprocess.Popen([str(self.parent_exec), str(os.getpid()), *map(str, argv)],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             start_new_session=True)
        try:
            output, _ = p.communicate(timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            with (self.out/'commands.log').open('ab') as log:
                log.write(('TIMEOUT '+repr(list(map(str, argv)))+'\n').encode()+(exc.output or b'')+b'\n')
            raise
        finally:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            p.wait()
        with (self.out/'commands.log').open('ab') as log:
            log.write(('COMMAND '+repr(list(map(str, argv)))+'\n').encode()+output+b'\n')
        if p.returncode not in accepted:
            raise RuntimeError(f'Command failed ({p.returncode}); see private commands.log')
        return output

    def identity(self, modes, wait=0):
        deadline = time.monotonic()+wait
        while True:
            cmd = ['/usr/bin/irecovery']
            if self.ecid is not None:
                cmd += ['-i', hex(self.ecid)]
            try:
                raw = self.command(cmd+['-q'], timeout=5)
                info = dict(line.split(': ', 1) for line in raw.decode().splitlines() if ': ' in line)
                if any(info.get(k) != v for k,v in {'PRODUCT':'iPad4,2','MODEL':'j72ap','CPID':'0x8960','BDID':'0x12'}.items()):
                    raise ValueError('Exact J72 recovery identity changed')
                number = int(info['ECID'], 0)
                if self.ecid is not None and number != self.ecid:
                    raise ValueError('Device ECID changed')
                if info['MODE'] not in modes:
                    raise RuntimeError('Unexpected recovery stage: '+info['MODE'])
                self.ecid = number
                return info
            except (RuntimeError, KeyError, subprocess.TimeoutExpired):
                if time.monotonic() >= deadline:
                    raise
                time.sleep(.5)

    def send(self, name, mode):
        self.identity(mode)
        print('Sending '+name, flush=True)
        self.command(['/usr/bin/irecovery','-i',hex(self.ecid),'-f',CAPSULE/name], timeout=60)

    def boot_command(self, command):
        if command not in ('ramdisk', 'devicetree', 'firmware', 'bootx'):
            raise ValueError('Command outside fixed RAM boot sequence')
        self.identity(('Recovery',))
        self.command(['/usr/bin/irecovery','-i',hex(self.ecid),'-c',command])

    def boot(self):
        devices = usb_devices()
        if len(devices) != 1 or devices[0][1] != '1227':
            raise RuntimeError('Require exactly one Apple USB device, in DFU')
        require_direct_pi(devices[0][0])
        self.identity(('DFU',))
        # gaster cannot select ECID; the exact-single-device guard above is mandatory.
        print('Exact J72 DFU/direct Pi verified. Starting one bounded gaster attempt.', flush=True)
        self.exploit()
        self.identity(('DFU',), wait=10)
        self.finish_boot()

    def resume(self, previous):
        """No exploit retry: require the original ECID and explicit gaster marker."""
        state=json.loads((previous/'state.json').read_text())
        if (state.get('profile')!='j72-ios12-ram-recovery-v1' or
            state.get('capsule_manifest_sha256')!=digest(CAPSULE/'manifest.json') or
            state.get('stage') not in ('exploit_timeout','a7_cable_cycles_required') or
            state.get('image_upload_started') is not False or
            type(state.get('ecid')) is not int or state['ecid']<=0):
            raise RuntimeError('Previous attempt is not eligible for pwned-DFU resume')
        devices=usb_devices()
        if len(devices)!=1 or devices[0][1]!='1227':
            raise RuntimeError('Resume requires exactly one DFU device')
        require_direct_pi(devices[0][0])
        serial=(devices[0][0]/'serial').read_text()
        if 'PWND:[gaster]' not in serial:
            raise RuntimeError('Resume refused: gaster PWND marker absent; no exploit repeated')
        self.ecid=state['ecid'];self.identity(('DFU',))
        print('Original exact J72 and gaster marker verified; resuming without another exploit.',flush=True)
        self.finish_boot()

    def finish_boot(self):
        gaster = WORK/'gaster-src/gaster'
        devices = usb_devices()
        if len(devices) != 1 or devices[0][1] != '1227':
            raise RuntimeError('DFU inventory changed before volatile state reset')
        # This clears DFU transfer state, not user data. Matches both pinned recipes.
        self.command([gaster,'reset'], timeout=12)
        self.identity(('DFU',), wait=10)
        # Any partial image upload forbids the pwned-DFU resume path above.
        self.save_state('image_upload_started')
        state=json.loads((self.out/'state.json').read_text());state['image_upload_started']=True
        (self.out/'state.json').write_text(json.dumps(state,indent=2)+'\n')
        self.send('iBSS.img4', ('DFU',))
        time.sleep(1)
        self.identity(('DFU',), wait=8)
        self.send('iBEC.img4', ('DFU',))
        self.identity(('Recovery',), wait=15)
        for file, command in [('ramdisk.img4','ramdisk'), ('devicetree.img4','devicetree'),
                              ('trustcache.img4','firmware'), ('kernel.img4','bootx')]:
            self.send(file, ('Recovery',))
            self.boot_command(command)
        self.inspect()

    def ssh_args(self):
        return ['/usr/bin/ssh','-F','/dev/null','-p','2244','-i',WORK/'keys/client_rsa_key',
                '-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','StrictHostKeyChecking=yes',
                '-o','UserKnownHostsFile='+str(WORK/'keys/known_hosts'),
                '-o','HostKeyAlgorithms=+ssh-rsa','-o','PubkeyAcceptedAlgorithms=+ssh-rsa',
                '-o','ConnectTimeout=3','root@127.0.0.1']

    def inspect(self):
        deadline = time.monotonic()+90
        while True:
            devices = usb_devices()
            marker = [p for p,_ in devices if (p/'serial').exists() and (p/'serial').read_text().strip()==MARKER]
            if len(devices)==1 and len(marker)==1:
                break
            if time.monotonic() >= deadline:
                raise RuntimeError('RAM recovery USB marker not observed; no normal-iOS SSH fallback')
            time.sleep(.5)
        # Binding first would mask an existing proxy. Refuse an occupied port.
        with socket.socket() as s:
            s.bind(('127.0.0.1',2244))
        iproxy = WORK/'host-deps/root/usr/bin/iproxy'
        self.proxy_log = (self.out/'iproxy.log').open('wb')
        self.proxy = subprocess.Popen([str(self.parent_exec),str(os.getpid()),str(iproxy),
                                       '-l','-u',MARKER,'-s','127.0.0.1','2244:22'],
                                      stdout=self.proxy_log,stderr=subprocess.STDOUT,start_new_session=True)
        deadline = time.monotonic()+20
        while True:
            try:
                # One inspector invocation: retries below concern connection setup only.
                with socket.create_connection(('127.0.0.1',2244),timeout=1) as s:
                    banner=s.recv(256)
                if banner.startswith(b'SSH-2.0-'):
                    break
            except OSError:
                pass
            if self.proxy.poll() is not None or time.monotonic()>=deadline:
                raise RuntimeError('Restricted recovery SSH transport did not become ready')
            time.sleep(.5)
        raw = self.command(self.ssh_args()+['inspect'],timeout=30)
        lines = [line[len(b'J72_INSPECT_JSON '):] for line in raw.splitlines() if line.startswith(b'J72_INSPECT_JSON ')]
        if len(lines)!=1:
            raise RuntimeError('Missing unique RAM recovery inspection result')
        data=json.loads(lines[0]);(self.out/'inspect.json').write_text(json.dumps(data,indent=2)+'\n')
        if data.get('read_only') is not True or data.get('root_is_hfs_md0') is not True or data.get('apfs_mounts')!=0:
            raise RuntimeError('RAM recovery guard result invalid')
        gpt=module(ROOT/'tools/j72_storage_preflight_recovery.py','recovery_gpt')
        blobs={k.replace('-','_').removesuffix('.bin'):bytes.fromhex(v) for k,v in data['files'].items()}
        inventory=gpt.audit(gpt.Geometry(data['logical_block_bytes'],data['total_blocks']),**blobs)
        (self.out/'gpt-report.json').write_text(json.dumps(gpt.report(inventory),indent=2)+'\n')
        print('PASS RAM recovery: restricted SSH, no APFS mounts, both GPT copies/CRCs valid.',flush=True)
        print('Recovery remains running. Private receipt: '+str(self.out),flush=True)

    def close(self):
        if self.proxy is not None:
            try:
                os.killpg(self.proxy.pid,signal.SIGKILL)
            except ProcessLookupError:
                pass
            self.proxy.wait();self.proxy_log.close()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group()
    mode.add_argument('--boot',action='store_true',help='Perform ONE changed physical DFU attempt; requires root and direct Pi')
    mode.add_argument('--resume-pwned-dfu',type=Path,help='Resume a saved exact attempt only after its gaster PWND marker returns')
    args=p.parse_args();os.umask(0o077);preflight()
    if not args.boot and args.resume_pwned_dfu is None:
        return
    if os.geteuid()!=0:
        raise RuntimeError('Use the task administrator terminal for a hardware attempt')
    with (ROOT/'private/j72-usb.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        out=WORK/('attempt-'+time.strftime('%Y%m%d-%H%M%S'));out.mkdir(mode=0o700)
        attempt=Attempt(out)
        try:
            if args.resume_pwned_dfu is not None:
                attempt.resume(args.resume_pwned_dfu.resolve())
            else:
                attempt.boot()
        except CableCycleRequired as exc:
            print(str(exc),flush=True)
            print('Saved resumable attempt: '+str(out),flush=True)
        finally:
            attempt.close()

if __name__=='__main__':
    main()
