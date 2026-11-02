#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Seal authored host-tool changes without changing kernel or artifact pins."""
import hashlib
import json
import os
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'private/j72-platform/power-storage-20261102/desktop-storage35'
TOOLS = ['j72-desktop-storage35-host.py', 'run-j72-network.py', 'run-j72-wifi-v3.py',
         'run-j72-ram-desktop.py', 'run-j72-storage-observer.py', 'run-j72-native35-readcheck.py',
         'run-j72-compressed-desktop.py', 'j72-pongo-pmic-boot.py', 'seal-j72-desktop-storage35.py']


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(data)
    return h.hexdigest()


def main():
    os.umask(0o077)
    m = json.loads((WORK / 'manifest.json').read_text())
    assert m['profile'] == 'desktop-storage35' and not m['device_tested']
    for name, digest in m['files'].items():
        assert sha(WORK / name) == digest, 'Artifact changed: ' + name
    source = json.loads((WORK / 'module-inputs.json').read_text())
    for name, digest in source['kernel_base_files'].items():
        assert sha(ROOT / name) == digest, 'Kernel changed: ' + name
    allowed = {'tools/' + name for name in TOOLS}
    for name, digest in m['inputs'].items():
        if name not in allowed:
            assert sha(ROOT / name) == digest, 'Unreviewed non-host input changed: ' + name
    archive = WORK / ('source-seal-' + time.strftime('%Y%m%d-%H%M%S'))
    archive.mkdir()
    (archive / 'manifest-before.json').write_text(json.dumps(m, indent=2) + '\n')
    for name in TOOLS:
        m['inputs']['tools/' + name] = sha(ROOT / 'tools' / name)
    (WORK / 'manifest.json').write_text(json.dumps(m, indent=2) + '\n')
    paths = [ROOT / 'private/j72-platform/power-storage-20261102/compressed-root-prep/desktop-test34/manifest.json',
             WORK / 'compressed-desktop/manifest.json', WORK / 'container-desktop/manifest.json']
    for path in paths:
        old = json.loads(path.read_text())
        (archive / (path.parent.name + '-manifest-before.json')).write_text(json.dumps(old, indent=2) + '\n')
        replace = {'tools/run-j72-compressed-desktop.py', str((WORK / 'manifest.json').relative_to(ROOT))}
        for name, digest in old['files'].items():
            if name not in replace:
                assert sha(ROOT / name) == digest, 'Artifact/source changed outside host selector update: ' + name
        for name in replace & old['files'].keys():
            old['files'][name] = sha(ROOT / name)
        old['source_pin_update_note'] = 'Explicit #35/container modes remain device-untested; #34 measured source is archived separately.'
        path.write_text(json.dumps(old, indent=2) + '\n')
    (archive / 'result.json').write_text(json.dumps({'kernel_and_artifact_pins_unchanged': True,
                                                   'host_tools': {name: m['inputs']['tools/' + name] for name in TOOLS},
                                                   'new_modes_device_tested': False}, indent=2) + '\n')
    print('Sealed reviewed host sources; kernel/artifact pins unchanged; prior manifests archived; no device access')


if __name__ == '__main__':
    main()
