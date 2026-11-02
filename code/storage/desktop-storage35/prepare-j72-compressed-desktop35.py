#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Reuse the qualified compressed desktop format with an exact #35 module."""
import hashlib
import json
import os
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'private/j72-platform/power-storage-20261102'
BASE = WORK / 'compressed-root-prep/desktop-test34'
OUT = WORK / 'desktop-storage35/compressed-desktop'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    os.umask(0o077)
    assert not OUT.exists(), 'Refuse to overwrite a prepared test'
    source = json.loads((BASE / 'wifi-resume-tested-manifest.json').read_text())
    native = json.loads((WORK / 'desktop-storage35/manifest.json').read_text())
    assert native['uts_version'] == '#35 SMP PREEMPT Mon Nov 2 07:00:00 +08 2026'
    OUT.mkdir()
    for name in ('controller.sh', 'autostart'):
        assert sha(BASE / name) == source['files'][str((BASE / name).relative_to(ROOT))]
        shutil.copyfile(BASE / name, OUT / name)
    controller = OUT / 'controller.sh'
    text = controller.read_text()
    previous = '#34 SMP PREEMPT Sun Nov  1 07:40:27 +08 2026'
    assert text.count(previous) == 1
    controller.write_text(text.replace(previous, native['uts_version']))
    module = WORK / 'desktop-storage35/payload/rootfs/lib/modules/7.0.12-j72spi2/kernel/fs/squashfs/squashfs.ko'
    assert sha(module) == native['overlay_files'][str(module.relative_to(WORK / 'desktop-storage35/payload/rootfs'))]
    shutil.copyfile(module, OUT / 'squashfs.ko')
    module_inputs = json.loads((WORK / 'desktop-storage35/module-inputs.json').read_text())
    m = {k: v for k, v in source.items() if k not in ('files', 'base_kernel_files')}
    m.update(profile='j72-compressed-desktop35-v1', status='OFFLINE_PREPARED_DEVICE_UNTESTED',
             kernel_build=native['uts_version'],
             kernel_sha256=module_inputs['kernel_base_files']['private/j72-platform/power-storage-20261102/storage-kernel/out/arch/arm64/boot/Image'],
             boot_payload=native['payload'], boot_payload_sha256=native['payload_sha256'],
             base_kernel_files=module_inputs['kernel_base_files'], runtime_resume_added=True)
    files = ['tools/prepare-j72-compressed-desktop35.py', 'tools/run-j72-compressed-desktop.py',
             'tools/j72-desktop-storage35-host.py', 'tools/j72-wifi-host.py',
             'tools/run-j72-reader-audit.py', 'tools/run-j72-input-limit-hub1050-desktop.py',
             'tools/run-j72-wlan-enumeration-v2.py',
             str((WORK / 'desktop-storage35/manifest.json').relative_to(ROOT)),
             str((WORK / 'desktop-storage35/module-result.json').relative_to(ROOT)),
             str(Path(m['image']).relative_to(ROOT))]
    files += [str((OUT / name).relative_to(ROOT)) for name in ('controller.sh', 'autostart', 'squashfs.ko')]
    m['files'] = {name: sha(ROOT / name) for name in files}
    assert sha(Path(m['image'])) == m['image_sha256']
    (OUT / 'manifest.json').write_text(json.dumps(m, indent=2) + '\n')
    print('Prepared exact #35 compressed desktop candidate; controller build gate updated, lifecycle/autostart unchanged; device untested')


if __name__ == '__main__':
    main()
