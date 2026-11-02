#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Pure J72 interrupted-install classification; no disk or repair interface.

Inputs are previously captured bytes and an independently measured APFS size.
This model never invokes resize, a writer, mount, dmsetup or automatic repair.
Its results are preparation for a qualified native iOS implementation.
"""
from dataclasses import dataclass
import struct
import uuid

import j72_storage_preflight as g
import j72_rehearse_layout as layout
import j72_native_view_plan as view

BLOCK = 4096
BLOCKS = 31_250_000
APFS_ORIGINAL = (31_249_994 - 6 + 1) * BLOCK
APFS_TARGET = (view.FIRST - 6) * BLOCK
PARTS = ('mbr', 'primary_header', 'primary_entries', 'backup_header', 'backup_entries')


@dataclass(frozen=True)
class Transition:
    original: dict
    proposed: dict

    def __post_init__(self):
        # Capture immutable copies: mutating the caller's dictionaries must not
        # silently change the expected transaction after validation.
        from types import MappingProxyType
        old = {key: bytes(self.original[key]) for key in PARTS}
        new = {key: bytes(self.proposed[key]) for key in PARTS}
        geometry = g.Geometry(BLOCK, BLOCKS)
        g.audit(geometry, **old)
        g.audit(geometry, **new)
        identity = uuid.UUID(bytes_le=new['primary_entries'][144:160])
        expected, _ = layout.proposal(geometry, old, APFS_TARGET, identity)
        g.require(new == expected, 'Proposed metadata differs from the exact reviewed transition')
        object.__setattr__(self, 'original', MappingProxyType(old))
        object.__setattr__(self, 'proposed', MappingProxyType(new))

    def copy_state(self, captured, primary):
        prefix = 'primary' if primary else 'backup'
        keys = (prefix + '_header', prefix + '_entries')
        try:
            header = g.parse_header(captured[keys[0]], g.Geometry(BLOCK, BLOCKS), primary)
            table = captured[keys[1]]
            import zlib
            g.require(len(table) == header['table_blocks'] * BLOCK and
                      zlib.crc32(table[:header['table_bytes']]) == header['table_crc'],
                      'Incomplete or torn GPT entry array')
        except (g.Refusal, KeyError, TypeError, struct.error):
            return 'invalid'
        if all(captured[key] == self.original[key] for key in keys):
            return 'original'
        if all(captured[key] == self.proposed[key] for key in keys):
            return 'proposed'
        # Valid CRCs alone do not establish identity, ownership or authorization.
        return 'foreign'

    def classify(self, captured, apfs_bytes, *, image_verified=False):
        g.require(type(apfs_bytes) is int and apfs_bytes > 0,
                  'A positive independently measured APFS size is required')
        g.require(type(image_verified) is bool, 'Image verification must be explicit')
        p = self.copy_state(captured, True)
        q = self.copy_state(captured, False)
        result = dict(primary=p, backup=q, automatic_repair=False,
                      device_writes_permitted=False, execution_ready=False,
                      native_mount_candidate=False)
        if captured.get('mbr') != self.original['mbr']:
            status = 'STOP_PROTECTIVE_MBR_CHANGED'
        elif apfs_bytes not in (APFS_ORIGINAL, APFS_TARGET):
            status = 'STOP_APFS_SIZE_UNKNOWN_OR_PARTIAL'
        elif apfs_bytes == APFS_ORIGINAL:
            status = ('ORIGINAL_UNCHANGED' if (p, q) == ('original', 'original')
                      else 'STOP_GPT_CHANGED_BEFORE_CONFIRMED_SHRINK')
        elif 'foreign' in (p, q):
            status = 'STOP_UNRECOGNIZED_VALID_GPT'
        elif 'invalid' in (p, q):
            status = 'STOP_TORN_OR_INVALID_GPT_REQUIRES_RECOVERY_REVIEW'
        elif (p, q) == ('original', 'original'):
            status = 'APFS_SHRUNK_GPT_NOT_COMMITTED'
        elif (p, q) == ('original', 'proposed'):
            status = 'INTERRUPTED_BACKUP_COMMITTED_PRIMARY_ORIGINAL'
        elif (p, q) == ('proposed', 'original'):
            status = 'STOP_UNEXPECTED_PRIMARY_FIRST_ORDER'
        else:
            # This is only a model state. A real reader must independently bind
            # live disk identity, APFS extent, both GPT copies and image hash.
            status = ('LOCAL_IMAGE_VERIFIED_READ_ONLY_CANDIDATE' if image_verified
                      else 'PARTITIONS_COMMITTED_IMAGE_NOT_VERIFIED')
            result['native_mount_candidate'] = image_verified
        return {**result, 'status': status}

    def metadata_steps(self):
        """Proposed backup-before-primary order, not executable write requests."""
        return [dict(name=key, lba=lba, blocks=len(self.proposed[key]) // BLOCK,
                     sha256=g.digest(self.proposed[key])) for key, lba in (
                         ('backup_entries', BLOCKS - 5), ('backup_header', BLOCKS - 1),
                         ('primary_entries', 2), ('primary_header', 1))]

    def image_range(self, offset, length, observed, apfs_bytes):
        """Review a single image chunk. No I/O, authorization or repair occurs."""
        state = self.classify(observed, apfs_bytes)
        g.require(state['status'] == 'PARTITIONS_COMMITTED_IMAGE_NOT_VERIFIED',
                  'Both exact GPT copies and confirmed shrink are prerequisites')
        g.require(type(offset) is int and type(length) is int and
                  0 <= offset < view.CONTAINER_BYTES and 0 < length <= (1 << 20) and
                  offset % BLOCK == 0 and length % BLOCK == 0 and
                  length <= view.CONTAINER_BYTES - offset,
                  'Image chunk is unaligned, exceeds the bounded extent or budget')
        absolute = view.FIRST * BLOCK + offset
        g.require(absolute >= view.FIRST * BLOCK and
                  absolute + length <= (view.LAST + 1) * BLOCK,
                  'Image chunk crosses the Linux partition fence')
        return dict(disk_byte_offset=absolute, length=length, executable=False)


def interrupted_metadata_matrix(transition):
    """Memory-only old/new/torn 4KiB outcomes for every proposed GPT step.

    Each logical block is modelled independently as old, new or torn. This
    exposes all mixed states that arise along the proposed sequential order;
    it does not claim physical atomicity, flush support or power-loss coverage.
    """
    current = dict(transition.original)
    rows = [dict(point='after_confirmed_apfs_shrink',
                 state=transition.classify(current, APFS_TARGET))]
    for step in transition.metadata_steps():
        key = step['name']
        before = current[key]
        for block in range(step['blocks']):
            a, b = block * BLOCK, (block + 1) * BLOCK
            # New prefix / old suffix after each block completion.
            current[key] = transition.proposed[key][:b] + before[b:]
            rows.append(dict(point=f'{key}:completed-block-{block}',
                             state=transition.classify(current, APFS_TARGET)))
            # A torn block may remain CRC-valid if damage is in header padding;
            # exact byte comparisons must still reject it as unrecognized.
            torn = bytearray(current[key]); torn[b - 1] ^= 1
            damaged = {**current, key: bytes(torn)}
            rows.append(dict(point=f'{key}:torn-block-{block}',
                             state=transition.classify(damaged, APFS_TARGET)))
        current[key] = transition.proposed[key]
    rows.append(dict(point='after_full_image_hash_readback',
                     state=transition.classify(current, APFS_TARGET, image_verified=True)))
    return rows
