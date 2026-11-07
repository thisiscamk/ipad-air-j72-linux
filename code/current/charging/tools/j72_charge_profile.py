#!/usr/bin/python3
"""Reusable J72 installation profiles. Reading a profile never enables charge."""
import hashlib
import json
from pathlib import Path
import re
import stat

CHECKS = ('source_rating', 'disconnect_restore', 'freeze_restore', 'kill_restore',
          'invalid_admissions', 'host_independence', 'fresh_boot_default_off',
          'gauge_pairing', 'window_restore_restart', 'two_hour_soak',
          'continuous_mode', 'sleep_inhibitor', 'final_health')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def installation_identity(profile):
    # No password, SSH key, host address or runtime boot ID belongs in evidence.
    identity = {k: profile[k] for k in ('hardware_id', 'ecid', 'source', 'root_device', 'boot_device')}
    return hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()


def validate(profile, directory, trusted=False):
    directory = Path(directory)
    require(profile['schema'] == 1, 'Unsupported profile schema')
    require(re.fullmatch('[0-9a-fA-F]{16}', profile['ecid']) is not None, 'Set this installation ECID')
    require(profile['hardware_id'] == 'apple-j72-charge-1050-v1', 'Unsupported hardware policy')
    require(all(profile.get(k, '').startswith('/dev/') for k in ('root_device', 'boot_device')),
            'Set installation root and boot device paths')
    source = profile['source']
    require(isinstance(source['model'], str) and 0 < len(source['model']) <= 80,
            'Set the measured source model')
    require(source['kind'] == 'powered-data-hub', 'Only powered data hubs are supported')
    require(source['rated_mV'] == 5000 and isinstance(source['qualified_mA'], int) and
            source['qualified_mA'] >= 1500,
            'Source rating/measurement insufficient for this policy')
    for key, digits in (('idVendor', 4), ('idProduct', 4), ('bcdDevice', 4), ('bmAttributes', 2)):
        require(re.fullmatch('[0-9a-f]{' + str(digits) + '}', source['hub'][key]) is not None,
                'Set measured hub descriptor: ' + key)
    require(int(source['hub']['bmAttributes'], 16) & 0x40, 'Hub is not self-powered')
    require(source['port'] and source['hub_port'] and
            source['port'].startswith(source['hub_port'] + '.'), 'Set exact qualified USB port')
    hardware = directory / profile['hardware_file']
    require(sha(hardware) == profile['hardware_sha256'], 'Hardware profile changed')
    h = json.loads(hardware.read_text())
    require(h['id'] == profile['hardware_id'], 'Wrong hardware profile')
    require(h['controller_input_limit_mA'] == 1050, 'Unqualified input limit')
    record = directory / profile['qualification_file']
    require(sha(record) == profile['qualification_sha256'], 'Qualification record changed')
    q = json.loads(record.read_text())
    require(q['status'] == 'QUALIFIED', 'Installation is not qualified')
    require(q['installation_sha256'] == installation_identity(profile), 'Evidence belongs to another installation')
    require(q['hardware_sha256'] == profile['hardware_sha256'], 'Evidence uses another hardware build')
    require(set(q['checks']) == set(CHECKS), 'Incomplete qualification checklist')
    for name in CHECKS:
        check = q['checks'][name]
        require(check['passed'] is True, 'Qualification check failed: ' + name)
        evidence = directory / check['evidence_file']
        require(sha(evidence) == check['evidence_sha256'], 'Evidence changed: ' + name)
    require(q['two_hour_seconds'] >= 7200 and q['continuous_seconds'] >= 2700,
            'Real observation durations incomplete')
    require(q['two_hour_net_mAh'] > 0 and q['continuous_net_mAh'] > 0,
            'No measured net positive charging')
    require(q['guard_violations'] == 0 and q['restoration_failures'] == 0,
            'Safety qualification failed')
    if trusted:
        paths = [directory, hardware, record]
        paths += [directory / q['checks'][k]['evidence_file'] for k in CHECKS]
        for path in paths:
            info = path.lstat()
            require(info.st_uid == 0 and not info.st_mode & 0o022 and
                    not stat.S_ISLNK(info.st_mode), 'Profile/evidence must be root-owned and not writable by others')
    return h


def read(path, trusted=False):
    path = Path(path)
    if trusted:
        info = path.lstat()
        require(info.st_uid == 0 and not info.st_mode & 0o022 and
                not stat.S_ISLNK(info.st_mode), 'Untrusted installation profile')
    p = json.loads(path.read_text())
    return p, validate(p, path.parent, trusted=trusted)
