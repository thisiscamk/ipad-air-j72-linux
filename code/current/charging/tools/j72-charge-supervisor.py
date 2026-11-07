#!/usr/bin/python3
"""On-device supervision of an explicitly qualified J72 source.

This does not detect charger ratings. A fresh, single-use authorization from
the physical-source admission step is required. Losing the source, the kernel
controller, or the supervisor latches the session off; no automatic retry.
The kernel retains all battery, temperature, deadline and restoration guards.
"""
import argparse
import fcntl
import hashlib
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import signal
import socket
import stat
import subprocess
import time

RELEASE = '7.3.0-rc1-j72-pw1-orchard-apple-4k'
MODULE_SHA256 = 'ff7e8a695b9d9e9523d3b919d43e827b32a992004a71c84d05d237147486d2a5'
SOURCE_KIND = 'owner-qualified-powered-JCH377-1500mA'
LEASE = 'qualified-JCH377-1500mA\n'
ARM = 'maintain-qualified-JCH377\n'
BEGIN = 'begin-qualified-maintenance\n'
PARAMS = Path('/sys/module/j72_charge_maintain/parameters')
ONLINE = Path('/sys/class/power_supply/j72-external-power/online')
UDC = Path('/sys/class/udc/20c100000.usbdev/state')


def boottime():
    return time.clock_gettime(time.CLOCK_BOOTTIME)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def fields(text):
    result = {}
    for line in text.splitlines():
        key, value = line.split('=', 1)
        require(key not in result, 'Duplicate controller field')
        result[key] = value
    return result


def notify(message):
    address = os.environ.get('NOTIFY_SOCKET')
    if not address:
        return
    if address.startswith('@'):
        address = '\0' + address[1:]
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sock:
        sock.connect(address)
        sock.sendall(message.encode())


def validate_grant(grant, boot, now, seconds):
    require(grant['boot_id'] == boot, 'Authorization belongs to another boot')
    require(grant['source_kind'] == SOURCE_KIND, 'Unqualified source kind')
    require(grant['module_sha256'] == MODULE_SHA256, 'Unqualified module')
    require(grant['source_qualification_id'], 'Missing source evidence')
    issued, expires = grant['issued_boottime'], grant['valid_until_boottime']
    require(0 <= issued <= now < expires <= issued + 60, 'Stale authorization')
    if seconds == 0:
        require(grant['max_session_s'] == 0 and
                grant.get('mode') == 'continuous-maintenance', 'Continuous maintenance is not authorized')
    else:
        require(1 <= seconds <= grant['max_session_s'] <= 43200, 'Session exceeds authorization')


def check_status(value, started):
    require(value['ready'] == '1', 'Controller unavailable')
    require(value['fault'] == '0', 'Kernel fault latched')
    require(value['restore_failed'] == '0', 'Restoration failure')
    require(value['error'] == '0' and value['controller_error'] == '0', 'Controller error')
    if started:
        require(value['enabled'] == '1', 'Kernel stopped the session')
    else:
        require(value['enabled'] == '0' and value['active'] == '0', 'Controller already in use')
        require(value['armed'] == '0', 'Controller already armed')
    if value['active'] == '1':
        require(value['mode'] == '1', 'Unexpected active mode')
    if int(value['cycles']) and value['active'] == '0':
        require(value['restored'] == '1', 'Inactive cycle has not restored')


