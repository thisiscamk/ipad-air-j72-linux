#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Offline refusal checks; synthetic files only, no USB or module loading."""
import importlib.util
from pathlib import Path
import struct
import tempfile
from types import SimpleNamespace
import unittest
import zlib

spec = importlib.util.spec_from_file_location('wifi', Path(__file__).with_name('prepare-j72-wifi.py'))
wifi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wifi)


class Refusals(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.tree = self.root / 'kernel'
        self.tree.mkdir()
        names = ('.config', 'Module.symvers', 'arch/arm64/boot/Image',
                 'include/generated/utsrelease.h', *wifi.MODULES[:-1])
        self.receipt = {'files': {}}
        for name in names:
            path = self.tree / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'synthetic build input')
            self.receipt['files'][name] = {'size': path.stat().st_size, 'sha256': wifi.sha(path)}

    def test_changed_same_size_build_refused(self):
        wifi.check_pins(self.tree, self.receipt)
        path = self.tree / '.config'
        path.write_bytes(b'X' * path.stat().st_size)
        with self.assertRaisesRegex(ValueError, 'changed build input'):
            wifi.check_pins(self.tree, self.receipt)

    def test_incomplete_receipt_refused(self):
        del self.receipt['files']['Module.symvers']
        with self.assertRaisesRegex(ValueError, 'missing required pin'):
            wifi.check_pins(self.tree, self.receipt)

    def test_parent_escape_refused_even_when_hash_matches(self):
        outside = self.root / 'outside'
        outside.write_bytes(b'outside')
        self.receipt['files']['../outside'] = {'size': 7, 'sha256': wifi.sha(outside)}
        with self.assertRaisesRegex(ValueError, 'escapes'):
            wifi.check_pins(self.tree, self.receipt)

    def test_symlink_escape_refused(self):
        outside = self.root / 'outside'
        outside.write_bytes(b'outside')
        (self.tree / 'escape').symlink_to(outside)
        self.receipt['files']['escape'] = {'size': 7, 'sha256': wifi.sha(outside)}
        with self.assertRaisesRegex(ValueError, 'escapes'):
            wifi.check_pins(self.tree, self.receipt)

    def firmware(self, nvram_bytes=0):
        trx, nvram = self.root / 'fake.trx', self.root / 'fake.txt'
        data = bytearray(struct.pack('<7I', 0x30524448, 36, 0, 0x10020, 8, 0, nvram_bytes) + b'FAKECODE')
        struct.pack_into('<I', data, 8, zlib.crc32(data[12:]) ^ 0xffffffff)
        trx.write_bytes(data)
        nvram.write_text('boardtype=0\n# synthetic only\n')
        return trx, nvram

    def test_corrupt_trx_refused(self):
        trx, nvram = self.firmware()
        self.assertTrue(wifi.check_firmware(trx, nvram)['trx_crc_valid'])
        trx.write_bytes(trx.read_bytes()[:-1] + b'X')
        with self.assertRaisesRegex(ValueError, 'CRC mismatch'):
            wifi.check_firmware(trx, nvram)

    def test_already_packed_nvram_refused(self):
        with self.assertRaisesRegex(ValueError, 'original TRX'):
            wifi.check_firmware(*self.firmware(nvram_bytes=4))

    def test_existing_candidate_untouched(self):
        dest = self.root / 'pinned-candidate'
        dest.mkdir()
        marker = dest / 'immutable'
        marker.write_bytes(b'original')
        with self.assertRaisesRegex(ValueError, 'already exists'):
            wifi.stage(SimpleNamespace(destination=dest), {})
        self.assertEqual(marker.read_bytes(), b'original')


if __name__ == '__main__':
    unittest.main()
