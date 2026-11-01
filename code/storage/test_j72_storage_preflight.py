#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Synthetic GPT/failure tests. Never opens an iPad or a block device."""
import copy
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
import uuid
import zlib
import j72_storage_preflight as s

def header_crc(block):
    result = bytearray(block); result[16:20] = bytes(4)
    struct.pack_into('<I', result, 16, zlib.crc32(result[:struct.unpack_from('<I', result, 12)[0]]))
    return bytes(result)

def fixture(block=4096, occupied=False, entries=None):
    g = s.Geometry(block, 8*1024*1024*1024//block)
    count, stride = 128, 128
    table_blocks = (count*stride+block-1)//block
    first, last = 2+table_blocks, g.blocks-2-table_blocks
    if entries is None:
        entries = [(first, last if occupied else first+1023, s.APFS, 123)]
    table = bytearray(table_blocks*block)
    for i,(start,end,kind,identity) in enumerate(entries):
        offset=i*stride
        table[offset:offset+16]=uuid.UUID(kind).bytes_le
        table[offset+16:offset+32]=uuid.UUID(int=identity).bytes_le
        struct.pack_into('<QQQ', table, offset+32, start, end, 0)
        text='SyntheticOwnerName'.encode('utf-16-le');table[offset+56:offset+56+len(text)]=text
    crc = zlib.crc32(table[:count*stride])
    def h(current, alternate, where):
        data=bytearray(block);data[:8]=b'EFI PART'
        struct.pack_into('<IIIIQQQQ', data, 8, 0x10000,92,0,0,current,alternate,first,last)
        data[56:72]=uuid.UUID(int=456).bytes_le
        struct.pack_into('<QIII', data,72,where,count,stride,crc)
        return header_crc(data)
    mbr=bytearray(block);mbr[510:512]=b'\x55\xaa';mbr[450]=0xee
    struct.pack_into('<II',mbr,454,1,min(g.blocks-1,0xffffffff))
    return g, dict(mbr=bytes(mbr),primary_header=h(1,g.blocks-1,2),primary_entries=bytes(table),
                   backup_header=h(g.blocks-1,1,g.blocks-1-table_blocks),backup_entries=bytes(table))

def changed_header(data, name, offset, fmt, *values):
    result=copy.copy(data);b=bytearray(result[name]);struct.pack_into(fmt,b,offset,*values)
    result[name]=header_crc(b);return result

class GPTTests(unittest.TestCase):
    def test_valid_both_logical_sizes(self):
        for block in (512,4096):
            with self.subTest(block=block):
                g,d=fixture(block);a=s.audit(g,**d)
                self.assertEqual(a['partitions'][0]['bytes'],1024*block)
                self.assertTrue(a['gaps'])

    def test_geometry_refuses_guesses_overflow_and_bool(self):
        for block,blocks in [(0,1000),(1024,1000),(4096,0),(4096,(1<<32)+1),(True,1000),(4096,True)]:
            with self.subTest(block=block,blocks=blocks):
                with self.assertRaises(s.Refusal):s.Geometry(block,blocks)

    def test_primary_and_backup_crc_corruption(self):
        for name in ('primary_header','backup_header'):
            g,d=fixture();bad=bytearray(d[name]);bad[40]^=1;d[name]=bytes(bad)
            with self.assertRaisesRegex(s.Refusal,'CRC'):s.audit(g,**d)

    def test_entry_crc_corruption(self):
        for name in ('primary_entries','backup_entries'):
            g,d=fixture();bad=bytearray(d[name]);bad[40]^=1;d[name]=bytes(bad)
            with self.assertRaisesRegex(s.Refusal,'CRC'):s.audit(g,**d)

    def test_backup_identity_mismatch_even_with_valid_crc(self):
        g,d=fixture();d=changed_header(d,'backup_header',56,'16s',uuid.UUID(int=999).bytes_le)
        with self.assertRaisesRegex(s.Refusal,'disagree'):s.audit(g,**d)

    def test_header_location_and_usable_table_overlap(self):
        cases=[('primary_header',24,'Q',(2,)),('backup_header',32,'Q',(2,)),
               ('primary_header',72,'Q',(1000,)),
               ('backup_header',72,'Q',(1,)),('primary_header',84,'I',(129,)),
               ('primary_header',80,'I',(0xffffffff,))]
        for name,offset,fmt,values in cases:
            g,d=fixture();d=changed_header(d,name,offset,fmt,*values)
            with self.subTest(name=name,offset=offset):
                with self.assertRaises(s.Refusal):s.audit(g,**d)

    def test_truncated_and_excess_captures(self):
        for name in ('mbr','primary_header','primary_entries','backup_header','backup_entries'):
            for delta in (-1,1):
                g,d=fixture();d[name]=d[name][:-1] if delta<0 else d[name]+b'0'
                with self.subTest(name=name,delta=delta):
                    with self.assertRaises(s.Refusal):s.audit(g,**d)

    def test_undersized_entry_table_refused(self):
        g,d=fixture()
        d=changed_header(d,'primary_header',80,'I',1)
        with self.assertRaisesRegex(s.Refusal,'16 KiB'):s.audit(g,**d)

    def test_hybrid_mbr_refused(self):
        g,d=fixture();b=bytearray(d['mbr']);b[466]=0x83;d['mbr']=bytes(b)
        with self.assertRaisesRegex(s.Refusal,'hybrid'):s.audit(g,**d)

    def test_partition_overlap_and_invalid_ranges(self):
        for entries in [[(6,200,s.APFS,1),(200,300,s.APFS,2)],
                        [(6,5,s.APFS,1)],[(0,200,s.APFS,1)],
                        [(6,1<<32,s.APFS,1)]]:
            g,d=fixture(entries=entries)
            with self.assertRaises(s.Refusal):s.audit(g,**d)

    def test_null_and_duplicate_partition_identity(self):
        for entries in [[(6,100,s.APFS,0)],[(6,100,s.APFS,1),(200,300,s.APFS,1)]]:
            g,d=fixture(entries=entries)
            with self.assertRaisesRegex(s.Refusal,'identity'):s.audit(g,**d)

    def test_full_apfs_is_blocked_without_resize(self):
        g,d=fixture(occupied=True);a=s.audit(g,**d);p=s.free_space_plan(a,32*s.MIB,64*s.MIB)
        self.assertEqual(p['status'],'blocked');self.assertEqual(p['proposed_partitions'],[])
        self.assertFalse(p['approved_for_execution']);self.assertEqual(p['write_operations'],[])

    def test_existing_linux_is_preserved_too(self):
        g,d=fixture(occupied=True);first,last=6,g.blocks-6
        g,d=fixture(entries=[(first,last,'0fc63daf-8483-4772-8e79-3d69d8477de4',1)])
        p=s.free_space_plan(s.audit(g,**d),32*s.MIB,64*s.MIB)
        self.assertEqual(p['status'],'blocked')

    def test_only_unallocated_aligned_ranges_proposed(self):
        for block in (512,4096):
            g,d=fixture(block);a=s.audit(g,**d);p=s.free_space_plan(a,32*s.MIB,64*s.MIB)
            self.assertEqual(p['status'],'dry_run_only');self.assertFalse(p['approved_for_execution'])
            self.assertTrue(p['preserve_all_existing']);self.assertEqual(p['write_operations'],[])
            for part in p['proposed_partitions']:
                self.assertEqual(part['first_lba']*block%s.MIB,0)
                self.assertTrue(any(start<=part['first_lba']<=part['last_lba']<=end for start,end in a['gaps']))

    def test_report_omits_unique_identifiers_and_names(self):
        g,d=fixture();text=json.dumps(s.report(s.audit(g,**d)))
        self.assertNotIn('SyntheticOwnerName',text)
        self.assertNotIn(str(uuid.UUID(int=123)),text);self.assertNotIn(str(uuid.UUID(int=456)),text)
        self.assertIn(s.APFS,text)

    def test_read_interface_refuses_symlinks_fifos_devices_and_oversize(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);p=root/'real';p.write_bytes(b'1234')
            self.assertEqual(s.regular_bytes(p,4),b'1234')
            with self.assertRaises(s.Refusal):s.regular_bytes(p,3)
            link=root/'link';link.symlink_to(p)
            with self.assertRaises(OSError):s.regular_bytes(link,8)
            fifo=root/'fifo';os.mkfifo(fifo)
            with self.assertRaises(s.Refusal):s.regular_bytes(fifo,8)
            with self.assertRaises(s.Refusal):s.regular_bytes(Path('/dev/null'),8)

if __name__=='__main__':unittest.main()
