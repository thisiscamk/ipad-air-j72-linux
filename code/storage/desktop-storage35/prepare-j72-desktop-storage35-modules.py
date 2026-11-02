#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build an isolated #35 desktop/radio/filesystem module closure; no device access."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
POWER = ROOT / 'private/j72-platform/power-wifi-20261101'
WORK = ROOT / 'private/j72-platform/power-storage-20261102'
KERNEL = WORK / 'storage-kernel'
OUT = WORK / 'desktop-storage35'
VERSION = '#35 SMP PREEMPT Mon Nov 2 07:00:00 +08 2026'
OLD_VERSION = '#34 SMP PREEMPT Sun Nov  1 07:40:27 +08 2026'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    os.umask(0o077)
    assert not OUT.exists(), 'Refuse to overwrite a candidate or its build evidence'
    base = json.loads((WORK / 'compressed-root-prep/module-inputs.json').read_text())['base_files']
    for name, digest in base.items():
        assert sha(ROOT / name) == digest, name
    assert VERSION in (KERNEL / 'out/include/generated/utsversion.h').read_text()
    v4 = json.loads((POWER / 'wifi-driver-v4/staged/manifest.json').read_text())
    for name, digest in v4['files'].items():
        assert sha(ROOT / name) == digest, name
    touch = ROOT / 'private/j72-touch/continuous-session/module34'
    touch_receipt = json.loads((touch.parent / 'build-result.json').read_text())['builds']['module34']
    assert sha(touch / 'j72_touch_session.c') == touch_receipt['source_sha256']
    OUT.mkdir()
    modules = OUT / 'modules'
    modules.mkdir()
    inputs = {'tools/prepare-j72-desktop-storage35-modules.py': sha(Path(__file__))}

    def copy_sources(source, destination):
        # Firmware includes stay private. Never copy old objects or module metadata.
        for path in sorted(source.rglob('*')):
            if not path.is_file() or path.name.endswith('.mod.c'):
                continue
            if path.suffix not in ('.c', '.h', '.inc', '.hex') and path.name not in ('Makefile', 'Kconfig'):
                continue
            target = destination / path.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            inputs[str(path.relative_to(ROOT))] = sha(path)

    for name in ('net/wireless', 'net/rfkill'):
        copy_sources(KERNEL / 'src' / name, modules / name)
    wireless = 'drivers/net/wireless/broadcom/brcm80211'
    copy_sources(POWER / 'wifi-driver-v4/src' / wireless, modules / wireless)
    copy_sources(touch, modules / 'touch')
    copy_sources(POWER / 'wlan-transport-v3', modules / 'radio')
    copy_sources(POWER / 'wlan-ready-observer34', modules / 'snapshot')
    copy_sources(KERNEL / 'src/fs/squashfs', modules / 'squashfs')
    copy_sources(WORK / 'maintain34/module', modules / 'charge')
    # Only exact-build gates and descriptions change in these already-tested owners.
    for name in ('radio/j72_wlan_transport_v3.c', 'snapshot/j72_wlan_ready_snapshot.c',
                 'charge/j72_charge_maintain34.c'):
        path = modules / name
        text = path.read_text()
        assert text.count(OLD_VERSION) == 1, name
        text = text.replace(OLD_VERSION, VERSION).replace('J72/#34', 'J72/#35')
        path.write_text(text)
    # Use a distinct maintenance owner; never confuse a #34 worker with #35.
    source = modules / 'charge/j72_charge_maintain34.c'
    source.rename(source.with_name('j72_charge_maintain35.c'))
    (modules / 'charge/Makefile').write_text('obj-m += j72_charge_maintain35.o\nccflags-y += -I$(srctree)/drivers/usb/dwc2\n')
    paths = ['net/wireless', 'net/rfkill', wireless + '/brcmutil', wireless + '/brcmfmac',
             'touch', 'radio', 'snapshot', 'squashfs', 'charge']
    (modules / 'Makefile').write_text('obj-m += ' + ' '.join(p + '/' for p in paths) + '\n')
    (OUT / 'module-inputs.json').write_text(json.dumps({
        'kernel_base_files': base, 'copied_source_files': inputs,
        'kernel_version': VERSION, 'internal_storage_access': False,
        'runtime_policy_changes': False, 'firmware_includes_private': True,
        'status': 'PREPARED_NOT_BUILT',
    }, indent=2) + '\n')
    command = ['make', '-C', str(KERNEL / 'src'), 'O=' + str(KERNEL / 'out'),
               'ARCH=arm64', 'M=' + str(modules), '-j2', 'modules']
    with (OUT / 'build-modules.log').open('wb') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    for name, digest in base.items():
        assert sha(ROOT / name) == digest, 'Pinned kernel input changed: ' + name
    if result.returncode:
        raise RuntimeError('Module build failed; retain private build log and unchanged kernel inputs')
    # Resolve only actual built-in exports and modules that will be packaged.
    exports = {line.split()[1] for line in (KERNEL / 'out/Module.symvers').read_text().splitlines()
               if line.split()[2] == 'vmlinux'}
    exports |= {line.split()[1] for line in (modules / 'Module.symvers').read_text().splitlines()}
    results = {}
    for path in sorted(modules.rglob('*.ko')):
        imports = [parts[1] for line in subprocess.check_output(['nm', '-u', str(path)], text=True).splitlines()
                   if len(parts := line.split()) == 2 and parts[0] == 'U']
        missing = sorted(set(imports) - exports)
        assert not missing, (path, missing)
        vermagic = subprocess.check_output(['modinfo', '-F', 'vermagic', str(path)], text=True).strip()
        assert vermagic == '7.0.12-j72spi2 SMP preempt aarch64', path
        results[str(path.relative_to(modules))] = {'sha256': sha(path), 'strong_imports': len(imports), 'missing': []}
    assert len(results) >= 10, 'Incomplete radio/input/filesystem closure'
    (OUT / 'module-result.json').write_text(json.dumps({
        'status': 'BUILT_IMPORTS_AND_UNCHANGED_KERNEL_PASS_DEVICE_UNTESTED',
        'kernel_version': VERSION, 'modules': results,
        'kernel_base_files_unchanged': True, 'internal_storage_access': False,
    }, indent=2) + '\n')
    print('PASS: isolated exact #35 module closure; all strong imports resolved, kernel pins unchanged; device untested')


if __name__ == '__main__':
    main()
