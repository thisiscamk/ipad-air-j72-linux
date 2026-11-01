#!/usr/bin/env python3
"""Preflight or observe J72 HSIC1 registers after a clean RAM workload stop."""
import argparse
import base64
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import shlex
import time

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'private/j72-platform/power-wifi-20261101/hsic-phy-observer-v2'
CHARGE = ROOT / 'private/j72-platform/continuous-charge-session'


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fields(raw):
    return dict(line.split('=', 1) for line in raw.decode().splitlines() if '=' in line)


def stopped_trial(raw):
    status = fields(raw)
    required = dict(ready='1', used='1', active='0', armed='0', restored='1', restore_failed='0')
    assert all(status.get(key) == value for key, value in required.items()), 'Charge worker must have ended and restored'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--preflight', action='store_true')
    action.add_argument('--run', action='store_true')
    args = parser.parse_args()
    manifest = json.loads((WORK / 'manifest.json').read_text())
    for name, expected in manifest['files'].items():
        assert digest(ROOT / name) == expected, name
    host = load('host', 'j72-integrated-host.py')
    bundle = host.preflight(verify_desktop=False, continuous_touch=True)
    assert bundle['uts_version'] == manifest['uts_version']
    assert bundle['payload_sha256'] == manifest['payload_sha256']
    if args.preflight:
        print('PASS: exact #33 image/build/module pins. Existing Linux genpd owner; no PHY/GPIO/PMIC writes. No device contacted.')
        return
    h = load('parent', 'run-j72-input-limit-hub1050-desktop.py')
    command = h.locked_ram(host.ram())
    current = json.loads((CHARGE / 'current-desktop.json').read_text())
    assert command('busybox cat /proc/sys/kernel/random/boot_id').decode().strip() == current['target_boot_id']
    assert command('uname -v').decode().strip() == manifest['uts_version']
    command("""busybox sh -ec '
[ "$(cat /proc/device-tree/model)" = "Apple iPad Air (Cellular)" ]
[ "$(cat /sys/block/nbd2/size)" = 0 ]
! busybox grep -q " /mnt/omarchy " /proc/mounts
[ "$(cat /sys/module/j72_touch_session/parameters/session_state)" = 0 ]
[ "$(cat /sys/module/j72_touch_session/parameters/cleanup_ok)" = Y ]
[ "$(cat /sys/module/j72_touch_session/parameters/firmware_healthy)" = 1 ]
[ ! -d /sys/module/j72_hsic_phy_observer_v2 ]
[ ! -e /sys/bus/platform/devices/j72-hsic-phy-observer-v2 ]
'""")
    stopped_trial(command('busybox cat /sys/module/j72_input_limit_hub1050_session/parameters/status'))
    assert fields(command('busybox cat ' + h.SNAP))['reg_04c0'] == '02'
    assert not host.server_pid(bundle['desktop_image']), 'Stop owned read-only export first'
    output = WORK / ('capture-' + time.strftime('%Y%m%d-%H%M%S'))
    output.mkdir(mode=0o700)
    (output / 'pmic-before.txt').write_bytes(command('busybox cat ' + h.SNAP))
    src = WORK / 'j72_hsic_phy_observer_v2.ko'
    destination = '/run/j72-hsic-phy-observer-v2.ko'
    data = base64.b64encode(gzip.compress(src.read_bytes())).decode('ascii')
    command('busybox sh -ec ' + shlex.quote(': > ' + destination + '.b64'))
    for offset in range(0, len(data), 8192):
        command('busybox sh -ec ' + shlex.quote("printf '%s' '" + data[offset:offset+8192] + "' >> " + destination + '.b64'))
    command('busybox sh -ec ' + shlex.quote('busybox base64 -d ' + destination + '.b64 | busybox gunzip > ' + destination))
    assert command('busybox sha256sum ' + destination).decode().split()[0] == digest(src)
    command('busybox rm ' + destination + '.b64')
    try:
        (output / 'load.txt').write_bytes(command('insmod ' + destination, timeout=10))
        raw = command('busybox cat /sys/module/j72_hsic_phy_observer_v2/parameters/status')
        (output / 'status.txt').write_bytes(raw)
        status = fields(raw)
        for name in ('observed', 'restored', 'consumer_removed'):
            assert status[name] == '1', (name, status)
        assert status['result'] == '0' and status['detach_result'] == '0', status
        for name in ('phy', 'host'):
            assert int(status[name + '_before'], 16) & 255 == 0
            state = int(status[name + '_active'], 16)
            assert state & 15 == 15 and ((state >> 4) & 15 == 15 or (state & (1 << 28) and (state >> 4) & 15 == 4))
            assert int(status[name + '_after'], 16) & 255 == 0
        print('PASS: HSIC1/parent domain active and restored; two PHY registers observed. No radio enumeration claimed.')
    finally:
        (output / 'pmic-after.txt').write_bytes(command('busybox cat ' + h.SNAP))
        (output / 'cleanup.txt').write_bytes(command('test ! -e /sys/bus/platform/devices/j72-hsic-phy-observer-v2 && echo TEMPORARY_CONSUMER_REMOVED'))
        (output / 'kernel-tail.txt').write_bytes(command('dmesg | busybox tail -n 80'))
    print('Saved privately:', output)


if __name__ == '__main__':
    main()
