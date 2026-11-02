#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Prepare the ext4-container/loop/SquashFS desktop rehearsal; no device access."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'private/j72-platform/power-storage-20261102/desktop-storage35'
SOURCE = WORK / 'compressed-desktop'
OUT = WORK / 'container-desktop'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(data)
    return h.hexdigest()


def main():
    os.umask(0o077)
    assert not OUT.exists(), 'Refuse to overwrite a prepared candidate'
    m = json.loads((SOURCE / 'manifest.json').read_text())
    image_result = json.loads((WORK / 'local-root-image/result.json').read_text())
    assert image_result['image_bytes'] == 1610612736 and image_result['readonly_loop_readback_pass']
    assert image_result['normal_host_unmount_and_loop_detach'] and not image_result['device_access']
    image = WORK / 'local-root-image/j72-local-root-1536.ext4'
    assert sha(image) == image_result['image_sha256']
    OUT.mkdir()
    for name in ('squashfs.ko', 'autostart'):
        assert sha(SOURCE / name) == m['files'][str((SOURCE / name).relative_to(ROOT))]
        shutil.copyfile(SOURCE / name, OUT / name)
    source = (SOURCE / 'controller.sh').read_text()
    assert '#35 SMP PREEMPT Mon Nov 2 07:00:00 +08 2026' in source
    source = source.replace('10831', '10832').replace('1117192', '3145728')
    old = ' mount -t squashfs -o ro /dev/nbd2 "$root"\n'
    assert source.count(old) == 1
    before = ''' store=/mnt/j72-store
 mounted "$store" && return 1
 [ ! -e "$state/container-loop" ] || return 1
 mkdir -p "$store"
 mount -t ext4 -o ro,noload,nodev,nosuid,noexec /dev/nbd2 "$store"
 grep -q '^/dev/nbd2 /mnt/j72-store ext4 ro,' /proc/mounts || return 1
 [ "$(busybox sha256sum "$store/j72-root-contract.json" | busybox awk '{print $1}')" = CONTRACT ] || return 1
 [ "$(busybox stat -c %s "$store/base/desktop-A.squashfs")" = 572002304 ] || return 1
 loop=$(busybox losetup -f)
 case ${loop#/dev/loop} in ''|*[!0-9]*) return 1;; esac
 [ ! -e "/sys/class/block/${loop##*/}/loop/backing_file" ] || return 1
 busybox losetup -r "$loop" "$store/base/desktop-A.squashfs"
 echo "$loop" > "$state/container-loop"
 [ "$(cat "/sys/class/block/${loop##*/}/ro")" = 1 ] || return 1
 mount -t squashfs -o ro "$loop" "$root"
'''.replace('CONTRACT', sha(WORK / 'local-root-image/staging/j72-root-contract.json'))
    source = source.replace(old, before)
    old = ' if [ "$(cat /sys/block/nbd2/size)" != 0 ]; then busybox nbd-client -d /dev/nbd2; fi\n'
    assert source.count(old) == 1
    cleanup = ''' if [ -f "$state/container-loop" ]; then
  loop=$(cat "$state/container-loop")
  case ${loop#/dev/loop} in ''|*[!0-9]*) return 1;; esac
  [ "$(cat "/sys/class/block/${loop##*/}/ro")" = 1 ] || return 1
  [ "$(cat "/sys/class/block/${loop##*/}/loop/backing_file")" = /mnt/j72-store/base/desktop-A.squashfs ] || return 1
  busybox losetup -d "$loop"
  rm "$state/container-loop"
 fi
 if mounted /mnt/j72-store; then umount /mnt/j72-store; fi
'''
    source = source.replace(old, cleanup + old)
    (OUT / 'controller.sh').write_text(source)
    subprocess.run(['sh', '-n', str(OUT / 'controller.sh')], check=True)
    m.update(profile='j72-container-desktop35-v1', nbd_port=10832,
             image=str(image), image_bytes=image_result['image_bytes'], image_sha256=image_result['image_sha256'],
             outer_filesystem='ext4 ro,noload', inner_filesystem='read-only loop/SquashFS',
             internal_storage_access=False, requires_usb_cable_until_stop=True,
             device_boot_tested=False, status='OFFLINE_PREPARED_DEVICE_UNTESTED')
    # Keep common source/kernel/payload pins; replace only the test artifact pins.
    excluded = {str((SOURCE / name).relative_to(ROOT)) for name in ('squashfs.ko', 'autostart', 'controller.sh')}
    files = {name: digest for name, digest in m['files'].items()
             if name not in excluded and not name.endswith('desktop-capacity.squashfs')}
    for path in [Path(__file__), ROOT / 'tools/run-j72-compressed-desktop.py',
                 WORK / 'local-root-image/result.json', image,
                 *[OUT / name for name in ('squashfs.ko', 'autostart', 'controller.sh')]]:
        files[str(path.relative_to(ROOT))] = sha(path)
    m['files'] = files
    (OUT / 'manifest.json').write_text(json.dumps(m, indent=2) + '\n')
    print('Prepared #35 read-only container/loop/SquashFS USB rehearsal; no native disk or writes')


if __name__ == '__main__':
    main()
