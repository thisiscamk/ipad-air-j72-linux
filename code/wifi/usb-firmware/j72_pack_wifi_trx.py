#!/usr/bin/env python3
"""Build a private J72 USB TRX with the owner's NVRAM and MAC, offline.

Layout follows Project Cascadia scripts/trx-add-nvram.py at c20b85e.
Reject malformed input and non-padding trailers before constructing output.
No device access, reference MAC, firmware download or network settings.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import zlib

HEADER = 28
RAM = 0x90000


def crc(image):
    return zlib.crc32(image[12:]) ^ 0xffffffff


def nvram(text, mac):
    if len(mac) != 6 or mac[0] & 1 or mac == bytes(6) or mac == b'\xff' * 6:
        raise ValueError('A real unicast six-byte owner MAC is required')
    text.encode('ascii', errors='strict')
    if '\0' in text:
        raise ValueError('NVRAM input contains NUL')
    values = {}
    for raw in text.splitlines():
        line = raw.split('#', 1)[0].strip()
        if not line:
            continue
        if '=' not in line:
            raise ValueError('NVRAM line lacks a value')
        key, value = (part.strip() for part in line.split('=', 1))
        if not re.fullmatch(r'[A-Za-z0-9_.:/-]+', key) or key in values:
            raise ValueError('Invalid or duplicate NVRAM key')
        if any(ord(c) < 32 or ord(c) > 126 for c in value):
            raise ValueError('NVRAM value contains a control character')
        values[key] = value
    if not values:
        raise ValueError('Empty board NVRAM')
    address = ':'.join(f'{v:02x}' for v in mac)
    if 'macaddr' in values and values['macaddr'].lower() != address:
        raise ValueError('Board MAC differs from owner MAC')
    values['macaddr'] = address
    body = ('\0'.join(f'{key}={value}' for key, value in values.items()) + '\0\0').encode('ascii')
    body = body.ljust((len(body) + 3) & ~3, b'\0')
    words = len(body) // 4
    if words > 0xffff:
        raise ValueError('NVRAM exceeds token range')
    return body + struct.pack('<I', words | ((~words & 0xffff) << 16))


def pack(firmware, text, mac):
    if not HEADER <= len(firmware) <= RAM:
        raise ValueError('Firmware length outside ROM RAM bound')
    magic, length, checksum, flags, fwlen, jump, nvlen = struct.unpack_from('<7I', firmware)
    if magic != 0x30524448 or length != len(firmware) or flags != 0x10020:
        raise ValueError('Unexpected J72 TRX header')
    if crc(firmware) != checksum:
        raise ValueError('Original firmware CRC failed')
    if not fwlen or fwlen > length - HEADER or jump >= fwlen or nvlen:
        raise ValueError('Invalid firmware offsets or input already has NVRAM')
    if any(firmware[HEADER + fwlen:]):
        raise ValueError('Non-padding firmware trailer requires review')
    board = nvram(text, mac)
    image = bytearray(firmware[:HEADER + fwlen] + board)
    if len(image) > RAM:
        raise ValueError('Combined image exceeds observed ROM RAM')
    struct.pack_into('<I', image, 4, len(image))
    struct.pack_into('<I', image, 24, len(board))
    struct.pack_into('<I', image, 8, crc(image))
    assert crc(image) == struct.unpack_from('<I', image, 8)[0]
    return bytes(image)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--firmware', type=Path, required=True)
    p.add_argument('--nvram', type=Path, required=True)
    p.add_argument('--mac-file', type=Path, required=True, help='Private raw six-byte owner MAC file')
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise ValueError('Refusing to replace a pinned private image')
    image = pack(args.firmware.read_bytes(), args.nvram.read_text(encoding='ascii'), args.mac_file.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('xb') as f:
        f.write(image)
    args.output.chmod(0o600)
    receipt = {'bytes': len(image), 'sha256': hashlib.sha256(image).hexdigest(),
               'rom_chip': '0x4324', 'rom_revision': 6, 'radio_upload_performed': False}
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
