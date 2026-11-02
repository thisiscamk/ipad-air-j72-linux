#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Plan a fenced read-only J72 root view from captured GPT; never execute it."""
import argparse
import json
import os
from pathlib import Path

import j72_storage_preflight as gpt

BLOCK_BYTES = 4096
TOTAL_BLOCKS = 31_250_000
LINUX_TYPE = '0fc63daf-8483-4772-8e79-3d69d8477de4'
FIRST = 30_856_704
LAST = 31_249_919
CONTAINER_BYTES = 1536 * 1024 * 1024


def native_view_plan(inventory):
    """A future installed layout must already exist; never carve an APFS view."""
    g = inventory['geometry']
    gpt.require(g.block_bytes == BLOCK_BYTES and g.blocks == TOTAL_BLOCKS,
                'Only the measured J72 128 GB / 4096-byte geometry is qualified')
    parts = sorted(inventory['partitions'], key=lambda p: p['first_lba'])
    gpt.require(len(parts) == 2, 'An existing APFS partition and a separate Linux partition are required')
    apple, linux = parts
    gpt.require(apple['type_guid'] == gpt.APFS and apple['index'] == 1 and apple['first_lba'] == 6,
                'Preserved Apple partition identity/type/position differs')
    gpt.require(linux['type_guid'] == LINUX_TYPE and linux['index'] == 2,
                'Second partition must already be the expected Linux filesystem type')
    gpt.require(linux['first_lba'] == FIRST and linux['last_lba'] == LAST,
                'Linux extent differs from the conditional 1536 MiB layout')
    gpt.require(apple['last_lba'] == FIRST - 1,
                'APFS must already end before the Linux extent; this tool cannot resize it')
    gpt.require(linux['attributes'] == 0 and linux['bytes'] == CONTAINER_BYTES,
                'Unexpected Linux attributes or extent size')
    offset_bytes = FIRST * BLOCK_BYTES
    gpt.require(offset_bytes % 512 == 0 and CONTAINER_BYTES % 512 == 0,
                'Device-mapper units must be exact 512-byte sectors')
    sectors, offset = CONTAINER_BYTES // 512, offset_bytes // 512
    gpt.require((offset + sectors) * 512 == (LAST + 1) * BLOCK_BYTES,
                'View endpoint does not match the partition boundary')
    return {
        'status': 'READ_ONLY_MAPPING_PLAN_ONLY', 'executed': False,
        'internal_writes_authorized': False, 'write_operations': [],
        'live_board_boot_and_backing_device_identity_verified': False,
        'geometry_bytes': g.blocks * g.block_bytes,
        'backing_logical_block_bytes': BLOCK_BYTES,
        'partition_first_lba_4096': FIRST, 'partition_last_lba_4096': LAST,
        'view_bytes': CONTAINER_BYTES, 'view_read_only_required': True,
        'backing_device_read_only_required': True,
        'dm_table_sector_bytes': 512,
        'dm_table_for_review_only': f'0 {sectors} linear /dev/asp0n1 {offset}',
        'dm_suspend_load_resume_or_create_executed': False,
        'readback_requirements': ['exact view size', 'read-only flag', 'exact table and backing device',
                                  'verified ext4/base contract', 'normal mapping removal after unmount'],
        'initial_ext4_mount_options': 'ro,noload,nodev,nosuid,noexec',
        'persistent_overlay_enabled': False,
    }


def capture_inventory(directory):
    meta = json.loads(gpt.regular_bytes(directory / 'geometry.json', 16384))
    geometry = gpt.Geometry(meta['logical_block_bytes'], meta['total_blocks'])
    captured = {name: gpt.regular_bytes(directory / (name.replace('_', '-') + '.bin'),
                                      gpt.MAX_TABLE_BYTES if 'entries' in name else geometry.block_bytes)
                for name in ('mbr', 'primary_header', 'primary_entries', 'backup_header', 'backup_entries')}
    return gpt.audit(geometry, **captured)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture', type=Path, required=True)
    p.add_argument('--report', type=Path)
    a = p.parse_args()
    os.umask(0o077)
    inventory = capture_inventory(a.capture)
    try:
        result = native_view_plan(inventory)
        rc = 0
    except gpt.Refusal as exc:
        result = {'status': 'REFUSED', 'reason': str(exc), 'metadata_valid': True,
                  'executed': False, 'write_operations': [], 'internal_writes_authorized': False}
        rc = 2
    text = json.dumps(result, indent=2) + '\n'
    if a.report:
        with a.report.open('x') as stream:
            stream.write(text)
    else:
        print(text, end='')
    return rc


if __name__ == '__main__':
    raise SystemExit(main())
