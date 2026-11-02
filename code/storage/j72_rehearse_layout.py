#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Rehearse conditional J72 GPT bytes in new host files; no installation API."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import struct
import uuid
import zlib

import j72_storage_preflight as gpt
import j72_native_view_plan as view


def proposal(geometry, captured, minimum_bytes, partition_guid):
    before = gpt.audit(geometry, **captured)
    gpt.require(geometry.block_bytes == 4096 and geometry.blocks == 31_250_000,
                'Only the measured J72 disk geometry is supported')
    gpt.require(len(before['partitions']) == 1, 'Expected the original single APFS partition')
    apple = before['partitions'][0]
    gpt.require(apple['type_guid'] == gpt.APFS and apple['index'] == 1 and
                apple['first_lba'] == 6 and apple['last_lba'] == 31_249_994,
                'Original APFS extent/type differs from the measured layout')
    gpt.require(2 in before['empty_slots'] and before['primary']['stride'] == 128 and
                before['primary']['count'] == 128,
                'Expected 128 GPT entries and an unused second 128-byte entry')
    target_bytes = (view.FIRST - apple['first_lba']) * geometry.block_bytes
    gpt.require(type(minimum_bytes) is int and 0 < minimum_bytes <= target_bytes < apple['bytes'],
                'Explicit observed minimum must fit below the proposed APFS target')
    gpt.require(minimum_bytes % 4096 == 0, 'Minimum size must be 4096-byte aligned')
    gpt.require(partition_guid.int != 0, 'Proposed Linux partition identity must not be null')
    table = bytearray(captured['primary_entries'])
    gpt.require(table[128:256] == bytes(128), 'Second GPT slot is not empty')
    struct.pack_into('<Q', table, 40, view.FIRST - 1)
    table[128:144] = uuid.UUID(view.LINUX_TYPE).bytes_le
    table[144:160] = partition_guid.bytes_le
    struct.pack_into('<QQQ', table, 160, view.FIRST, view.LAST, 0)
    name = 'J72Linux'.encode('utf-16-le')
    table[184:184 + len(name)] = name
    gpt.require(table[:40] == captured['primary_entries'][:40] and
                table[48:128] == captured['primary_entries'][48:128] and
                table[256:] == captured['primary_entries'][256:],
                'Unexpected change outside APFS endpoint and the new Linux entry')
    table_crc = zlib.crc32(table[:before['primary']['table_bytes']])
    future = dict(captured)
    for key in ('primary_entries', 'backup_entries'):
        future[key] = bytes(table)
    for key in ('primary_header', 'backup_header'):
        header = bytearray(captured[key])
        struct.pack_into('<I', header, 88, table_crc)
        header[16:20] = bytes(4)
        size = struct.unpack_from('<I', header, 12)[0]
        struct.pack_into('<I', header, 16, zlib.crc32(header[:size]))
        future[key] = bytes(header)
    after = gpt.audit(geometry, **future)
    mapping = view.native_view_plan(after)
    result = {
        'status': 'OFFLINE_GPT_REHEARSAL_PASS_NOT_EXECUTABLE',
        'device_access': False, 'internal_writes_authorized': False,
        'approval_ready': False,
        'unresolved': ['qualified iOS 12 APFS resize and recovery procedure',
                       'partition-fenced iOS image/GPT writer and verification',
                       'normal mounted desktop cleanup and owner UI check',
                       'current restore/recovery availability', 'exact owner write authorization'],
        'original_apfs_bytes': apple['bytes'], 'observed_minimum_bytes': minimum_bytes,
        'proposed_apfs_bytes': target_bytes,
        'headroom_above_observed_minimum_bytes': target_bytes - minimum_bytes,
        'linux_bytes': view.CONTAINER_BYTES,
        'linux_first_lba_4096': view.FIRST, 'linux_last_lba_4096': view.LAST,
        'protective_mbr_changed': False,
        'apple_type_unique_id_name_attributes_and_start_preserved': True,
        'original_disk_identity_and_header_positions_preserved': True,
        'future_primary_and_backup_gpt_crc_pass': True,
        'snapshot_deletion_planned': False,
        'native_linux_driver_write_support_required_for_first_read_only_root': False,
        'proposed_first_install_write_backend': 'iOS native storage stack; helper unqualified',
        'write_operations_executed': [], 'future_read_only_view': mapping,
        'phase_order_for_review_only': [
            'qualify resize/write/recovery helpers; obtain exact authorization',
            'APFS resize to explicit nonzero byte target; verify success and actual container size',
            'update and independently verify both GPT copies using a qualified transaction/recovery protocol',
            'write verified image only inside the newly verified Linux extent using a fenced iOS helper',
            'flush and full image readback; revalidate preserved metadata and normal iOS boot',
            'changed host-assisted Linux boot; readonly bounded map, ro,noload ext4 and compressed base',
        ],
    }
    return future, result


def image_digest(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        gpt.require(stat.S_ISREG(info.st_mode) and info.st_size == view.CONTAINER_BYTES,
                    'Image must be a regular 1536 MiB host file')
        digest = hashlib.sha256()
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            while block := stream.read(1024 * 1024):
                digest.update(block)
        after = os.fstat(fd)
        gpt.require((after.st_size, after.st_mtime_ns, after.st_ctime_ns) ==
                    (info.st_size, info.st_mtime_ns, info.st_ctime_ns),
                    'Image changed during hashing')
        return digest.hexdigest()
    finally:
        os.close(fd)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture', type=Path, required=True)
    p.add_argument('--image', type=Path, required=True)
    p.add_argument('--minimum-bytes', type=int, required=True)
    p.add_argument('--output', type=Path, required=True, help='New host directory; never a block device')
    a = p.parse_args()
    os.umask(0o077)
    meta = json.loads(gpt.regular_bytes(a.capture / 'geometry.json', 16384))
    geometry = gpt.Geometry(meta['logical_block_bytes'], meta['total_blocks'])
    captured = {name: gpt.regular_bytes(a.capture / (name.replace('_', '-') + '.bin'),
                                      gpt.MAX_TABLE_BYTES if 'entries' in name else geometry.block_bytes)
                for name in ('mbr', 'primary_header', 'primary_entries', 'backup_header', 'backup_entries')}
    future, result = proposal(geometry, captured, a.minimum_bytes, uuid.uuid4())
    result['image_sha256'] = image_digest(a.image)
    a.output.mkdir(mode=0o700, parents=False, exist_ok=False)
    (a.output / 'geometry.json').write_text(json.dumps(meta, indent=2) + '\n')
    for name, data in future.items():
        (a.output / (name.replace('_', '-') + '.bin')).write_bytes(data)
    (a.output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS: future GPT CRCs, preserved Apple fields, bounded mapping and host image hash; no device access')
    print('This is not an installation proposal ready for authorization; resize/write/recovery qualification remains')


if __name__ == '__main__':
    main()
