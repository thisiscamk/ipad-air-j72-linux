#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Supervise the explicit voltage-hold restart candidate using Wi-Fi health.

No DFU, brightness/current/governor changes or new charging implementation.
--preflight is host-only. --observe invokes the original opt-in charge watch.
"""
import argparse,importlib.util,json,os,signal,subprocess,sys,time
from pathlib import Path
from j72_observation_health import Health,StopObservation,fields,restored,scoped_shell
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'private/j72-platform/power-storage-20261102/voltage-resume35/resync-observations'
COLLECT=r'''
t=/sys/module/j72_touch_session/parameters
for k in session_state session_number enabled continuous capture_seconds input_frames input_recoveries input_bad_layouts input_timeouts wire_anomalies xfer_errors recovery_stop_reason; do
 printf 'touch_%s=' "$k"; cat "$t/$k"
done
for k in phase_resync_policy phase_resync_headers phase_resync_frames phase_resync_failures; do
 printf 'touch_%s=' "$k"; cat "$t/$k"
done
cat /sys/module/j72_charge_maintain35/parameters/status | busybox sed 's/^/charge_/'
printf 'nbd_blocks='; cat /sys/block/nbd2/size
if busybox grep -Eq '^/dev/(nbd|sd|mmc|nvme|asp|dm|mapper)' /proc/mounts; then echo native_mounts=1; else echo native_mounts=0; fi
if test -f /run/j72/desktop-ready; then echo desktop_ready=1; else echo desktop_ready=0; fi
printf 'wifi_state='
busybox chroot /opt/j72-network /usr/bin/wpa_cli -p /run/wpa_supplicant -i wlan0 status | busybox sed -n 's/^wpa_state=//p'
printf 'governor='; cat /sys/devices/system/cpu/cpufreq/policy0/scaling_governor
selected=
for b in /sys/class/backlight/*; do
 test -r "$b/device/of_node/compatible" || continue
 if busybox tr '\000' '\n' < "$b/device/of_node/compatible" | busybox grep -qx apple,anya-pmic-bl; then
  test -z "$selected"; selected=$b
 fi
done
test -n "$selected"; test "$(cat "$selected/max_brightness")" = 2047
printf 'brightness='; cat "$selected/actual_brightness"
for k in CAPACITY TEMP VOLTAGE_NOW; do
 printf 'battery_%s=' "$k"
 busybox sed -n "s/^POWER_SUPPLY_${k}=//p" /sys/class/power_supply/j72-bq27545-battery/uevent
done
'''
FINAL=r'''
cat /sys/module/j72_charge_maintain35/parameters/status
cat /sys/module/j72_wlan_ready_snapshot/parameters/snapshot | busybox grep '^reg_04c0='
'''

def load(name,file):
 spec=importlib.util.spec_from_file_location(name,ROOT/'tools'/file)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


class ObserverSignals:
    """Turn the first INT/TERM into cleanup; defer repeat signals during cleanup."""
    def __init__(self):
        self.closing=False
        self.previous={}
    def __enter__(self):
        for sig in (signal.SIGINT,signal.SIGTERM):
            self.previous[sig]=signal.signal(sig,self.interrupt)
        return self
    def interrupt(self,signum,frame):
        if not self.closing:raise KeyboardInterrupt('observation signal '+str(signum))
    def __exit__(self,*unused):
        for sig,handler in self.previous.items():signal.signal(sig,handler)


def stop_child(process):
    """Interrupt our process group so the existing watch can run its finally."""
    if process.poll() is None:
        os.killpg(process.pid,signal.SIGINT)
        try:process.wait(timeout=18)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid,signal.SIGTERM)
            try:process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=3)
            raise StopObservation('Charging watch did not complete graceful cleanup; verify hardware')
    else:process.wait()


def policy_health(row):
 if row.get('touch_phase_resync_policy')!='1':raise StopObservation('Wrong touch resync policy')
 for key in ('touch_phase_resync_headers','touch_phase_resync_frames','touch_phase_resync_failures'):
  value=row.get(key,'')
  if not value.isascii() or not value.isdecimal():raise StopObservation('Invalid resync counter '+key)
 if row.get('charge_resume_policy')!='1':raise StopObservation('Wrong voltage-hold restart policy')
 if row.get('charge_thermal_latched') not in ('0','1'):raise StopObservation('Missing thermal latch status')
 if row.get('charge_last_pause') not in tuple(str(i) for i in range(7)):raise StopObservation('Invalid pause status')
 value=row.get('charge_warm_full_resumes','')
 if not value.isascii() or not value.isdecimal():raise StopObservation('Invalid warm-restart count')


def main():
 p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
 g.add_argument('--preflight',action='store_true');g.add_argument('--observe',action='store_true')
 p.add_argument('--seconds',type=int,choices=[3600,5400],default=5400)
 p.add_argument('--brightness',type=int,choices=[802,1604],default=802)
 a=p.parse_args();os.umask(0o077)
 for tool,args in [('run-j72-touch-resync35.py',['--preflight']),('run-j72-voltage-resume35.py',['preflight'])]:
  subprocess.run([sys.executable,str(ROOT/'tools'/tool),*args],check=True,timeout=30)
 if a.preflight:print('PASS: batched observation inputs; no device contacted');return
 wifi=load('observation_wifi','j72_wifi_ssh.py');health=Health(a.brightness)
 first=fields(wifi.command(scoped_shell(COLLECT),timeout=12));policy_health(first);health.check(first,initial=True)
 WORK.mkdir(mode=0o700,exist_ok=True);out=WORK/('capture-'+time.strftime('%Y%m%d-%H%M%S'));out.mkdir()
 (out/'initial.json').write_text(json.dumps(first,indent=2)+'\n')
 # Informational only: never change the radio's power policy mid-measurement.
 try:(out/'wifi-power-save.txt').write_bytes(wifi.command('busybox chroot /opt/j72-network /usr/bin/iw dev wlan0 get power_save',timeout=8))
 except Exception:(out/'wifi-power-save.txt').write_text('Query unavailable; no setting changed\n')
 started=time.monotonic();process=None;failure=None;clean=False;last=first
 with ObserverSignals() as signals:
  try:
   with (out/'charge-watch.log').open('wb') as log, (out/'health.jsonl').open('w') as samples:
    process=subprocess.Popen([sys.executable,str(ROOT/'tools/run-j72-voltage-resume35.py'),'watch','--seconds',str(a.seconds)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    while process.poll() is None:
     if time.monotonic()-started>a.seconds+30:raise StopObservation('Charging watch exceeded its bounded deadline')
     last=fields(wifi.command(scoped_shell(COLLECT),timeout=12));policy_health(last);health.check(last)
     samples.write(json.dumps(dict(elapsed_s=round(time.monotonic()-started,3),health=last))+'\n');samples.flush()
     time.sleep(10)
    if process.wait()!=0:raise StopObservation('Existing charging watch exited unsuccessfully; inspect its log')
  except BaseException as exc:
   failure=type(exc).__name__+': '+str(exc)
  finally:
   signals.closing=True
   if process is not None:
    try:stop_child(process)
    except Exception as exc:failure=(failure or '')+'; '+str(exc)
   try:
    (out/'last-health.json').write_text(json.dumps(last,indent=2)+'\n')
   except Exception as exc:failure=(failure or '')+'; saving last health: '+str(exc)
   try:
    final=fields(wifi.command(scoped_shell(FINAL),timeout=12));restored(final);clean=True
    (out/'independent-final.json').write_text(json.dumps(final,indent=2)+'\n')
   except Exception as exc:failure=(failure or '')+'; restoration verification: '+str(exc)
   # Export the stable ring only after a stopped/failed touch session. Never
   # interrupt active input to get a snapshot or relax its export guard.
   try:
    state=wifi.command('cat /sys/module/j72_touch_session/parameters/session_state',timeout=5).strip()
    if state in (b'0',b'4'):
     (out/'touch-anomalies.bin').write_bytes(wifi.command('busybox cat /sys/kernel/j72_touch_session_anomalies',timeout=12))
     (out/'touch-kernel.txt').write_bytes(wifi.command('dmesg | busybox tail -n 180',timeout=8))
   except Exception as exc:(out/'capture-error.txt').write_text(str(exc)+'\n')
   (out/'result.json').write_text(json.dumps(dict(status='ABORTED' if failure else 'WATCH_AND_HEALTH_COMPLETE_ANALYSIS_PENDING',reason=failure,independent_restoration_verified=clean,observation_s=round(time.monotonic()-started,3),brightness=a.brightness,workload_settings_changed=False,native_charger_classification_qualified=False,net_gain_or_restart_claimed=False,device_storage_writes=False,restart_policy_changed=True,touch_resync_changed=True),indent=2)+'\n')
 if failure:raise StopObservation(failure)
 print('PASS: bounded health/watch complete; analyze fresh current vectors separately. Private receipt:',out)
if __name__=='__main__':main()
