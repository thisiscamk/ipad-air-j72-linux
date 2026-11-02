#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Prepare a full #35 desktop/storage RAM payload, then use orchard build."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'private/j72-platform/power-storage-20261102'
OUT = WORK / 'desktop-storage35'
BASE = WORK / 'storage-observer35'
OLD = ROOT / 'private/j72-platform/wifi-ram-desktop'
VERSION = '#35 SMP PREEMPT Mon Nov 2 07:00:00 +08 2026'
RELEASE = '7.0.12-j72spi2'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    os.umask(0o077)
    assert not (OUT / 'payload').exists(), 'Refuse to overwrite an assembled candidate'
    result = json.loads((OUT / 'module-result.json').read_text())
    assert result['kernel_base_files_unchanged'] and result['kernel_version'] == VERSION
    base = json.loads((BASE / 'manifest.json').read_text())
    assert sha(Path(base['payload'])) == base['payload_sha256']
    assert base['payload_sha256'] == 'a132327742bf7942c1bbccdc8a38e0039921209edbbc31dada860d41e1dd5661'
    old = json.loads((OLD / 'manifest.json').read_text())
    for name, digest in old['overlay_files'].items():
        assert sha(OLD / 'overlay' / name) == digest, name
    for name, info in result['modules'].items():
        assert sha(OUT / 'modules' / name) == info['sha256'], name
    (OUT / 'payload').mkdir()
    payload = OUT / 'payload'
    root = payload / 'rootfs'
    shutil.copytree(OLD / 'overlay', root)
    assert not any(p.is_symlink() for p in root.rglob('*')), 'Orchard payload files must be regular'
    # Recompile modules and update the matching userspace build gate together.
    # Never leave a #34 controller accepting a #35 module merely by release name.
    old_version = '#34 SMP PREEMPT Sun Nov  1 07:40:27 +08 2026'
    for path in (root / 'sbin').iterdir():
        if path.is_file() and path.read_bytes().startswith(b'#!'):
            text = path.read_text()
            if old_version in text:
                path.write_text(text.replace(old_version, VERSION))
    # The validated #35 recovery init provides static BusyBox aliases and both
    # recovery shells. Keep radio, touch, storage and charging opt-in initially.
    text = (BASE / 'payload/init').read_text()
    assert 'storage-observer35-recovery-only' in text
    text = text.replace('storage-observer35-recovery-only', 'desktop-storage35-recovery-only')
    text = text.replace('J72 storage observer:', 'J72 desktop/storage candidate:')
    marker = '# ------------------------------------------------------------------ console'
    assert text.count(marker) == 1
    text = text.replace(marker, '/sbin/j72-wifi-widget </dev/null >/run/j72-wifi-widget.log 2>&1 &\n'
                        'echo $! >/run/j72-wifi-widget.pid\n\n' + marker)
    (payload / 'init').write_text(text)
    (payload / 'init').chmod(0o755)
    (root / 'init').unlink()
    (payload / 'payload.toml').write_text('transport = false\nmodules = false\nfirmware = false\n')
    module_root = root / 'lib/modules' / RELEASE
    shutil.rmtree(module_root)
    module_root.mkdir(parents=True)

    def module(source, destination):
        target = root / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        subprocess.run(['strip', '--strip-debug', str(target)], check=True)

    # Recovery modules must match #35, even though uname -r is shared with #34.
    for name in ('drivers/usb/gadget/function/usb_f_ncm.ko', 'drivers/usb/gadget/function/usb_f_fs.ko',
                 'drivers/input/evdev.ko', 'drivers/block/nbd.ko'):
        source = BASE / 'payload/rootfs/lib/modules' / RELEASE / 'kernel' / name
        assert sha(source) == base['files'][str(source.relative_to(BASE))]
        module(source, 'lib/modules/' + RELEASE + '/kernel/' + name)
    for name in result['modules']:
        if name.startswith(('charge/', 'snapshot/')) or '/bca/' in name or '/cyw/' in name:
            continue
        if name.startswith(('net/', 'drivers/')):
            destination = 'kernel/' + name
        elif name == 'squashfs/squashfs.ko':
            destination = 'kernel/fs/squashfs/squashfs.ko'
        else:
            destination = 'extra/' + Path(name).name
        module(OUT / 'modules' / name, 'lib/modules/' + RELEASE + '/' + destination)
    module(OUT / 'modules/touch/j72_touch_session.ko', 'opt/j72/j72_touch_session.ko')
    for name, target in [('charge/j72_charge_maintain35.ko', 'opt/j72/charge-maintain35.ko'),
                         ('snapshot/j72_wlan_ready_snapshot.ko', 'opt/j72/wlan-ready35.ko')]:
        module(OUT / 'modules' / name, target)
    source = BASE / 'payload/rootfs/opt/j72/asp-readonly.ko'
    assert sha(source) == base['files']['payload/rootfs/opt/j72/asp-readonly.ko']
    module(source, 'opt/j72/asp-readonly.ko')
    for name in ('modules.builtin', 'modules.builtin.modinfo'):
        shutil.copyfile(WORK / 'storage-kernel/out' / name, module_root / name)
    (module_root / 'modules.order').write_text(''.join(str(p.relative_to(module_root)) + '\n'
                                                   for p in sorted(module_root.rglob('*.ko'))))
    subprocess.run(['depmod', '-e', '-F', str(WORK / 'storage-kernel/out/System.map'),
                    '-b', str(root), RELEASE], check=True, capture_output=True)
    # Cold image must never auto-probe storage or arm charging/radio.
    assert not list(module_root.rglob('*asp*.ko'))
    assert not list(module_root.rglob('*maintain*.ko'))
    for name in ('usb_f_ncm', 'usb_f_fs', 'evdev', 'nbd', 'squashfs', 'brcmfmac_wcc'):
        deps = subprocess.check_output(['modprobe', '-d', str(root), '-S', RELEASE,
                                        '--show-depends', name], text=True)
        assert 'insmod' in deps, name
        if name == 'brcmfmac_wcc':
            assert deps.index('j72_wlan_transport_v3.ko') < deps.index('/brcmfmac.ko') < deps.index('/brcmfmac-wcc.ko')
    for name in ['init', *[str(p.relative_to(payload)) for p in (root / 'sbin').glob('j72-*')]]:
        subprocess.run(['sh', '-n', str(payload / name)], check=True)
    inputs = {str(Path(__file__).relative_to(ROOT)): sha(Path(__file__)),
              str((OUT / 'module-result.json').relative_to(ROOT)): sha(OUT / 'module-result.json'),
              str((BASE / 'manifest.json').relative_to(ROOT)): sha(BASE / 'manifest.json'),
              str((OLD / 'manifest.json').relative_to(ROOT)): sha(OLD / 'manifest.json')}
    (OUT / 'payload-inputs.json').write_text(json.dumps({
        'profile': 'desktop-storage35', 'uts_version': VERSION, 'inputs': inputs,
        'overlay_files': {str(p.relative_to(root)): sha(p) for p in sorted(root.rglob('*')) if p.is_file()},
        'init_sha256': sha(payload / 'init'), 'storage_autoload': False,
        'radio_autoload': False, 'charging_autoload': False, 'touch_autoload': False,
        'internal_write_support': False, 'device_tested': False,
    }, indent=2) + '\n')
    # The public Orchard entry point owns cache access and component locking.
    build = json.loads((BASE / 'payload/out/apple-4k/build.json').read_text())
    checkout = WORK / 'orchard-source/OrchardLinux-orchard-25b46df'
    command = [str(WORK / 'orchard-venv/bin/orchard'), 'build', str(payload),
               '--platform', 'apple-4k', '--hardware', str(checkout),
               '--cache', str(WORK / 'orchard-cache'), '--kernel-dir', str(BASE / 'kernel'),
               '--loader', build['assembly']['loader'], '--pongo', str(BASE / 'payload/out/apple-4k/pongo.bin')]
    with (OUT / 'build-payload.log').open('wb') as log:
        subprocess.run(command, cwd=checkout, stdout=log, stderr=subprocess.STDOUT, check=True)
    print('PASS: orchard build assembled combined #35 RAM candidate; no device accessed; final audit pending')


if __name__ == '__main__':
    main()
