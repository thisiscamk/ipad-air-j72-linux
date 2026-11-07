#!/usr/bin/env python3
"""Stage the measured audio service privately; never install/load/enable it."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

RELEASE = '7.3.0-rc1-j72-pw1-orchard-apple-4k'
FIRMWARE_SHA = 'af3d61851d4a2dd53d7301d945d7ff3f0d94eef2e15947f1de2c9a8982708e33'
MODULES = ('apple-sio-core.ko', 'apple-sio-dma.ko', 'virt-dma.ko',
           'j72_mca.ko', 'j72_audio_overlay.ko')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--modules-dir', type=Path, required=True)
    parser.add_argument('--firmware', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), 'Refuse replacing an existing staging root'
    firmware = args.firmware.read_bytes()
    assert len(firmware) == 464208 and hashlib.sha256(firmware).hexdigest() == FIRMWARE_SHA
    inputs = {}
    for name in MODULES:
        path = args.modules_dir / name
        result = subprocess.run(['modinfo', '-F', 'vermagic', str(path)],
                                capture_output=True, text=True, check=True, timeout=10)
        assert result.stdout.startswith(RELEASE + ' '), 'Wrong module ABI: ' + name
        inputs[name] = path
    os.umask(0o077)
    args.output.mkdir(mode=0o700, parents=True)
    base = args.output / 'usr/local/lib/orchard/j72-audio'
    base.mkdir(parents=True)
    manifest = {}
    for name, path in inputs.items():
        shutil.copyfile(path, base / name)
    runtime = Path(__file__).resolve().parent / 'runtime'
    for name in ('start-audio.py', 'mute-controls.py'):
        shutil.copyfile(runtime / name, base / name)
    (base / 's5l8960x-smartio.bin').write_bytes(firmware)
    for path in base.iterdir():
        manifest[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    (base / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    unit = args.output / 'etc/systemd/system/orchard-j72-audio.service'
    unit.parent.mkdir(parents=True)
    shutil.copyfile(runtime / unit.name, unit)
    firmware_path = args.output / 'lib/firmware/apple/s5l8960x-smartio.bin'
    firmware_path.parent.mkdir(parents=True)
    firmware_path.symlink_to('/usr/local/lib/orchard/j72-audio/s5l8960x-smartio.bin')
    print('Private staging complete. Nothing installed, loaded or enabled. Do not publish this output.')


if __name__ == '__main__':
    main()
