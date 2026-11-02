#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
import os
from pathlib import Path
import tempfile
import unittest
import uuid

import j72_host_write_rehearsal as host
import j72_install_state as state
import j72_rehearse_layout as layout
import j72_storage_preflight as g
from test_j72_rehearse_layout import fixture


class HostWriteTests(unittest.TestCase):
    def setUp(self):
        geometry, old = fixture()
        new, _ = layout.proposal(geometry, old, 126_357_602_304, uuid.UUID(int=10))
        self.transition = state.Transition(old, new)
        self.tmp = tempfile.TemporaryDirectory(prefix='j72-host-write-test-')
        self.disk = host.HostWriteRehearsal(self.tmp.name, self.transition)

    def tearDown(self):
        self.disk.close()
        self.tmp.cleanup()

    def commit(self):
        for row in self.transition.metadata_steps(): self.disk.commit_next_metadata(row['name'])

    def test_existing_file_and_symlink_refused(self):
        with self.assertRaises(FileExistsError): host.HostWriteRehearsal(self.tmp.name, self.transition)
        self.disk.close(); self.disk.path.unlink(); self.disk.path.symlink_to('/dev/null')
        with self.assertRaises(FileExistsError): host.HostWriteRehearsal(self.tmp.name, self.transition)

    def test_wrong_order_or_image_before_metadata_no_change(self):
        old = self.disk.metadata()
        with self.assertRaises(g.Refusal): self.disk.commit_next_metadata('primary_entries')
        with self.assertRaises(g.Refusal): self.disk.write_image_chunk(0, b'X' * 4096)
        self.assertEqual(self.disk.metadata(), old)

    def test_actual_commit_order_and_classification(self):
        expected = ['STOP_TORN_OR_INVALID_GPT_REQUIRES_RECOVERY_REVIEW',
                    'INTERRUPTED_BACKUP_COMMITTED_PRIMARY_ORIGINAL',
                    'STOP_TORN_OR_INVALID_GPT_REQUIRES_RECOVERY_REVIEW',
                    'PARTITIONS_COMMITTED_IMAGE_NOT_VERIFIED']
        for step, status in zip(self.transition.metadata_steps(), expected):
            self.disk.commit_next_metadata(step['name'])
            self.assertEqual(self.transition.classify(self.disk.metadata(), state.APFS_TARGET)['status'], status)
        self.assertEqual([r['step'] for r in self.disk.receipts], [r['name'] for r in self.transition.metadata_steps()])

    def test_host_image_write_and_outside_fences(self):
        self.commit(); first=host.view.FIRST * 4096
        self.disk.write_image_chunk(0,b'Z' * 4096)
        self.assertEqual(os.pread(self.disk.fd,4096,first), b'Z' * 4096)
        self.assertEqual(os.pread(self.disk.fd,4096,first-4096), self.disk.before)
        self.assertEqual(os.pread(self.disk.fd,4096,(host.view.LAST+1)*4096), self.disk.after)
        for offset,data in [(0,b'Z'*4096),(8192,b'Z'*4096),(4096,b'Z'*512),(4096,b'Z'*(1048576+4096))]:
            with self.assertRaises(g.Refusal): self.disk.write_image_chunk(offset,data)

    def test_aligned_short_write_and_eintr(self):
        real=os.pwrite; calls=[]
        def partial(fd,data,offset):
            calls.append(offset)
            if len(calls)==1: raise InterruptedError()
            return real(fd,data[:4096],offset)
        self.disk._pwrite=partial
        self.disk.commit_next_metadata('backup_entries')
        self.assertEqual(len(calls),5)
        self.assertEqual(os.pread(self.disk.fd,16384,31_249_995*4096),self.transition.proposed['backup_entries'])

    def test_unaligned_partial_write_latches_and_does_not_retry(self):
        calls=[]
        def partial(fd,data,offset):
            calls.append(offset);return os.pwrite(fd,data[:512],offset)
        self.disk._pwrite=partial
        with self.assertRaises(OSError):self.disk.commit_next_metadata('backup_entries')
        self.assertEqual(len(calls),1);self.assertTrue(self.disk.failed)
        with self.assertRaises(g.Refusal):self.disk.commit_next_metadata('backup_entries')

    def test_zero_write_repeated_eintr_and_sync_failure_latch(self):
        for kind in ('zero','eintr','sync'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                disk=host.HostWriteRehearsal(tmp,self.transition)
                try:
                    if kind=='zero':disk._pwrite=lambda *a:0
                    elif kind=='eintr':
                        def interrupted(*a):raise InterruptedError()
                        disk._pwrite=interrupted
                    else:
                        def failed(*a):raise OSError('injected host fsync failure')
                        disk._sync=failed
                    with self.assertRaises(OSError):disk.commit_next_metadata('backup_entries')
                    self.assertTrue(disk.failed);self.assertEqual(disk.receipts,[])
                finally:disk.close()

    def test_external_metadata_change_and_size_change_refused(self):
        os.pwrite(self.disk.fd,b'X'*4096,4096)
        with self.assertRaises(g.Refusal):self.disk.commit_next_metadata('backup_entries')
        os.ftruncate(self.disk.fd,4096)
        with self.assertRaises(g.Refusal):self.disk.metadata()

    def test_incomplete_image_never_verified(self):
        self.commit();self.disk.write_image_chunk(0,b'X'*4096)
        with self.assertRaises(g.Refusal):self.disk.finish('0'*64)


if __name__=='__main__':unittest.main()
