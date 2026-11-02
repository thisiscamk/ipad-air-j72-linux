#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
import copy
import struct
import unittest
import uuid
import zlib
import j72_install_state as s
import j72_storage_preflight as g
import j72_rehearse_layout as layout
import j72_native_view_plan as view
from test_j72_rehearse_layout import fixture


class InterruptedInstallTests(unittest.TestCase):
    def setUp(self):
        geometry, self.old = fixture()
        self.new, _ = layout.proposal(geometry, self.old, 126_357_602_304, uuid.UUID(int=10))
        self.transition = s.Transition(self.old, self.new)

    def test_every_primary_backup_state_against_container_size(self):
        expected = {('original', 'original'): 'APFS_SHRUNK_GPT_NOT_COMMITTED',
                    ('original', 'proposed'): 'INTERRUPTED_BACKUP_COMMITTED_PRIMARY_ORIGINAL',
                    ('proposed', 'original'): 'STOP_UNEXPECTED_PRIMARY_FIRST_ORDER',
                    ('proposed', 'proposed'): 'PARTITIONS_COMMITTED_IMAGE_NOT_VERIFIED'}
        for p, q in expected:
            snapshot = dict(self.old)
            for prefix, state in [('primary', p), ('backup', q)]:
                source = self.old if state == 'original' else self.new
                for suffix in ('_header', '_entries'):
                    snapshot[prefix + suffix] = source[prefix + suffix]
            with self.subTest(primary=p, backup=q):
                self.assertEqual(self.transition.classify(snapshot, s.APFS_TARGET)['status'], expected[p, q])
                result = self.transition.classify(snapshot, s.APFS_ORIGINAL)
                self.assertEqual(result['status'], 'ORIGINAL_UNCHANGED' if p == q == 'original'
                                 else 'STOP_GPT_CHANGED_BEFORE_CONFIRMED_SHRINK')

    def test_unknown_partial_size_and_ambiguous_input_refused(self):
        for size in (s.APFS_TARGET - 4096, s.APFS_TARGET + 4096):
            self.assertEqual(self.transition.classify(self.new, size)['status'],
                             'STOP_APFS_SIZE_UNKNOWN_OR_PARTIAL')
        for size in (True, 0, -1, '126389035008'):
            with self.assertRaises(g.Refusal): self.transition.classify(self.new, size)
        with self.assertRaises(g.Refusal):
            self.transition.classify(self.new, s.APFS_TARGET, image_verified=1)

    def test_crc_valid_foreign_identity_is_not_adopted(self):
        alien = copy.deepcopy(self.new)
        h = bytearray(alien['backup_header']); h[56] ^= 1
        h[16:20] = bytes(4); struct.pack_into('<I', h, 16, zlib.crc32(h[:92]))
        alien['backup_header'] = bytes(h)
        self.assertEqual(self.transition.classify(alien, s.APFS_TARGET)['status'],
                         'STOP_UNRECOGNIZED_VALID_GPT')

    def test_crc_valid_header_padding_difference_is_not_adopted(self):
        alien = dict(self.new); h = bytearray(alien['primary_header']); h[-1] ^= 1
        alien['primary_header'] = bytes(h)
        self.assertEqual(self.transition.classify(alien, s.APFS_TARGET)['primary'], 'foreign')

    def test_corrupt_missing_or_truncated_copy_never_permits_image(self):
        for key in ('primary_header', 'primary_entries', 'backup_header', 'backup_entries'):
            for replacement in (b'', self.new[key][:-1], b'X' * len(self.new[key])):
                bad = {**self.new, key: replacement}
                with self.subTest(key=key), self.assertRaises(g.Refusal):
                    self.transition.image_range(0, 4096, bad, s.APFS_TARGET)

    def test_mbr_preserved_and_invalid_proposal_refused(self):
        bad = {**self.new, 'mbr': bytes(4096)}
        self.assertEqual(self.transition.classify(bad, s.APFS_TARGET)['status'],
                         'STOP_PROTECTIVE_MBR_CHANGED')
        with self.assertRaises(g.Refusal): s.Transition(self.old, bad)

    def test_valid_proposal_with_unreviewed_apple_field_refused(self):
        bad = dict(self.new)
        table = bytearray(bad['primary_entries']); table[56:58] = 'X'.encode('utf-16-le')
        for prefix in ('primary', 'backup'):
            bad[prefix + '_entries'] = bytes(table)
            h = bytearray(bad[prefix + '_header'])
            struct.pack_into('<I', h, 88, zlib.crc32(table)); h[16:20] = bytes(4)
            struct.pack_into('<I', h, 16, zlib.crc32(h[:92])); bad[prefix + '_header'] = bytes(h)
        g.audit(g.Geometry(4096, s.BLOCKS), **bad)
        with self.assertRaises(g.Refusal): s.Transition(self.old, bad)

    def test_final_candidate_needs_both_copies_size_and_image(self):
        for image_verified in (False, True):
            result = self.transition.classify(self.new, s.APFS_TARGET, image_verified=image_verified)
            self.assertEqual(result['native_mount_candidate'], image_verified)
            self.assertFalse(result['execution_ready'])
            self.assertFalse(result['device_writes_permitted'])
            self.assertFalse(result['automatic_repair'])

    def test_image_range_fences_zero_overflow_wrong_units_and_boundaries(self):
        first = self.transition.image_range(0, 4096, self.new, s.APFS_TARGET)
        last = self.transition.image_range(view.CONTAINER_BYTES - 4096, 4096, self.new, s.APFS_TARGET)
        self.assertEqual(first['disk_byte_offset'], view.FIRST * 4096)
        self.assertEqual(last['disk_byte_offset'] + 4096, (view.LAST + 1) * 4096)
        for offset, length in ((-4096, 4096), (True, 4096), (0, True), (0, 0),
                               (512, 4096), (0, 512), (0, (1 << 20) + 4096),
                               (view.CONTAINER_BYTES - 4096, 8192),
                               (view.CONTAINER_BYTES, 4096), (1 << 64, 4096)):
            with self.subTest(offset=offset, length=length), self.assertRaises(g.Refusal):
                self.transition.image_range(offset, length, self.new, s.APFS_TARGET)
        with self.assertRaises(g.Refusal):
            self.transition.image_range(0, 4096, self.old, s.APFS_TARGET)

    def test_interruption_matrix_cannot_automatically_repair_or_write(self):
        rows = s.interrupted_metadata_matrix(self.transition)
        self.assertEqual(len(rows), 22)
        for row in rows:
            self.assertFalse(row['state']['automatic_repair'])
            self.assertFalse(row['state']['device_writes_permitted'])
            if row['state']['native_mount_candidate']:
                self.assertEqual(row['point'], 'after_full_image_hash_readback')
        self.assertTrue(rows[-1]['state']['native_mount_candidate'])

    def test_inputs_frozen_after_validation(self):
        before = dict(self.transition.proposed)
        self.new['primary_header'] = bytes(4096)
        self.assertEqual(dict(self.transition.proposed), before)
        with self.assertRaises(TypeError): self.transition.proposed['mbr'] = b''


if __name__ == '__main__':
    unittest.main()
