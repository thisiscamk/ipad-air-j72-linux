#!/usr/bin/env python3
"""After the morning tests finish, leave the exact iPad in iOS on its hub.

Does not alter the live experiment. Normal-iOS diagnostics may require unlock;
an unavailable reading is recorded as unverified, never as charging success.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import plistlib
import shlex
import signal
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'private/j72-platform/power-storage-20261102'
OUT = WORK / 'observation35-prep/after-tests-ios-charging-20261103'


def charging_state(document):
    if not isinstance(document, dict) or 'IORegistry' not in document:
        return 'UNVERIFIED'
    battery = document.get('IORegistry', {})
    if not isinstance(battery, dict):
        return 'UNVERIFIED'
    if battery.get('ExternalConnected') is not True or battery.get('ExternalChargeCapable') is not True:
        return 'EXTERNAL_CHARGING_NOT_CONFIRMED'
    if battery.get('IsCharging') is True:
        return 'IOS_REPORTS_CHARGING'
    capacity = battery.get('CurrentCapacity')
    if battery.get('FullyCharged') is True and type(capacity) is int and 99 <= capacity <= 100:
        return 'IOS_REPORTS_FULL_ON_EXTERNAL_POWER'
    return 'EXTERNAL_POWER_PRESENT_CHARGE_NOT_CONFIRMED'


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def running_test():
    watched = {'run-j72-morning35.py', 'run-j72-observation35.py', 'run-j72-charge-maintain35.py',
               'run-j72-voltage-resume35.py', 'run-j72-voltage-observation35.py',
               'run-j72-voltage-session35.py', 'run-j72-resync-observation35.py',
               'run-j72-state1-session35.py', 'run-j72-state1-observation35.py'}
    for p in Path('/proc').iterdir():
        if not p.name.isdecimal():
            continue
        try:
            args = (p / 'cmdline').read_bytes().split(b'\0')
            if any(Path(os.fsdecode(a)).name in watched for a in args if a):
                return True
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            pass
    return False


def port_presence(source):
    """An absent device is a boot/USB wait, never permission for Linux recovery."""
    assert Path('/proc/sys/kernel/random/boot_id').read_text().strip() == source['host_boot_id']
    parent = Path('/sys/bus/usb/devices') / source['hub_port']
    assert (parent / 'idVendor').read_text().strip() == '05e3'
    assert (parent / 'idProduct').read_text().strip() == '0610'
    assert (parent / 'bcdDevice').read_text().strip() == source['hub_bcdDevice']
    assert int((parent / 'bmAttributes').read_text().strip(), 16) & 0x40
    p = Path('/sys/bus/usb/devices') / source['source_port']
    try:
        identity = ((p / 'idVendor').read_text().strip(), (p / 'idProduct').read_text().strip())
    except FileNotFoundError:
        return 'absent'
    assert p.resolve().parent == parent.resolve()
    return {('05ac', '12ab'): 'ios', ('1d6b', '0104'): 'linux'}.get(identity, 'foreign')


def source_port(source, vendor, product):
    expected = {('05ac', '12ab'): 'ios', ('1d6b', '0104'): 'linux'}[(vendor, product)]
    assert port_presence(source) == expected
    p = Path('/sys/bus/usb/devices') / source['source_port']
    return p


def stop_charge_if_present(command, stop):
    """Same-boot absent module is distinct from a stale prior staging receipt."""
    present = command('if test -d /sys/module/j72_charge_maintain35; then echo Y; else echo N; fi').strip()
    if present not in (b'Y', b'N'):
        raise RuntimeError('Unknown charging owner state')
    if present == b'Y':
        stop()
        checks = ('test "$(cat /sys/block/nbd2/size)" = 0; '
                      '! busybox grep -Eq "^/dev/(nbd|sd|mmc|nvme|asp|dm|mapper)" /proc/mounts; '
                      'p=/sys/module/j72_charge_maintain35/parameters/status; '
                      'busybox grep -qx enabled=0 "$p"; busybox grep -qx active=0 "$p"; '
                      'busybox grep -qx armed=0 "$p"; busybox grep -qx restore_failed=0 "$p"; '
                      'busybox grep -qx reg_04c0=02 /sys/module/j72_wlan_ready_snapshot/parameters/snapshot; ')
    else:
        checks = ('test "$(cat /sys/block/nbd2/size)" = 0; '
                  '! busybox grep -Eq "^/dev/(nbd|sd|mmc|nvme|asp|dm|mapper)" /proc/mounts; '
                  'for p in /sys/module/j72_input_limit* /sys/module/j72_charge_maintain*; do test ! -d "$p"; done; '
                  'busybox grep -qx reg_04c0=02 /sys/module/j72_wlan_ready_snapshot/parameters/snapshot; ')
    command(checks + 'echo CHARGE_BASELINE_VERIFIED')
    return checks


def main():
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--preflight', action='store_true')
    group.add_argument('--run', action='store_true')
    parser.add_argument('--touch-state135', action='store_true',
                        help='Select the separate voltage-hold candidate and a fresh output')
    args = parser.parse_args()
    controller = 'run-j72-charge-maintain35.py'
    if args.touch_state135:
        controller = 'run-j72-voltage-resume35.py'
        OUT = WORK / 'voltage-resume35' / ('state1-ios-charging-' + time.strftime('%Y%m%d-%H%M%S'))
        subprocess.run([os.sys.executable, str(ROOT / 'tools' / controller), 'preflight'], check=True)
    os.umask(0o077)
    os.chdir(ROOT)
    host = load('charging_return_host', 'j72-desktop-storage35-host.py')
    host.preflight(verify_desktop=False)
    source = json.loads((WORK / 'qualified-hub-source35.json').read_text())
    session = json.loads((ROOT / 'private/j72-platform/power-wifi-20261101/network-userspace/live-wifi-session.json').read_text())
    assert session['uts_version'] == host.VERSION
    if args.preflight:
        assert charging_state(plistlib.loads((WORK / 'AppleARMPMUCharger.plist').read_bytes())) == 'IOS_REPORTS_CHARGING'
        print('PASS: exact inputs and archived iOS diagnostic classification; no device contact')
        return
    assert os.geteuid() == 0
    OUT.mkdir()
    result = dict(status='WAITING_FOR_TESTS', experiment_interrupted=False,
                  charging_confirmed=False, internal_writes=False)
    try:
        # Initial entry may wait 90 minutes before the 90-minute observation.
        # Include idle/setup and cleanup without interrupting either owner.
        deadline = time.monotonic() + 12000
        while running_test():
            if time.monotonic() >= deadline:
                raise TimeoutError('Tests still running; did not interrupt them or request reboot')
            time.sleep(2)

        # Normal success has already returned to iOS. On failure, try the
        # existing cleanup before the independently guarded RAM recovery reboot.
        deadline = time.monotonic() + 120
        mode = port_presence(source)
        while mode == 'absent' and time.monotonic() < deadline:
            time.sleep(2)
            mode = port_presence(source)
        if mode == 'absent':
            result['status'] = 'IOS_RETURN_REQUESTED_USB_ABSENT_CHARGING_UNVERIFIED'
            return
        if mode == 'foreign':
            raise RuntimeError('Unexpected device on the qualified port; no recovery command sent')
        ios_present = mode == 'ios'
        if not ios_present:
            source_port(source, '1d6b', '0104')
            lock = load('charging_return_lock', 'run-j72-input-limit-hub1050-desktop.py')
            raw = lock.locked_ram(host.ram())
            guard = ('test "$(uname -v)" = ' + shlex.quote(host.VERSION) + '; '
                     'test "$(cat /proc/sys/kernel/random/boot_id)" = ' + shlex.quote(session['boot_id']) + '; '
                     'test "$(cat /proc/device-tree/model)" = "Apple iPad Air (Cellular)"; ')

            def command(body, timeout=8):
                return raw('busybox sh -ec ' + shlex.quote(guard + body), timeout=timeout)

            (OUT / 'before-recovery.txt').write_bytes(command('cat /proc/mounts; cat /proc/modules; /sbin/j72-touch-session status; dmesg | busybox tail -n 180'))
            checks = stop_charge_if_present(command, lambda: subprocess.run([os.sys.executable, str(ROOT / 'tools' / controller), 'stop'], check=True))
            normal = subprocess.run([os.sys.executable, str(ROOT / 'tools/run-j72-wifi-v3.py'), '--storage35', '--stop'], capture_output=True)
            (OUT / 'normal-cleanup.txt').write_bytes(normal.stdout + normal.stderr)
            result['normal_cleanup_returncode'] = normal.returncode
            # Do not reset a failed worker, force unload, or relabel failed
            # cleanup as passing. Let the existing stopped-ring collector save
            # evidence before a normal recovery reboot if its guard permits it.
            deadline = time.monotonic() + (0 if args.touch_state135 else 35)
            receipt = WORK / 'observation35-prep/morning-final-touch-20261103/result.json'
            while not receipt.exists() and time.monotonic() < deadline:
                time.sleep(1)
            (OUT / 'recovery-gates.txt').write_bytes(command(checks + 'echo RAM_ROOT_NO_BLOCK_MOUNTS_CHARGER_RESTORED'))
            command(checks + 'busybox setsid busybox sh -c "sleep 2; sync; busybox reboot -f" </dev/null >/run/j72-charging-return.log 2>&1 &')
            result['recovery_reboot_requested'] = True

        deadline = time.monotonic() + 120
        while True:
            try:
                source_port(source, '05ac', '12ab')
                break
            except (AssertionError, FileNotFoundError):
                if time.monotonic() >= deadline:
                    raise TimeoutError('Normal iOS USB did not return; charging not verified')
                time.sleep(2)
        deadline = time.monotonic() + 120
        while True:
            try:
                model = subprocess.check_output(['ideviceinfo', '-k', 'ProductType'], stderr=subprocess.PIPE, timeout=10).strip()
                version = subprocess.check_output(['ideviceinfo', '-k', 'ProductVersion'], stderr=subprocess.PIPE, timeout=10).strip()
                assert model == b'iPad4,2' and version == b'12.5.7'
                break
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                if time.monotonic() >= deadline:
                    raise TimeoutError('iOS USB returned but identity service is unavailable')
                time.sleep(5)
        result.update(ios_identity_verified=True, qualified_powered_hub_port_verified=True)
        confirmed = 0
        for attempt in range(6):
            sample = subprocess.run(['idevicediagnostics', 'ioregentry', 'AppleARMPMUCharger'], capture_output=True, timeout=20)
            (OUT / ('ios-battery-' + str(attempt) + '.plist')).write_bytes(sample.stdout)
            try:
                document = plistlib.loads(sample.stdout)
                classification = charging_state(document)
                battery = document.get('IORegistry', {})
                summary = {k: battery[k] for k in ('IsCharging', 'FullyCharged', 'ExternalConnected', 'ExternalChargeCapable', 'CurrentCapacity') if k in battery}
            except (ValueError, plistlib.InvalidFileException, TypeError):
                classification, summary = 'DIAGNOSTICS_UNAVAILABLE', {}
            good = classification in ('IOS_REPORTS_CHARGING', 'IOS_REPORTS_FULL_ON_EXTERNAL_POWER')
            confirmed = confirmed + 1 if good else 0
            result.update(last_classification=classification, last_battery=summary)
            (OUT / ('sample-' + str(attempt) + '.json')).write_text(json.dumps(dict(classification=classification, battery=summary), indent=2) + '\n')
            if confirmed >= 2:
                result.update(status='IOS_CHARGING_VERIFIED_ON_HUB', charging_confirmed=True)
                break
            time.sleep(30)
        else:
            result['status'] = 'IOS_ON_POWERED_HUB_CHARGING_UNVERIFIED'
        # Leave stock iOS connected. No new jailbreak, test, boot or USB reset.
    except BaseException as exc:
        # sudo can forward a second interrupt while we are recording the first.
        signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT, signal.SIGTERM})
        result.update(status='RETURN_OR_VERIFICATION_FAILED', reason=type(exc).__name__ + ': ' + str(exc))
        raise
    finally:
        (OUT / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        print('After-test iOS charging:', result['status'], OUT, flush=True)


if __name__ == '__main__':
    main()
