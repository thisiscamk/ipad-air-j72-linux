#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Bound captured J72 APFS checkpoint descriptors; never mount or repair APFS.

Format: Apple's File System Reference (2020), Container / Objects sections.
Fletcher-64 arithmetic cross-checked against linux-apfs/apfsprogs checksum.c.
Selecting a superblock candidate is NOT full checkpoint validation.
"""
import struct
import j72_storage_preflight as g

BLOCK = 4096
MAX_DESCRIPTOR_BLOCKS = 1024  # 4 MiB capture budget, never an unbounded scan.
APFS_FIRST = 6
APFS_MAX_BLOCKS = 31_249_989


def checksum(data):
    g.require(len(data) == BLOCK, 'Expected one complete 4096-byte APFS object')
    one = two = 0
    modulus = 0xffffffff
    for word, in struct.iter_unpack('<I', data[8:]):
        one += word
        two += one
    first = modulus - (one + two) % modulus
    second = modulus - (one + first) % modulus
    return struct.pack('<II', first, second)


def superblock(data, partition_blocks):
    g.require(type(partition_blocks) is int and 0 < partition_blocks <= APFS_MAX_BLOCKS,
              'Explicit measured APFS partition bounds are required')
    g.require(len(data) == BLOCK and data[:8] == checksum(data), 'APFS object checksum invalid')
    oid, xid, kind, subtype = struct.unpack_from('<QQII', data, 8)
    g.require(oid == 1 and xid > 0 and kind == 0x80000001 and subtype == 0,
              'Expected the measured ephemeral NX superblock object type')
    magic, size, blocks = struct.unpack_from('<4sIQ', data, 32)
    g.require(magic == b'NXSB' and size == BLOCK and 0 < blocks <= partition_blocks,
              'Wrong APFS magic, block size or container extent')
    features, rofeatures, incompatible = struct.unpack_from('<QQQ', data, 48)
    g.require(rofeatures == 0 and incompatible == 2,
              'Only the measured non-Fusion version-2 container is supported')
    identity = data[72:88]
    g.require(identity != bytes(16), 'Null APFS container identity')
    descriptors, datacount, base, database = struct.unpack_from('<IIQQ', data, 104)
    g.require(0 < descriptors <= MAX_DESCRIPTOR_BLOCKS and datacount > 0 and datacount < (1 << 31),
              'Tree descriptor layouts, empty areas or scan budgets are unsupported')
    g.require(0 < base < blocks and descriptors <= blocks - base and
              0 < database < blocks and datacount <= blocks - database,
              'Checkpoint area crosses the actual container boundary')
    g.require(base + descriptors <= database or database + datacount <= base,
              'Checkpoint descriptor and data areas overlap')
    return dict(xid=xid, blocks=blocks, bytes=blocks * BLOCK, identity=identity,
                descriptor_base=base, descriptor_blocks=descriptors,
                data_base=database, data_blocks=datacount,
                features=features, readonly_features=rofeatures, incompatible=incompatible)


def descriptor_plan(anchor, partition_blocks):
    sb = superblock(anchor, partition_blocks)
    return dict(status='BOUNDED_DESCRIPTOR_READ_PLAN_ONLY', executed=False,
                disk_first_lba=APFS_FIRST + sb['descriptor_base'],
                count_4096=sb['descriptor_blocks'], bytes=sb['descriptor_blocks'] * BLOCK,
                capture_all_descriptor_blocks_required=True,
                block_zero_is_authoritative=False, internal_writes=False)


def candidates(anchor, descriptors, partition_blocks):
    sb = superblock(anchor, partition_blocks)
    g.require(len(descriptors) == sb['descriptor_blocks'] * BLOCK,
              'Full descriptor-area capture is required; partial scan cannot pick the latest candidate')
    found, malformed = [], 0
    for index in range(sb['descriptor_blocks']):
        data = descriptors[index * BLOCK:(index + 1) * BLOCK]
        kind = struct.unpack_from('<I', data, 24)[0] & 0xffff
        if data[32:36] != b'NXSB' and kind != 1:
            continue
        try:
            item = superblock(data, partition_blocks)
            g.require(item['identity'] == sb['identity'] and
                      item['descriptor_base'] == sb['descriptor_base'] and
                      item['descriptor_blocks'] == sb['descriptor_blocks'],
                      'Candidate identity or descriptor layout differs from the anchor')
        except g.Refusal:
            malformed += 1
            continue
        found.append((item['xid'], index, item, data))
    g.require(found, 'No valid NX superblock candidate in the captured descriptor area')
    newest = max(item[0] for item in found)
    choices = [item for item in found if item[0] == newest]
    g.require(all(item[3] == choices[0][3] for item in choices),
              'Conflicting NX superblocks have the same transaction identifier')
    selected = choices[0]
    return dict(status='LATEST_NX_SUPERBLOCK_CANDIDATE_ONLY',
                anchor_xid=sb['xid'], candidate_xid=newest,
                candidate_container_bytes=selected[2]['bytes'],
                candidate_disk_lba=APFS_FIRST + sb['descriptor_base'] + selected[1],
                valid_nx_candidates=len(found), malformed_nx_candidates=malformed,
                block_zero_matches_candidate_size=sb['blocks'] == selected[2]['blocks'],
                checkpoint_maps_and_ephemeral_objects_validated=False,
                sufficient_for_resize_or_write_authorization=False,
                internal_writes=False)


def checkpoint_object_plan(anchor, descriptors, partition_blocks):
    """Validate the selected candidate's descriptor chain and fence object reads.

    First qualification deliberately supports only one-block ephemeral objects.
    No arbitrary address, object-tree traversal or APFS volume reads are exposed.
    """
    result = candidates(anchor, descriptors, partition_blocks)
    root = superblock(anchor, partition_blocks)
    selected_index = result['candidate_disk_lba'] - APFS_FIRST - root['descriptor_base']
    selected_bytes = descriptors[selected_index * BLOCK:(selected_index + 1) * BLOCK]
    selected = superblock(selected_bytes, partition_blocks)
    next_desc, next_data, index, length, data_index, data_length = struct.unpack_from('<IIIIII', selected_bytes, 128)
    count = root['descriptor_blocks']
    g.require(0 <= index < count and 2 <= length <= count and
              (index + length - 1) % count == selected_index and
              next_desc == (index + length) % count,
              'Candidate descriptor chain endpoints disagree')
    g.require(0 <= data_index < selected['data_blocks'] and
              0 < data_length <= 256 and data_length <= selected['data_blocks'] and
              next_data == (data_index + data_length) % selected['data_blocks'],
              'Active checkpoint data ring is unsupported or inconsistent')
    objects, seen_ids, seen_positions = [], set(), set()
    for ordinal in range(length - 1):
        position = (index + ordinal) % count
        raw = descriptors[position * BLOCK:(position + 1) * BLOCK]
        g.require(raw[:8] == checksum(raw), 'Checkpoint mapping checksum invalid')
        oid, xid, kind, subtype, flags, entries = struct.unpack_from('<QQIIII', raw, 8)
        g.require(oid == root['descriptor_base'] + position and
                  xid == selected['xid'] and kind == 0x4000000c and subtype == 0,
                  'Checkpoint mapping header does not match selected transaction')
        g.require(flags == int(ordinal == length - 2) and 0 < entries <= (BLOCK - 40) // 40,
                  'Checkpoint mapping flags or entry count invalid')
        for item in range(entries):
            kind, subtype, size, reserved, fs, oid, addr = struct.unpack_from('<IIIIQQQ', raw, 40 + item * 40)
            g.require(kind >> 16 == 0x8000 and kind & 0xffff not in (0, 1, 12) and
                      size == BLOCK and reserved == 0 and oid > 0,
                      'Unsupported mapped object type, size or reserved field')
            relative = addr - selected['data_base']
            g.require(0 <= relative < selected['data_blocks'] and
                      (relative - data_index) % selected['data_blocks'] < data_length,
                      'Mapped ephemeral object crosses the active checkpoint data ring')
            g.require((fs, oid) not in seen_ids and relative not in seen_positions,
                      'Duplicate object identity or overlapping physical object')
            seen_ids.add((fs, oid)); seen_positions.add(relative)
            objects.append(dict(container_lba=addr, disk_lba=APFS_FIRST + addr,
                                bytes=size, oid=oid, xid=xid, kind=kind, subtype=subtype))
    g.require(len(objects) == data_length and len(objects) <= 256,
              'Mapped objects do not cover the entire bounded checkpoint data ring')
    return dict(status='CHECKPOINT_OBJECT_READ_PLAN_ONLY', executed=False,
                candidate=result, objects=objects, object_bytes=len(objects) * BLOCK,
                mapping_chain_validated=True, ephemeral_objects_validated=False,
                internal_writes=False)


def verify_checkpoint(anchor, descriptors, partition_blocks, captured_objects):
    plan = checkpoint_object_plan(anchor, descriptors, partition_blocks)
    g.require(set(captured_objects) == {obj['disk_lba'] for obj in plan['objects']},
              'Captured objects differ from the exact bounded read plan')
    for obj in plan['objects']:
        raw = captured_objects[obj['disk_lba']]
        g.require(len(raw) == BLOCK and raw[:8] == checksum(raw),
                  'Ephemeral object size or checksum invalid')
        oid, xid, kind, subtype = struct.unpack_from('<QQII', raw, 8)
        g.require((oid, xid, kind, subtype) == (obj['oid'], obj['xid'], obj['kind'], obj['subtype']),
                  'Ephemeral object header differs from checkpoint mapping')
    return dict(status='BOUNDED_CHECKPOINT_HEADERS_AND_CHECKSUMS_PASS',
                candidate_container_bytes=plan['candidate']['candidate_container_bytes'],
                mapping_chain_validated=True, ephemeral_object_count=len(plan['objects']),
                ephemeral_object_headers_and_checksums_validated=True,
                full_filesystem_semantics_validated=False,
                sufficient_for_resize_or_write_authorization=False,
                internal_writes=False)
