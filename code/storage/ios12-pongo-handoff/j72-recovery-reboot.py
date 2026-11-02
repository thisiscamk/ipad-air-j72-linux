#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Request normal reboot only from an already inspected, pinned J72 RAM recovery."""
import argparse, fcntl, importlib.util, json, os, signal, socket, subprocess, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'private/j72-platform/power-storage-20261102/recovery-prep/pongo-route/handoff-v3'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def reboot(folder):
 if os.geteuid()!=0:raise RuntimeError('Use sudo for the restricted recovery transport')
 folder=folder.resolve()
 if folder.parent!=WORK or not folder.name.startswith('stage-'):raise RuntimeError('Wrong revision3 receipt directory')
 runner=load('handoff',ROOT/'tools/run-j72-pongo-recovery-handoff.py');runner.preflight()
 state=json.loads((folder/'state.json').read_text())
 if state.get('state')!='recovery_inspected' or state.get('manifest_sha256')!=runner.sha(WORK/'manifest.json'):raise RuntimeError('No completed matching inspection receipt')
 guard=json.loads((folder/'mount-guard.json').read_text())
 if guard.get('root_is_hfs_md0') is not True or guard.get('device_numbers_match')!=1 or guard.get('apfs_mounts')!=0:raise RuntimeError('Missing RAM device identity proof')
 transport=load('transport',ROOT/'tools/j72-recovery-inspect-live.py')
 os.umask(0o077)
 with (ROOT/'private/j72-usb.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);transport.target()
  out=folder/('shutdown-'+time.strftime('%Y%m%d-%H%M%S'));out.mkdir(mode=0o700)
  m=transport.load_inspector();attempt=m.Attempt(out)
  active=subprocess.run(['systemctl','is-active','--quiet','usbmuxd'],capture_output=True).returncode==0
  server=None
  with (out/'usbmuxd.log').open('wb') as log:
   try:
    subprocess.run(['systemctl','stop','usbmuxd'],check=True,timeout=15);transport.target()
    parent=str(ROOT/'tools/host/aarch64/bin/j72-parent-bound-exec')
    server=subprocess.Popen([parent,str(os.getpid()),'/usr/sbin/usbmuxd','-f','-p','-U','usbmux'],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    time.sleep(.5)
    if server.poll() is not None:raise RuntimeError('Temporary USB transport exited')
    with socket.socket() as sock:sock.bind(('127.0.0.1',2244))
    attempt.proxy_log=(out/'iproxy.log').open('wb')
    attempt.proxy=subprocess.Popen([parent,str(os.getpid()),str(m.WORK/'host-deps/root/usr/bin/iproxy'),'-l','-u',m.MARKER,'-s','127.0.0.1','2244:22'],stdout=attempt.proxy_log,stderr=subprocess.STDOUT,start_new_session=True)
    deadline=time.monotonic()+20
    while True:
     try:
      with socket.create_connection(('127.0.0.1',2244),timeout=1) as sock:
       if sock.recv(256).startswith(b'SSH-2.0-'):break
     except OSError:pass
     if attempt.proxy.poll() is not None or time.monotonic()>=deadline:raise RuntimeError('SSH transport not ready')
     time.sleep(.5)
    args=[x.replace('PubkeyAcceptedAlgorithms=+ssh-rsa','PubkeyAcceptedAlgorithms=ssh-rsa') if isinstance(x,str) else x for x in attempt.ssh_args()]
    raw=attempt.command(args+['reboot'],timeout=20,accepted=(0,255))
    rows=[json.loads(x[len(b'J72_GUARD_JSON '):]) for x in raw.splitlines() if x.startswith(b'J72_GUARD_JSON ')]
    if len(rows)!=1 or rows[0].get('root_is_hfs_md0') is not True or rows[0].get('bootargs_approved') is not True or rows[0].get('apfs_mounts')!=0 or b'J72 recovery reboot requested' not in raw:raise RuntimeError('Reboot acknowledgement and live RAM guard not received')
    (out/'result.json').write_text(json.dumps({'reboot_requested':True,'live_root_guard_pass':True,'storage_write_requested':False},indent=2)+'\n')
    print('Normal iOS reboot requested through the fixed authenticated recovery command.',flush=True)
   finally:
    attempt.close()
    if server:
     try:os.killpg(server.pid,signal.SIGTERM)
     except ProcessLookupError:pass
     try:server.wait(timeout=5)
     except subprocess.TimeoutExpired:os.killpg(server.pid,signal.SIGKILL);server.wait()
    if active:subprocess.run(['systemctl','start','usbmuxd'],check=True,timeout=15)
    print('Temporary USB groups reaped; original host service state restored.',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--receipt',type=Path,required=True);a=p.parse_args();reboot(a.receipt)
