#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Stage isolated RAM tools and query DM target versions; never create a map."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shlex
import time

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'private/j72-platform/power-storage-20261102/desktop-storage35/native-view-tools'


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resume', action='store_true', help='Verify and reuse the already staged RAM closure')
    args = parser.parse_args()
    os.umask(0o077)
    h = load('h35', 'j72-desktop-storage35-host.py')
    base = h.preflight(verify_desktop=False)
    m = json.loads((WORK / 'manifest.json').read_text())
    for name, digest in m['files'].items():
        assert h.sha(WORK / 'root' / name) == digest, name
    archive = WORK / 'native-view-tools.tar.gz'
    assert h.sha(archive) == m['archive_sha256']
    c = load('lock', 'run-j72-input-limit-hub1050-desktop.py').locked_ram(h.ram())
    assert c('uname -v', timeout=4).decode().strip() == base['uts_version']
    assert c('cat /proc/device-tree/model', timeout=4).rstrip(b'\0\n') == b'Apple iPad Air (Cellular)'
    assert c('busybox sha256sum /run/j72-fetch/busybox', timeout=4).decode().split()[0] == '999cb969d09093a71716cfc747bb53cdada3f332c05eb5046c56e0f66a4d6d22'
    c('test "$(busybox stat -f -c %T /run)" = tmpfs && '
      'test "$(cat /sys/class/misc/device-mapper/dev)" = 10:236 && test -c /dev/mapper/control', timeout=5)
    if not args.resume:
        c('test ! -e /run/j72-native-view-tools', timeout=4)
        serve = load('network', 'j72_network_userspace.py').serve
        with serve(archive, port=10813) as url:
            c('/run/j72-fetch/busybox wget -Y off -q -T 15 -O /run/j72-native-view-tools.tar.gz ' + shlex.quote(url), timeout=30)
        assert c('busybox sha256sum /run/j72-native-view-tools.tar.gz', timeout=4).decode().split()[0] == m['archive_sha256']
        c('mkdir -m 700 /run/j72-native-view-tools && busybox tar -xzf /run/j72-native-view-tools.tar.gz -C /run/j72-native-view-tools && '
          'rm /run/j72-native-view-tools.tar.gz', timeout=12)
    for name, digest in m['files'].items():
        assert c('busybox sha256sum ' + shlex.quote('/run/j72-native-view-tools/' + name), timeout=4).decode().split()[0] == digest
    c('mkdir -p /run/j72-native-view-tools/proc && mount -o bind /dev /run/j72-native-view-tools/dev', timeout=5)
    out = WORK / ('inspect-' + time.strftime('%Y%m%d-%H%M%S'))
    out.mkdir()
    try:
        c('mount -o bind /proc /run/j72-native-view-tools/proc', timeout=5)
        # DM_LIST_VERSIONS only; no table, create, load, resume or mount.
        data = c('busybox chroot /run/j72-native-view-tools /usr/sbin/dmsetup targets', timeout=6)
        (out / 'targets.txt').write_bytes(data)
        assert any(line.split()[:1] == [b'linear'] for line in data.splitlines()), 'Linear target absent'
    finally:
        c('if grep -q " /run/j72-native-view-tools/proc " /proc/mounts; then umount /run/j72-native-view-tools/proc; fi', timeout=6)
        c('umount /run/j72-native-view-tools/dev', timeout=6)
    (out / 'result.json').write_text(json.dumps({'linear_target_present': True, 'mapping_created': False,
        'internal_block_device_opened': False, 'internal_writes': False, 'kernel_changed': False,
        'tool_dev_and_proc_binds_removed': True, 'tools_resident_in_ram': True}, indent=2) + '\n')
    print('PASS: actual #35 kernel reports a linear DM target; no mapping or internal device open')


if __name__ == '__main__':
    main()
