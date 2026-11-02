#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Validate captured GPT metadata and plan only unallocated space, offline.

No USB, block device, mount, resize, format or installation interface exists.
Disk identity and partition names are omitted from the default report.
"""
import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import stat
import struct
import uuid
import zlib

MIB = 1 << 20
MAX_TABLE_BYTES = 4 * MIB
APFS = '7c3457ef-0000-11aa-aa11-00306543ecac'

class Refusal(ValueError):
    pass

def require(condition, message):
    if not condition:
        raise Refusal(message)

@dataclass(frozen=True)
class Geometry:
    block_bytes: int
    blocks: int

    def __post_init__(self):
        require(type(self.block_bytes) is int and self.block_bytes in (512, 4096),
                'Only explicit 512/4096-byte logical geometry is supported')
        require(type(self.blocks) is int and 128 <= self.blocks <= (1 << 32),
                'Geometry exceeds the audited ANS1 32-bit LBA range')

def digest(data):
    return hashlib.sha256(data).hexdigest()

def parse_header(data, geometry, primary):
    b, n = geometry.block_bytes, geometry.blocks
    require(len(data) == b and data[:8] == b'EFI PART', 'GPT signature or header block size invalid')
    revision, size, crc, reserved = struct.unpack_from('<IIII', data, 8)
    require(revision == 0x10000 and 92 <= size <= b and reserved == 0,
            'Unsupported GPT revision, header length or reserved field')
    checked = bytearray(data[:size]); checked[16:20] = bytes(4)
    require(zlib.crc32(checked) == crc, 'GPT header CRC mismatch')
    current, alternate, first, last = struct.unpack_from('<QQQQ', data, 24)
    require((current, alternate) == ((1, n-1) if primary else (n-1, 1)),
            'GPT primary/backup header locations do not match geometry')
    require(2 <= first <= last < n-1, 'GPT usable range invalid')
    disk_guid = data[56:72]
    require(disk_guid != bytes(16), 'Null GPT disk identity')
    table, count, stride, table_crc = struct.unpack_from('<QIII', data, 72)
    require(1 <= count <= 4096 and 128 <= stride <= 1024 and stride & (stride-1) == 0,
            'Unsupported GPT entry dimensions')
    table_bytes = count * stride
    require(16384 <= table_bytes <= MAX_TABLE_BYTES,
            'GPT entry table must reserve at least 16 KiB and fit the metadata budget')
    table_blocks = (table_bytes + b-1) // b
    if primary:
        require(2 <= table and table + table_blocks <= first,
                'Primary GPT entries overlap usable space or metadata')
    else:
        require(last < table and table + table_blocks <= n-1,
                'Backup GPT entries overlap usable space or header')
    return dict(current=current, alternate=alternate, first=first, last=last,
                disk_guid=disk_guid, table=table, count=count, stride=stride,
                table_crc=table_crc, table_bytes=table_bytes, table_blocks=table_blocks)

def check_mbr(data, geometry):
    require(len(data) == geometry.block_bytes and data[510:512] == b'\x55\xaa',
            'Protective MBR signature or block size invalid')
    used = [data[446+i*16:462+i*16] for i in range(4) if data[446+i*16+4]]
    require(len(used) == 1 and used[0][4] == 0xee, 'Missing protective MBR or unsupported hybrid MBR')
    start, blocks = struct.unpack_from('<II', used[0], 8)
    require(start == 1 and blocks == min(geometry.blocks-1, 0xffffffff),
            'Protective MBR geometry mismatch')

def audit(geometry, mbr, primary_header, primary_entries, backup_header, backup_entries):
    check_mbr(mbr, geometry)
    p = parse_header(primary_header, geometry, True)
    q = parse_header(backup_header, geometry, False)
    for key in ('first', 'last', 'disk_guid', 'count', 'stride', 'table_crc'):
        require(p[key] == q[key], 'Primary and backup GPT disagree: ' + key)
    for h, data in ((p, primary_entries), (q, backup_entries)):
        require(len(data) == h['table_blocks'] * geometry.block_bytes, 'Incomplete or oversized GPT entry capture')
        require(zlib.crc32(data[:h['table_bytes']]) == h['table_crc'], 'GPT entry-table CRC mismatch')
    require(primary_entries[:p['table_bytes']] == backup_entries[:q['table_bytes']],
            'Primary and backup GPT entry arrays differ')
    partitions, identities, empty_slots = [], set(), []
    for i in range(p['count']):
        entry = primary_entries[i*p['stride']:(i+1)*p['stride']]
        if entry[:16] == bytes(16):
            require(entry == bytes(p['stride']), 'Nonzero unused GPT entry needs separate review')
            empty_slots.append(i+1)
            continue
        identity = entry[16:32]
        require(identity != bytes(16) and identity not in identities, 'Null or duplicate partition identity')
        identities.add(identity)
        first, last, flags = struct.unpack_from('<QQQ', entry, 32)
        require(p['first'] <= first <= last <= p['last'], 'Partition outside usable GPT range')
        try:
            entry[56:128].decode('utf-16-le', errors='strict')
        except UnicodeError as exc:
            raise Refusal('Invalid UTF-16 GPT partition name') from exc
        partitions.append(dict(index=i+1, type_guid=str(uuid.UUID(bytes_le=entry[:16])),
                               first_lba=first, last_lba=last, attributes=flags,
                               bytes=(last-first+1)*geometry.block_bytes))
    ordered = sorted(partitions, key=lambda x: x['first_lba'])
    gaps, cursor = [], p['first']
    for item in ordered:
        require(cursor <= item['first_lba'], 'Overlapping partitions')
        if cursor < item['first_lba']:
            gaps.append((cursor, item['first_lba']-1))
        cursor = item['last_lba']+1
    if cursor <= p['last']:
        gaps.append((cursor, p['last']))
    return dict(geometry=geometry, primary=p, backup=q, partitions=partitions,
                gaps=gaps, empty_slots=empty_slots,
                capture_hashes={k:digest(v) for k,v in dict(mbr=mbr, primary_header=primary_header,
                primary_entries=primary_entries, backup_header=backup_header, backup_entries=backup_entries).items()})

def free_space_plan(inventory, boot_bytes, root_bytes):
    """Pure dry run. Never replace, shrink or reinterpret an existing partition."""
    require(type(boot_bytes) is int and type(root_bytes) is int and
            MIB <= boot_bytes <= (1 << 40) and MIB <= root_bytes <= (1 << 40),
            'Explicit positive image/headroom sizes are required')
    g = inventory['geometry']; alignment = MIB // g.block_bytes
    up = lambda value: ((value + alignment-1) // alignment)*alignment
    boot = up((boot_bytes + g.block_bytes-1)//g.block_bytes)
    root = up((root_bytes + g.block_bytes-1)//g.block_bytes)
    result = dict(approved_for_execution=False, write_operations=[], preserve_all_existing=True,
                  requested_boot_bytes=boot_bytes, requested_root_bytes=root_bytes, proposed_partitions=[])
    if len(inventory['empty_slots']) < 2:
        return {**result, 'status':'blocked', 'reason':'Two unused GPT entries are required'}
    for first, last in inventory['gaps']:
        start, end = up(first), ((last+1)//alignment)*alignment
        if end-start < boot+root:
            continue
        proposed = [dict(purpose='boot', index=inventory['empty_slots'][0], first_lba=start, last_lba=start+boot-1),
                    dict(purpose='root', index=inventory['empty_slots'][1], first_lba=start+boot, last_lba=start+boot+root-1)]
        return {**result, 'status':'dry_run_only', 'proposed_partitions':proposed,
                'reason':'Free-space geometry fits; driver, backups, filesystem and approval gates remain'}
    return {**result, 'status':'blocked', 'reason':'No existing unallocated range fits; APFS shrink is not implemented or authorized'}

def report(inventory, plan=None):
    g = inventory['geometry']
    result = dict(status='metadata_valid', offline_only=True, writes_authorized=False,
                  device_identity_verified_by_this_tool=False,
                  logical_block_bytes=g.block_bytes, total_blocks=g.blocks, disk_bytes=g.blocks*g.block_bytes,
                  partitions=inventory['partitions'],
                  unallocated_ranges=[dict(first_lba=a, last_lba=b, bytes=(b-a+1)*g.block_bytes) for a,b in inventory['gaps']],
                  unique_disk_and_partition_ids_omitted=True, partition_names_omitted=True,
                  capture_hashes=inventory['capture_hashes'])
    if plan is not None:
        result['plan'] = plan
    return result

def regular_bytes(path, maximum):
    # Refuse devices, symlinks and FIFOs even if their name resembles a capture.
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        st = os.fstat(fd)
        require(stat.S_ISREG(st.st_mode) and 0 < st.st_size <= maximum, 'Expected bounded regular capture file')
        with os.fdopen(fd, 'rb', closefd=False) as file:
            return file.read(maximum+1)
    finally:
        os.close(fd)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture', type=Path, required=True, help='Host directory of immutable captured metadata files')
    p.add_argument('--report', type=Path, help='New host JSON report; existing files are refused')
    p.add_argument('--plan-free-space', action='store_true')
    p.add_argument('--boot-mib', type=int, default=1024, help='Upstream planning default; not an install command')
    p.add_argument('--root-mib', type=int, default=8192, help='Upstream planning default; not an install command')
    args = p.parse_args(); os.umask(0o077)
    metadata = json.loads(regular_bytes(args.capture/'geometry.json', 16384))
    g = Geometry(metadata['logical_block_bytes'], metadata['total_blocks'])
    data = {name:regular_bytes(args.capture/(name.replace('_','-')+'.bin'),
                 MAX_TABLE_BYTES if 'entries' in name else g.block_bytes)
            for name in ['mbr','primary_header','primary_entries','backup_header','backup_entries']}
    inventory = audit(g, **data)
    plan = free_space_plan(inventory, args.boot_mib*MIB, args.root_mib*MIB) if args.plan_free_space else None
    text = json.dumps(report(inventory, plan), indent=2)+'\n'
    if args.report:
        fd = os.open(args.report, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as file:
            file.write(text)
        print('Offline report saved; device writes are not authorized')
    else:
        print(text, end='')
    return 2 if plan and plan['status']=='blocked' else 0

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (Refusal, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise SystemExit('REFUSED: '+str(exc))
