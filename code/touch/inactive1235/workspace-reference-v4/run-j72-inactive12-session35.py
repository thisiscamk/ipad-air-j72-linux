#!/usr/bin/env python3
"""Prepared voltage-hold comparison after a fresh #35 RAM boot; no storage writes.

Preflight is host-only. --run needs this boot's read-only ASP receipt, prepared
Wi-Fi/RAM desktop and qualified hub. Keep the successful touch worker unchanged.
Wait for original initial-entry criteria, compare at fixed brightness 802 for
90 minutes, independently restore, normally clean up and request iOS.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

from j72_observation_health import Health, fields, integer, restored, scoped_shell
from j72_wifi_ssh import command
from j72_inactive12_failure_capture import capture as capture_input_failure

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'private/j72-platform/power-storage-20261102'
MEASUREMENT_BRIGHTNESS = r'''
test "$(cat /sys/devices/system/cpu/cpufreq/policy0/scaling_governor)" = schedutil
for p in /sys/module/j72_input_limit* /sys/module/j72_charge_maintain*; do test ! -d "$p"; done
selected=
for b in /sys/class/backlight/*; do
 test -r "$b/device/of_node/compatible" || continue
 if busybox tr '\000' '\n' < "$b/device/of_node/compatible" | busybox grep -qx apple,anya-pmic-bl; then
  test -z "$selected"; selected=$b
 fi
done
test -n "$selected"; test "$(cat "$selected/max_brightness")" = 2047
echo 802 > "$selected/brightness"
test "$(cat "$selected/actual_brightness")" = 802
'''


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(*args):
    print('STEP:', *args, flush=True)
    subprocess.run([sys.executable, str(ROOT / 'tools' / args[0]), *args[1:]], check=True)


def check_receipt(checked, reads, session, version):
    assert checked.get('boot_id') == session['boot_id']
    assert checked.get('uts_version') == session.get('uts_version') == version
    for key, value in {'probe_pass': True, 'device_read_only': True,
                       'internal_writes': False, 'mounted_internal_filesystem': False,
                       'logical_block_bytes': 4096, 'device_bytes': 128000000000}.items():
        assert type(checked.get(key)) is type(value) and checked[key] == value, key
    assert reads.get('bytes_each') == 4096 and reads.get('internal_writes') is False
    pairs = reads.get('repeated_hash_pairs', {})
    assert set(pairs) == {'0', '1', '31249999'}
    for pair in pairs.values():
        assert type(pair) is list and len(pair) == 2 and pair[0] == pair[1]
        assert type(pair[0]) is str and len(pair[0]) == 64
        assert all(c in '0123456789abcdef' for c in pair[0])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--preflight', action='store_true')
    group.add_argument('--run', action='store_true')
    parser.add_argument('--readcheck', type=Path, help="Fresh same-boot native readcheck directory")
    parser.add_argument('--touch-inactive1235', action='store_true', required=True,
                        help='Require the separately built state-1/2 inactive touch candidate')
    args = parser.parse_args()
    prepared = json.loads((WORK / 'voltage-resume35/session-preparation-inactive12-v4.json').read_text())
    assert prepared['status'] == 'HOST_SOURCE_TESTS_PREFLIGHT_PASS_DEVICE_UNTESTED'
    for name, digest in prepared['files'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    observer_file = 'run-j72-inactive12-observation35.py' if args.touch_inactive1235 else 'run-j72-voltage-observation35.py'
    run(observer_file, '--preflight')
    if args.preflight:
        print('PASS: voltage comparison session inputs; no device contact')
        return
    assert args.readcheck, 'Fresh same-boot readcheck directory required'
    assert os.geteuid() == 0
    os.umask(0o077)
    os.chdir(ROOT)
    observer = load('morning_observer', observer_file)
    lock = load('morning_lock', 'run-j72-input-limit-hub1050-desktop.py')
    host = load('morning_host', 'j72-desktop-storage35-host.py')
    source = json.loads((WORK / 'qualified-hub-source35.json').read_text())
    session = json.loads((ROOT / 'private/j72-platform/power-wifi-20261101/network-userspace/live-wifi-session.json').read_text())
    assert session['uts_version'] == host.VERSION
    receipt = args.readcheck.resolve()
    assert receipt.parent == (WORK / 'desktop-storage35').resolve() and receipt.name.startswith('readcheck-')
    checked = json.loads((receipt / 'result.json').read_text())
    check_receipt(checked, json.loads((receipt / 'reads.json').read_text()), session, host.VERSION)
    lock.verify_hub(source)
    assert command(scoped_shell('test -d /sys/module/asp; test "$(cat /sys/block/asp0n1/ro)" = 1; test ! -d /sys/module/j72_charge_maintain35; echo READY'), timeout=10).strip() == b'READY'
    out = WORK / 'voltage-resume35' / ('inactive12-session-' + time.strftime('%Y%m%d-%H%M%S'))
    out.mkdir()
    result = dict(status='RUNNING', internal_writes=False, restart_policy_changed=True,
                  touch_resync_changed=True, touch_state1_changed=args.touch_inactive1235, charging_entry_wait_limit_s=5400,
                  charging_observation_limit_s=5400, readcheck=str(receipt.relative_to(ROOT)))
    try:
        # The recorder is read-only; set the agreed measurement brightness
        # explicitly here, before its settle interval and first sample.
        command(scoped_shell(MEASUREMENT_BRIGHTNESS), timeout=10)
        time.sleep(30)  # settle after the six bounded native reads
        run('record-j72-idle35.py', '--seconds', '300', '--asp', 'present', '--brightness', '802')
        run('run-j72-voltage-resume35.py', 'stage')  # disabled; no current override
        health = Health(802)
        began = time.monotonic()
        eligible = False
        with (out / 'entry-wait.jsonl').open('w') as stream:
            while time.monotonic() - began < 5400:
                lock.verify_hub(source)
                row = fields(command(scoped_shell(observer.COLLECT), timeout=12))
                observer.policy_health(row)
                health.check(row)
                assert row['charge_enabled'] == '0' and row['charge_active'] == '0'
                assert 10 <= integer(row, 'battery_CAPACITY') <= 100
                assert 200 <= integer(row, 'battery_TEMP') <= 380
                stream.write(json.dumps(dict(elapsed_s=round(time.monotonic()-began, 3), health=row)) + '\n')
                stream.flush()
                eligible = (integer(row, 'battery_CAPACITY') <= 90 and
                            3500000 <= integer(row, 'battery_VOLTAGE_NOW') <= 4100000 and
                            integer(row, 'battery_TEMP') <= 365)
                if eligible:
                    health.check(row, initial=True)
                    break
                if int(time.monotonic()-began) % 60 < 11:
                    print('WAIT: unchanged entry criteria; SOC', row['battery_CAPACITY'],
                          'temperature', row['battery_TEMP'], flush=True)
                time.sleep(10)
        result['entry_eligible'] = eligible
        if eligible:
            run(observer_file, '--observe', '--seconds', '5400', '--brightness', '802')
            result['observation'] = 'COMPLETE_ANALYSIS_PENDING'
        else:
            result['observation'] = 'DEFERRED_ENTRY_THRESHOLDS_NOT_REACHED'
        run('run-j72-voltage-resume35.py', 'stop')
        final = fields(command(scoped_shell(observer.FINAL), timeout=12))
        restored(final)
        (out / 'independent-final.json').write_text(json.dumps(final, indent=2) + '\n')
        # End the fixed-brightness measurement before normal desktop cleanup.
        command(scoped_shell('''selected=
for b in /sys/class/backlight/*; do
 test -r "$b/device/of_node/compatible" || continue
 if busybox tr '\\000' '\\n' < "$b/device/of_node/compatible" | busybox grep -qx apple,anya-pmic-bl; then test -z "$selected"; selected=$b; fi
done
test -n "$selected"; echo 1604 > "$selected/brightness"
test "$(cat "$selected/actual_brightness")" = 1604
'''), timeout=10)
        run('run-j72-wifi-v3.py', '--storage35', '--stop')
        c = lock.locked_ram(host.ram())
        body = ('test "$(uname -v)" = ' + shlex.quote(host.VERSION) + '; '
                'test "$(cat /proc/sys/kernel/random/boot_id)" = ' + shlex.quote(session['boot_id']) + '; '
                'test "$(cat /sys/block/nbd2/size)" = 0; '
                '! busybox grep -Eq "^/dev/(nbd|sd|mmc|nvme|asp|dm|mapper)" /proc/mounts; '
                'test "$(cat /sys/module/j72_touch_session/parameters/session_state)" = 0; '
                'test "$(cat /sys/module/j72_touch_session/parameters/cleanup_ok)" = Y; '
                'test "$(cat /sys/module/j72_touch_session/parameters/firmware_healthy)" = 1; '
                'busybox setsid busybox sh -c "sleep 2; sync; busybox reboot -f" </dev/null >/run/j72-voltage-comparison-reboot.log 2>&1 &')
        # The entire sequence stays behind the shell's errexit guards.
        c(scoped_shell(body), timeout=8)
        result['reboot_requested'] = True
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            for p in Path('/sys/bus/usb/devices').iterdir():
                try:
                    if (p/'idVendor').read_text().strip() == '05ac' and (p/'idProduct').read_text().strip() == '12ab':
                        result['ios_usb_seen'] = True
                except FileNotFoundError:
                    pass
            if result.get('ios_usb_seen'):
                break
            time.sleep(2)
        result['status'] = 'CLEANUP_PASS_IOS_REQUESTED'
    except BaseException as exc:
        result.update(status='ABORTED_PROGRESSION_STOPPED', reason=type(exc).__name__ + ': ' + str(exc))
        # Original observer owns charging-watch cleanup. Never restart workers,
        # reset faults or bypass the normal radio/touch cleanup after failure.
        try:
            (out / 'failure-health.txt').write_bytes(command(scoped_shell(observer.COLLECT), timeout=12))
            (out / 'failure-kernel.txt').write_bytes(command('dmesg | busybox tail -n 180', timeout=10))
        except Exception as diagnostic:
            result['diagnostic_error'] = str(diagnostic)
        # Preserve the stopped ring BEFORE returning control to the iOS-return
        # helper. A separate post-cleanup collector can otherwise lose the race
        # with provider shutdown and reboot, as in the first precharge abort.
        try:
            present = command(scoped_shell('if test -d /sys/module/j72_charge_maintain35; then echo Y; else echo N; fi'), timeout=6).strip()
            if present == b'Y':
                run('run-j72-voltage-resume35.py', 'stop')
            elif present != b'N':
                raise RuntimeError('Unknown charging owner state')
            captured = capture_input_failure(command, out / 'stopped-input')
            result['failure_capture_status'] = captured['status']
        except Exception as diagnostic:
            result['failure_capture_error'] = type(diagnostic).__name__ + ': ' + str(diagnostic)
        raise
    finally:
        (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        print('SESSION RESULT:', result['status'], out, flush=True)


if __name__ == '__main__':
    main()
