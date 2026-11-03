#!/usr/bin/env python3
"""Opt-in #35 voltage-hold restart candidate; no general source detection.

Initial/thermal/window starts still need 36.5 C; voltage-only restarts may
use the unchanged active temperature range through 38 C. Device untested.
"""
import argparse, importlib.util, json, os, shlex, subprocess, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'private/j72-platform/power-storage-20261102/voltage-resume35'
SOURCE=WORK.parent/'qualified-hub-source35.json'
NAME='j72_charge_maintain35'
PARAM='/sys/module/'+NAME+'/parameters/'
SNAP='/sys/module/j72_wlan_ready_snapshot/parameters/snapshot'
def load(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'tools'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('action',choices=['preflight','stage','status','watch','stop','requalify'])
 p.add_argument('--seconds',type=int,default=3600,help='Bounded host observation window; always stop/verify at end')
 a=p.parse_args();os.umask(0o077)
 assert 1<=a.seconds<=43200
 h=load('h','j72-desktop-storage35-host.py');u=load('u','run-j72-wlan-enumeration-v2.py');lock=load('lock','run-j72-input-limit-hub1050-desktop.py')
 m=json.loads((WORK/'manifest.json').read_text())
 base=h.preflight(verify_desktop=False)
 assert m['uts_version']==base['uts_version'] and WORK.name=='voltage-resume35'
 assert 'tools/run-j72-voltage-resume35.py' in m['files']
 for name,digest in m['files'].items():assert h.sha(ROOT/name)==digest,name
 assert m['nominal_mA']==1050 and m['unchanged_active_limits'] and m['strong_imports_resolved']
 if a.action=='preflight':print('PASS: voltage-hold candidate pins; restart policy changed, hard limits unchanged; no device access');return
 c=lock.locked_ram(h.ram())
 assert c('uname -v',timeout=4).decode().strip()==m['uts_version']
 assert c('busybox cat /proc/device-tree/model',timeout=4).rstrip(b'\0\r\n')==b'Apple iPad Air (Cellular)'
 def status():
  value=u.fields(c('busybox cat '+PARAM+'status',timeout=3))
  assert value.get('resume_policy')=='1', 'Different loaded charging policy'
  return value
 def snapshot():return u.fields(c('busybox cat '+SNAP,timeout=3))
 def stop():
  c('echo stop > '+PARAM+'arm_hub',timeout=4)
  s=status();v=snapshot()
  assert s['enabled']=='0' and s['active']=='0' and s['restore_failed']=='0' and v['reg_04c0']=='02'
  if int(s['cycles']):assert s['restored']=='1'
  return {'worker':s,'independent':v}
 if a.action=='stage':
  # No other input-limit/maintenance owner may share PMIC 04c0.
  names=c('for p in /sys/module/j72_input_limit* /sys/module/j72_charge_maintain*; do test ! -d "$p" || echo "$p"; done',timeout=4).decode().splitlines()
  assert not names,names
  assert snapshot()['reg_04c0']=='02'
  u.upload(c,h,WORK/'module'/ (NAME+'.ko'),'/run/'+NAME+'.ko')
  c('insmod /run/'+NAME+'.ko',timeout=8)
  s=status();assert all(s[k]==v for k,v in {'ready':'1','enabled':'0','active':'0','armed':'0','fault':'0','cycles':'0'}.items())
  assert snapshot()['reg_04c0']=='02'
  (WORK/'staged-boot-id.txt').write_bytes(c('busybox cat /proc/sys/kernel/random/boot_id',timeout=3))
  print('PASS: exact maintenance worker loaded DISABLED, no PMIC change');return
 assert c('busybox cat /proc/sys/kernel/random/boot_id',timeout=3)==(WORK/'staged-boot-id.txt').read_bytes()
 if a.action=='status':print(json.dumps({'worker':status(),'independent':snapshot()},indent=2));return
 if a.action=='stop':
  result=stop();(WORK/'manual-stop.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS: disabled and independently restored');return
 source=json.loads(SOURCE.read_text())
 assert source['model']=='JCH377' and source['ios_reported_adapter_mA']==1500 and source['ios_reported_adapter_mV']==5000 and source['ios_IsCharging']
 assert h.sha(ROOT/source['ios_capture'])==source['ios_capture_sha256']
 lock.verify_hub(source) # BEFORE lease/arming/any current override.
 # Require proven RAM root and an interactive, connected Wi-Fi desktop.
 ramwork=ROOT/'private/j72-platform/power-wifi-20261101/ram-desktop-plan'
 rm=json.loads((ramwork/'build-manifest.json').read_text());digest=shlex.quote(rm['archive_sha256'])
 checks=('test -f /run/j72/desktop-ready; '
         'test "$(cat /sys/module/j72_touch_session/parameters/session_state)" = 2; '
         'test "$(cat /sys/module/j72_wlan_transport_v3/parameters/session_active)" = Y; '
         'test "$(cat /mnt/omarchy/.j72-ram-root)" = '+digest+'; '
         'test "$(cat /opt/j72-ramdesktop/.j72-ram-root)" = '+digest+'; '
         'test "$(cat /sys/block/nbd2/size)" = 0; '
         '! busybox grep -Eq "^/dev/(nbd|sd|mmc|nvme|asp|dm|mapper)" /proc/mounts; '
         'test "$(busybox stat -f -c %T /mnt/omarchy)" = tmpfs')
 c('busybox sh -ec '+shlex.quote(checks),timeout=4)
 bundle=json.loads((ROOT/'private/j72-platform/wifi-desktop-v3/manifest.json').read_text())
 assert h.server_pid(bundle['desktop_image']) is None
 assert not (WORK.parent/'desktop-storage35/container-desktop/export.json').exists(), 'Normal container/export cleanup required first'
 c('busybox chroot /opt/j72-network /usr/bin/wpa_cli -p /run/wpa_supplicant -i wlan0 status | busybox grep -qx wpa_state=COMPLETED',timeout=4)
 if a.action=='requalify':
  s=status();assert s['enabled']=='0' and s['fault']=='1' and s['active']=='0' and s['restore_failed']=='0' and snapshot()['reg_04c0']=='02'
  c('echo qualified-JCH377-1500mA > '+PARAM+'source_lease',timeout=3)
  c('echo requalify-verified-restoration > '+PARAM+'requalify_source',timeout=6)
  s=status();assert s['fault']=='0' and s['enabled']=='0' and s['active']=='0' and snapshot()['reg_04c0']=='02'
  print('PASS: explicitly requalified after fresh source/battery/baseline checks; remains DISABLED');return
 s=status();assert s['enabled']=='0' and s['fault']=='0' and s['active']=='0' and snapshot()['reg_04c0']=='02'
 out=WORK/('capture-'+time.strftime('%Y%m%d-%H%M%S'));out.mkdir()
 started=False;start=time.monotonic();ended_by='host_deadline'
 try:
  started=True
  c('echo qualified-JCH377-1500mA > '+PARAM+'source_lease',timeout=3)
  c('echo maintain-qualified-JCH377 > '+PARAM+'arm_hub',timeout=3)
  c('echo begin-qualified-maintenance > '+PARAM+'begin_session',timeout=3)
  last=-1
  with (out/'samples.jsonl').open('w') as f:
   while time.monotonic()-start<a.seconds:
    lock.verify_hub(source)
    c('echo qualified-JCH377-1500mA > '+PARAM+'source_lease',timeout=3)
    s=status();elapsed=time.monotonic()-start
    f.write(json.dumps({'elapsed_s':round(elapsed,3),'worker':s})+'\n');f.flush()
    if s['fault']=='1':ended_by='kernel_fault';break
    if elapsed>8 and s['enabled']!='1':ended_by='controller_disabled';break
    if int(elapsed)//15!=last:
     last=int(elapsed)//15
     print('Maintenance:',round(elapsed),'s mode',s['mode'],'active',s['active'],'cycles',s['cycles'],'SOC',s['guard_soc'],'temperature',s['guard_temp_tenthC'],'voltage',s['guard_voltage_uV'],flush=True)
    time.sleep(.35)
 except BaseException:
  ended_by='host_error_or_interrupt';raise
 finally:
  if started:
   result=stop();result.update(ended_by=ended_by,observed_controller_s=round(time.monotonic()-start,3))
   (out/'final.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Bounded maintenance observation ended; independently restored:',out)
if __name__=='__main__':main()
