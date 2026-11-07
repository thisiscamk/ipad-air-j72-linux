#!/usr/bin/python3
"""Source-identity and fault-recovery boundary tests for automatic admission."""
import importlib.util
from pathlib import Path
import tempfile
import unittest


def load(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


host = load('j72-charge-auto-host')
target = load('j72-charge-auto-target')


class AutoTests(unittest.TestCase):
    def test_clean_source_exit_only(self):
        good = dict(fault='0', enabled='0', active='0', error='0', controller_error='0',
                    restore_failed='0', failed_guard_faults='0', last_read_failure_ms='0',
                    restored='1', cycles='7')
        rows = [{'event': 'stopped', 'started': True, 'status': {'cycles': '7'}},
                {'event': 'failure', 'error': "RuntimeError('External source lost or unknown')"}]
        self.assertTrue(target.clean_disconnect_exit(good, True, rows))
        self.assertFalse(target.clean_disconnect_exit(good, False, rows))
        for error in ("RuntimeError('Slow source/status read; do not renew')", 'OSError(5)',
                      "RuntimeError('Sleep inhibitor exited')"):
            self.assertFalse(target.clean_disconnect_exit(good, True, [rows[0], dict(rows[1], error=error)]))
        self.assertFalse(target.clean_disconnect_exit(dict(good, cycles='8'), True, rows))
        self.assertFalse(target.clean_disconnect_exit(dict(good, restore_failed='1'), True, rows))

    def test_only_proven_disconnect_can_reset(self):
        good = dict(fault='1', controller_error='-107', error='0', restore_failed='0',
                    restored='1', enabled='0', active='0', failed_guard_faults='0',
                    last_read_failure_ms='0')
        self.assertTrue(target.reconnect_allowed(good, True))
        self.assertFalse(target.reconnect_allowed(good, False))
        bad = {'controller_error': ('-62', '-5', '-16', '-34'), 'error': ('-5',),
               'restore_failed': ('1',), 'restored': ('0',), 'enabled': ('1',),
               'active': ('1',), 'failed_guard_faults': ('1',),
               'last_read_failure_ms': ('1234',), 'fault': ('0',)}
        for key, values in bad.items():
            for value in values:
                with self.subTest(key=key, value=value):
                    self.assertFalse(target.reconnect_allowed(dict(good, **{key: value}), True))

    def test_new_boot_is_not_permission_to_clear_old_fault(self):
        old = ('old', '1', '50')
        new = ('new', '1', '51')
        r = host.request_for(new, old, True, 'hash')
        self.assertTrue(r['new_boot'])
        self.assertFalse(r['observed_previous_connection_loss'])

    def test_generation_and_observed_disconnect(self):
        a = ('boot', '1', '50')
        b = ('boot', '1', '51')
        self.assertFalse(host.request_for(a, None, False, 'hash')['observed_previous_connection_loss'])
        self.assertFalse(host.request_for(a, a, False, 'hash')['observed_previous_connection_loss'])
        self.assertTrue(host.request_for(b, a, False, 'hash')['observed_previous_connection_loss'])
        self.assertTrue(host.request_for(a, a, True, 'hash')['observed_previous_connection_loss'])

    def test_hub_and_owner_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            hub = root / 'physical' / '1-1.3'
            device = hub / '1-1.3.1'
            device.mkdir(parents=True)
            (root / '1-1.3.1').symlink_to(device)
            cfg = dict(port='1-1.3.1', hub_port='1-1.3', ecid='0000000000000001',
                       hub={'idVendor': '05e3', 'idProduct': '0610', 'bcdDevice': '4427',
                            'bmAttributes': 'e0'},
                       device={'idVendor': '05ac', 'idProduct': '4145', 'bcdDevice': '0703'})
            for p, fields in ((hub, cfg['hub']), (device, cfg['device'])):
                for k, v in fields.items():
                    (p / k).write_text(v)
            serial = 'ECID:0000000000000001 BOOT:11111111-1111-4111-8111-111111111111 BOARD:j72'
            for k, v in dict(serial=serial, bConfigurationValue='1', speed='480', busnum='1', devnum='90').items():
                (device / k).write_text(v)
            nop = lambda _: None
            self.assertEqual(host.snapshot(cfg, root, nop)[2], '90')
            for p, k, v in ((device, 'serial', serial.replace('0000000000000001', '0000000000000002')),
                            (device, 'bConfigurationValue', '0'), (device, 'speed', '12'),
                            (hub, 'idVendor', '1234'), (hub, 'bmAttributes', 'a0'),
                            (hub, 'bcdDevice', '9999')):
                original = (p / k).read_text()
                (p / k).write_text(v)
                with self.subTest(field=k), self.assertRaises(ValueError):
                    host.snapshot(cfg, root, nop)
                (p / k).write_text(original)
            def power_failed(_):
                raise ValueError('No hub adapter power')
            with self.assertRaises(ValueError):
                host.snapshot(cfg, root, power_failed)
            with self.assertRaises(ValueError):
                host.snapshot(dict(cfg, hub_port='1-1.4'), root, nop)


if __name__ == '__main__':
    unittest.main()
