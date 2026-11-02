#!/usr/bin/env python3
"""Opt-in userspace tests on the exact #34 RAM boot. Private evidence only."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
def load(name, file):
    s = importlib.util.spec_from_file_location(name, ROOT / 'tools' / file)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['preflight', 'stage', 'inspect', 'scan', 'connect', 'status', 'ssh', 'https', 'stop'])
    p.add_argument('--interface', default='wlan0')
    p.add_argument('--profile', type=Path, help='Private JSON containing ssid and passphrase or psk; connect only')
    p.add_argument('--storage35', action='store_true', help='Require the separately pinned combined #35 payload')
    a = p.parse_args()
    os.umask(0o077)
    n = load('network', 'j72_network_userspace.py'); manifest = n.preflight()
    if a.action == 'preflight': return
    h = load('v3host', 'j72-desktop-storage35-host.py' if a.storage35 else 'j72-wifi-v3-host.py'); bundle = h.preflight(verify_desktop=False)
    c = load('lock', 'run-j72-input-limit-hub1050-desktop.py').locked_ram(h.ram())
    assert c('uname -v', timeout=4).decode().strip() == bundle['uts_version']
    assert c('busybox cat /proc/device-tree/model', timeout=4).rstrip(b'\0\r\n') == b'Apple iPad Air (Cellular)'
    if a.action == 'stage':
        n.stage(c, manifest)
        print('RAM-only network tools staged; no scan or association requested')
        return
    assert re.fullmatch(r'[a-zA-Z0-9_-]{1,15}', a.interface)
    c('test -e /sys/class/net/' + a.interface + '/phy80211 && test "$(cat /sys/module/j72_wlan_transport_v3/parameters/session_active)" = Y', timeout=4)
    c('test -x ' + n.REMOTE + '/usr/sbin/j72-network', timeout=4)
    out = n.WORK / ('capture-' + time.strftime('%Y%m%d-%H%M%S') + '-' + a.action)
    out.mkdir()
    if a.action == 'connect':
        assert a.profile and a.profile.resolve().is_relative_to(ROOT / 'private'), 'Keep profiles under private/'
        assert a.profile.stat().st_mode & 0o077 == 0, 'Profile must have mode 600'
        profile = json.loads(a.profile.read_text())
        config = n.wpa_config(profile['ssid'], profile.get('passphrase'), profile.get('psk'))
        config_file = n.WORK / 'wpa_supplicant.conf'
        config_file.write_text(config); config_file.chmod(0o600)
        load('uploader', 'run-j72-wlan-enumeration-v2.py').upload(c, h, config_file, n.REMOTE + '/etc/wpa_supplicant.conf')
        c('busybox chmod 600 ' + n.REMOTE + '/etc/wpa_supplicant.conf', timeout=4)
    command = 'busybox chroot ' + n.REMOTE + ' /usr/sbin/j72-network ' + a.action + ' ' + shlex.quote(a.interface)
    raw = c(command, timeout=65 if a.action == 'connect' else 30)
    (out / 'result.txt').write_bytes(raw)
    if a.action == 'ssh':
        status = c('busybox chroot ' + n.REMOTE + ' /bin/ip -4 -o address show dev ' + a.interface, timeout=4).decode()
        addresses = re.findall(r'\binet ([0-9.]+)/', status)
        assert len(addresses) == 1
        cmd = ['ssh', '-F', '/dev/null', '-o', 'BatchMode=yes', '-o', 'IdentitiesOnly=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'UserKnownHostsFile=' + str(n.WORK / 'known_hosts'), '-o', 'HostKeyAlias=j72-linux-ram', '-o', 'ConnectTimeout=5', '-i', manifest['owner_client_key_path'], '-T', 'root@' + addresses[0], '/bin/busybox echo J72_WIFI_SSH; /bin/busybox id; /usr/bin/iw --version']
        r = subprocess.run(cmd, capture_output=True, timeout=10)
        (out / 'ssh-stdout.txt').write_bytes(r.stdout); (out / 'ssh-stderr.txt').write_bytes(r.stderr)
        assert r.returncode == 0 and b'J72_WIFI_SSH' in r.stdout and b'uid=0(root)' in r.stdout
        boot_id=c('busybox cat /proc/sys/kernel/random/boot_id',timeout=4).decode().strip()
        (n.WORK/'live-wifi-session.json').write_text(json.dumps({'address':addresses[0],'boot_id':boot_id,'uts_version':bundle['uts_version']},indent=2)+'\n')
        (n.WORK/'live-wifi-session.json').chmod(0o600)
        print('PASS: pinned-key SSH and remote command over the assigned Wi-Fi IPv4 address')
    print('Private evidence:', out, '; USB recovery remains available')

if __name__ == '__main__': main()
