#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
import importlib.util
from pathlib import Path
import tempfile
import unittest
import subprocess
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('charging_return', Path(__file__).with_name('ensure-j72-state1-ios-charging.py'))
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class ChargingReturnTests(unittest.TestCase):
    def test_actual_recovery_shell_requires_baseline_and_inactive_owner(self):
        for present in (b'N', b'Y'):
            with self.subTest(present=present), tempfile.TemporaryDirectory() as d:
                root = Path(d)
                def write(path, data):
                    p = root/path
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_text(data)
                write('sys/block/nbd2/size', '0\n')
                write('proc/mounts', '')
                write('sys/module/j72_wlan_ready_snapshot/parameters/snapshot', 'reg_04c0=02\n')
                if present == b'Y':
                    write('sys/module/j72_charge_maintain35/parameters/status', 'enabled=0\nactive=0\narmed=0\nrestore_failed=0\n')
                calls=[]
                def command(body):
                    calls.append(body)
                    return present if len(calls)==1 else b'CHARGE_BASELINE_VERIFIED'
                checks=helper.stop_charge_if_present(command,lambda:None)
                body=checks.replace('/sys/',str(root/'sys')+'/').replace('/proc/mounts',str(root/'proc/mounts'))
                subprocess.run(['/bin/sh','-ec',body],check=True,capture_output=True)
                write('sys/module/j72_wlan_ready_snapshot/parameters/snapshot','reg_04c0=3c\n')
                with self.assertRaises(subprocess.CalledProcessError):
                    subprocess.run(['/bin/sh','-ec',body],check=True,capture_output=True)
                write('sys/module/j72_wlan_ready_snapshot/parameters/snapshot','reg_04c0=02\n')
                if present == b'Y':
                    write('sys/module/j72_charge_maintain35/parameters/status','enabled=0\nactive=1\narmed=0\nrestore_failed=0\n')
                else:
                    write('sys/module/j72_charge_maintain35/parameters/status','active=0\n')
                with self.assertRaises(subprocess.CalledProcessError):
                    subprocess.run(['/bin/sh','-ec',body],check=True,capture_output=True)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.hub = self.root / 'top/hub'
        self.hub.mkdir(parents=True)
        self.devices = self.root / 'devices'
        self.devices.mkdir()
        (self.devices / 'hub').symlink_to(self.hub, target_is_directory=True)
        self.boot = self.root / 'boot'
        self.boot.write_text('host-boot\n')
        self.source = dict(host_boot_id='host-boot', hub_port='hub',
                           hub_bcdDevice='1234', source_port='target')
        for key, value in dict(idVendor='05e3', idProduct='0610',
                               bcdDevice='1234', bmAttributes='c0').items():
            (self.hub / key).write_text(value + '\n')

    def fake_path(self, value):
        if value == '/sys/bus/usb/devices':
            return self.devices
        if value == '/proc/sys/kernel/random/boot_id':
            return self.boot
        raise AssertionError('Unexpected path in port-presence query: ' + str(value))

    def presence(self):
        with patch.object(helper, 'Path', side_effect=self.fake_path):
            return helper.port_presence(self.source)

    def attach(self, vendor, product):
        target = self.hub / 'target'
        target.mkdir()
        (target / 'idVendor').write_text(vendor + '\n')
        (target / 'idProduct').write_text(product + '\n')
        (self.devices / 'target').symlink_to(target, target_is_directory=True)

    def test_absent_charger_does_not_use_prior_staging_receipt(self):
        for present, expected in [(b'N',0),(b'Y',1)]:
            calls=[];stops=[]
            def command(body):
                calls.append(body)
                return present if len(calls)==1 else b'CHARGE_BASELINE_VERIFIED'
            checks=helper.stop_charge_if_present(command,lambda:stops.append(1))
            self.assertEqual(len(stops),expected)
            self.assertIn('reg_04c0=02',checks)
            self.assertIn('CHARGE_BASELINE_VERIFIED',calls[-1])
        with self.assertRaises(RuntimeError):
            helper.stop_charge_if_present(lambda body:b'unknown',lambda:self.fail('must not stop'))
        with self.assertRaises(RuntimeError):
            def failure(body):
                if body.startswith('if test'):return b'N'
                raise RuntimeError('baseline failure')
            helper.stop_charge_if_present(failure,lambda:self.fail('must not stop'))

    def test_absent_is_not_linux(self):
        self.assertEqual(self.presence(), 'absent')

    def test_ios_linux_and_foreign_classified_separately(self):
        for vendor, product, expected in [('05ac','12ab','ios'), ('1d6b','0104','linux'), ('abcd','0123','foreign')]:
            with self.subTest(expected=expected):
                self.setUp()
                self.attach(vendor, product)
                self.assertEqual(self.presence(), expected)

    def test_host_boot_revision_and_bus_power_change_refused(self):
        for path, value in [('boot','different'), ('bcdDevice','ffff'), ('bmAttributes','80')]:
            with self.subTest(path=path):
                self.setUp()
                (self.boot if path=='boot' else self.hub/path).write_text(value)
                with self.assertRaises(AssertionError):
                    self.presence()

    def test_charging_needs_external_capability_and_positive_evidence(self):
        base=dict(ExternalConnected=True, ExternalChargeCapable=True)
        for record, expected in [({},'UNVERIFIED'),
                                  ({'IORegistry':base},'EXTERNAL_POWER_PRESENT_CHARGE_NOT_CONFIRMED'),
                                  ({'IORegistry':{**base,'IsCharging':True}},'IOS_REPORTS_CHARGING'),
                                  ({'IORegistry':{**base,'FullyCharged':True,'CurrentCapacity':100}},'IOS_REPORTS_FULL_ON_EXTERNAL_POWER'),
                                  ({'IORegistry':{**base,'CurrentCapacity':100}},'EXTERNAL_POWER_PRESENT_CHARGE_NOT_CONFIRMED'),
                                  ({'IORegistry':{'IsCharging':True}},'EXTERNAL_CHARGING_NOT_CONFIRMED')]:
            with self.subTest(expected=expected):
                self.assertEqual(helper.charging_state(record), expected)


if __name__ == '__main__':
    unittest.main()