class SleepInhibitor:
    """Keep kernel supervision awake; releasing charging also releases this FD."""
    WHO = 'J72-qualified-charging'

    def __init__(self):
        self.process = None
        self.reference = None
        self.logind_identity = None

    @staticmethod
    def process_start(pid):
        # Linux /proc stat field 22, with comm (which can contain spaces) removed.
        return (Path('/proc') / str(pid) / 'stat').read_text().rsplit(')', 1)[1].split()[19]

    def listed(self):
        result = subprocess.run(['systemd-inhibit', '--list', '--json=short'],
                                capture_output=True, text=True, timeout=3)
        require(result.returncode == 0, 'Cannot verify sleep inhibitor')
        return any(row['who'] == self.WHO and row['what'] == 'sleep' and
                   row['mode'] == 'block' and row['pid'] == self.process.pid
                   for row in json.loads(result.stdout))

    def start(self):
        self.process = subprocess.Popen(
            ['systemd-inhibit', '--what=sleep', '--mode=block', '--who=' + self.WHO,
             '--why=J72 charging requires awake kernel supervision', 'sleep', 'infinity'],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True)
        until = boottime() + 3
        try:
            while True:
                require(self.process.poll() is None, 'Sleep inhibitor exited')
                if self.listed():
                    pid = int(subprocess.check_output(
                        ['systemctl', 'show', 'systemd-logind.service', '-p', 'MainPID', '--value'],
                        text=True, timeout=3).strip())
                    require(pid > 0, 'No login manager')
                    self.logind_identity = (pid, self.process_start(pid))
                    refs = []
                    for fd in (Path('/proc') / str(self.process.pid) / 'fd').iterdir():
                        try:
                            target = Path(os.readlink(fd))
                            info = fd.stat()
                        except OSError:
                            continue
                        if target.parent == Path('/run/systemd/inhibit') and stat.S_ISFIFO(info.st_mode):
                            refs.append((fd, target, (info.st_dev, info.st_ino)))
                    require(len(refs) == 1, 'Cannot identify the acquired inhibitor FD')
                    self.reference = refs[0]
                    self.check()
                    return self
                require(boottime() < until, 'Sleep inhibitor did not become ready')
                time.sleep(.05)
        except BaseException:
            self.close()
            raise

    def check(self):
        require(self.process.poll() is None, 'Sleep inhibitor exited')
        require(self.reference is not None and self.logind_identity is not None, 'Inhibitor not acquired')
        pid, start = self.logind_identity
        require(self.process_start(pid) == start, 'Login manager restarted; session admission ended')
        fd, target, identity = self.reference
        # Observe the lifetime of our own acquired FD. No parsing systemd's
        # private metadata, and no D-Bus round trip in the lease-renewal loop.
        for endpoint in (fd, target):
            info = endpoint.stat()
            require(stat.S_ISFIFO(info.st_mode) and (info.st_dev, info.st_ino) == identity,
                    'Sleep inhibitor reference was lost')

    def close(self):
        if self.process is None:
            return
        try:
            os.killpg(self.process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            os.killpg(self.process.pid, signal.SIGKILL)
            self.process.wait(timeout=1)


class Controller:
    def __init__(self, sleep_inhibitor=None):
        self.sleep_inhibitor = sleep_inhibitor

    def source(self):
        require(ONLINE.read_text().strip() == '1', 'External source lost or unknown')
        require(UDC.read_text().strip() == 'configured', 'USB source session lost')
        if self.sleep_inhibitor is not None:
            self.sleep_inhibitor.check()

    def status(self):
        return fields((PARAMS / 'status').read_text())

    def write(self, name, value):
        (PARAMS / name).write_text(value)

    def stop(self):
        self.write('arm_hub', 'stop\n')
        value = self.status()
        require(value['enabled'] == '0' and value['active'] == '0', 'Stop did not disable')
        require(value['restore_failed'] == '0', 'Stop restoration failed')
        if int(value['cycles']):
            require(value['restored'] == '1', 'Stop did not restore baseline')
        return value


def run_session(controller, seconds, log, stop_requested, clock=boottime,
                sleep=time.sleep, send_notify=notify):
    """No restart/requalification path. Exceptions always attempt safe stop."""
    started = False
    last_tick = clock()
    deadline = last_tick + seconds if seconds else float('inf')
    last_sample = None
    last_record = 0
    summary = {'samples': 0, 'positive_samples': 0, 'first_soc': None,
               'last_soc': None, 'max_temp_tenthC': None, 'cycles': 0}
    try:
        controller.source()
        check_status(controller.status(), False)
        controller.write('source_lease', LEASE)
        controller.write('arm_hub', ARM)
        controller.write('begin_session', BEGIN)
        # request_work is asynchronous; give it a short bounded start interval.
        start_until = clock() + 1
        while True:
            controller.source()
            status_read_started = clock()
            value = controller.status()
            status_read_finished = clock()
            if value['enabled'] == '1':
                break
            require(value['fault'] == '0' and clock() < start_until,
                    'Kernel did not start the authorized session')
            sleep(.02)
        started = True
        last_tick = clock()
        send_notify('READY=1\nWATCHDOG=1\nSTATUS=Guarded qualified-source session')
        log({'event': 'started', 'uptime': last_tick, 'status': value,
             'status_read_started': status_read_started, 'status_read_finished': status_read_finished})
        while not stop_requested():
            now = clock()
            if now >= deadline:
                break
            require(0 <= now - last_tick < 1.5, 'Supervisor scheduling gap; do not renew')
            controller.source()
            status_read_started = clock()
            value = controller.status()
            status_read_finished = clock()
            check_status(value, True)
            # Check before every renewal; unknown source is never a grant.
            require(0 <= clock() - last_tick < 1.5, 'Slow source/status read; do not renew')
            controller.write('source_lease', LEASE)
            last_tick = clock()
            send_notify('WATCHDOG=1')
            sample = value['guard_at_ms']
            if sample != last_sample:
                last_sample = sample
                summary['samples'] += 1
                soc = int(value['guard_soc'])
                temp = int(value['guard_temp_tenthC'])
                if summary['first_soc'] is None:
                    summary['first_soc'] = soc
                summary['last_soc'] = soc
                summary['max_temp_tenthC'] = max(temp, summary['max_temp_tenthC'] or temp)
                summary['cycles'] = int(value['cycles'])
                if value['active'] == '1' and int(value['guard_current_uA']) > 0:
                    summary['positive_samples'] += 1
            if now - last_record >= 2:
                log({'event': 'sample', 'uptime': status_read_finished, 'status': value,
                     'status_read_started': status_read_started, 'status_read_finished': status_read_finished,
                     'summary': dict(summary)})
                last_record = now
            sleep(.25)
        return summary
    finally:
        # Also stop after an arm/start error, not just after a successful start.
        value = controller.stop()
        log({'event': 'stopped', 'uptime': clock(), 'started': started,
             'status': value, 'summary': dict(summary)})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--grant', type=Path)
    parser.add_argument('--seconds', type=int)
    parser.add_argument('--log', type=Path)
    parser.add_argument('--stop', action='store_true')
    args = parser.parse_args()
    require(os.getuid() == 0, 'Root required')
    require(os.uname().release == RELEASE, 'Wrong kernel')
    require(b'apple,j72\0' in Path('/proc/device-tree/compatible').read_bytes(), 'Wrong board')
    if args.stop:
        require(args.grant is None and args.seconds is None and args.log is None, 'Stop takes no authorization')
        print(json.dumps({'status': 'STOPPED_AND_RESTORED', 'controller': Controller().stop()}))
        return
    require(args.grant is not None and args.seconds is not None and args.log is not None,
            'Grant, explicit seconds (0 for authorized continuous maintenance) and log are required')
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    require(args.grant.parent.stat().st_uid == 0 and
            args.grant.parent.stat().st_mode & 0o077 == 0, 'Grant directory is not private')
    fd = os.open(args.grant, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd) as stream:
        info = os.fstat(stream.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_uid == 0 and
                info.st_mode & 0o077 == 0 and info.st_size <= 16384,
                'Invalid authorization file')
        grant = json.load(stream)
    validate_grant(grant, boot, boottime(), args.seconds)
    module = Path('/lib/modules') / RELEASE / 'kernel/drivers/power/supply/j72_charge_maintain.ko'
    require(hashlib.sha256(module.read_bytes()).hexdigest() == MODULE_SHA256, 'Installed module changed')
    require(PARAMS.is_dir(), 'Qualified controller must be loaded first')
    lockfd = os.open('/run/lock/orchard-j72-charge-supervisor.lock',
                     os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    fcntl.flock(lockfd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    check_status(Controller().status(), False)
    Controller().source()
    used = args.grant.with_name(args.grant.name + '.used')
    require(not used.exists(), 'Authorization was already consumed')
    os.rename(args.grant, used)
    args.log.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    class EvidenceHandler(RotatingFileHandler):
        def handleError(self, record):
            raise RuntimeError('Charging evidence could not be written')
    handler = EvidenceHandler(args.log, maxBytes=2*1024*1024, backupCount=7)
    os.chmod(args.log, 0o600)
    logger = logging.getLogger('j72-charge')
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    stopped = False
    def handle_stop(_signum, _frame):
        nonlocal stopped
        stopped = True
    signal.signal(signal.SIGTERM, handle_stop)
    signal.signal(signal.SIGINT, handle_stop)
    inhibitor = None
    try:
        inhibitor = SleepInhibitor().start()
        summary = run_session(Controller(inhibitor), args.seconds,
                              lambda row: logger.info(json.dumps(row)), lambda: stopped)
        print(json.dumps({'status': 'STOPPED_AND_RESTORED', 'summary': summary}), flush=True)
    except BaseException as error:
        logger.error(json.dumps({'event': 'failure', 'error': repr(error)}))
        raise
    finally:
        if inhibitor is not None:
            inhibitor.close()


if __name__ == '__main__':
    main()
