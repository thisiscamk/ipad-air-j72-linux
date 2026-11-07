#!/usr/bin/env python3
"""Verify the reviewed source manifest and reject private/binary publication."""
from pathlib import Path
import ast
import hashlib
import json
import re

root = Path(__file__).resolve().parents[1] / 'code/current'
manifest = json.loads((root / 'MANIFEST.json').read_text())
assert manifest['source_only'] is True
for name, digest in manifest['files'].items():
    path = root / name
    assert path.is_file() and not path.is_symlink(), name
    data = path.read_bytes()
    assert hashlib.sha256(data).hexdigest() == digest, 'Source changed: ' + name
    assert b'\x00' not in data, 'Binary data: ' + name
    assert not any(token in data for token in (
        b'-----BEGIN OPENSSH PRIVATE KEY-----', b'-----BEGIN RSA PRIVATE KEY-----',
        b'ghp_', b'gho_', b'/home/pi/')), 'Private/local content: ' + name
    for identity in re.findall(rb'ECID:([0-9a-fA-F]{16})', data):
        assert identity == b'0000000000000001', 'Non-synthetic ECID: ' + name
    if path.suffix == '.py':
        ast.parse(data, filename=name)
print('PASS: source manifest, Python syntax and publication exclusions')
