#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Rehearse a 1536 MiB ext4 container with a compressed base, on host files only."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'private/j72-platform/power-storage-20261102'
OUT = WORK / 'desktop-storage35/local-root-image'
SOURCE = WORK / 'compressed-root-prep/desktop-capacity.squashfs'
BYTES = 1536 * 1024 * 1024
BASE_SHA = '8553fcf74045771ff67a72e35b6cedec3a330cef71437a1044546fa13721cd9d'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    os.umask(0o077)
    assert os.geteuid() == 0, 'Use sudo for private inputs and read-only host loop mount'
    assert not OUT.exists(), 'Refuse to overwrite a prepared image'
    assert SOURCE.is_file() and SOURCE.stat().st_size == 572002304 and sha(SOURCE) == BASE_SHA
    OUT.mkdir()
    stage = OUT / 'staging'
    (stage / 'base').mkdir(parents=True)
    (stage / 'state').mkdir()
    shutil.copyfile(SOURCE, stage / 'base/desktop-A.squashfs')
    contract = {'profile': 'j72-local-root-container-v1', 'model': 'Apple iPad Air (Cellular)',
                'container_bytes': BYTES, 'container_filesystem': 'ext4',
                'active_base': 'base/desktop-A.squashfs', 'base_sha256': BASE_SHA,
                'initial_container_mount': 'ro,noload,nodev,nosuid', 'base_mount': 'squashfs,ro',
                'writable_runtime': 'RAM', 'persistent_overlay_enabled': False,
                'installation_authorized': False}
    (stage / 'j72-root-contract.json').write_text(json.dumps(contract, indent=2) + '\n')
    image = OUT / 'j72-local-root-1536.ext4'
    with image.open('xb') as stream:
        stream.truncate(BYTES)
    assert stat.S_ISREG(image.stat().st_mode) and not image.is_symlink()
    tools = {name: Path(shutil.which(name)) for name in ('mke2fs', 'e2fsck', 'losetup', 'mount', 'umount')}
    tool_hashes = {name: sha(path) for name, path in tools.items()}
    with (OUT / 'make-filesystem.log').open('wb') as log:
        subprocess.run([str(tools['mke2fs']), '-q', '-t', 'ext4', '-b', '4096', '-m', '0',
                        '-L', 'J72LINUX', '-O', '^orphan_file,^metadata_csum_seed',
                        '-E', 'lazy_itable_init=0,lazy_journal_init=0', '-d', str(stage), str(image)],
                       stdout=log, stderr=subprocess.STDOUT, check=True, timeout=180)
    with (OUT / 'readonly-fsck.log').open('wb') as log:
        subprocess.run([str(tools['e2fsck']), '-fn', str(image)], stdout=log,
                       stderr=subprocess.STDOUT, check=True, timeout=180)
    mountpoint = OUT / 'check-mount'
    mountpoint.mkdir()
    loop = None
    mounted = False
    try:
        loop = subprocess.check_output([str(tools['losetup']), '--find', '--show', '--read-only', str(image)], text=True).strip()
        assert Path(loop).name.startswith('loop') and Path('/sys/class/block', Path(loop).name, 'ro').read_text().strip() == '1'
        subprocess.run([str(tools['mount']), '-t', 'ext4', '-o', 'ro,noload,nodev,nosuid,noexec', loop, str(mountpoint)], check=True, timeout=10)
        mounted = True
        assert sha(mountpoint / 'base/desktop-A.squashfs') == BASE_SHA
        assert json.loads((mountpoint / 'j72-root-contract.json').read_text()) == contract
        fs = os.statvfs(mountpoint)
        assert fs.f_flag & os.ST_RDONLY
        available = fs.f_bavail * fs.f_frsize
        second_base_headroom = available - SOURCE.stat().st_size
        assert second_base_headroom > 256 * 1024 * 1024, 'Insufficient budget for a second equal-size base and 256 MiB state'
    finally:
        if mounted:
            subprocess.run([str(tools['umount']), str(mountpoint)], check=True, timeout=10)
        # Do not detach a loop device if normal unmount failed.
        if loop:
            subprocess.run([str(tools['losetup']), '--detach', loop], check=True, timeout=10)
    assert image.stat().st_size == BYTES and sha(SOURCE) == BASE_SHA
    result = {'status': 'HOST_FILE_CAPACITY_FSCK_READBACK_CLEANUP_PASS_DEVICE_UNTESTED',
              'image_bytes': BYTES, 'image_sha256': sha(image), 'base_bytes': SOURCE.stat().st_size,
              'base_sha256': BASE_SHA, 'available_bytes_after_first_base': available,
              'remaining_bytes_after_equal_second_base': second_base_headroom,
              'readonly_fsck_pass': True, 'readonly_loop_readback_pass': True,
              'normal_host_unmount_and_loop_detach': True, 'source_unchanged': True,
              'device_access': False, 'internal_storage_writes': False,
              'native_root_boot_tested': False, 'persistent_overlay_enabled': False,
              'tools': tool_hashes, 'source_sha256': sha(Path(__file__))}
    (OUT / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS: 1536 MiB host-file filesystem, read-only fsck/readback/cleanup; no iPad access')
    print('Free bytes:', available, '; after an equal second base:', second_base_headroom)


if __name__ == '__main__':
    main()
