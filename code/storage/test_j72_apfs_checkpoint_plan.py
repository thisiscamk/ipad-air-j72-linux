#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
import struct
import unittest
import j72_apfs_checkpoint_plan as a
import j72_storage_preflight as g


def fixture(xid=10, blocks=31_249_989):
    b = bytearray(4096)
    struct.pack_into('<QQII', b, 8, 1, xid, 0x80000001, 0)
    struct.pack_into('<4sIQQQQ', b, 32, b'NXSB', 4096, blocks, 1, 0, 2)
    b[72:88] = bytes(range(16))
    struct.pack_into('<IIQQ', b, 104, 4, 8, 1, 5)
    b[:8] = a.checksum(b)
    return bytes(b)


def reseal(b):
    b = bytearray(b); b[:8] = a.checksum(b); return bytes(b)


def checkpoint_fixture():
    anchor = fixture()
    nx = bytearray(fixture(xid=12))
    struct.pack_into('<IIIIII', nx, 128, 2, 2, 0, 2, 0, 2)
    mapping = bytearray(4096)
    struct.pack_into('<QQIIII', mapping, 8, 1, 12, 0x4000000c, 0, 1, 2)
    objects = {}
    for i, kind in enumerate((0x80000005, 0x8000000b)):
        struct.pack_into('<IIIIQQQ', mapping, 40 + i * 40, kind, 0, 4096, 0, 0, 1024 + i, 5 + i)
        obj = bytearray(4096); struct.pack_into('<QQII', obj, 8, 1024 + i, 12, kind, 0)
        objects[11 + i] = reseal(obj)
    return anchor, reseal(mapping) + reseal(nx) + bytes(8192), objects


