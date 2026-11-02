#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Inspect the exact running RAM recovery using temporary no-preflight usbmuxd.

No boot, filesystem mount or storage-write command. The normal host service is
restored after the bounded inspector and all temporary process groups are reaped.
"""
import argparse, fcntl, importlib.util, os, signal, subprocess, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'private/j72-platform/power-storage-20261102/recovery-prep'
MARKER='J72_RO_RECOVERY_V1'
def load_inspector():
 s=importlib.util.spec_from_file_location('recovery',ROOT/'tools/boot-j72-ios-recovery.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def target():
 found=[]
 for p in Path('/sys/bus/usb/devices').iterdir():
  try:
   if (p/'idVendor').read_text().strip()=='05ac':found.append(p)
  except FileNotFoundError:pass
 if len(found)!=1 or (found[0]/'idProduct').read_text().strip()!='12ab' or (found[0]/'serial').read_text().strip()!=MARKER:raise RuntimeError('Exact unique RAM recovery USB marker absent')
 from j72_usb_path import require_direct_pi
 require_direct_pi(found[0])
def inspect_live(receipt):
 if os.geteuid()!=0:raise RuntimeError('Use sudo for the temporary RAM recovery transport')
 folder=receipt.resolve()
 if folder.parent.parent!=BASE/'pongo-route' or folder.parent.name not in ('handoff-v1','handoff-v2') or not folder.name.startswith('stage-'):raise RuntimeError('Not this candidate stage receipt')
 os.umask(0o077)
 with (ROOT/'private/j72-usb.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  deadline=time.monotonic()+90
  while True:
   try:target();break
   except RuntimeError:
    if time.monotonic()>=deadline:raise RuntimeError('RAM recovery marker not observed; no normal-iOS SSH fallback')
    time.sleep(.5)
  m=load_inspector()
  active=subprocess.run(['/usr/bin/systemctl','is-active','--quiet','usbmuxd'],capture_output=True).returncode==0
  server=None;attempt=m.Attempt(folder)
  original_args=attempt.ssh_args
  def legacy_rsa_args():
   args=original_args()
   args=[x.replace('PubkeyAcceptedAlgorithms=+ssh-rsa','PubkeyAcceptedAlgorithms=ssh-rsa') if isinstance(x,str) else x for x in args]
   return args[:-1]+['-vvv',args[-1]]
  attempt.ssh_args=legacy_rsa_args
  log=(folder/('usbmuxd-no-preflight-'+time.strftime('%H%M%S')+'.log')).open('wb')
  try:
   subprocess.run(['/usr/bin/systemctl','stop','usbmuxd'],check=True,timeout=15)
   target()
   server=subprocess.Popen([str(ROOT/'tools/host/aarch64/bin/j72-parent-bound-exec'),str(os.getpid()),'/usr/sbin/usbmuxd','-f','-p','-U','usbmux'],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   time.sleep(.5)
   if server.poll() is not None:raise RuntimeError('Temporary recovery usbmuxd exited')
   attempt.inspect()
  finally:
   attempt.close()
   if server:
    try:os.killpg(server.pid,signal.SIGTERM)
    except ProcessLookupError:pass
    try:server.wait(timeout=5)
    except subprocess.TimeoutExpired:
     os.killpg(server.pid,signal.SIGKILL);server.wait()
   log.close()
   if active:subprocess.run(['/usr/bin/systemctl','start','usbmuxd'],check=True,timeout=15)
   print('Temporary recovery proxies reaped; normal usbmuxd service restored.' if active else 'Temporary recovery proxies reaped; original inactive host service preserved.',flush=True)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--receipt',type=Path,required=True);a=p.parse_args();inspect_live(a.receipt)
if __name__=='__main__':main()
