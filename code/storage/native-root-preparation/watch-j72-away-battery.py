#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Preserve the current screen test, returning to iOS if battery gets low."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'private/j72-platform/power-storage-20261102/desktop-storage35'


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seconds', type=int, default=7200)
    p.add_argument('--cancel', action='store_true', help='Cancel the observer; keep the desktop attached')
    a = p.parse_args()
    os.umask(0o077)
    marker = WORK / 'away-watch.json'
    if a.cancel:
        state = json.loads(marker.read_text())
        Path(state['capture'], 'cancel').touch(exist_ok=False)
        print('Cancellation requested; desktop/export unchanged')
        return
    assert 60 <= a.seconds <= 7200
    if marker.exists():
        old = json.loads(marker.read_text())
        assert not Path('/proc', str(old['pid'])).exists(), 'Previous observer may still be running'
    wifi = load('wifi', 'j72_wifi_ssh.py')
    assert wifi.command('uname -v', timeout=6).decode().strip() == '#35 SMP PREEMPT Mon Nov 2 07:00:00 +08 2026'
    h = load('h35', 'j72-desktop-storage35-host.py')
    raw = load('lock', 'run-j72-input-limit-hub1050-desktop.py').locked_ram(h.ram())
    boot = raw('cat /proc/sys/kernel/random/boot_id', timeout=5).decode().strip()
    out = WORK / ('away-watch-' + time.strftime('%Y%m%d-%H%M%S'))
    out.mkdir()
    marker.write_text(json.dumps({'pid': os.getpid(), 'capture': str(out), 'boot_id': boot}, indent=2) + '\n')
    end = time.monotonic() + a.seconds
    reason = 'deadline'
    with (out / 'samples.jsonl').open('w') as f:
        while time.monotonic() < end:
            if (out / 'cancel').exists():
                reason = 'owner_return_cancelled'
                break
            try:
                data = wifi.command('cat /sys/class/power_supply/j72-bq27545-battery/capacity; cat /sys/class/power_supply/j72-bq27545-battery/temp', timeout=6)
                soc, temp = map(int, data.split())
                assert 0 <= soc <= 100 and 100 <= temp <= 500
            except Exception:
                # Preserve the mounted export if communication is uncertain.
                reason = 'health_read_failed_preserve_export'
                break
            f.write(json.dumps({'at_monotonic_s': time.monotonic(), 'soc': soc, 'temperature_tenthC': temp}) + '\n')
            f.flush()
            print('Away battery:', soc, 'percent, temperature', temp, flush=True)
            if soc <= 30 or temp >= 400:
                reason = 'low_battery' if soc <= 30 else 'temperature'
                break
            for _ in range(20):
                if (out / 'cancel').exists():
                    break
                time.sleep(1)
    if reason in ('owner_return_cancelled', 'health_read_failed_preserve_export'):
        (out / 'result.json').write_text(json.dumps({'reason': reason, 'desktop_and_export_preserved': True}) + '\n')
        print(reason, '; desktop/export preserved', flush=True)
        return
    # Refuse cleanup commands against any later boot.
    assert raw('cat /proc/sys/kernel/random/boot_id', timeout=5).decode().strip() == boot
    for name, command in [
        ('desktop-stop', ['run-j72-compressed-desktop.py', '--container35', '--stop']),
        ('radio-stop', ['run-j72-wifi-v3.py', '--storage35', '--stop']),
    ]:
        with (out / (name + '.log')).open('wb') as log:
            subprocess.run([sys.executable, str(ROOT / 'tools' / command[0]), *command[1:]],
                           stdout=log, stderr=subprocess.STDOUT, check=True, timeout=100)
    assert raw('cat /proc/sys/kernel/random/boot_id', timeout=5).decode().strip() == boot
    raw("busybox setsid busybox sh -c 'sleep 2; busybox reboot -f' </dev/null >/run/j72-away-reboot.log 2>&1 & echo REBOOT_REQUESTED", timeout=5)
    (out / 'result.json').write_text(json.dumps({'reason': reason, 'normal_desktop_and_provider_cleanup_pass': True,
                                              'ios_reboot_requested': True, 'internal_writes': False}) + '\n')
    print('Normal cleanup complete; iOS reboot requested:', reason, flush=True)


if __name__ == '__main__':
    main()
