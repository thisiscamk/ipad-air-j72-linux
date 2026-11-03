#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Pure health checks for a fixed-workload, bounded #35 observation."""
from dataclasses import dataclass
import shlex


def scoped_shell(body):
    # Keep the whole multi-command body behind the pinned transport's identity
    # AND-list. A failed boot guard must not fall through to later body lines.
    return 'busybox sh -ec ' + shlex.quote(body)


class StopObservation(RuntimeError):
    pass


def fields(raw):
    result = {}
    for line in raw.decode('ascii').splitlines():
        if '=' not in line: raise StopObservation('Malformed status line')
        key, value = line.split('=', 1)
        if not key or key in result: raise StopObservation('Duplicate or empty status key')
        result[key] = value
    return result


def integer(row, key):
    value = row.get(key, '')
    if not value or not value.isascii() or not value.isdecimal():
        raise StopObservation('Missing or invalid ' + key)
    return int(value)


@dataclass
class Health:
    brightness: int
    previous: dict | None = None
    stalled: int = 0

    def check(self, row, *, initial=False):
        required = dict(touch_session_state='2', touch_enabled='Y',
                        touch_continuous='Y', touch_capture_seconds='3',
                        touch_recovery_stop_reason='0', touch_xfer_errors='0',
                        touch_input_bad_layouts='0', wifi_state='COMPLETED',
                        desktop_ready='1', nbd_blocks='0', native_mounts='0',
                        charge_ready='1', charge_fault='0', charge_restore_failed='0',
                        governor='schedutil', brightness=str(self.brightness))
        for key, expected in required.items():
            if row.get(key) != expected: raise StopObservation('Health changed: ' + key)
        frames = integer(row, 'touch_input_frames')
        if frames < 10: raise StopObservation('Insufficient initial native frames')
        for key in ('touch_session_number', 'touch_input_recoveries', 'touch_wire_anomalies',
                    'touch_input_timeouts'):
            integer(row, key)
        if initial:
            # Advisory entry criteria only; the unchanged kernel controller
            # still obtains its own fresh vector before any current override.
            if (not 10 <= integer(row, 'battery_CAPACITY') <= 90 or
                not 200 <= integer(row, 'battery_TEMP') <= 365 or
                not 3_500_000 <= integer(row, 'battery_VOLTAGE_NOW') <= 4_100_000):
                raise StopObservation('Wait for the existing charging restart thresholds before measuring')
            if row.get('charge_enabled') != '0' or row.get('charge_active') != '0':
                raise StopObservation('Controller must start disabled')
        if self.previous:
            if row['touch_session_number'] != self.previous['touch_session_number']:
                raise StopObservation('Touch session restarted unexpectedly')
            for key in ('touch_input_frames', 'touch_input_recoveries', 'touch_wire_anomalies',
                        'touch_input_timeouts'):
                if integer(row, key) < integer(self.previous, key):
                    raise StopObservation('Touch counter regressed: ' + key)
            self.stalled = self.stalled + 1 if frames == integer(self.previous, 'touch_input_frames') else 0
            if self.stalled >= 3: raise StopObservation('Native frame counter stalled for three observations')
            if integer(row, 'touch_input_timeouts') > integer(self.previous, 'touch_input_timeouts'):
                raise StopObservation('New input timeout')
        self.previous = dict(row)


def restored(row):
    for key, expected in dict(enabled='0', active='0', armed='0', restore_failed='0', reg_04c0='02').items():
        if row.get(key) != expected: raise StopObservation('Final restoration unverified: ' + key)
    # An aborted observation can have a latched controller fault. A baseline
    # readback does not clear it or turn the aborted test into a pass.
    if integer(row, 'cycles') and row.get('restored') != '1':
        raise StopObservation('A used controller did not report restoration')
