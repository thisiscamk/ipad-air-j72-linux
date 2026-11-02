#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Exact #35 combined-payload preflight and shared USB transport functions."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'private/j72-platform/power-storage-20261102/desktop-storage35'
VERSION = '#35 SMP PREEMPT Mon Nov 2 07:00:00 +08 2026'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()


def preflight(verify_desktop=True):
    m = json.loads((WORK / 'manifest.json').read_text())
    assert m['profile'] == 'desktop-storage35' and m['uts_version'] == VERSION
    assert m['same_proven_loader_dtb_kernel'] and m['strong_imports_resolved']
    for key in ('storage_autoload', 'radio_autoload', 'touch_autoload', 'charging_autoload', 'internal_write_support'):
        assert m[key] is False, key
    for name, digest in m['inputs'].items():
        assert sha(ROOT / name) == digest, name
    for name, digest in m['files'].items():
        assert sha(WORK / name) == digest, name
    for name, digest in m['overlay_files'].items():
        assert sha(WORK / 'payload/rootfs' / name) == digest, name
    assert sha(Path(m['payload'])) == m['payload_sha256']
    tree = ast.parse((ROOT / 'tools/j72-pongo-pmic-boot.py').read_text())
    pins = [ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == 'DESKTOP_STORAGE35_SHA256' for t in n.targets)]
    assert pins == [m['payload_sha256']]
    source = json.loads((WORK / 'module-inputs.json').read_text())
    for name, digest in source['kernel_base_files'].items():
        assert sha(ROOT / name) == digest, name
    # Same regular desktop input for compatible lifecycle cleanup helpers.
    old = json.loads((ROOT / 'private/j72-platform/wifi-desktop-v3/manifest.json').read_text())
    m['desktop_image'], m['desktop_sha256'] = old['desktop_image'], old['desktop_sha256']
    if verify_desktop:
        assert sha(Path(m['desktop_image'])) == m['desktop_sha256']
    print('PASS: combined #35 loader/kernel/module/archive pins; storage/radio/charge/input opt-in; no device contacted', flush=True)
    return m


spec = importlib.util.spec_from_file_location('j72_original_transport', ROOT / 'tools/j72-wifi-host.py')
transport = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transport)
ram, server_pid, PIDFILE = transport.ram, transport.server_pid, transport.PIDFILE

if __name__ == '__main__':
    preflight()
