#!/usr/bin/env python3
"""Opt-in v3 J72 radio RAM-firmware test on an exact, already booted payload."""
import argparse,hashlib,importlib.util,json,os,shlex,signal,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'tools'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
h=load('v3_host','j72-wifi-v3-host.py');old=load('probe_utils','run-j72-wlan-enumeration-v2.py')
update=load('runtime_driver_update','j72_wifi_runtime_update.py')
P='/sys/module/j72_wlan_transport_v3/parameters/'
SNAP='/sys/module/j72_wlan_ready_snapshot/parameters/snapshot'
MODULE='lib/modules/7.0.12-j72spi2/extra/j72_wlan_transport_v3.ko'
DRIVER='lib/modules/7.0.12-j72spi2/kernel/drivers/net/wireless/broadcom/brcm80211/brcmfmac/brcmfmac.ko'
FW='lib/firmware/brcm/brcmfmac43241-j72-usb.bin'
def main():
 global h
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--storage35',action='store_true',help='Require the separately pinned combined #35 payload');g=p.add_mutually_exclusive_group(required=True);g.add_argument('--preflight',action='store_true');g.add_argument('--run',action='store_true');g.add_argument('--stop',action='store_true');args=p.parse_args()
 if args.storage35:h=load('storage35_host','j72-desktop-storage35-host.py')
 m=h.preflight(verify_desktop=False)
 runtime=({'old_boot_module_sha256':m['overlay_files'][DRIVER],'new_module_sha256':m['overlay_files'][DRIVER]} if args.storage35 else update.preflight(m))
 if args.preflight:return
 c=load('lock','run-j72-input-limit-hub1050-desktop.py').locked_ram(h.ram())
 assert c('uname -v',timeout=4).decode().strip()==m['uts_version']
 assert c('busybox cat /proc/device-tree/model',timeout=4).rstrip(b'\0\r\n')==b'Apple iPad Air (Cellular)'
 if args.run:
  c('test ! -d /sys/module/j72_wlan_enumeration_v2 && test ! -d /sys/module/j72_wlan_transport_v3 && test ! -d /sys/module/brcmfmac',timeout=4)
 for file in [MODULE,FW,'sbin/j72-start-brightness']:
  assert c('busybox sha256sum /'+file,timeout=4).decode().split()[0]==m['overlay_files'][file],file
 assert c('busybox sha256sum /'+DRIVER,timeout=4).decode().split()[0] in (runtime['old_boot_module_sha256'],runtime['new_module_sha256'])
 battery=dict(l.split('=',1) for l in c('busybox cat /sys/class/power_supply/j72-bq27545-battery/uevent',timeout=4).decode().splitlines() if '=' in l)
 if args.run:
  assert 3500000<=int(battery['POWER_SUPPLY_VOLTAGE_NOW'])<=4200000
  assert 200<=int(battery['POWER_SUPPLY_TEMP'])<=380
 os.umask(0o077);out=ROOT/('private/j72-platform/power-storage-20261102/desktop-storage35/wifi-captures' if args.storage35 else 'private/j72-platform/power-wifi-20261101/wifi-v3-captures')/time.strftime('%Y%m%d-%H%M%S');out.mkdir(parents=True)
 (out/'battery-before.json').write_text(json.dumps(battery,indent=2)+'\n')
 def save(name,command,timeout=5):
  raw=c(command,timeout=timeout);(out/name).write_bytes(raw);return raw
 # The same radio session can now host a RAM-resident desktop. Use its
 # matching teardown so binds and the marker are checked before removal.
 c('! busybox grep -q " /mnt/omarchy squashfs " /proc/mounts',timeout=4)
 if args.storage35 and args.run:
  c('if test ! -d /sys/module/j72_touch_session; then /sbin/j72-touch-session selfcheck; fi',timeout=25)
 save('stop-desktop.txt','if test -f /mnt/omarchy/.j72-ram-root; then /sbin/j72-ram-desktop-session stop; else /sbin/j72-desktop-session stop; fi; /sbin/j72-touch-session stop',35)
 c("test \"$(cat /sys/block/nbd2/size)\" = 0 && test \"$(cat /sys/module/j72_touch_session/parameters/session_state)\" = 0 && test \"$(cat /sys/module/j72_touch_session/parameters/cleanup_ok)\" = Y && test \"$(cat /sys/module/j72_touch_session/parameters/firmware_healthy)\" = 1",timeout=5)
 pid=h.server_pid(m['desktop_image'])
 if pid:
  os.killpg(pid,signal.SIGTERM);end=time.monotonic()+5
  while Path('/proc',str(pid)).exists() and time.monotonic()<end:time.sleep(.1)
  assert not Path('/proc',str(pid)).exists();h.PIDFILE.unlink()
 if c('if test -d /sys/module/j72_wlan_ready_snapshot; then echo Y; else echo N; fi',timeout=3).strip()==b'N':
  file=(h.WORK/'payload/rootfs/opt/j72/wlan-ready35.ko' if args.storage35 else ROOT/'private/j72-platform/power-wifi-20261101/wlan-ready-observer34/j72_wlan_ready_snapshot.ko');old.upload(c,h,file,'/run/j72-ready-observer.ko');c('insmod /run/j72-ready-observer.ko',timeout=4)
 def stop():
  # A userspace consumer must leave before the provider stops its bus.
  save('stop-network.txt',"busybox sh -ec 'if test -x /opt/j72-network/usr/sbin/j72-network; then for n in /sys/class/net/*; do test -e \"$n/phy80211\" || continue; busybox chroot /opt/j72-network /usr/sbin/j72-network stop \"${n##*/}\"; done; fi'",20)
  save('stop-request.txt','echo 1 > '+P+'stop',15)
  status=old.fields(save('stopped-status.txt','busybox cat '+P+'status'))
  after=old.fields(save('stopped-independent.txt','busybox cat '+SNAP))
  assert all(status[k]=='1' for k in ['restored','consumer_removed','gpio_released','phy_restored','reset_restored','hcd_stopped','controller_restored'])
  assert status['retain_controller']=='0'
  assert after['reg_0403']=='09' and after['reg_04c0']=='02' and after['host_ready_cfg']=='00072602' and after['device_ready_cfg']=='00070200'
  print('PASS: full provider stop and independent reset/GPIO/input-limit restoration')
 if args.stop:stop();return
 before=old.fields(save('independent-before.txt','busybox cat '+SNAP))
 assert before['reg_0403']=='09' and before['reg_04c0']=='02' and before['host_ready_cfg']=='00072602' and before['device_ready_cfg']=='00070200'
 # Update only the RAM file, while absent from /sys/module. The cold payload
 # and its original v3 module/source pins remain immutable on the host.
 if not args.storage35:update.stage(c,h,old.upload,runtime)
 (out/'runtime-driver.json').write_text(json.dumps(runtime,indent=2)+'\n')
 def detached(name,body):
  state='/run/j72-wifi-v3-'+name
  command=body+'; result=$?; printf "%s\\n" "$result" > '+state+'.result'
  spawn='busybox setsid busybox sh -c '+shlex.quote(command)+' </dev/null > '+state+'.log 2>&1 & echo $! > '+state+'.pid; echo STARTED'
  save(name+'-start.txt','busybox sh -ec '+shlex.quote(spawn))
  return state
 def wait(state,seconds):
  end=time.monotonic()+seconds
  while time.monotonic()<end:
   raw=c('if test -f '+state+'.result; then busybox cat '+state+'.result; else echo WAIT; fi',timeout=4).strip()
   if raw!=b'WAIT':return int(raw)
   time.sleep(.5)
  raise TimeoutError('Detached loader did not complete; preserve recovery path and private logs')
 state=detached('provider','insmod /'+MODULE+' confirm_native=1 keep_active=1')
 assert wait(state,30)==0
 status=old.fields(save('provider-status.txt','busybox cat '+P+'status'))
 assert c('busybox cat '+P+'session_active',timeout=3).strip()==b'Y'
 assert status['result']=='0' and status['rom_result']=='0' and status['rom_identity']=='00004324,00000006,00090000,60000000,00000000,00000000'
 print('PASS: exact v3 HSIC host and measured ROM identity; external recovery responds',flush=True)
 find="""busybox sh -ec '
found=
for d in /sys/bus/usb/devices/*; do
 [ -f "$d/idVendor" ] && [ -f "$d/idProduct" ] || continue
 if [ "$(cat "$d/idVendor")" = 0a5c ] && [ "$(cat "$d/idProduct")" = bd1c ]; then
  [ -z "$found" ]; found=${d##*/}
 fi
done
[ -n "$found" ]; echo "$found"
'"""
 device=c(find,timeout=4).decode().strip();assert device and all(x.isdigit() or x in '-.' for x in device)
 save('usb-descriptors.b64','busybox base64 /sys/bus/usb/devices/'+device+'/descriptors')
 interface=device+':1.0'
 c('test -d /sys/bus/usb/devices/'+interface,timeout=4)
 # Deliberate first-probe holdoff prevents the USB core from binding before
 # the WCC helper finishes registration, including implicit dependency loads.
 save('vendor-helper.txt','modprobe brcmfmac_wcc',15)
 c('test -d /sys/module/brcmfmac_wcc && test "$(cat /sys/module/brcmfmac/parameters/j72_bind)" = N',timeout=4)
 save('ready-before-firmware.txt','busybox cat '+SNAP)
 state=detached('firmware','echo 1 > /sys/module/brcmfmac/parameters/j72_bind; echo '+shlex.quote(interface)+' > /sys/bus/usb/drivers/brcmfmac/bind')
 rc=wait(state,15);(out/'bind-result.txt').write_text(str(rc)+'\n')
 # Firmware completion and reset/re-enumeration are asynchronous. A successful
 # sysfs bind does not prove firmware startup or a wireless interface.
 interface_name=''
 for i in range(40):
  raw=c("for n in /sys/class/net/*; do if test -e \"$n/phy80211\"; then echo \"${n##*/}\"; fi; done",timeout=4).decode().strip()
  save('kernel-progress.txt','dmesg | busybox tail -n 100')
  if raw:interface_name=raw;break
  time.sleep(1)
 save('provider-after.txt','busybox cat '+P+'status')
 save('independent-after.txt','busybox cat '+SNAP)
 save('kernel-after.txt','dmesg | busybox tail -n 180')
 save('modules-after.txt','busybox cat /proc/modules')
 (out/'result.json').write_text(json.dumps({'bind_returncode':rc,'wireless_interface':interface_name,'association_tested':False,'radio_owner_left_active':True},indent=2)+'\n')
 if interface_name:print('Wireless interface appeared:',interface_name,'; association is not yet tested.')
 else:print('No wireless interface yet. Preserve current boot for diagnosis; provider remains active.')
 print('Private evidence:',out)
if __name__=='__main__':main()
