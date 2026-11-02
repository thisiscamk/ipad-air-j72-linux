#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Audit the assembled #35 combined RAM payload; no device access."""
import gzip
import hashlib
import json
from pathlib import Path
import stat
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'private/j72-platform/power-storage-20261102'
OUT = WORK / 'desktop-storage35'
BASE = WORK / 'storage-observer35'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    m = json.loads((OUT / 'payload-inputs.json').read_text())
    for name, digest in m['inputs'].items():
        assert sha((ROOT / name).read_bytes()) == digest, name
    for name, digest in m['overlay_files'].items():
        assert sha((OUT / 'payload/rootfs' / name).read_bytes()) == digest, name
    out = OUT / 'payload/out/apple-4k'
    receipt = json.loads((out / 'linux.bin.json').read_text())
    original = json.loads((BASE / 'payload/out/apple-4k/linux.bin.json').read_text())
    image = (out / 'linux.bin').read_bytes()
    assert len(image) <= 128 * 1024 * 1024
    before = [c for c in original['components'] if c['name'] not in ('initramfs', 'initramfs_header')]
    after = [c for c in receipt['components'] if c['name'] not in ('initramfs', 'initramfs_header')]
    assert before == after, 'Loader, bootargs, DTBs or kernel changed from proven storage boot'
    for c in receipt['components']:
        data = image[c['offset']:c['offset'] + c['bytes']]
        assert sha(data) == c['sha256'], c['name']
        if c['name'] == 'kernel':
            assert sha(gzip.decompress(data)) == '84c5e14862923ec27a28cf6bdc08c8c294500e432ddf548e66a44d5f9cf53955'
        elif c['name'] == 'initramfs_header':
            assert data[:14] == b'm1n1_initramfs'
            assert struct.unpack_from('<I', data, 14)[0] == (out / 'initramfs.cpio.gz').stat().st_size
    archive = gzip.decompress((out / 'initramfs.cpio.gz').read_bytes())
    offset = 0
    entries = {}
    while offset + 110 <= len(archive):
        assert archive[offset:offset + 6] == b'070701'
        fields = [int(archive[offset + 6 + i * 8:offset + 14 + i * 8], 16) for i in range(13)]
        size, namesize = fields[6], fields[11]
        assert 1 <= namesize <= 4096
        name = archive[offset + 110:offset + 110 + namesize - 1].decode()
        start = (offset + 110 + namesize + 3) & ~3
        assert start + size <= len(archive)
        data = archive[start:start + size]
        offset = (start + size + 3) & ~3
        if name == 'TRAILER!!!':
            break
        path = Path(name)
        assert not path.is_absolute() and '..' not in path.parts and name not in entries
        entries[name] = (fields[1], data)
    assert 'TRAILER!!!' == name
    init = entries['init'][1].decode()
    assert init.startswith('#!/bin/busybox sh\n') and 'busybox --install -s /bin' in init
    assert 'desktop-storage35-recovery-only' in init
    assert '/sbin/j72-session-autostart' not in init and 'insmod' not in init
    assert sha(entries['init'][1]) == m['init_sha256']
    assert entries['init'][0] & 0o111
    assert entries['bin/busybox'][1].startswith(b'\x7fELF\x02\x01')
    controller = entries['sbin/j72-touch-session'][1]
    assert b'#35 SMP PREEMPT Mon Nov 2 07:00:00 +08 2026' in controller
    for name, (_, data) in entries.items():
        if name.startswith('sbin/') and data.startswith(b'#!'):
            assert b'#34 SMP PREEMPT' not in data, name
    for name, digest in m['overlay_files'].items():
        assert stat.S_ISREG(entries[name][0]) and sha(entries[name][1]) == digest, name
    module_paths = sorted(n for n in entries if n.endswith('.ko'))
    release = 'lib/modules/7.0.12-j72spi2/'
    dep = entries[release + 'modules.dep'][1].decode()
    assert 'asp' not in dep and 'maintain' not in dep, 'Explicit-only owners entered module autoload index'
    assert 'opt/j72/asp-readonly.ko' in module_paths and 'opt/j72/charge-maintain35.ko' in module_paths
    # Only actual included providers may satisfy imports, not an unbuilt module.
    names = {Path(name).name for name in module_paths}
    exports = set()
    for table in [WORK / 'storage-kernel/out/Module.symvers', OUT / 'modules/Module.symvers']:
        for line in table.read_text().splitlines():
            fields = line.split()
            if fields[2] == 'vmlinux' or Path(fields[2]).name + '.ko' in names:
                exports.add(fields[1])
    for name in module_paths:
        path = OUT / 'payload/rootfs' / name
        imports = [parts[1] for line in subprocess.check_output(['nm', '-u', str(path)], text=True).splitlines()
                   if len(parts := line.split()) == 2 and parts[0] == 'U']
        assert not (set(imports) - exports), (name, sorted(set(imports) - exports))
    sources = json.loads((OUT / 'module-inputs.json').read_text())
    for name, digest in sources['kernel_base_files'].items():
        assert sha((ROOT / name).read_bytes()) == digest
    m.update(payload=str(out / 'linux.bin'), payload_sha256=sha(image), payload_bytes=len(image),
             same_proven_loader_dtb_kernel=True, archive_entries=len(entries),
             matching_module_build_pass=True, strong_imports_resolved=True,
             files={str(p.relative_to(OUT)): sha(p.read_bytes()) for p in [
                 out / 'linux.bin', out / 'linux.bin.json', out / 'initramfs.cpio.gz', out / 'build.json',
                 OUT / 'module-inputs.json', OUT / 'module-result.json']})
    m['inputs'][str(Path(__file__).relative_to(ROOT))] = sha(Path(__file__).read_bytes())
    (OUT / 'manifest.json').write_text(json.dumps(m, indent=2) + '\n')
    print('PASS: exact proven #35 loader/DTB/kernel, framing, full archive and explicit-only owners')
    print('Candidate bytes:', len(image), '; SHA256:', m['payload_sha256'])


if __name__ == '__main__':
    main()
