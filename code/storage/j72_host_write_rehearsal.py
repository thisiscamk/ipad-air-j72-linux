#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Exercise write/failure mechanics on a NEW regular HOST file only.

This is not an iOS writer or installer. APFS size is a model input, not a
filesystem measurement. There is no disk-device path or authorization interface.
"""
import hashlib
import os
from pathlib import Path
import stat
import sys

import j72_install_state as transaction
import j72_native_view_plan as view
import j72_storage_preflight as g

BLOCK = 4096
POSITIONS = dict(mbr=0, primary_header=1, primary_entries=2,
                 backup_entries=31_249_995, backup_header=31_249_999)


class HostWriteRehearsal:
    def __init__(self, directory, transition):
        g.require(sys.platform.startswith('linux'), 'This rehearsal runs on Linux hosts only')
        g.require(isinstance(transition, transaction.Transition), 'Validated transition required')
        self.transition = transition
        self.path = Path(directory) / 'new-disposable-host-disk.raw'
        # A fixed NEW filename, never an existing disk/file supplied by the caller.
        self.fd = os.open(self.path, os.O_RDWR | os.O_CREAT | os.O_EXCL |
                          os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
        self.failed = False
        self.closed = False
        self._step = 0
        self._next_image = 0
        self.receipts = []
        self._pwrite = os.pwrite
        self._sync = os.fsync
        try:
            os.ftruncate(self.fd, 128_000_000_000)
            self._identity = self._fd_identity()
            for key, lba in POSITIONS.items():
                data = transition.original[key]
                self._write_exact(lba * BLOCK, data, lba * BLOCK, lba * BLOCK + len(data))
            # Fence sentinels are synthetic bytes in a disposable host file.
            self.before = b'J72-HOST-BEFORE'.ljust(BLOCK, b'B')
            self.after = b'J72-HOST-AFTER'.ljust(BLOCK, b'A')
            first, end = view.FIRST * BLOCK, (view.LAST + 1) * BLOCK
            self._write_exact(first - BLOCK, self.before, first - BLOCK, first)
            self._write_exact(end, self.after, end, end + BLOCK)
            os.fsync(self.fd)
            self._expected = dict(transition.original)
        except BaseException:
            self.close()
            raise

    def _fd_identity(self):
        st = os.fstat(self.fd)
        g.require(stat.S_ISREG(st.st_mode) and st.st_size == 128_000_000_000,
                  'New host regular-file identity/size changed')
        return st.st_dev, st.st_ino, st.st_size

    def _guard(self):
        g.require(not self.closed and not self.failed, 'Closed or failed rehearsal cannot continue')
        g.require(self._fd_identity() == self._identity, 'Host file identity changed')

    def metadata(self):
        self._guard()
        return {key: os.pread(self.fd, len(self.transition.original[key]), lba * BLOCK)
                for key, lba in POSITIONS.items()}

    def _write_exact(self, offset, data, low, high):
        self._guard()
        g.require(type(offset) is int and type(data) is bytes and data and
                  offset % BLOCK == 0 and len(data) % BLOCK == 0 and
                  low <= offset and len(data) <= high - offset,
                  'Unaligned write or region fence crossed')
        cursor = 0
        interruptions = 0
        try:
            while cursor < len(data):
                try:
                    n = self._pwrite(self.fd, data[cursor:], offset + cursor)
                except InterruptedError:
                    interruptions += 1
                    if interruptions > 3:
                        raise OSError('Repeated interrupted write; stop for inspection')
                    continue
                # A partial unaligned write is uncertain: never continue with
                # an unaligned tail or automatically retry the whole operation.
                if type(n) is not int or n <= 0 or n > len(data) - cursor or n % BLOCK:
                    raise OSError('Zero, invalid or unaligned partial write')
                cursor += n
        except BaseException:
            self.failed = True
            raise

    def commit_next_metadata(self, key):
        self._guard()
        steps = self.transition.metadata_steps()
        g.require(self._step < len(steps) and key == steps[self._step]['name'],
                  'Metadata order is backup entries/header then primary entries/header')
        g.require(self.metadata() == self._expected, 'Metadata changed outside this host transaction')
        step = steps[self._step]
        data = self.transition.proposed[key]
        offset = step['lba'] * BLOCK
        try:
            self._write_exact(offset, data, offset, offset + len(data))
            self._sync(self.fd)
            g.require(os.pread(self.fd, len(data), offset) == data, 'Metadata readback mismatch')
            self._expected[key] = data
            g.require(self.metadata() == self._expected, 'Unexpected metadata readback')
        except BaseException:
            self.failed = True
            raise
        self.receipts.append(dict(step=key, host_fsync_and_exact_readback=True))
        self._step += 1

    def write_image_chunk(self, offset, data):
        self._guard()
        g.require(self._step == 4, 'All four metadata steps must finish first')
        g.require(type(offset) is int and offset == self._next_image,
                  'Image chunks must be sequential without holes or replay')
        bounds = self.transition.image_range(offset, len(data), self.metadata(),
                                              transaction.APFS_TARGET)
        first, end = view.FIRST * BLOCK, (view.LAST + 1) * BLOCK
        self._write_exact(bounds['disk_byte_offset'], data, first, end)
        self._next_image += len(data)

    def finish(self, expected_sha256):
        self._guard()
        g.require(self._next_image == view.CONTAINER_BYTES, 'Incomplete image cannot be verified')
        g.require(isinstance(expected_sha256, str) and len(expected_sha256) == 64 and
                  all(c in '0123456789abcdef' for c in expected_sha256), 'Invalid expected SHA256')
        try:
            self._sync(self.fd)
            h = hashlib.sha256()
            first = view.FIRST * BLOCK
            for offset in range(0, view.CONTAINER_BYTES, 1 << 20):
                data = os.pread(self.fd, 1 << 20, first + offset)
                g.require(len(data) == 1 << 20, 'Incomplete full image readback')
                h.update(data)
            g.require(h.hexdigest() == expected_sha256, 'Full image hash mismatch')
            g.require(self.metadata() == self.transition.proposed, 'Final GPT differs')
            g.require(os.pread(self.fd, BLOCK, first - BLOCK) == self.before and
                      os.pread(self.fd, BLOCK, (view.LAST + 1) * BLOCK) == self.after,
                      'Outside-extent sentinel changed')
        except BaseException:
            self.failed = True
            raise
        return dict(status='HOST_REGULAR_FILE_STREAM_FLUSH_READBACK_PASS',
                    model_apfs_size_only=True, apfs_resize_executed=False,
                    ipad_contacted=False, internal_storage_writes=False,
                    native_ios_writer_qualified=False, power_loss_durability_tested=False,
                    image_bytes=view.CONTAINER_BYTES, ordered_metadata_steps=self.receipts,
                    sequential_image_and_full_hash_pass=True, outside_fences_unchanged=True,
                    automatic_resume_or_repair=False, approval_ready=False)

    def close(self):
        if not self.closed:
            os.close(self.fd)
            self.closed = True
