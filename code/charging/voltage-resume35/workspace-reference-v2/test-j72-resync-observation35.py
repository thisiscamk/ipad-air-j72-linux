#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from j72_observation_health import fields, Health, StopObservation

spec=importlib.util.spec_from_file_location('resync_observer',Path(__file__).with_name('run-j72-resync-observation35.py'))
observer=importlib.util.module_from_spec(spec);spec.loader.exec_module(observer)


class ResyncObservationTests(unittest.TestCase):
    def status(self):
        return dict(charge_resume_policy='1',charge_thermal_latched='0',
                    charge_last_pause='0',charge_warm_full_resumes='0',
                    touch_phase_resync_policy='1',touch_phase_resync_headers='20',
                    touch_phase_resync_frames='19',touch_phase_resync_failures='1')
    def test_policy_and_numeric_counter_refusals(self):
        observer.policy_health(self.status())
        for key in self.status():
            r=self.status();del r[key]
            with self.subTest(key=key),self.assertRaises(StopObservation):observer.policy_health(r)
        for key in ('touch_phase_resync_headers','touch_phase_resync_frames','touch_phase_resync_failures'):
            for value in ('-1','a','١','1.0'):
                r=self.status();r[key]=value
                with self.subTest(key=key,value=value),self.assertRaises(StopObservation):observer.policy_health(r)
    def test_actual_collector_reads_fixture_phase_fields(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            def write(name,value):
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(value if isinstance(value,bytes) else value.encode())
            touch=dict(session_state='2',session_number='3',enabled='Y',continuous='Y',capture_seconds='3',input_frames='100',input_recoveries='0',input_bad_layouts='0',input_timeouts='0',wire_anomalies='20',xfer_errors='0',recovery_stop_reason='0',phase_resync_policy='1',phase_resync_headers='20',phase_resync_frames='19',phase_resync_failures='1')
            for k,v in touch.items():write('sys/module/j72_touch_session/parameters/'+k,v+'\n')
            charge=dict(ready='1',enabled='0',active='0',fault='0',restore_failed='0',resume_policy='1',thermal_latched='0',last_pause='0',warm_full_resumes='0')
            write('sys/module/j72_charge_maintain35/parameters/status',''.join(k+'='+v+'\n' for k,v in charge.items()))
            write('sys/block/nbd2/size','0\n');write('proc/mounts','');write('run/j72/desktop-ready','')
            write('sys/devices/system/cpu/cpufreq/policy0/scaling_governor','schedutil\n')
            write('sys/class/backlight/test/device/of_node/compatible',b'apple,anya-pmic-bl\0')
            write('sys/class/backlight/test/max_brightness','2047\n');write('sys/class/backlight/test/actual_brightness','802\n')
            write('sys/class/power_supply/j72-bq27545-battery/uevent','POWER_SUPPLY_CAPACITY=80\nPOWER_SUPPLY_TEMP=330\nPOWER_SUPPLY_VOLTAGE_NOW=4000000\n')
            body=observer.COLLECT.replace('/sys/',str(root/'sys')+'/').replace('/run/',str(root/'run')+'/').replace('/proc/mounts',str(root/'proc/mounts'))
            # Substitute only the unrelated network service, retaining the real
            # collector loops, sysfs reads, prefixes, filters and shell semantics.
            old='busybox chroot /opt/j72-network /usr/bin/wpa_cli -p '+str(root/'run/wpa_supplicant')+' -i wlan0 status'
            assert body.count(old)==1
            body=body.replace(old,"printf 'wpa_state=COMPLETED\\n'")
            raw=subprocess.check_output(['/bin/sh','-ec',body],stderr=subprocess.PIPE)
            r=fields(raw);observer.policy_health(r);Health(802).check(r,initial=True)
            for k,v in self.status().items():
                if k.startswith('touch_'):self.assertEqual(r[k],v)


if __name__=='__main__':unittest.main()
