#!/usr/bin/env python3
"""Offline DHCP shell logic, WPA2 known vector and private HTTP transfer tests."""
import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from urllib.error import HTTPError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
s = importlib.util.spec_from_file_location('network', ROOT / 'tools/j72_network_userspace.py')
n = importlib.util.module_from_spec(s); s.loader.exec_module(n)

def main():
    # IEEE WPA test vector: avoid deriving credentials from an owner's profile.
    conf = n.wpa_config('IEEE', 'password')
    assert 'psk=f42c6fc52df0ebef9ebb4b90b38a5f902e83fe1b135a70e23aed762e9710a12e' in conf
    assert 'ssid=49454545' in conf and 'password' not in conf
    for args in [('', 'password'), ('x'*33, 'password'), ('SSID', 'short')]:
        try: n.wpa_config(*args)
        except ValueError: pass
        else: raise AssertionError('Invalid credentials accepted')
    assert 'ssid=61220a62' in n.wpa_config('a"\nb', psk='ab'*32)
    with tempfile.TemporaryDirectory(prefix='j72-dhcp-test-') as d:
        root = Path(d)
        for name in ['sys/class/net/testwlan', 'run', 'etc', 'bin']: (root/name).mkdir(parents=True, exist_ok=True)
        (root/'sys/class/net/testwlan/phy80211').touch()
        log = root/'ip.log'
        mock = root/'bin/ip'
        mock.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> '+str(log)+'\n'); mock.chmod(0o755)
        # Only redirect absolute filesystem paths. Execute the actual shell
        # validation/prefix/route/resolver logic, never host network commands.
        source = (ROOT/'tools/j72-network-dhcp-hook.sh').read_text()
        for path in ['/sys/', '/bin/ip', '/etc/resolv.conf', '/run/lease-info']:
            source = source.replace(path, str(root)+path)
        hook = root/'hook.sh'; hook.write_text(source)
        base = {**os.environ, 'interface':'testwlan', 'ip':'192.0.2.5', 'subnet':'255.255.255.0', 'router':'192.0.2.1', 'dns':'192.0.2.53 192.0.2.54'}
        def run(event='bound', **extra):
            return subprocess.run(['sh', str(hook), event], env={**base, **extra}, capture_output=True)
        assert run().returncode == 0
        assert log.read_text().splitlines() == ['-4 address replace 192.0.2.5/24 dev testwlan', '-4 route replace default via 192.0.2.1 dev testwlan metric 600']
        assert (root/'etc/resolv.conf').read_text() == 'nameserver 192.0.2.53\nnameserver 192.0.2.54\n'
        for mask, bits in [('255.255.254.0',23), ('255.255.255.255',32), ('0.0.0.0',0)]:
            assert run('renew', subnet=mask).returncode == 0
            assert 'prefix='+str(bits)+'\n' in (root/'run/lease-info').read_text()
        for extra in [{'subnet':'255.0.255.0'}, {'subnet':'255.254.128.0'}, {'subnet':'255.255.255'}, {'interface':'usb0'}, {'interface':'../usb0'}, {'ip':'1;touch nope'}]:
            before = log.read_text()
            assert run(**extra).returncode != 0 and log.read_text() == before
        assert run('deconfig').returncode == 0 and not (root/'run/lease-info').exists()
        assert log.read_text().splitlines()[-2:] == ['-4 address flush dev testwlan', '-4 route flush dev testwlan']
    if '--logic-only' in sys.argv:
        print('PASS: WPA2 known vector/input validation and DHCP prefix/renewal/cleanup/failures; no device or host-network change.')
        return
    archive = n.WORK/'network-root.tar.gz'
    with n.serve(archive, '127.0.0.1', 0, '127.0.0.1') as url:
        try: urlopen(url+'/wrong', timeout=3)
        except HTTPError as e: assert e.code == 404
        else: raise AssertionError('Unexpected URL accepted')
        # Same static BusyBox executable as the iPad's bootstrap initramfs.
        busybox = n.WORK/'bootstrap-busybox'
        with tempfile.TemporaryDirectory(prefix='j72-transfer-test-') as d:
            target = Path(d)/'archive'
            r = subprocess.run(['busybox','wget','-Y','off','-q','-T','15','-O',str(target),url], executable=str(busybox), capture_output=True, timeout=25)
            assert r.returncode == 0, r.stderr
            assert hashlib.sha256(target.read_bytes()).digest() == hashlib.sha256(archive.read_bytes()).digest()
    print('PASS: WPA2 known vector/input validation; DHCP prefix/renewal/cleanup/failures; exact BusyBox private HTTP transfer. No iPad or host-network change.')

if __name__ == '__main__': main()
