#!/usr/bin/env python3
"""Compile the public DT overlay; contains no Apple firmware or calibration."""
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parent
dtbo = root / 'audio.dtbo'
subprocess.run(['dtc', '-@', '-I', 'dts', '-O', 'dtb', '-o', str(dtbo),
                str(root / 'audio.dts')], check=True)
# No exported labels are needed; retain local fixups for phandle relocation.
subprocess.run(['fdtput', '-r', str(dtbo), '/__symbols__'], check=True)
data = dtbo.read_bytes()
body = ','.join('0x%02x' % value for value in data)
(root / 'audio-blob.h').write_text(
    '/* Generated from public audio.dts; no firmware. */\n'
    'static const unsigned char j72_sio_fdt[] __aligned(8) = {' + body + '};\n')
print('Generated aligned overlay header; no hardware accessed')
