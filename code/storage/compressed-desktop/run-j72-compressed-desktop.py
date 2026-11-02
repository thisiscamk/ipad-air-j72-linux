#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Preflight, start or stop the read-only compressed desktop on exact #34 RAM Linux."""
import argparse, hashlib, importlib.util, json, os, shlex, signal, socket, subprocess, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'private/j72-platform/power-storage-20261102/compressed-root-prep/desktop-test34'
PIDFILE=WORK/'export.json'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def load(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'tools'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def preflight():
 m=json.loads((WORK/'manifest.json').read_text())
 if m['profile']!='j72-compressed-desktop34-v1' or m['internal_storage_access'] or not m['nbd_read_only'] or m['nbd_device']!='/dev/nbd2' or m['nbd_port']!=10831:raise RuntimeError('Wrong compressed desktop profile')
 if m['kernel_build']!='#34 SMP PREEMPT Sun Nov  1 07:40:27 +08 2026':raise RuntimeError('Wrong kernel build')
 for group in ['files','base_kernel_files']:
  for name,digest in m[group].items():
   if sha(ROOT/name)!=digest:raise RuntimeError('Compressed test source/input changed: '+name)
 if sha(Path(m['boot_payload']))!=m['boot_payload_sha256']:raise RuntimeError('Proven boot payload changed')
 print('PASS offline: compressed image/module/controller/source and exact proven #34 kernel pins; no device access',flush=True)
 return m
def export_pid(m):
 if not PIDFILE.exists():return None
 record=json.loads(PIDFILE.read_text());pid=record['pid'];p=Path('/proc')/str(pid)
 if not p.exists():return None
 args=(p/'cmdline').read_bytes().split(b'\0')
 if p.stat().st_uid!=os.geteuid() or os.getpgid(pid)!=pid or int((p/'stat').read_text().split()[21])!=record['start_ticks']:raise RuntimeError('Stale export process identity')
 if not args or Path(os.fsdecode(args[0])).name!='qemu-nbd' or os.fsencode(m['image']) not in args or b'--read-only' not in args or b'10831' not in args:raise RuntimeError('Export process does not match this candidate')
 return pid
def configure_usb():
 found=[]
 for p in Path('/sys/class/net').iterdir():
  if not (p/'device').exists():continue
  for parent in (p/'device').resolve().parents:
   try:
    if (parent/'idVendor').read_text().strip()=='1d6b' and (parent/'idProduct').read_text().strip()=='0104':found.append(p.name);break
   except FileNotFoundError:pass
 if len(found)!=1:raise RuntimeError('Expected exactly one RAM Linux gadget network interface')
 subprocess.run(['nmcli','device','set',found[0],'managed','no'],check=True,capture_output=True,timeout=10)
 subprocess.run(['ip','addr','replace','10.0.0.1/24','dev',found[0]],check=True,timeout=5)
 subprocess.run(['ip','link','set',found[0],'up'],check=True,timeout=5)
def main():
 p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group();g.add_argument('--run',action='store_true');g.add_argument('--stop',action='store_true');a=p.parse_args()
 os.umask(0o077);m=preflight()
 if not(a.run or a.stop):return
 if os.geteuid()!=0:raise RuntimeError('Use sudo for this private image/export and USB setup')
 configure_usb();host=load('network_host','j72-wifi-host.py');raw=load('locked_shell','run-j72-input-limit-hub1050-desktop.py').locked_ram(host.ram())
 def c(script,timeout=15):return raw('busybox sh -ec '+shlex.quote(script),timeout=timeout)
 if c('uname -v',4).decode().strip()!=m['kernel_build'] or c('cat /proc/device-tree/model',4).rstrip(b'\0\n')!=b'Apple iPad Air (Cellular)':raise RuntimeError('Wrong live RAM target')
 c('test "$(busybox stat -f -c %T /)" = tmpfs',4)
 out=WORK/(('stop-' if a.stop else 'run-')+time.strftime('%Y%m%d-%H%M%S'));out.mkdir(mode=0o700)
 if a.stop:
  (out/'target-stop.txt').write_bytes(c('/sbin/j72-compressed-desktop-session stop; /sbin/j72-touch-session stop',40))
  c('test "$(cat /sys/block/nbd2/size)" = 0; ! busybox grep -q " /mnt/omarchy " /proc/mounts; test "$(cat /sys/module/j72_touch_session/parameters/cleanup_ok)" = Y',5)
  pid=export_pid(m)
  if pid:
   os.killpg(pid,signal.SIGTERM);deadline=time.monotonic()+5
   while Path('/proc',str(pid)).exists() and time.monotonic()<deadline:time.sleep(.1)
   if Path('/proc',str(pid)).exists():raise RuntimeError('Detached export did not exit')
  PIDFILE.unlink(missing_ok=True);print('Compressed desktop unmounted, NBD detached, touch cleaned up and owned host export stopped.',flush=True);return
 c('test "$(cat /sys/block/nbd2/size)" = 0; ! busybox grep -q " /mnt/omarchy " /proc/mounts; test ! -e /opt/j72-compressed; test ! -d /sys/module/squashfs; test "$(cat /sys/module/j72_touch_session/parameters/session_state)" = 0',5)
 (out/'before.txt').write_bytes(c('cat /proc/meminfo; /sbin/j72-touch-session status || true',5))
 available=int(c('busybox grep MemAvailable /proc/meminfo',4).split()[1])*1024
 if available<256*1024**2:raise RuntimeError('Insufficient RAM headroom before desktop')
 if export_pid(m):raise RuntimeError('This export is already running; inspect/stop it first')
 with socket.socket() as sock:sock.bind(('10.0.0.1',10831))
 c('mkdir -m 700 /opt/j72-compressed',4)
 uploader=load('uploader','run-j72-wlan-enumeration-v2.py')
 for name,target in [('squashfs.ko','/opt/j72-compressed/squashfs.ko'),('autostart','/opt/j72-compressed/autostart'),('controller.sh','/sbin/j72-compressed-desktop-session')]:uploader.upload(c,host,WORK/name,target)
 c('chmod 755 /opt/j72-compressed/autostart /sbin/j72-compressed-desktop-session; busybox sh -n /sbin/j72-compressed-desktop-session; insmod /opt/j72-compressed/squashfs.ko; busybox grep -q squashfs /proc/filesystems',10)
 with (out/'qemu-nbd.log').open('wb') as log:
  server=subprocess.Popen(['qemu-nbd','--read-only','--format=raw','--bind=10.0.0.1','--port','10831','--persistent',m['image']],stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
  record={'pid':server.pid,'start_ticks':int(Path('/proc',str(server.pid),'stat').read_text().split()[21]),'image_sha256':m['image_sha256']}
  PIDFILE.write_text(json.dumps(record)+'\n');time.sleep(.3)
  if server.poll() is not None:raise RuntimeError('Read-only export exited; inspect private log')
 body='/sbin/j72-touch-session selfcheck && /sbin/j72-touch-session start && /sbin/j72-start-brightness && /sbin/j72-compressed-desktop-session start'
 c('busybox setsid busybox sh -ec '+shlex.quote(body)+' </dev/null >/run/j72-compressed-start.log 2>&1 & echo $! >/run/j72-compressed-start.pid',5)
 print('Compressed read-only export started; preparing RAM desktop. Keep USB connected until --stop.',flush=True)
 for _ in range(100):
  if c('if test -f /run/j72/desktop-ready; then echo READY; else echo WAIT; fi',5).strip()==b'READY':break
  time.sleep(1)
 else:
  (out/'startup-log.txt').write_bytes(c('cat /run/j72-compressed-start.log; busybox tail -n 40 /run/j72/labwc.log',5))
  raise RuntimeError('Desktop did not become ready; keep USB/export for inspection, no repeated DFU')
 c('busybox grep -q " /mnt/omarchy squashfs ro," /proc/mounts; test "$(cat /sys/block/nbd2/ro)" = 1; test "$(cat /sys/block/nbd2/size)" = '+str(m['image_bytes']//512),5)
 (out/'ready.txt').write_bytes(c('cat /proc/meminfo; cat /proc/mounts; /sbin/j72-touch-session status',5))
 print('PASS target reports compressed desktop ready on read-only NBD/SquashFS. Owner menu/keyboard check required; keep USB connected.',flush=True)
if __name__=='__main__':main()
