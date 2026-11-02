#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Read-only fixed-workload idle capture before any charging module is loaded."""
import argparse,importlib.util,json,os,time
from pathlib import Path
from j72_observation_health import fields,StopObservation,scoped_shell
ROOT=Path(__file__).resolve().parents[1]
BODY=r'''
test -f /run/j72/desktop-ready
test "$(cat /sys/block/nbd2/size)" = 0
! busybox grep -Eq '^/dev/(nbd|sd|mmc|nvme|asp|dm|mapper)' /proc/mounts
for p in /sys/module/j72_input_limit* /sys/module/j72_charge_maintain*; do test ! -d "$p"; done
if test -d /sys/module/asp; then echo asp=present; else echo asp=absent; fi
p=/sys/module/j72_touch_session/parameters
for k in session_state input_frames xfer_errors recovery_stop_reason; do printf 'touch_%s=' "$k"; cat "$p/$k"; done
printf 'governor='; cat /sys/devices/system/cpu/cpufreq/policy0/scaling_governor
selected=
for b in /sys/class/backlight/*; do
 test -r "$b/device/of_node/compatible" || continue
 if busybox tr '\000' '\n' < "$b/device/of_node/compatible" | busybox grep -qx apple,anya-pmic-bl; then test -z "$selected"; selected=$b; fi
done
test -n "$selected"; printf 'brightness='; cat "$selected/actual_brightness"
for k in CAPACITY TEMP VOLTAGE_NOW CURRENT_NOW; do
 printf 'battery_%s=' "$k"
 busybox sed -n "s/^POWER_SUPPLY_${k}=//p" /sys/class/power_supply/j72-bq27545-battery/uevent
done
'''
def load(name,file):
 spec=importlib.util.spec_from_file_location(name,ROOT/'tools'/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--preflight',action='store_true');p.add_argument('--seconds',type=int,choices=[300,600],default=300);p.add_argument('--asp',choices=['absent','present']);p.add_argument('--brightness',type=int,choices=[802,1604],default=802);a=p.parse_args()
 h=load('idle_host','j72-desktop-storage35-host.py');h.preflight(verify_desktop=False)
 if a.preflight:print('PASS: idle recorder inputs only; no device contacted');return
 if a.asp is None:p.error('--asp is required for an actual capture')
 os.umask(0o077);work=ROOT/'private/j72-platform/power-storage-20261102/observation35-prep';work.mkdir(mode=0o700,exist_ok=True);out=work/('idle-'+a.asp+'-'+time.strftime('%Y%m%d-%H%M%S'));out.mkdir()
 wifi=load('idle_wifi','j72_wifi_ssh.py');start=time.monotonic();count=0;failure=None
 try:
  with (out/'samples.jsonl').open('w') as stream:
   while time.monotonic()-start<a.seconds:
    row=fields(wifi.command(scoped_shell(BODY),timeout=12))
    for k,v in dict(asp=a.asp,touch_session_state='2',touch_xfer_errors='0',touch_recovery_stop_reason='0',governor='schedutil',brightness=str(a.brightness)).items():
     if row.get(k)!=v:raise StopObservation('Idle workload changed: '+k)
    if int(row['touch_input_frames'])<10 or not 10<=int(row['battery_CAPACITY'])<=100 or abs(int(row['battery_CURRENT_NOW']))>1500000:raise StopObservation('Invalid idle battery/input reading')
    stream.write(json.dumps(dict(elapsed_s=round(time.monotonic()-start,3),readings=row))+'\n');stream.flush();count+=1;time.sleep(10)
 except BaseException as exc:failure=type(exc).__name__+': '+str(exc)
 finally:
  (out/'result.json').write_text(json.dumps(dict(status='ABORTED' if failure else 'READ_ONLY_IDLE_CAPTURE_COMPLETE',reason=failure,samples=count,asp=a.asp,brightness=a.brightness,observed_s=round(time.monotonic()-start,3),capture_requires_no_charging_module=True,settings_changed=False,causal_power_saving_proved=False,gauge_cache_or_identical_updates_may_repeat=True,storage_writes=False),indent=2)+'\n')
 if failure:raise StopObservation(failure)
 print('Idle capture saved privately; compare temperature/SOC/time drift before interpretation:',out)
if __name__=='__main__':main()
