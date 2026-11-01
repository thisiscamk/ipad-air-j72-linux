#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Audit/stage a private J72 WLAN candidate offline; never contact a device.

This packages build inputs, not a working Wi-Fi image. HSIC, reset sequencing
and the BCM4324B5 USB transport must still be implemented and qualified.
"""
import argparse
import fnmatch
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
import zlib

WLAN = 'drivers/net/wireless/broadcom/brcm80211'
MODULES = (
    'net/rfkill/rfkill.ko', 'net/wireless/cfg80211.ko',
    f'{WLAN}/brcmutil/brcmutil.ko', f'{WLAN}/brcmfmac/brcmfmac.ko',
    f'{WLAN}/brcmfmac/wcc/brcmfmac-wcc.ko',
)
REQUIRED = {'CONFIG_WIRELESS': 'y', 'CONFIG_WLAN': 'y',
            'CONFIG_CFG80211': 'm', 'CONFIG_RFKILL': 'm',
            'CONFIG_BRCMUTIL': 'm', 'CONFIG_BRCMFMAC': 'm',
            'CONFIG_BRCMFMAC_USB': 'y', 'CONFIG_BRCMFMAC_PROTO_BCDC': 'y',
            'CONFIG_USB_EHCI_HCD': 'y', 'CONFIG_USB_EHCI_HCD_PLATFORM': 'y',
            'CONFIG_MODULE_UNLOAD': 'n', 'CONFIG_MODVERSIONS': 'n'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def output(*args):
    return subprocess.check_output(args, text=True, timeout=60).strip()


def check_pins(root, receipt):
    require(bool(receipt['files']), 'empty build receipt')
    for name, pin in receipt['files'].items():
        path = root / name
        require(not Path(name).is_absolute() and root in path.resolve().parents,
                'receipt path escapes kernel output')
        require(path.is_file() and path.stat().st_size == pin['size'],
                f'missing or resized build input: {name}')
        require(sha(path) == pin['sha256'], f'changed build input: {name}')
    for name in ('.config', 'Module.symvers', 'arch/arm64/boot/Image',
                 'include/generated/utsrelease.h', *MODULES[:-1]):
        require(name in receipt['files'], f'build receipt missing required pin: {name}')


def check_firmware(trx, nvram):
    data = trx.read_bytes()
    require(len(data) >= 28, 'short TRX')
    magic, length, crc, flags, firmware_bytes, _, nvram_bytes = struct.unpack_from('<7I', data)
    require(magic == 0x30524448 and 28 <= length <= len(data), 'invalid TRX header')
    require((zlib.crc32(data[12:length]) ^ 0xffffffff) == crc, 'TRX CRC mismatch')
    require(0 < firmware_bytes <= length - 28 and nvram_bytes == 0,
            'expected original TRX with separate board NVRAM')
    text = nvram.read_text(encoding='ascii')
    require('\x00' not in text and any(line.startswith('boardtype=')
            for line in text.splitlines()), 'unrecognized board NVRAM')
    return {'trx_crc_valid': True, 'trx_bytes': len(data),
            'trx_sha256': sha(trx), 'nvram_sha256': sha(nvram),
            'transformed_or_uploaded': False}


def audit(args):
    root = args.kernel_out.resolve()
    receipt = json.loads(args.receipt.read_text())
    check_pins(root, receipt)
    config = dict(re.findall(r'^(CONFIG_\w+)=(.+)$', (root / '.config').read_text(), re.M))
    for key, value in REQUIRED.items():
        require(config.get(key, 'n') == value, f'wrong configuration: {key}')
    release = re.fullmatch(r'#define UTS_RELEASE "([\w.+-]+)"',
                          (root / 'include/generated/utsrelease.h').read_text().strip())
    require(release is not None, 'invalid kernel release')
    release = release[1]
    exports = {line.split()[1] for line in (root / 'Module.symvers').read_text().splitlines()}
    touch_receipt = json.loads(args.touch_receipt.read_text())
    matching_touch = [entry for entry in touch_receipt['builds'].values()
                      if entry['kernel_config_sha256'] == sha(root / '.config')
                      and entry['module_sha256'] == sha(args.touch_module)]
    require(len(matching_touch) == 1, 'touch module not pinned to this exact kernel configuration')
    modules = {}
    vermagic = output('modinfo', '-F', 'vermagic', str(root / MODULES[3]))
    require(vermagic.split()[0] == release, 'kernel/module release mismatch')
    for path in [root / name for name in MODULES] + [args.touch_module.resolve()]:
        require(output('modinfo', '-F', 'vermagic', str(path)) == vermagic,
                'module vermagic mismatch')
        imports = {line.split()[-1] for line in output('nm', '-u', str(path)).splitlines()
                   if line.split()[0] == 'U'}
        require(not imports - exports, f'unexported imports in {path.name}: {sorted(imports - exports)}')
        name = output('modinfo', '-F', 'name', str(path))
        modules[name] = {'file': path.name, 'sha256': sha(path), 'imports': len(imports),
                         'depends': output('modinfo', '-F', 'depends', str(path)).split(',')}
    for module in modules.values():
        require(all(dep.replace('-', '_') in modules for dep in module['depends'] if dep),
                f'module dependency missing: {module["file"]}')
    aliases = output('modinfo', '-F', 'alias', str(root / MODULES[3])).splitlines()
    # Descriptor identity captured in iOS; Linux enumeration is still pending.
    modalias = 'usb:v0A5CpBD1Cd0000dcFFdsc00dp00icFFisc02ipFFin00'
    matches = any(fnmatch.fnmatchcase(modalias, alias) for alias in aliases)
    return {'schema': 1, 'status': 'offline build inputs verified; NOT boot or Wi-Fi qualification',
            'preparation_tool_sha256': sha(Path(__file__)),
            'device': 'J72 / iPad4,2', 'kernel_release': release,
            'kernel_image_sha256': sha(root / 'arch/arm64/boot/Image'),
            'kernel_config_sha256': sha(root / '.config'), 'modules': modules,
            'modversions_enabled': False,
            'abi_check_limit': 'Export presence and pinned build provenance; no modversion CRCs exist.',
            'firmware': check_firmware(args.trx, args.nvram),
            'ios_observed_usb_id': '0a5c:bd1c', 'built_driver_alias_matches': matches,
            'probe_ready': False,
            'remaining': ['J72-owned HSIC PHY/domain/clock/reset sequencing and DT',
                          'Linux USB descriptors; no forced brcmfmac bind',
                          'BCM4324B5 USB download, host-ready and board-data adaptation',
                          'signed regulatory database and network userspace',
                          'matched complete boot bundle, USB recovery and live qualification'],
            'vendor_module_order': ['rfkill', 'cfg80211', 'brcmutil', 'brcmfmac', 'brcmfmac_wcc'],
            'vendor_note': 'Keep USB binding disabled until brcmfmac_wcc is registered; '
                           'ordinary modprobe of wcc loads brcmfmac as its dependency.',
            'device_access': False, 'ipad_storage_writes': False}


def stage(args, report):
    dest = args.destination.resolve()
    require(not dest.exists(), 'destination already exists; do not overwrite pinned candidates')
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.wifi-stage-', dir=dest.parent) as temporary:
        directory = Path(temporary)
        directory.chmod(0o700)
        modules = directory / 'lib/modules' / report['kernel_release']
        for name in MODULES:
            target = modules / 'kernel' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(args.kernel_out / name, target)
        extra = modules / 'extra'
        extra.mkdir()
        shutil.copyfile(args.touch_module, extra / args.touch_module.name)
        for name in ('modules.builtin', 'modules.builtin.modinfo'):
            shutil.copyfile(args.kernel_out / name, modules / name)
        (modules / 'modules.order').write_text('\n'.join(
            ['kernel/' + name for name in MODULES] + ['extra/' + args.touch_module.name]) + '\n')
        # No install to /lib/modules on the host and no modprobe/insmod call.
        output('depmod', '-b', str(directory), report['kernel_release'])
        private = directory / 'private-inputs'
        private.mkdir(mode=0o700)
        shutil.copyfile(args.trx, private / 'dureza.trx')
        shutil.copyfile(args.nvram, private / 'dureza-u-kk.txt')
        report['staged_files'] = {str(p.relative_to(directory)): sha(p)
                                  for p in directory.rglob('*') if p.is_file()}
        (directory / 'audit.json').write_text(json.dumps(report, indent=2) + '\n')
        # Move the completed private candidate into place only after all checks.
        directory.rename(dest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('kernel-out', 'receipt', 'touch-module', 'touch-receipt', 'trx', 'nvram', 'destination'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    try:
        report = audit(args)
        stage(args, report)
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as error:
        parser.exit(1, f'REFUSED: {error}\n')
    print('Offline WLAN inputs staged. Probe ready: false. No device contacted.')


if __name__ == '__main__':
    main()
