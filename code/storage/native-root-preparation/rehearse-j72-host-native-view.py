#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Rehearse the proposed bounded native root on a NEW disposable host file.

No iPad connection, target block device argument, modprobe or kernel change.
Uses only a newly attached read-only host loop and a newly owned read-only DM map.
"""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'private/j72-platform/power-storage-20261102/desktop-storage35'
sys.path.insert(0, '/home/pi/ipad-air-j72-linux/code/storage')
import j72_storage_preflight as g
import j72_native_view_plan as view


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for data in iter(lambda: f.read(1 << 20), b''): h.update(data)
    return h.hexdigest()


def run(args, **kw):
    return subprocess.run(args, check=True, capture_output=True, timeout=45, **kw)


def main():
    assert os.geteuid() == 0, 'Private host inputs and isolated read-only loop/DM mounts need sudo'
    os.umask(0o077)
    kernel = os.uname().release
    image = WORK / 'local-root-image/j72-local-root-1536.ext4'
    reference = json.loads((WORK / 'local-root-image/result.json').read_text())
    assert image.is_file() and not image.is_symlink() and image.stat().st_size == view.CONTAINER_BYTES
    assert sha(image) == reference['image_sha256']
    proposal = WORK / 'layout-rehearsal-v2'
    captured = {key: g.regular_bytes(proposal / (key.replace('_', '-') + '.bin'),
                                    16384 if 'entries' in key else 4096)
                for key in ('mbr', 'primary_header', 'primary_entries', 'backup_header', 'backup_entries')}
    inventory = g.audit(g.Geometry(4096, 31_250_000), **captured)
    plan = view.native_view_plan(inventory)
    assert plan['view_bytes'] == image.stat().st_size
    assert os.statvfs(WORK).f_bavail * os.statvfs(WORK).f_frsize > 3 * (1 << 30)
    assert b'linear' in run(['dmsetup', 'targets']).stdout
    name = 'j72-host-ro-rehearsal-' + time.strftime('%Y%m%d-%H%M%S')
    out = WORK / name; out.mkdir(mode=0o700)
    disk = out / 'disposable-host-disk.raw'
    with disk.open('xb') as f:
        f.truncate(128_000_000_000)
        for key, lba in [('mbr', 0), ('primary_header', 1), ('primary_entries', 2),
                         ('backup_entries', 31_249_995), ('backup_header', 31_249_999)]:
            f.seek(lba * 4096); f.write(captured[key])
    assert stat.S_ISREG(disk.lstat().st_mode)
    offset = view.FIRST * 4096
    assert offset % (1 << 20) == 0
    print('Preparing sparse disposable host disk; iPad is not contacted', flush=True)
    run(['dd', 'if=' + str(image), 'of=' + str(disk), 'bs=1048576',
         'seek=' + str(offset // (1 << 20)), 'conv=notrunc,sparse', 'status=none'])
    mountpoint = out / 'root'; mountpoint.mkdir()
    loop = None; mapping = None; mounted = False
    result = dict(status='HOST_REHEARSAL_IN_PROGRESS', ipad_contacted=False,
                  internal_storage_writes=False, native_root_boot_tested=False)
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    try:
        loop = run(['losetup', '--find', '--show', '--read-only', '--sector-size', '4096', str(disk)]).stdout.decode().strip()
        assert loop.startswith('/dev/loop') and Path(loop).name[4:].isdigit()
        sysloop = Path('/sys/class/block') / Path(loop).name
        assert (sysloop / 'ro').read_text().strip() == '1'
        assert Path((sysloop / 'loop/backing_file').read_text().strip()) == disk
        assert (sysloop / 'queue/logical_block_size').read_text().strip() == '4096'
        major_minor = (sysloop / 'dev').read_text().strip()
        table = f'0 {view.CONTAINER_BYTES // 512} linear {major_minor} {offset // 512}'
        assert subprocess.run(['dmsetup', 'info', name], capture_output=True).returncode != 0
        run(['dmsetup', '--noudevsync', 'create', name, '--readonly', '--table', table])
        mapping = '/dev/mapper/' + name
        run(['dmsetup', 'mknodes', name])
        run(['udevadm', 'settle', '--timeout=5'])
        assert run(['dmsetup', 'table', name]).stdout.decode().strip() == table
        assert run(['blockdev', '--getsize64', mapping]).stdout.decode().strip() == str(view.CONTAINER_BYTES)
        assert run(['blockdev', '--getro', mapping]).stdout.decode().strip() == '1'
        # EOF at the exact fence. No writes are attempted, including a test write.
        node = Path(mapping).resolve(strict=True)
        info = node.stat(); assert stat.S_ISBLK(info.st_mode)
        dev = f'{os.major(info.st_rdev)}:{os.minor(info.st_rdev)}'
        assert (Path('/sys/dev/block') / dev / 'dm/name').read_text().strip() == name
        fd = os.open(node, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            assert os.pread(fd, 4096, view.CONTAINER_BYTES) == b''
            with image.open('rb') as f:
                for position in (0, view.CONTAINER_BYTES - 4096):
                    f.seek(position); assert os.pread(fd, 4096, position) == f.read(4096)
        finally: os.close(fd)
        run(['e2fsck', '-fn', mapping])
        run(['mount', '-t', 'ext4', '-o', 'ro,noload,nodev,nosuid,noexec', mapping, str(mountpoint)])
        mounted = True
        contract = json.loads((mountpoint / 'j72-root-contract.json').read_text())
        assert contract['container_bytes'] == view.CONTAINER_BYTES and contract['writable_runtime'] == 'RAM'
        assert contract['persistent_overlay_enabled'] is False
        assert sha(mountpoint / contract['active_base']) == reference['base_sha256']
        assert os.statvfs(mountpoint).f_flag & os.ST_RDONLY
        result.update(status='HOST_4K_LOOP_BOUNDED_READONLY_DM_EXT4_BASE_PASS',
                      backing_loop_read_only=True, backing_logical_block_bytes=4096,
                      view_read_only=True, view_bytes=view.CONTAINER_BYTES,
                      dm_sector_bytes=512, exact_table_backing_and_length_pass=True,
                      eof_at_partition_boundary_pass=True, readonly_fsck_pass=True,
                      readonly_ext4_mount_pass=True, base_hash_readback_pass=True,
                      persistent_overlay_enabled=False)
    finally:
        if mounted: run(['umount', str(mountpoint)])
        # Exceptions here stop cleanup rather than tearing down a mounted or
        # otherwise busy device. Never use lazy unmount or forced map removal.
        if mapping: run(['dmsetup', '--noudevsync', 'remove', '--retry', name])
        if loop: run(['losetup', '--detach', loop])
    assert sha(image) == reference['image_sha256'] and os.uname().release == kernel
    result.update(normal_unmount_map_removal_loop_detach_pass=True, source_image_unchanged=True,
                  host_kernel_unchanged=True, approval_ready=False, tool_sha256=sha(Path(__file__)))
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS disposable HOST file: 4KiB RO loop -> bounded RO map -> ext4/base hash; normal cleanup')
    print('Private receipt:', out)


if __name__ == '__main__': main()
