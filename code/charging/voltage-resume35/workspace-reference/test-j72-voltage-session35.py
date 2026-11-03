#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
import importlib.util
from pathlib import Path
import subprocess
import unittest

spec = importlib.util.spec_from_file_location('voltage_session', Path(__file__).with_name('run-j72-voltage-session35.py'))
session = importlib.util.module_from_spec(spec)
spec.loader.exec_module(session)


class ReadReceiptTests(unittest.TestCase):
    def setUp(self):
        self.boot = dict(boot_id='same-boot', uts_version='build35')
        self.checked = dict(**self.boot, probe_pass=True, device_read_only=True,
                            internal_writes=False, mounted_internal_filesystem=False,
                            logical_block_bytes=4096, device_bytes=128000000000)
        self.reads = dict(bytes_each=4096, internal_writes=False,
                          repeated_hash_pairs={str(n): ['a' * 64, 'a' * 64]
                                               for n in (0, 1, 31249999)})

    def check(self):
        session.check_receipt(self.checked, self.reads, self.boot, 'build35')

    def test_same_boot_read_only_matching_pairs(self):
        self.check()

    def test_stale_boot_wrong_geometry_or_writable_refused(self):
        for key, value in dict(boot_id='old-boot', uts_version='build34',
                               probe_pass=False, device_read_only=1,
                               internal_writes=True, mounted_internal_filesystem=True,
                               logical_block_bytes=512, device_bytes=128000000001).items():
            with self.subTest(key=key):
                self.setUp()
                self.checked[key] = value
                with self.assertRaises(AssertionError):
                    self.check()

    def test_missing_or_unmatched_reads_refused(self):
        pairs = self.reads['repeated_hash_pairs']
        for invalid in ({}, {**pairs, '2': ['a'*64]*2},
                        {**pairs, '0': ['a'*64, 'b'*64]},
                        {**pairs, '0': ['g'*64]*2},
                        {**pairs, '0': ['a'*63]*2}):
            self.reads['repeated_hash_pairs'] = invalid
            with self.subTest(invalid=invalid), self.assertRaises(AssertionError):
                self.check()

    def test_changed_read_scope_refused(self):
        for key, value in [('bytes_each', 512), ('internal_writes', True)]:
            self.setUp()
            self.reads[key] = value
            with self.subTest(key=key), self.assertRaises(AssertionError):
                self.check()

    def test_measurement_setup_shell_parses_without_execution(self):
        subprocess.run(['/bin/sh', '-n'], input=session.MEASUREMENT_BRIGHTNESS,
                       text=True, check=True)


if __name__ == '__main__':
    unittest.main()
