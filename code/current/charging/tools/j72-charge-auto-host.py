#!/usr/bin/python3
"""Automatically admit only the owner's J72 on the tested powered hub port.

Runs on the Pi, not the tablet. It issues source admissions, never charging
leases. The existing on-device supervisor remains independent of Pi uptime.
"""
import argparse
import ctypes
import fcntl
import hashlib
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import re
import shlex
import subprocess
import struct
import time


def hub_power(hub):
    """USB GET_STATUS, no reset, driver claim or configuration change."""
    bus = int((hub / 'busnum').read_text())
    dev = int((hub / 'devnum').read_text())
    fd = os.open('/dev/bus/usb/%03d/%03d' % (bus, dev), os.O_RDWR)
    try:
        results = []
        for kind, size in ((0x80, 2), (0xa0, 4)):
            buf = ctypes.create_string_buffer(size)
            request = struct.pack('@BBHHHIQ', kind, 0, 0, 0, size, 1000,
                                  ctypes.addressof(buf))
            fcntl.ioctl(fd, 0xc0185500, request)  # USBDEVFS_CONTROL, ARM64
            results.append(int.from_bytes(buf.raw[:2], 'little'))
        if not results[0] & 1 or results[1] & 3:
            raise ValueError('Hub local power lost or overcurrent')
    finally:
        os.close(fd)


def snapshot(config, root=Path('/sys/bus/usb/devices'), check_power=hub_power):
    p = root / config['port']
    if not p.exists():
        raise FileNotFoundError('Qualified device absent')
    read = lambda path: path.read_text().strip()
    hub = p.resolve().parent
    if hub.name != config['hub_port']:
        raise ValueError('Changed hub route')
    for name, expected in config['hub'].items():
        if read(hub / name) != expected:
            raise ValueError('Changed hub descriptor: ' + name)
    if not int(read(hub / 'bmAttributes'), 16) & 0x40:
        raise ValueError('Hub not self-powered')
    check_power(hub)
    for name, expected in config['device'].items():
        if read(p / name) != expected:
            raise ValueError('Wrong USB device: ' + name)
    serial = read(p / 'serial')
    match = re.fullmatch(r'ECID:' + re.escape(config['ecid']) +
                         r' BOOT:([0-9a-f-]{36}) BOARD:j72', serial)
    if not match or read(p / 'bConfigurationValue') == '0' or read(p / 'speed') != '480':
        raise ValueError('Wrong owner, board, boot serial or USB configuration')
    # Device number changes even when a quick reconnect is missed by polling.
    return (match[1], read(p / 'busnum'), read(p / 'devnum'))


def request_for(current, previous, lost, core):
    return {'action': 'admit', 'boot_id': current[0], 'core_sha256': core,
            'new_boot': not previous or previous[0] != current[0],
            'source_qualification_id': hashlib.sha256(repr(current).encode()).hexdigest(),
            'observed_previous_connection_loss': bool(previous and previous[0] == current[0]
                                                       and (lost or previous != current))}


def invoke(config, request, wifi=False):
    # Credentials and pinned SSH host key are copied to root-private files;
    # never depend on an interactive agent, Wi-Fi address or unlocked desktop.
    password = Path(config['password_file']).read_text().rstrip('\n')
    command = 'sudo -S -p "" /usr/lib/orchard/j72_charge_auto.py'
    if config.get('target_profile'):
        command += ' --profile ' + shlex.quote(config['target_profile'])
    p = subprocess.run(config['wifi_ssh_argv' if wifi else 'ssh_argv'] + [command],
                       input=password + '\n' + json.dumps(request),
                       text=True, capture_output=True, timeout=35)
    if p.returncode == 255:
        raise ConnectionError('USB SSH is not ready')
    if p.returncode:
        raise RuntimeError('Tablet admission refused: ' + p.stderr[-500:])
    return json.loads(p.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    os.umask(0o077)
    config = json.loads(args.config.read_text())
    handler = RotatingFileHandler(config['log'], maxBytes=256*1024, backupCount=3)
    logger = logging.getLogger('j72-auto-charge')
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    state_file = Path(config.get('state_file', '/run/orchard-j72-charge-auto.json'))
    previous = tuple(json.loads(state_file.read_text())['previous']) if state_file.exists() else None
    lost = False
    attempted = None
    stable_since = None
    candidate = None
    last_error = None
    power_stop_attempted = None
    missing_since = None
    recovery_done = False
    last_recovery = 0
    while True:
        try:
            current = snapshot(config)
            missing_since = None
            recovery_done = False
            if candidate != current:
                candidate, stable_since = current, time.monotonic()
            if args.once or time.monotonic() - stable_since >= 5:
                if attempted != current:
                    # Recheck after SSH too; no identical retry on a refused
                    # generation. A later reconnect is a genuinely new event.
                    request = request_for(current, previous, lost, config['core_sha256'])
                    result = invoke(config, request)
                    if snapshot(config) != current:
                        raise RuntimeError('USB changed during admission')
                    logger.info(json.dumps({'event': 'admitted', 'result': result}))
                    print(json.dumps(result), flush=True)
                    previous, attempted, lost = current, current, False
                    temporary = state_file.with_suffix('.new')
                    temporary.write_text(json.dumps({'previous': current}))
                    temporary.replace(state_file)
                if args.once:
                    return
        except FileNotFoundError:
            lost = previous is not None
            candidate, stable_since = None, None
            if missing_since is None:
                missing_since = time.monotonic()
            if (previous and not recovery_done and 'wifi_ssh_argv' in config and
                    time.monotonic() - missing_since > 10 and time.monotonic() - last_recovery > 30):
                last_recovery = time.monotonic()
                try:
                    result = invoke(config, {'action': 'recover-usb', 'boot_id': previous[0]}, wifi=True)
                    recovery_done = result['state'] == 'usb-rebound'
                    logger.info(json.dumps({'event': 'usb-recovery', 'result': result}))
                except Exception as error:
                    logger.warning(json.dumps({'event': 'usb-recovery-unavailable', 'error': str(error)}))
        except ValueError as error:
            lost = previous is not None
            candidate, stable_since = None, None
            if previous and power_stop_attempted != previous:
                # A different hub/port, identity or adapter power is not the
                # original admission. Stop the old boot if it is reachable.
                power_stop_attempted = previous
                try:
                    result = invoke(config, {'action': 'stop', 'boot_id': previous[0]})
                    logger.warning(json.dumps({'event': 'source-invalid-stop', 'result': result}))
                except Exception as stopped_error:
                    logger.error(json.dumps({'event': 'source-invalid-stop-unreachable',
                                             'error': str(stopped_error)}))
        except ConnectionError as error:
            if args.once:
                raise
            # SSH may take longer than gadget enumeration on a fresh boot.
            # Readiness retry never clears a controller fault.
            stable_since = time.monotonic() + 25
            if str(error) != last_error:
                logger.info(str(error))
                last_error = str(error)
        except Exception as error:
            # A target policy refusal is not an invitation to reset it.
            message = str(error)
            if message != last_error:
                logger.error(json.dumps({'event': 'refused', 'error': message}))
                last_error = message
            if candidate:
                attempted = candidate
            if args.once:
                raise
        if args.once:
            raise RuntimeError('Qualified USB source absent')
        time.sleep(1)


if __name__ == '__main__':
    main()
