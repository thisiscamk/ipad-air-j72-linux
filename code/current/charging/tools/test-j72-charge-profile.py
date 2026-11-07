#!/usr/bin/python3
"""Qualification isolation and tamper tests; fixtures are not hardware results."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from j72_charge_profile import CHECKS, installation_identity, sha, validate


class Profiles(unittest.TestCase):
    def test_installation_evidence_and_build_cannot_be_reused_blindly(self):
        with tempfile.TemporaryDirectory() as temp:
            d = Path(temp)
            shutil.copyfile(Path(__file__).parents[1] / 'config/j72-charging/hardware.json', d / 'hardware.json')
            # These synthetic fixture bytes exercise validation, not hardware.
            (d / 'test-evidence.json').write_text('{"synthetic_unit_test":true}')
            p = {'schema': 1, 'hardware_id': 'apple-j72-charge-1050-v1', 'ecid': '0000000000000001',
                 'root_device': '/dev/asp0n1p3', 'boot_device': '/dev/asp0n1p2',
                 'hardware_file': 'hardware.json', 'hardware_sha256': sha(d / 'hardware.json'),
                 'source': {'model': 'JCH377', 'port': '1-1.3.1', 'hub_port': '1-1.3',
                            'kind': 'powered-data-hub',
                            'hub': {'idVendor':'05e3','idProduct':'0610','bcdDevice':'4427','bmAttributes':'e0'},
                            'rated_mV': 5000, 'qualified_mA': 1500},
                 'qualification_file': 'qualification.json', 'qualification_sha256': None}
            q = {'status': 'QUALIFIED', 'installation_sha256': installation_identity(p),
                 'hardware_sha256': p['hardware_sha256'],
                 'checks': {k: {'passed': True, 'evidence_file': 'test-evidence.json',
                               'evidence_sha256': sha(d / 'test-evidence.json')} for k in CHECKS},
                 'two_hour_seconds': 7200, 'continuous_seconds': 2700,
                 'two_hour_net_mAh': 100, 'continuous_net_mAh': 50,
                 'guard_violations': 0, 'restoration_failures': 0}
            def write(record):
                (d / 'qualification.json').write_text(json.dumps(record))
                p['qualification_sha256'] = sha(d / 'qualification.json')
            write(q)
            self.assertEqual(validate(p, d)['controller_input_limit_mA'], 1050)
            for key, value in (('status', 'PENDING'), ('two_hour_seconds', 7199),
                               ('continuous_seconds', 2699), ('continuous_net_mAh', -1),
                               ('guard_violations', 1), ('restoration_failures', 1)):
                bad = dict(q, **{key: value});write(bad)
                with self.subTest(key=key), self.assertRaises(ValueError):
                    validate(p, d)
            write(q)
            other = dict(p, ecid='0000000000000002')
            with self.assertRaises(ValueError):
                validate(other, d)
            other = copy.deepcopy(p);other['source']['port'] = '1-1.3.2'
            with self.assertRaises(ValueError):
                validate(other, d)
            other = copy.deepcopy(p);other['source']['qualified_mA'] = 500
            with self.assertRaises(ValueError):
                validate(other, d)
            (d / 'test-evidence.json').write_text('changed')
            with self.assertRaises(ValueError):
                validate(p, d)


if __name__ == '__main__':
    unittest.main()
