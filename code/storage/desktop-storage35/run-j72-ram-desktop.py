#!/usr/bin/env python3
"""Stage/start a private RAM-only desktop on the already-running exact #34 boot."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import signal
import tarfile
import time

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'private/j72-platform/power-wifi-20261101/ram-desktop-plan'
TARGET='/opt/j72-ramdesktop'
def load(name,file):
    s=importlib.util.spec_from_file_location(name,ROOT/'tools'/file)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['preflight','stage','start']);p.add_argument('--storage35',action='store_true',help='Require the separately pinned combined #35 payload');a=p.parse_args()
    os.umask(0o077);m=json.loads((WORK/'build-manifest.json').read_text());archive=WORK/'ram-desktop-root.tar.gz'
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==m['archive_sha256']
    fixes=WORK/'locale-repair/locale-data.tar.gz'
    fixes_manifest=json.loads((WORK/'locale-repair/manifest.json').read_text())
    assert fixes_manifest['read_only_image_match']
    assert hashlib.sha256(fixes.read_bytes()).hexdigest()==fixes_manifest['archive_sha256']
    assert m['all_selected_files_match_image'] and m['uid1000_version_smoke'] and m['dbus_uid1000_smoke']
    with tarfile.open(archive) as tar:
        for entry in tar:
            assert not entry.name.startswith('/') and '..' not in entry.name.split('/'),entry.name
    if a.action=='preflight':print('PASS: private RAM archive/hash/path/version/D-Bus gates; no device contacted');return
    h=load('host','j72-wifi-v3-host.py');c=load('lock','run-j72-input-limit-hub1050-desktop.py').locked_ram(h.ram())
    wifi=load('wifi','j72_wifi_ssh.py');network=load('network','j72_network_userspace.py')
    expected=(load('storage35','j72-desktop-storage35-host.py').preflight(verify_desktop=False) if a.storage35 else json.loads((ROOT/'private/j72-platform/wifi-desktop-v3/manifest.json').read_text()))
    assert c('uname -v',timeout=4).decode().strip()==expected['uts_version']
    wifi.command('test "$(cat /sys/module/j72_wlan_transport_v3/parameters/session_active)" = Y; echo WIFI_RECOVERY_READY',timeout=5)
    out=WORK/('live-'+a.action+'-'+time.strftime('%Y%m%d-%H%M%S'));out.mkdir()
    if a.action=='stage':
        assert c('busybox stat -f -c %T /',timeout=4).strip()==b'tmpfs'
        c('test ! -e '+TARGET+' && test ! -e /run/j72-ram-stage',timeout=4)
        (out/'before.txt').write_bytes(c('/sbin/j72-touch-session status; busybox cat /proc/meminfo; busybox cat /proc/mounts',timeout=5))
        # All charging workers are terminal before disturbing the workload.
        c("for p in /sys/module/j72_input_limit*/parameters; do test -f \"$p/status\" || continue; busybox grep -qx active=0 \"$p/status\" || exit 1; busybox grep -qx armed=0 \"$p/status\" || exit 1; done",timeout=5)
        (out/'old-desktop-stop.txt').write_bytes(c('/sbin/j72-desktop-session stop; /sbin/j72-touch-session stop',timeout=35))
        c('test "$(cat /sys/block/nbd2/size)" = 0 && ! busybox grep -q " /mnt/omarchy " /proc/mounts && test "$(cat /sys/module/j72_touch_session/parameters/session_state)" = 0 && test "$(cat /sys/module/j72_touch_session/parameters/cleanup_ok)" = Y && test "$(cat /sys/module/j72_touch_session/parameters/firmware_healthy)" = 1',timeout=5)
        pid=h.server_pid(expected['desktop_image'])
        if pid:
            os.killpg(pid,signal.SIGTERM);end=time.monotonic()+5
            while Path('/proc',str(pid)).exists() and time.monotonic()<end:time.sleep(.1)
            assert not Path('/proc',str(pid)).exists();h.PIDFILE.unlink()
        info=c('busybox grep MemAvailable /proc/meminfo',timeout=4).split();available=int(info[1])*1024
        assert available>m['regular_bytes']+m['archive_bytes']+128*1024*1024,'Insufficient measured headroom; retain Wi-Fi recovery'
        blocks,size=map(int,c('busybox stat -f -c "%a %S" /',timeout=4).split())
        assert blocks*size>m['regular_bytes']+32*1024*1024,'Initramfs filesystem capacity too small'
        c('busybox mkdir -m 700 /run/j72-ram-stage; mount -t tmpfs -o size=128m,mode=700 tmpfs /run/j72-ram-stage',timeout=5)
        with network.serve(archive) as url:
            c('busybox wget -Y off -q -T 15 -O /run/j72-ram-stage/root.tar.gz '+shlex.quote(url),timeout=45)
        assert c('busybox sha256sum /run/j72-ram-stage/root.tar.gz',timeout=5).decode().split()[0]==m['archive_sha256']
        c('busybox mkdir -m 755 '+TARGET+'; busybox tar -xzf /run/j72-ram-stage/root.tar.gz -C '+TARGET,timeout=45)
        c('busybox rm /run/j72-ram-stage/root.tar.gz; umount /run/j72-ram-stage; busybox rmdir /run/j72-ram-stage',timeout=5)
        c('busybox touch '+TARGET+'/etc/resolv.conf; chmod 644 '+TARGET+'/etc/resolv.conf; echo '+m['archive_sha256']+' > '+TARGET+'/.j72-ram-root',timeout=5)
        load('locale_uploader','run-j72-wlan-enumeration-v2.py').upload(c,h,fixes,'/run/j72-locale-repair.tar.gz')
        c('busybox tar -xzf /run/j72-locale-repair.tar.gz -C '+TARGET+'; busybox rm /run/j72-locale-repair.tar.gz',timeout=5)
        # Recorded live qualifications of the first subset: labwc launches
        # autostart through /bin/sh, and curl needs trusted CA data as well as
        # its ELF closure. Keep the sealed archive unchanged; apply RAM fixes.
        c('test -x '+TARGET+'/usr/bin/bash; if test ! -e '+TARGET+'/usr/bin/sh; then busybox ln -s bash '+TARGET+'/usr/bin/sh; fi; '
          'test -s /opt/j72-network/etc/ssl/certs/ca-certificates.crt; busybox mkdir -p '+TARGET+'/etc/ssl/certs; '
          'busybox cp /opt/j72-network/etc/ssl/certs/ca-certificates.crt '+TARGET+'/etc/ssl/certs/ca-certificates.crt; '
          'busybox chmod 644 '+TARGET+'/etc/ssl/certs/ca-certificates.crt; '
          'busybox chroot '+TARGET+' /bin/sh -c "echo SHELL_READY"',timeout=5)
        # Derive the same known desktop lifecycle, replacing only its block
        # transport. The original NBD controller remains available for fallback.
        script=c('busybox cat /sbin/j72-desktop-session',timeout=5).decode()
        (out/'original-nbd-controller.sh').write_text(script)
        start=script.index(' i=0\n until busybox nbd-client ')
        end=script.index(' for path in dev dev/pts dev/shm proc sys;',start)
        script=script[:start]+' mount --bind '+TARGET+' "$root"\n'+script[end:]
        script=script.replace(' if [ "$(cat /sys/block/nbd2/size)" != 0 ]; then busybox nbd-client -d /dev/nbd2; fi\n','')
        assert 'nbd-client' not in script
        script=script.replace(' if mounted "$root"; then',' if mounted "$root"; then\n  [ "$(cat "$root/.j72-ram-root")" = '+m['archive_sha256']+' ] || return 1',1)
        (out/'ram-controller.sh').write_text(script)
        load('uploader','run-j72-wlan-enumeration-v2.py').upload(c,h,out/'ram-controller.sh','/sbin/j72-ram-desktop-session')
        c('chmod 755 /sbin/j72-ram-desktop-session; busybox sh -n /sbin/j72-ram-desktop-session',timeout=5)
        (out/'memory-after.txt').write_bytes(c('busybox cat /proc/meminfo; busybox cat /proc/mounts',timeout=5))
        print('PASS: archive verified/deployed to initramfs, old NBD/export detached, matching RAM controller staged; no GUI started',flush=True)
        return
    c('test "$(cat '+TARGET+'/.j72-ram-root)" = '+m['archive_sha256']+' && test "$(cat /sys/block/nbd2/size)" = 0 && ! busybox grep -q " /mnt/omarchy " /proc/mounts',timeout=5)
    body='/sbin/j72-touch-session selfcheck && /sbin/j72-touch-session start && /sbin/j72-ram-desktop-session start'
    spawn='busybox setsid busybox sh -ec '+shlex.quote(body)+' </dev/null >/run/j72-ram-desktop-start.log 2>&1 & echo $! >/run/j72-ram-desktop-start.pid; echo STARTED'
    c('busybox sh -ec '+shlex.quote(spawn),timeout=5)
    for _ in range(60):
        state=c('if test -f /run/j72/desktop-ready; then echo READY; else echo WAIT; fi',timeout=4).strip()
        if state==b'READY':break
        time.sleep(1)
    else:
        (out/'startup-log.txt').write_bytes(c('busybox cat /run/j72-ram-desktop-start.log; busybox tail -n 50 /run/j72/labwc.log',timeout=5))
        raise RuntimeError('RAM desktop not ready; retain current boot and inspect private logs')
    c('test "$(cat /sys/block/nbd2/size)" = 0 && test "$(cat /mnt/omarchy/.j72-ram-root)" = '+m['archive_sha256'],timeout=5)
    (out/'status.txt').write_bytes(c('/sbin/j72-touch-session status; busybox cat /proc/meminfo; busybox cat /proc/mounts',timeout=5))
    print('RAM desktop startup reports ready; NBD remains detached. Process, memory and owner UI checks still required.')
if __name__=='__main__':main()
