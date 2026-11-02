#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Test bounded 4096-to-512 mapping plans; no block device or ioctl access."""
import copy
import unittest
import j72_storage_preflight as g
import j72_native_view_plan as v


def fixture():
    return {'geometry': g.Geometry(4096, 31_250_000), 'partitions': [
        dict(index=1, type_guid=g.APFS, first_lba=6, last_lba=v.FIRST - 1,
             bytes=(v.FIRST - 6) * 4096, attributes=0),
        dict(index=2, type_guid=v.LINUX_TYPE, first_lba=v.FIRST, last_lba=v.LAST,
             bytes=v.CONTAINER_BYTES, attributes=0)]}


class NativeViewTests(unittest.TestCase):
    def test_exact_bounded_sector_conversion(self):
        p = v.native_view_plan(fixture())
        self.assertEqual(p['dm_table_for_review_only'], '0 3145728 linear /dev/asp0n1 246853632')
        self.assertEqual(p['view_bytes'], 1610612736)
        self.assertFalse(p['executed'])
        self.assertEqual(p['write_operations'], [])

    def test_current_single_apfs_layout_refused(self):
        f = fixture(); f['partitions'] = f['partitions'][:1]
        f['partitions'][0]['last_lba'] = 31_249_994
        with self.assertRaises(g.Refusal): v.native_view_plan(f)

    def test_wrong_logical_sector_or_capacity_refused(self):
        for block, count in [(512, 250_000_000), (4096, 31_249_999)]:
            f = fixture(); f['geometry'] = g.Geometry(block, count)
            with self.subTest(block=block), self.assertRaises(g.Refusal): v.native_view_plan(f)

    def test_apple_extent_cannot_be_reinterpreted(self):
        f = fixture(); f['partitions'][1]['type_guid'] = g.APFS
        with self.assertRaises(g.Refusal): v.native_view_plan(f)

    def test_shrink_must_already_have_happened(self):
        f = fixture(); f['partitions'][0]['last_lba'] = v.FIRST
        with self.assertRaises(g.Refusal): v.native_view_plan(f)

    def test_off_by_one_or_wrong_unit_boundaries_refused(self):
        for key, value in [('first_lba', v.FIRST + 1), ('last_lba', v.LAST + 1),
                           ('first_lba', v.FIRST * 8)]:
            f = fixture(); f['partitions'][1][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(g.Refusal): v.native_view_plan(f)

    def test_unknown_extra_partition_refused(self):
        f = fixture(); f['partitions'].append(copy.deepcopy(f['partitions'][1]))
        with self.assertRaises(g.Refusal): v.native_view_plan(f)

    def test_wrong_partition_slot_flags_or_size_refused(self):
        for key, value in [('index', 3), ('attributes', 1), ('bytes', v.CONTAINER_BYTES - 4096)]:
            f = fixture(); f['partitions'][1][key] = value
            with self.subTest(key=key), self.assertRaises(g.Refusal): v.native_view_plan(f)


if __name__ == '__main__':
    unittest.main()