class CheckpointTests(unittest.TestCase):
    def test_bounded_full_scan_uses_latest_candidate_not_stale_anchor(self):
        anchor = fixture()
        scan = bytes(4096) + fixture(xid=12, blocks=30_856_698) + fixture(xid=11) + bytes(4096)
        r = a.candidates(anchor, scan, a.APFS_MAX_BLOCKS)
        self.assertEqual(r['candidate_xid'], 12)
        self.assertEqual(r['candidate_container_bytes'], 126_389_035_008)
        self.assertFalse(r['block_zero_matches_candidate_size'])
        self.assertFalse(r['sufficient_for_resize_or_write_authorization'])
        self.assertEqual(a.descriptor_plan(anchor, a.APFS_MAX_BLOCKS)['disk_first_lba'], 7)

    def test_checksum_magic_geometry_or_feature_errors_refused(self):
        cases = [bytearray(fixture()), bytearray(fixture()), bytearray(fixture()), bytearray(fixture())]
        cases[0][-1] ^= 1
        struct.pack_into('<I', cases[1], 36, 512)
        struct.pack_into('<Q', cases[2], 64, 0x102)
        struct.pack_into('<Q', cases[3], 40, a.APFS_MAX_BLOCKS + 1)
        for index, b in enumerate(cases):
            if index: b[:8] = a.checksum(b)
            with self.subTest(index=index), self.assertRaises(g.Refusal):
                a.superblock(bytes(b), a.APFS_MAX_BLOCKS)

    def test_tree_layout_out_of_bounds_and_overlap_refused(self):
        for offset, fmt, value in ((104, '<I', 0x80000004), (104, '<I', 1025),
                                    (112, '<Q', a.APFS_MAX_BLOCKS - 2),
                                    (120, '<Q', 2), (108, '<I', 0),
                                    (120, '<Q', 1 << 63)):
            b = bytearray(fixture()); struct.pack_into(fmt, b, offset, value); b[:8] = a.checksum(b)
            with self.subTest(offset=offset, value=value), self.assertRaises(g.Refusal):
                a.superblock(bytes(b), a.APFS_MAX_BLOCKS)

    def test_full_capture_required_even_if_valid_candidate_is_present(self):
        for data in (fixture(), fixture() + bytes(4096 * 2), fixture() + bytes(4096 * 4)):
            with self.assertRaises(g.Refusal): a.candidates(fixture(), data, a.APFS_MAX_BLOCKS)

    def test_torn_latest_nx_cannot_claim_complete_checkpoint_validation(self):
        bad = bytearray(fixture(xid=12)); bad[-1] ^= 1
        r = a.candidates(fixture(), fixture(xid=11) + bytes(bad) + bytes(8192), a.APFS_MAX_BLOCKS)
        self.assertEqual(r['candidate_xid'], 11)
        self.assertEqual(r['malformed_nx_candidates'], 1)
        self.assertFalse(r['checkpoint_maps_and_ephemeral_objects_validated'])

    def test_same_transaction_conflict_refused(self):
        scan = fixture(xid=12) + fixture(xid=12, blocks=30_856_698) + bytes(8192)
        with self.assertRaises(g.Refusal): a.candidates(fixture(), scan, a.APFS_MAX_BLOCKS)

    def test_foreign_identity_is_never_selected(self):
        bad = bytearray(fixture(xid=999)); bad[72] ^= 1; bad[:8] = a.checksum(bad)
        r = a.candidates(fixture(), fixture(xid=11) + bytes(bad) + bytes(8192), a.APFS_MAX_BLOCKS)
        self.assertEqual(r['candidate_xid'], 11)
        self.assertEqual(r['malformed_nx_candidates'], 1)

    def test_complete_bounded_mapping_and_object_checksums(self):
        anchor, descriptors, objects = checkpoint_fixture()
        r = a.verify_checkpoint(anchor, descriptors, a.APFS_MAX_BLOCKS, objects)
        self.assertEqual(r['ephemeral_object_count'], 2)
        self.assertTrue(r['mapping_chain_validated'])
        self.assertTrue(r['ephemeral_object_headers_and_checksums_validated'])
        self.assertFalse(r['full_filesystem_semantics_validated'])
        self.assertFalse(r['sufficient_for_resize_or_write_authorization'])

    def test_mapping_wrong_transaction_flags_size_duplicate_and_fences(self):
        anchor, descriptors, objects = checkpoint_fixture()
        # Each mutation is re-checksummed so structural checks, not just CRC,
        # must reject it before planning any subsequent object reads.
        mutations = ((16, '<Q', 13), (32, '<I', 0), (36, '<I', 102),
                     (48, '<I', 8192), (52, '<I', 1), (40, '<I', 0xc0000005),
                     (72, '<Q', 4), (72, '<Q', 13), (72, '<Q', 7),
                     (112, '<Q', 5), (104, '<Q', 1024))
        for offset, fmt, value in mutations:
            m = bytearray(descriptors[:4096]); struct.pack_into(fmt, m, offset, value)
            bad = reseal(m) + descriptors[4096:]
            with self.subTest(offset=offset, value=value), self.assertRaises(g.Refusal):
                a.checkpoint_object_plan(anchor, bad, a.APFS_MAX_BLOCKS)

    def test_mapping_chain_next_indices_and_wrap_are_checked(self):
        anchor, descriptors, objects = checkpoint_fixture()
        for offset, value in ((128, 3), (132, 3), (136, 3), (140, 1), (148, 3)):
            nx = bytearray(descriptors[4096:8192]); struct.pack_into('<I', nx, offset, value)
            bad = descriptors[:4096] + reseal(nx) + descriptors[8192:]
            with self.subTest(offset=offset), self.assertRaises(g.Refusal):
                a.checkpoint_object_plan(anchor, bad, a.APFS_MAX_BLOCKS)
        # Move the mapping and its final NX across the end of the descriptor ring.
        m = bytearray(descriptors[:4096]); struct.pack_into('<Q', m, 8, 4)
        nx = bytearray(descriptors[4096:8192]); struct.pack_into('<IIIIII', nx, 128, 1, 2, 3, 2, 0, 2)
        wrapped = reseal(nx) + bytes(8192) + reseal(m)
        self.assertEqual(a.verify_checkpoint(anchor, wrapped, a.APFS_MAX_BLOCKS, objects)['ephemeral_object_count'], 2)

    def test_object_corruption_wrong_header_missing_and_extra_are_refused(self):
        anchor, descriptors, objects = checkpoint_fixture()
        bad = bytearray(objects[11]); bad[-1] ^= 1
        variants = [{12: objects[12]}, {**objects, 13: objects[11]},
                    {**objects, 11: bytes(bad)}, {**objects, 11: objects[11][:-1]}]
        for offset, fmt, value in ((8, '<Q', 999), (16, '<Q', 11), (24, '<I', 0x8000000b), (28, '<I', 1)):
            bad = bytearray(objects[11]); struct.pack_into(fmt, bad, offset, value)
            variants.append({**objects, 11: reseal(bad)})
        for index, bad in enumerate(variants):
            with self.subTest(index=index), self.assertRaises(g.Refusal):
                a.verify_checkpoint(anchor, descriptors, a.APFS_MAX_BLOCKS, bad)


if __name__ == '__main__': unittest.main()
