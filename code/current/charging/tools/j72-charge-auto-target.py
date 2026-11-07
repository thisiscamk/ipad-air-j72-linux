#!/usr/bin/python3
"""Root-only endpoint for the Pi's exact-port charging admission service.

This does not discover charger ratings. The caller has authenticated the
owner's USB gadget and qualified physical hub port immediately before calling.
The existing kernel controller and supervisor enforce the charging limits.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import importlib.util
import argparse

RELEASE = '7.3.0-rc1-j72-pw1-orchard-apple-4k'
SUPERVISOR_SHA = '48011e1d580a0ab5551b657b487902f8d5d732fac06d14a1ce2b3548dad5e7d0'
CORE_SHA = '7e429af5b10b0f0fa7569c046840e0e00f6e9bdd57e670037e3c1622a071d3fa'
MODULES = {
    'bq27xxx_battery_hdq_uart': (
        'a3e87cd3640c084c308543768e975090fafcf16eba1c7e79284cc6cf4db7cb2b',
        'adb4c35c650cdb58e4179c7f78e2d9663f05690d'),
    'j72_charge_maintain': (
        'ff7e8a695b9d9e9523d3b919d43e827b32a992004a71c84d05d237147486d2a5',
        'ac305c35e2b57462a2f605e76a32daceb17d72dd'),
}
PARAMS = Path('/sys/module/j72_charge_maintain/parameters')
UNIT = 'orchard-j72-charge.service'
ROOT_DEVICE = '/dev/asp0n1p3'
BOOT_DEVICE = '/dev/asp0n1p2'


def configure_profile(path):
    """Optional per-installation evidence; legacy live session stays unchanged."""
    global RELEASE, SUPERVISOR_SHA, CORE_SHA, MODULES, ROOT_DEVICE, BOOT_DEVICE
    from j72_charge_profile import read
    p, h = read(path, trusted=True)
    require(h['compatible'] == 'apple,j72', 'Only J72 is supported')
    RELEASE = h['kernel_release']
    SUPERVISOR_SHA = h['supervisor_sha256']
    CORE_SHA = p['qualification_sha256']
    MODULES = h['modules']
    ROOT_DEVICE = os.path.realpath(p['root_device'])
    BOOT_DEVICE = os.path.realpath(p['boot_device'])


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def reconnect_allowed(value, previous):
    """Only an observed USB loss can clear ENOTCONN, never lease/read faults."""
    return (previous and value['fault'] == '1' and
            value['controller_error'] == '-107' and value['error'] == '0' and
            value['restore_failed'] == '0' and value['restored'] == '1' and
            value['enabled'] == '0' and value['active'] == '0' and
            value['failed_guard_faults'] == '0' and
            value['last_read_failure_ms'] == '0')


def clean_disconnect_exit(value, previous, rows):
    """Supervisor may restore before the kernel observes a disconnect fault."""
    if not previous or len(rows) < 2:
        return False
    stopped, failure = rows[-2:]
    allowed = {"RuntimeError('External source lost or unknown')",
               "RuntimeError('USB source session lost')"}
    return (failure.get('event') == 'failure' and failure.get('error') in allowed and
            stopped.get('event') == 'stopped' and stopped.get('started') is True and
            stopped.get('status', {}).get('cycles') == value.get('cycles') and
            all(value.get(k) == '0' for k in ('fault', 'enabled', 'active', 'error',
                'controller_error', 'restore_failed', 'failed_guard_faults', 'last_read_failure_ms')) and
            value.get('restored') == '1')


def run(argv):
    p = subprocess.run(argv, capture_output=True, text=True, timeout=15)
    require(p.returncode == 0, 'Command failed: ' + argv[0] + ': ' + p.stderr[-300:])
    return p.stdout


def status():
    return dict(line.split('=', 1) for line in (PARAMS / 'status').read_text().splitlines())


def build_id(name):
    raw = (Path('/sys/module') / name / 'notes/.note.gnu.build-id').read_bytes()
    require(raw[:16].hex() == '040000001400000003000000474e5500', 'Bad build-id note')
    return raw[16:].hex()


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', type=Path)
    args = parser.parse_args()
    if args.profile:
        configure_profile(args.profile)
    request = json.loads(sys.stdin.read(16385))
    require(os.getuid() == 0 and os.uname().release == RELEASE, 'Wrong user/kernel')
    require(b'apple,j72\0' in Path('/proc/device-tree/compatible').read_bytes(), 'Wrong board')
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    require(request['boot_id'] == boot, 'USB and SSH boot identity differ')
    if request.get('action') == 'recover-usb':
        value = status()
        require(value['active'] == '0' and value['enabled'] == '0' and
                value['restore_failed'] == '0' and value['restored'] == '1',
                'USB recovery requires stopped and restored charging')
        require(run(['systemctl', 'show', UNIT, '-p', 'MainPID', '--value']).strip() == '0',
                'USB recovery requires supervisor stopped')
        if Path('/sys/class/power_supply/j72-external-power/online').read_text().strip() != '1':
            print(json.dumps({'state': 'waiting-for-cable', 'boot_id': boot}))
            return
        udcs = list(Path('/sys/kernel/config/usb_gadget').glob('*/UDC'))
        require(len(udcs) == 1 and udcs[0].read_text().strip() == '20c100000.usbdev',
                'Unexpected gadget binding')
        udcs[0].write_text('\n')
        time.sleep(1)
        udcs[0].write_text('20c100000.usbdev\n')
        time.sleep(3)
        print(json.dumps({'state': 'usb-rebound', 'boot_id': boot}))
        return
    if request.get('action') == 'stop':
        # Loss of the hub's own adapter must restore the baseline even if the
        # Pi still supplies enough USB power to keep the gadget configured.
        spec = importlib.util.spec_from_file_location('charge_supervisor',
                    '/usr/lib/orchard/j72_charge_supervisor.py')
        supervisor = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(supervisor)
        run(['systemctl', 'stop', UNIT])
        value = supervisor.Controller().stop()
        print(json.dumps({'state': 'stopped', 'boot_id': boot, 'restored': value['restored']}))
        return
    # This helper never runs in the RAM recovery root or on iOS.
    require(run(['findmnt', '-n', '-o', 'SOURCE', '/']).strip() == ROOT_DEVICE, 'Wrong root')
    require(run(['findmnt', '-n', '-o', 'SOURCE', '/boot']).strip() == BOOT_DEVICE, 'Wrong boot mount')
    script = Path('/usr/lib/orchard/j72_charge_supervisor.py')
    require(hashlib.sha256(script.read_bytes()).hexdigest() == SUPERVISOR_SHA, 'Supervisor changed')
    require(request['core_sha256'] == CORE_SHA, 'Wrong qualification record')
    base = Path('/lib/modules') / RELEASE / 'kernel/drivers/power/supply'
    for name, (sha, _) in MODULES.items():
        require(hashlib.sha256((base / (name + '.ko')).read_bytes()).hexdigest() == sha,
                'Installed driver changed: ' + name)
    if build_id('bq27xxx_battery_hdq_uart') != MODULES['bq27xxx_battery_hdq_uart'][1]:
        # The proven recovery image preloads the former gauge. Replace it only
        # before the FIRST charging session of a new boot, with no used grant
        # and no fault/cycle. Never unload a driver to escape a charging fault.
        require(request.get('new_boot'), 'Gauge replacement only before first admission')
        require(not Path('/run/orchard-j72-charge/source.json.used').exists(), 'Gauge already admitted')
        require(run(['systemctl', 'show', UNIT, '-p', 'MainPID', '--value']).strip() == '0',
                'Cannot replace gauge while supervisor exists')
        if PARAMS.exists():
            s = status()
            require(all(s[k] == '0' for k in ('enabled', 'active', 'fault', 'restore_failed', 'cycles')),
                    'Gauge replacement requires untouched controller')
            run(['rmmod', 'j72_charge_maintain'])
        run(['rmmod', 'bq27xxx_battery_hdq_uart'])
        run(['insmod', str(base / 'bq27xxx_battery_hdq_uart.ko')])
        time.sleep(4)  # Cache-only gauge needs its first fresh refresh.
        require(build_id('bq27xxx_battery_hdq_uart') == MODULES['bq27xxx_battery_hdq_uart'][1],
                'Corrected gauge did not load')
    run(['systemctl', 'start', 'orchard-j72-external-power.service'])
    if not PARAMS.exists():
        run(['insmod', str(base / 'j72_charge_maintain.ko')])
    require(build_id('j72_charge_maintain') == MODULES['j72_charge_maintain'][1], 'Running controller changed')
    spec = importlib.util.spec_from_file_location('charge_supervisor', script)
    supervisor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(supervisor)
    supervisor.Controller().source()
    value = status()
    service = dict(line.split('=', 1) for line in run([
        'systemctl', 'show', UNIT, '-p', 'MainPID', '-p', 'ActiveState', '-p', 'Result']).splitlines())
    if int(service['MainPID']) > 0:
        require(service['ActiveState'] == 'active', 'Existing supervisor not healthy')
        supervisor.check_status(value, True)
        print(json.dumps({'state': 'adopted', 'boot_id': boot, 'pid': int(service['MainPID'])}))
        return
    require(request.get('action') == 'admit', 'Observation cannot start charging')
    previous = request.get('observed_previous_connection_loss', False)
    rows = []
    if service['Result'] != 'success':
        # Rotated bounded evidence tail, never trust an arbitrary service exit.
        with Path('/var/log/orchard-j72-charge/session.jsonl').open('rb') as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 32768))
            lines = f.read().splitlines()[-2:]
        rows = [json.loads(line) for line in lines]
    require(service['Result'] == 'success' or reconnect_allowed(value, previous) or
            clean_disconnect_exit(value, previous, rows),
        'Failed supervisor requires inspection')
    require(value['restore_failed'] == '0' and value['active'] == '0' and
            value['enabled'] == '0', 'Controller not safely stopped')
    if value['fault'] == '1':
        require(reconnect_allowed(value, request.get('observed_previous_connection_loss', False)),
                'Fault requires inspection; not a proven USB disconnect')
        (PARAMS / 'source_lease').write_text(supervisor.LEASE)
        (PARAMS / 'requalify_source').write_text('requalify-verified-restoration\n')
    supervisor.check_status(status(), False)
    directory = Path('/run/orchard-j72-charge')
    directory.mkdir(mode=0o700, exist_ok=True)
    require(directory.stat().st_uid == 0 and directory.stat().st_mode & 0o077 == 0,
            'Grant directory not private')
    # Keep bounded grant history, preserving the original manual qualification.
    history = directory / 'automatic-history'
    history.mkdir(mode=0o700, exist_ok=True)
    for name in ('source.json', 'source.json.used'):
        old = directory / name
        if old.exists():
            old.rename(history / (str(time.time_ns()) + '-' + name))
    for old in sorted(history.iterdir())[:-16]:
        old.unlink()
    now = supervisor.boottime()
    grant = {'boot_id': boot, 'source_kind': supervisor.SOURCE_KIND,
             'module_sha256': supervisor.MODULE_SHA256,
             'source_qualification_id': request['source_qualification_id'],
             'issued_boottime': now, 'valid_until_boottime': now + 30,
             'max_session_s': 0, 'mode': 'continuous-maintenance',
             'qualification_report_sha256': CORE_SHA}
    with (directory / 'source.json').open('x') as f:
        json.dump(grant, f)
    (directory / 'session.env').write_text('J72_CHARGE_SECONDS=0\n')
    run(['systemctl', 'reset-failed', UNIT])
    run(['systemctl', 'start', UNIT])
    supervisor.check_status(status(), True)
    print(json.dumps({'state': 'started', 'boot_id': boot,
                     'pid': int(run(['systemctl', 'show', UNIT, '-p', 'MainPID', '--value']))}))


if __name__ == '__main__':
    main()
