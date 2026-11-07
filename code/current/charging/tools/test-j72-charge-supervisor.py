#!/usr/bin/env python3
"""Exercise the real supervisor loop against source/process/controller faults."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch
import json
import stat
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location('supervisor', Path(__file__).with_name('j72-charge-supervisor.py'))
supervisor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(supervisor)


class Fake:
    def __init__(self, failure=None):
        self.now = 100.
        self.failure = failure
        self.ticks = 0
        self.renewals = 0
        self.stops = 0
        self.running = False
        self.rows = []
        self.value = dict(ready='1', fault='0', restore_failed='0', error='0', controller_error='0',
                          enabled='0', active='0', armed='0', cycles='0', mode='0', restored='0',
                          guard_at_ms='100000', guard_soc='90', guard_temp_tenthC='350', guard_current_uA='300000')

    def source(self):
        if self.ticks >= 2 and self.failure in ('offline', 'unknown', 'source_read_error', 'udc_lost'):
            raise RuntimeError(self.failure)
        if self.ticks >= 2 and self.failure == 'slow_source':
            self.now += 1.6

    def status(self):
        value = dict(self.value)
        if self.ticks >= 2:
            if self.failure == 'fault': value['fault'] = '1'
            if self.failure == 'restore_failure': value['restore_failed'] = '1'
            if self.failure == 'disabled': value['enabled'] = '0'
            if self.failure == 'not_ready': value['ready'] = '0'
            if self.failure == 'error': value['error'] = '-5'
            if self.failure == 'controller_error': value['controller_error'] = '-5'
            if self.failure == 'active_wrong_mode': value['mode'] = '2'
            if self.failure == 'unrestored_pause':
                value.update(active='0', restored='0')
        return value

    def write(self, name, value):
        if name == 'source_lease':
            self.renewals += 1
        if name == 'arm_hub':
            self.value['armed'] = '1'
        if name == 'begin_session':
            if self.failure == 'begin_write_error': raise OSError('begin failed')
            if self.failure == 'start_timeout': return
            self.running = True
            self.value.update(enabled='1', active='1', mode='1', cycles='1')

    def stop(self):
        self.stops += 1
        self.value.update(enabled='0', active='0', armed='0', restored='1')
        return dict(self.value)

    def sleep(self, seconds):
        self.now += seconds
        if seconds == .25:
            self.ticks += 1
            self.value['guard_at_ms'] = str(int(self.now * 1000))
            if self.failure == 'scheduling_gap' and self.ticks >= 2:
                self.now += 2

    def log(self, row):
        if self.failure == 'log_error' and row['event'] == 'sample':
            raise OSError('disk full')
        self.rows.append(row)

    def notify(self, message):
        if self.failure == 'notify_error': raise OSError('watchdog notification failed')

    def run(self, stop=None, seconds=10):
        return supervisor.run_session(self, seconds, self.log, stop or (lambda: False),
                                      clock=lambda: self.now, sleep=self.sleep, send_notify=self.notify)


class SupervisorTests(unittest.TestCase):
    def test_healthy_bounded_session_stops(self):
        fake = Fake()
        result = fake.run()
        self.assertEqual(fake.stops, 1)
        self.assertGreater(result['positive_samples'], 0)
        self.assertEqual(fake.rows[-1]['event'], 'stopped')
        self.assertEqual(fake.value['active'], '0')

    def test_gauge_refresh_during_status_read_is_bracketed(self):
        class RefreshDuringRead(Fake):
            def status(self):
                self.now += .003
                self.value['guard_at_ms'] = str(int(self.now * 1000))
                return super().status()
        fake = RefreshDuringRead()
        fake.run(seconds=5)
        for row in fake.rows:
            if row['event'] not in ('started', 'sample'):
                continue
            stamp = int(row['status']['guard_at_ms']) / 1000
            self.assertLessEqual(row['status_read_started'], stamp + .001)
            self.assertLessEqual(stamp, row['status_read_finished'])
            self.assertLessEqual(row['status_read_finished'], row['uptime'])
            self.assertLess(row['status_read_finished'] - row['status_read_started'], 1.5)

    def test_faults_stop_without_retry(self):
        faults = ('offline', 'unknown', 'source_read_error', 'udc_lost', 'fault',
                  'restore_failure', 'disabled', 'not_ready', 'error', 'controller_error',
                  'active_wrong_mode', 'unrestored_pause', 'slow_source', 'scheduling_gap',
                  'begin_write_error', 'start_timeout', 'log_error', 'notify_error')
        for fault in faults:
            with self.subTest(fault=fault):
                fake = Fake(fault)
                with self.assertRaises((RuntimeError, OSError)):
                    fake.run()
                self.assertEqual(fake.stops, 1)
                self.assertEqual(fake.value['active'], '0')
                self.assertLessEqual(fake.renewals, 3)

    def test_explicit_stop(self):
        fake = Fake()
        fake.run(stop=lambda: fake.ticks >= 2)
        self.assertEqual(fake.stops, 1)
        self.assertLess(fake.now, 102)

    def test_continuous_mode_keeps_guards_and_can_stop(self):
        fake = Fake()
        fake.run(stop=lambda: fake.ticks >= 20, seconds=0)
        self.assertGreaterEqual(fake.now, 105)
        self.assertEqual(fake.stops, 1)
        bad = Fake('offline')
        with self.assertRaises(RuntimeError):
            bad.run(seconds=0)
        self.assertEqual(bad.stops, 1)

    def test_grant_bounds(self):
        good = {'boot_id': 'boot', 'source_kind': supervisor.SOURCE_KIND,
                'module_sha256': supervisor.MODULE_SHA256, 'source_qualification_id': 'proof',
                'issued_boottime': 100, 'valid_until_boottime': 130, 'max_session_s': 3600}
        supervisor.validate_grant(good, 'boot', 105, 3600)
        with self.assertRaises(RuntimeError):
            supervisor.validate_grant(good, 'boot', 105, 0)
        supervisor.validate_grant(dict(good, max_session_s=0, mode='continuous-maintenance'),
                                  'boot', 105, 0)
        with self.assertRaises(RuntimeError):
            supervisor.validate_grant(dict(good, max_session_s=0, mode='continuous-maintenance'),
                                      'boot', 105, 1)
        changes = [dict(boot_id='wrong'), dict(source_kind='unknown'), dict(module_sha256='wrong'),
                   dict(source_qualification_id=''), dict(issued_boottime=110),
                   dict(valid_until_boottime=104), dict(valid_until_boottime=161),
                   dict(max_session_s=3599), dict(max_session_s=43201)]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(RuntimeError):
                supervisor.validate_grant(dict(good, **change), 'boot', 105, 3600)

    def test_missing_or_duplicate_status_fails(self):
        with self.assertRaises(RuntimeError):
            supervisor.fields('fault=0\nfault=1\n')
        with self.assertRaises((RuntimeError, KeyError)):
            supervisor.check_status({}, True)

    def test_sleep_inhibitor_matches_live_owner_and_block_mode(self):
        item = supervisor.SleepInhibitor()
        item.process = Mock(pid=123)
        item.process.poll.return_value = None
        good = dict(who=item.WHO, what='sleep', mode='block', pid=123)
        for change, expected in [({}, True), ({'pid': 456}, False), ({'mode': 'delay'}, False),
                                 ({'who': 'unrelated'}, False), ({'what': 'shutdown'}, False)]:
            result = Mock(returncode=0, stdout=json.dumps([dict(good, **change)]))
            with patch.object(supervisor.subprocess, 'run', return_value=result):
                self.assertEqual(item.listed(), expected)

    def test_sleep_inhibitor_loss_fails_closed(self):
        item = supervisor.SleepInhibitor()
        item.process = Mock(pid=123)
        item.process.poll.return_value = 1
        with self.assertRaises(RuntimeError):
            item.check()
        item.process.poll.return_value = None
        with self.assertRaises(RuntimeError):
            item.check()

    def test_runtime_inhibitor_check_does_not_call_dbus(self):
        item = supervisor.SleepInhibitor()
        item.process = Mock(pid=123)
        item.process.poll.return_value = None
        fd, target = Mock(), Mock()
        fd.stat.return_value = target.stat.return_value = SimpleNamespace(
            st_mode=stat.S_IFIFO | 0o600, st_dev=29, st_ino=55)
        item.reference = (fd, target, (29, 55))
        item.logind_identity = (551, 'start')
        with patch.object(item, 'process_start', return_value='start'), \
             patch.object(supervisor.subprocess, 'run', side_effect=AssertionError('Runtime D-Bus call')):
            item.check()
            target.stat.return_value = SimpleNamespace(st_mode=stat.S_IFIFO, st_dev=29, st_ino=56)
            with self.assertRaises(RuntimeError):
                item.check()
        with patch.object(item, 'process_start', return_value='new-start'), self.assertRaises(RuntimeError):
            item.check()


if __name__ == '__main__':
    unittest.main(verbosity=2)
