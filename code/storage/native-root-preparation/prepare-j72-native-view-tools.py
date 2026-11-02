#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build a private ARM64 dmsetup userspace closure; host files only."""
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'private/j72-platform/power-storage-20261102/desktop-storage35/native-view-tools'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    os.umask(0o077)
    assert platform.machine() == 'aarch64'
    assert not WORK.exists(), 'Refuse to overwrite a prepared closure'
    root = WORK / 'root'
    root.mkdir(parents=True)
    binary = Path(shutil.which('dmsetup'))
    dependencies = subprocess.run(['ldd', str(binary)], check=True, capture_output=True, text=True).stdout
    assert 'not found' not in dependencies
    files = {Path('/usr/sbin/dmsetup'): binary}
    for line in dependencies.splitlines():
        found = re.search(r'(?:=>\s*)?(/\S+)\s+\(', line)
        if found:
            files[Path(found[1])] = Path(found[1])
    for destination, source in files.items():
        target = root / str(destination).lstrip('/')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        target.chmod(source.stat().st_mode & 0o777)
    (root / 'dev').mkdir()
    # Help parses userspace options only. No host /dev or /sys is exposed.
    smoke = subprocess.run(['chroot', str(root), '/usr/sbin/dmsetup', '--help'], capture_output=True, timeout=10)
    assert smoke.returncode == 0 and b'dmsetup' in smoke.stdout + smoke.stderr
    (WORK / 'help-smoke.txt').write_bytes(smoke.stdout + smoke.stderr)
    archive = WORK / 'native-view-tools.tar.gz'
    with tarfile.open(archive, 'w:gz') as tar:
        tar.add(root, arcname='.', recursive=True)
    manifest = {'status': 'HOST_NATIVE_HELP_SMOKE_PASS_NO_DEVICE_ACCESS',
                'files': {str(p.relative_to(root)): sha(p) for p in root.rglob('*') if p.is_file()},
                'sources': {str(source): sha(source) for source in files.values()},
                'archive_sha256': sha(archive), 'archive_bytes': archive.stat().st_size,
                'kernel_changed': False, 'device_access': False, 'mapping_created': False,
                'source_sha256': sha(Path(__file__))}
    (WORK / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('PASS: isolated ARM64 dmsetup closure/help smoke; archive bytes', archive.stat().st_size)


if __name__ == '__main__':
    main()
