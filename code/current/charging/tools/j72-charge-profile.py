#!/usr/bin/python3
"""Prepare or verify reusable J72 charging configuration; never starts charging."""
import argparse
import json
from pathlib import Path
import shutil
from j72_charge_profile import CHECKS, installation_identity, read, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    init = sub.add_parser('init')
    init.add_argument('directory', type=Path)
    init.add_argument('--ecid', required=True)
    init.add_argument('--port', required=True)
    init.add_argument('--hub-port', required=True)
    init.add_argument('--root-device', required=True)
    init.add_argument('--boot-device', required=True)
    init.add_argument('--hub-model', required=True)
    check = sub.add_parser('verify')
    check.add_argument('profile', type=Path)
    host = sub.add_parser('host-config')
    host.add_argument('profile', type=Path)
    host.add_argument('--ssh-key', required=True)
    host.add_argument('--known-hosts', required=True)
    host.add_argument('--password-file', required=True)
    host.add_argument('--output', type=Path, required=True)
    host.add_argument('--target-profile', default='/etc/orchard/j72-charge/installation.json')
    args = parser.parse_args()
    if args.action == 'host-config':
        p, h = read(args.profile)
        argv = ['ssh', '-i', args.ssh_key, '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes',
                '-o', 'StrictHostKeyChecking=yes', '-o', 'UserKnownHostsFile=' + args.known_hosts,
                '-o', 'ConnectTimeout=5', '-o', 'ServerAliveInterval=3', '-o', 'ServerAliveCountMax=2',
                '-o', 'HostKeyAlias=172.16.42.1', 'tablet@172.16.42.1']
        result = {'port': p['source']['port'], 'hub_port': p['source']['hub_port'],
                  'hub': p['source']['hub'], 'device': h['usb_device'], 'ecid': p['ecid'].lower(),
                  'core_sha256': p['qualification_sha256'], 'target_profile': args.target_profile,
                  'password_file': args.password_file, 'ssh_argv': argv,
                  'log': '/var/log/orchard-j72-charge-auto/events.jsonl'}
        with args.output.open('x') as f:
            import os
            os.fchmod(f.fileno(), 0o600)
            json.dump(result, f, indent=2)
        print(json.dumps({'status': 'HOST_CONFIGURATION_CREATED', 'charging_started': False}))
        return
    if args.action == 'verify':
        p, _ = read(args.profile)
        print(json.dumps({'status': 'QUALIFIED_PROFILE_VERIFIED', 'hardware': p['hardware_id'],
                          'charging_started': False}))
        return
    d = args.directory
    d.mkdir(mode=0o700)  # Refuse overwriting an existing installation/evidence.
    hardware = Path(__file__).resolve().parents[1] / 'config/j72-charging/hardware.json'
    shutil.copyfile(hardware, d / 'hardware.json')
    p = {'schema': 1, 'hardware_id': 'apple-j72-charge-1050-v1', 'ecid': args.ecid,
         'root_device': args.root_device, 'boot_device': args.boot_device,
         'hardware_file': 'hardware.json', 'hardware_sha256': sha(d / 'hardware.json'),
         'source': {'model': args.hub_model, 'kind': 'powered-data-hub',
                    'hub': {k: 'REPLACE' for k in ('idVendor', 'idProduct', 'bcdDevice', 'bmAttributes')},
                    'port': args.port, 'hub_port': args.hub_port,
                    'rated_mV': None, 'qualified_mA': None},
         'qualification_file': 'qualification.json', 'qualification_sha256': None}
    q = {'status': 'PENDING', 'installation_sha256': installation_identity(p),
         'hardware_sha256': p['hardware_sha256'],
         'checks': {k: {'passed': False, 'evidence_file': None, 'evidence_sha256': None} for k in CHECKS},
         'two_hour_seconds': 0, 'continuous_seconds': 0, 'two_hour_net_mAh': 0,
         'continuous_net_mAh': 0, 'guard_violations': None, 'restoration_failures': None}
    (d / 'installation.json').write_text(json.dumps(p, indent=2) + '\n')
    (d / 'qualification.json').write_text(json.dumps(q, indent=2) + '\n')
    print(json.dumps({'status': 'PENDING_TEMPLATE_CREATED', 'directory': str(d),
                      'charging_started': False, 'qualification_inherited': False}))


if __name__ == '__main__':
    main()
