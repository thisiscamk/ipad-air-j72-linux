#!/usr/bin/env python3
"""Pinned-key Wi-Fi control of the exact live RAM boot, independent of NCM."""
import ipaddress
import json
from pathlib import Path
import shlex
import subprocess

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'private/j72-platform/power-wifi-20261101/network-userspace'

def command(body, timeout=15):
    m=json.loads((WORK/'manifest.json').read_text())
    session=json.loads((WORK/'live-wifi-session.json').read_text())
    address=str(ipaddress.IPv4Address(session['address']))
    args=['ssh','-F','/dev/null','-o','BatchMode=yes','-o','IdentitiesOnly=yes',
          '-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+str(WORK/'known_hosts'),
          '-o','HostKeyAlias=j72-linux-ram','-o','ConnectTimeout=5',
          '-i',m['owner_client_key_path'],'-T','root@'+address]
    guarded=('test "$(cat /proc/sys/kernel/random/boot_id)" = '+shlex.quote(session['boot_id'])+
             ' && test "$(uname -v)" = '+shlex.quote(session['uts_version'])+
             ' && test "$(cat /proc/device-tree/model)" = "Apple iPad Air (Cellular)" && '+body)
    remote='/bin/busybox chroot /proc/1/root /bin/busybox sh -ec '+shlex.quote(guarded)
    r=subprocess.run(args+[remote],capture_output=True,timeout=timeout)
    if r.returncode:
        (WORK/'wifi-system-command-error.log').write_bytes(r.stdout+r.stderr)
        raise RuntimeError('Wi-Fi command failed; private error log retained')
    return r.stdout
