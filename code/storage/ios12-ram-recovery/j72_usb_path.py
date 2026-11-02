#!/usr/bin/env python3
"""Read-only topology checks for the Pi 4's direct USB boot path."""
from pathlib import Path

def require_direct_pi(target, model_file=Path('/proc/device-tree/model')):
    model = model_file.read_bytes().rstrip(b'\0\r\n')
    if not model.startswith(b'Raspberry Pi 4 Model B'):
        raise RuntimeError('Direct-Pi guard requires the verified Raspberry Pi 4 host')
    parent = target.resolve().parent
    def identity(path):
        return ((path/'idVendor').read_text().strip().lower(),
                (path/'idProduct').read_text().strip().lower())
    try:
        kind = identity(parent)
        # A Pi 4 USB2 device may sit under its onboard VIA hub. No path or
        # port number is assumed. An external hub below that is rejected.
        if kind == ('1d6b','0002'):
            return
        if kind == ('2109','3431') and identity(parent.parent) == ('1d6b','0002'):
            return
    except (FileNotFoundError, PermissionError) as exc:
        raise RuntimeError('Cannot verify the direct Pi USB topology') from exc
    raise RuntimeError('iPad is behind an external USB hub; move only its cable to a Pi USB port before booting')
