#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Host-only checks of candidate observation refusals and shell parsing."""
import importlib.util
from pathlib import Path
import subprocess
import unittest

spec = importlib.util.spec_from_file_location('voltage_observer', Path(__file__).with_name('run-j72-voltage-observation35.py'))
observer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(observer)


class PolicyHealthTests(unittest.TestCase):
    def valid(self):
        return dict(charge_resume_policy='1', charge_thermal_latched='0',
                    charge_last_pause='2', charge_warm_full_resumes='0')

    def test_known_policy_and_latched_thermal_hold_are_observable(self):
        for latch in ('0', '1'):
            for pause in range(7):
                row = self.valid()
                row.update(charge_thermal_latched=latch, charge_last_pause=str(pause))
                observer.policy_health(row)

    def test_missing_or_different_policy_is_refused(self):
        for key in self.valid():
            row = self.valid()
            del row[key]
            with self.subTest(key=key), self.assertRaises(observer.StopObservation):
                observer.policy_health(row)
        for key, values in {
            'charge_resume_policy': ('0', '2', '1\n'),
            'charge_thermal_latched': ('2', '-1', 'true'),
            'charge_last_pause': ('7', '-1', '02'),
            'charge_warm_full_resumes': ('-1', '1.0', '١', ' 1', '1\n'),
        }.items():
            for value in values:
                row = {**self.valid(), key: value}
                with self.subTest(key=key, value=value), self.assertRaises(observer.StopObservation):
                    observer.policy_health(row)

    def test_collectors_parse_without_execution(self):
        for body in (observer.COLLECT, observer.FINAL):
            subprocess.run(['/bin/sh', '-n'], input=body, text=True, check=True)


if __name__ == '__main__':
    unittest.main()
