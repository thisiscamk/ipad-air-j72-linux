#!/usr/bin/env python3
"""Offline actual-source USB response/ROM/TRX refusals and private packer tests."""
import importlib.util
from pathlib import Path
import re,struct,subprocess,tempfile
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('pack',ROOT/'j72_pack_wifi_trx.py');pack=importlib.util.module_from_spec(spec);spec.loader.exec_module(pack)
# Synthetic firmware and synthetic unicast address only.
mac=bytes([2,0,0,0,0,1]);body=b'X'*128
raw=bytearray(struct.pack('<7I',0x30524448,28+128+16,0,0x10020,128,4,0)+body+bytes(16));struct.pack_into('<I',raw,8,pack.crc(raw));raw=bytes(raw)
image=pack.pack(raw,'boardrev=1\nccode=XY\n',mac)
assert struct.unpack_from('<I',image,4)[0]==len(image)
assert pack.crc(image)==struct.unpack_from('<I',image,8)[0]
assert image[28:156]==body
count=1
bad=[]
for offset,value in [(0,0),(4,1),(8,0),(12,0),(16,0),(16,0xffffffff),(20,129),(24,4)]:
 b=bytearray(raw);struct.pack_into('<I',b,offset,value)
 if offset!=8:struct.pack_into('<I',b,8,pack.crc(b))
 bad.append((bytes(b),'boardrev=1',mac))
b=bytearray(raw);b[-1]=1;struct.pack_into('<I',b,8,pack.crc(b));bad.append((bytes(b),'boardrev=1',mac))
bad += [(raw,'a=1\na=2',mac),(raw,'a\n',mac),(raw,'a=\0',mac),(raw,'a=é',mac),(raw,'macaddr=00:00:00:00:00:01',mac),(raw,'a=1',bytes(6)),(raw,'a=1',bytes([1,0,0,0,0,1])),(b'X','a=1',mac)]
for args in bad:
 try:pack.pack(*args)
 except (ValueError,UnicodeError):count+=1
 else:raise AssertionError('Malformed packing input accepted')

print("PASS:",count,"synthetic packing/invalid-input cases; no firmware or device required.")
