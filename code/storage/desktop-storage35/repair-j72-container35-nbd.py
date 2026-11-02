#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Fix a stopped #35 RAM controller to use the pinned NBD-capable BusyBox."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'private/j72-platform/power-storage-20261102/desktop-storage35/container-desktop'
FETCH = '999cb969d09093a71716cfc747bb53cdada3f332c05eb5046c56e0f66a4d6d22'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    os.umask(0o077)
    h = load('host35', 'j72-desktop-storage35-host.py')
    base = h.preflight(verify_desktop=False)
    m = json.loads((WORK / 'manifest.json').read_text())
    assert m['profile'] == 'j72-container-desktop35-v1'
    assert not (WORK / 'export.json').exists(), 'Stop the owned export normally first'
    controller = WORK / 'controller.sh'
    name = str(controller.relative_to(ROOT))
    assert sha(controller) == m['files'][name]
    old = controller.read_text()
    assert old.count('busybox nbd-client') == 2 and 'nbd()' not in old
    c = load('lock', 'run-j72-input-limit-hub1050-desktop.py').locked_ram(h.ram())
    assert c('uname -v', timeout=4).decode().strip() == base['uts_version']
    c('test "$(cat /sys/block/nbd2/size)" = 0 && '
      '! grep -q " /mnt/omarchy " /proc/mounts && ! grep -q " /mnt/j72-store " /proc/mounts && '
      'test "$(cat /sys/module/j72_touch_session/parameters/session_state)" = 0 && '
      'test "$(cat /sys/module/j72_touch_session/parameters/cleanup_ok)" = Y && '
      'test "$(cat /sys/module/j72_touch_session/parameters/firmware_healthy)" = 1', timeout=5)
    assert c('busybox sha256sum /sbin/j72-compressed-desktop-session', timeout=4).decode().split()[0] == m['files'][name]
    assert c('busybox sha256sum /run/j72-fetch/busybox', timeout=4).decode().split()[0] == FETCH
    c('/run/j72-fetch/busybox --list | grep -qx nbd-client', timeout=4)
    out = WORK / ('nbd-helper-repair-' + time.strftime('%Y%m%d-%H%M%S'))
    out.mkdir()
    (out / 'controller-before.sh').write_text(old)
    (out / 'manifest-before.json').write_text(json.dumps(m, indent=2) + '\n')
    wrapper = ('nbd() {\n [ "$(busybox sha256sum /run/j72-fetch/busybox | busybox awk \'{print $1}\')" = ' + FETCH + ' ] || return 1\n'
               ' /run/j72-fetch/busybox nbd-client "$@"\n}\n')
    new = old.replace('busybox nbd-client', 'nbd').replace('start() {\n', wrapper + 'start() {\n', 1)
    controller.write_text(new)
    subprocess.run(['sh', '-n', str(controller)], check=True)
    m['files'][name] = sha(controller)
    m['files'][str(Path(__file__).relative_to(ROOT))] = sha(Path(__file__))
    m['nbd_helper_sha256'] = FETCH
    m['nbd_helper_runtime_path'] = '/run/j72-fetch/busybox'
    m['device_boot_tested'] = False
    (WORK / 'manifest.json').write_text(json.dumps(m, indent=2) + '\n')
    load('upload', 'run-j72-wlan-enumeration-v2.py').upload(c, h, controller, '/sbin/j72-compressed-desktop-session')
    c('chmod 755 /sbin/j72-compressed-desktop-session; busybox sh -n /sbin/j72-compressed-desktop-session', timeout=4)
    print('PASS: stopped RAM controller repaired with exact pinned NBD helper; no kernel, firmware, image or internal storage changes')


if __name__ == '__main__':
    main()
