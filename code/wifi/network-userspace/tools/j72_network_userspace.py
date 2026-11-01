#!/usr/bin/env python3
"""Private RAM networking bundle verification and a single-file USB transfer."""
from contextlib import contextmanager
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import shlex
import threading

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'private/j72-platform/power-wifi-20261101/network-userspace'
REMOTE = '/opt/j72-network'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def preflight():
    m = json.loads((WORK / 'manifest.json').read_text())
    assert m['private_archive'] and m['owner_private_key_staged'] is False
    for name, digest in m['files'].items():
        assert sha(WORK / 'root' / name) == digest, name
    assert sha(WORK / 'network-root.tar.gz') == m['archive_sha256']
    for name, digest in m['runtime_scripts'].items():
        assert sha(ROOT / name) == digest, name
    smoke = json.loads((WORK / 'ssh-smoke-result.json').read_text())
    assert smoke['public_key_login'] and smoke['strict_host_key_checking']
    print('PASS: private RAM networking bundle and native SSH smoke pins; iPad networking untested')
    return m

@contextmanager
def serve(archive, address='10.0.0.1', port=10812, allowed='10.0.0.2'):
    """One exact random URL; no directory listing, request logging or LAN bind."""
    token = '/' + secrets.token_hex(24)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_GET(self):
            if self.client_address[0] != allowed or self.path != token:
                self.send_error(404)
                return
            self.connection.settimeout(15)
            self.send_response(200)
            self.send_header('Content-Length', str(archive.stat().st_size))
            self.send_header('Content-Type', 'application/octet-stream')
            self.end_headers()
            try:
                with archive.open('rb') as f:
                    while chunk := f.read(256 * 1024):
                        self.wfile.write(chunk)
            except (BrokenPipeError, ConnectionResetError, TimeoutError):
                pass
    server = ThreadingHTTPServer((address, port), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield 'http://' + address + ':' + str(server.server_port) + token
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
        assert not thread.is_alive()

def stage(command, m):
    # This root is the initramfs, not the NBD desktop or internal storage.
    command("busybox sh -ec 'case \"$(busybox stat -f -c %T /)\" in tmpfs|ramfs|rootfs) ;; *) exit 1;; esac; test ! -e /opt/j72-network; test ! -e /opt/j72-network.next; test \"$(busybox awk '\''/MemAvailable:/ {print $2}'\'' /proc/meminfo)\" -gt 102400'", timeout=4)
    archive = WORK / 'network-root.tar.gz'
    with serve(archive) as url:
        command('busybox wget -Y off -q -T 15 -O /run/j72-network.tar.gz.part ' + shlex.quote(url), timeout=35)
    assert command('busybox sha256sum /run/j72-network.tar.gz.part', timeout=4).decode().split()[0] == m['archive_sha256']
    command('busybox sh -ec ' + shlex.quote('mkdir -m 700 /opt/j72-network.next; busybox tar -xzf /run/j72-network.tar.gz.part -C /opt/j72-network.next; busybox mv /opt/j72-network.next ' + REMOTE + '; busybox rm /run/j72-network.tar.gz.part'), timeout=20)
    # Bind existing RAM pseudo filesystems; no block device is opened.
    command('busybox sh -ec ' + shlex.quote('mount -o bind /dev ' + REMOTE + '/dev; mount -o bind /proc ' + REMOTE + '/proc; mount -o bind /sys ' + REMOTE + '/sys; if test -d /dev/pts; then mkdir -p ' + REMOTE + '/dev/pts; mount -o bind /dev/pts ' + REMOTE + '/dev/pts; fi'), timeout=5)
    (manifest := WORK / 'target-hashes.txt').write_text(''.join(digest + '  ' + REMOTE + '/' + name + '\n' for name, digest in m['files'].items()))
    # The archive digest already covers ownership/modes, symlinks and all files.
    command('busybox chroot ' + REMOTE + ' /usr/bin/iw --version', timeout=4)

def wpa_config(ssid, passphrase=None, psk=None):
    """Explicit WPA2 personal profile; never guess country or emit passphrases."""
    ssid_bytes = ssid.encode('utf-8')
    if not 1 <= len(ssid_bytes) <= 32:
        raise ValueError('SSID must contain 1..32 UTF-8 bytes')
    if (passphrase is None) == (psk is None):
        raise ValueError('Provide exactly one passphrase or PSK')
    if passphrase is not None:
        raw = passphrase.encode('utf-8')
        if not 8 <= len(raw) <= 63:
            raise ValueError('WPA2 passphrase must contain 8..63 bytes')
        psk = hashlib.pbkdf2_hmac('sha1', raw, ssid_bytes, 4096, 32).hex()
    if len(psk) != 64 or any(c not in '0123456789abcdefABCDEF' for c in psk):
        raise ValueError('PSK must be 64 hex digits')
    return ('ctrl_interface=/run/wpa_supplicant\nupdate_config=0\np2p_disabled=1\nnetwork={\n'
            '\tssid=' + ssid_bytes.hex() + '\n\tpsk=' + psk.lower() +
            '\n\tkey_mgmt=WPA-PSK\n\tproto=RSN\n\tpairwise=CCMP\n}\n')
