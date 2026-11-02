#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
import struct
import unittest
import uuid
import zlib
import j72_storage_preflight as g
import j72_rehearse_layout as r


def fixture():
    geometry = g.Geometry(4096, 31_250_000)
    table = bytearray(16384)
    table[:16] = uuid.UUID(g.APFS).bytes_le
    table[16:32] = uuid.UUID(int=7).bytes_le
    struct.pack_into('<QQQ', table, 32, 6, 31_249_994, 0)
    table[56:64] = 'APFS'.encode('utf-16-le')
    def header(current, alternate, entries):
        h = bytearray(4096); h[:8] = b'EFI PART'
        struct.pack_into('<IIIIQQQQ', h, 8, 0x10000, 92, 0, 0, current, alternate, 6, 31_249_994)
        h[56:72] = uuid.UUID(int=8).bytes_le
        struct.pack_into('<QIII', h, 72, entries, 128, 128, zlib.crc32(table))
        struct.pack_into('<I', h, 16, zlib.crc32(h[:92]))
        return bytes(h)
    mbr = bytearray(4096); mbr[510:512] = b'\x55\xaa'; mbr[450] = 0xee
    struct.pack_into('<II', mbr, 454, 1, 31_249_999)
    return geometry, dict(mbr=bytes(mbr), primary_header=header(1, 31_249_999, 2),
                          backup_header=header(31_249_999, 1, 31_249_995),
                          primary_entries=bytes(table), backup_entries=bytes(table))


class LayoutTests(unittest.TestCase):
    def test_real_size_arithmetic_preservation_and_future_crc(self):
        geometry, data = fixture()
        future, report = r.proposal(geometry, data, 126_357_602_304, uuid.UUID(int=10))
        self.assertEqual(report['proposed_apfs_bytes'], 126_389_035_008)
        self.assertEqual(report['headroom_above_observed_minimum_bytes'], 31_432_704)
        self.assertEqual(future['mbr'], data['mbr'])
        g.audit(geometry, **future)
        self.assertFalse(report['approval_ready'])
        self.assertEqual(report['write_operations_executed'], [])

    def test_bad_original_crc_refused_before_proposal(self):
        geometry, data = fixture(); bad = bytearray(data['primary_entries']); bad[10] ^= 1
        data['primary_entries'] = bytes(bad)
        with self.assertRaises(g.Refusal): r.proposal(geometry, data, 126_357_602_304, uuid.UUID(int=10))

    def test_zero_unaligned_or_excess_minimum_refused(self):
        for minimum in (0, 126_357_602_305, 127_000_000_000, True):
            geometry, data = fixture()
            with self.subTest(minimum=minimum), self.assertRaises(g.Refusal):
                r.proposal(geometry, data, minimum, uuid.UUID(int=10))

    def test_null_or_duplicate_future_partition_identity_refused(self):
        for identity in (0, 7):
            geometry, data = fixture()
            with self.subTest(identity=identity), self.assertRaises(g.Refusal):
                r.proposal(geometry, data, 126_357_602_304, uuid.UUID(int=identity))

    def test_proposal_cannot_be_applied_twice(self):
        geometry, data = fixture()
        future, _ = r.proposal(geometry, data, 126_357_602_304, uuid.UUID(int=10))
        with self.assertRaises(g.Refusal): r.proposal(geometry, future, 126_357_602_304, uuid.UUID(int=11))


if __name__ == '__main__':
    unittest.main()
