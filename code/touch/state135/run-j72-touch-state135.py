#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Opt-in RAM staging before touch/radio on the pinned combined #35 boot."""
import argparse,hashlib,importlib.util,json,os,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'private/j72-platform/power-storage-20261102/touch-state135'
def load(name,file):
 spec=importlib.util.spec_from_file_location(name,ROOT/'tools'/file)
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
 g.add_argument('--preflight',action='store_true');g.add_argument('--stage',action='store_true');args=p.parse_args()
 os.umask(0o077)
 h=load('touch35_host','j72-desktop-storage35-host.py');boot=h.preflight(verify_desktop=False)
 m=json.loads((WORK/'manifest.json').read_text());module=WORK/'module/j72_touch_session.ko'
 assert m['status']=='OFFLINE_STATE1_BUILD_TESTS_IMPORTS_PASS_DEVICE_UNTESTED'
 assert m['uts_version']==boot['uts_version'] and sha(module)==m['module_sha256']
 for file,digest in m['files'].items():assert sha(ROOT/file)==digest,file
 assert m['recovery_timeout_cleanup_unchanged'] and m['active_states_unchanged'] and m['unknown_states_still_rejected']
 if args.preflight:print('PASS: original boot and separate state-1 candidate pins; no device contacted');return
 out=WORK/('stage-'+time.strftime('%Y%m%d-%H%M%S'));out.mkdir()
 c=load('touch35_lock','run-j72-input-limit-hub1050-desktop.py').locked_ram(h.ram())
 assert c('uname -v',timeout=4).decode().strip()==boot['uts_version']
 assert c('cat /proc/device-tree/model',timeout=4).rstrip(b'\0\r\n')==b'Apple iPad Air (Cellular)'
 c('test ! -d /sys/module/j72_touch_session && test ! -d /sys/module/j72_wlan_transport_v3 && test ! -d /sys/module/brcmfmac && test ! -d /sys/module/j72_charge_maintain35 && test "$(cat /sys/block/nbd2/size)" = 0 && ! busybox grep -q " /mnt/omarchy " /proc/mounts',timeout=5)
 original='opt/j72/j72_touch_session.ko'
 assert c('busybox sha256sum /'+original,timeout=5).decode().split()[0]==boot['overlay_files'][original]
 target='/run/j72-touch-state135.ko'
 load('touch35_upload','run-j72-wlan-enumeration-v2.py').upload(c,h,module,target)
 assert c('busybox sha256sum '+target,timeout=5).decode().split()[0]==m['module_sha256']
 # Loading creates the idle worker/sysfs only; no enabling or protocol traffic.
 (out/'load.txt').write_bytes(c('insmod '+target+' continuous=1 capture_seconds=3',timeout=6))
 prefix='/sys/module/j72_touch_session/parameters/'
 for name,value in [('contact_state1_policy','1'),('contact_state1_frames','0'),('phase_resync_policy','1'),('phase_resync_headers','0'),('phase_resync_frames','0'),('phase_resync_failures','0'),('session_state','0'),('session_number','0'),('enabled','N'),('continuous','Y'),('capture_seconds','3'),('recovery_stop_reason','0'),('hardware_cleanup_ok','N')]:
  actual=c('cat '+prefix+name,timeout=3).decode().strip();assert actual==value,(name,actual)
 assert c('busybox sha256sum /'+original,timeout=5).decode().split()[0]==boot['overlay_files'][original]
 (out/'selfcheck.txt').write_bytes(c('/sbin/j72-touch-session selfcheck',timeout=30))
 for name,value in [('session_state','0'),('cleanup_ok','Y'),('hardware_cleanup_ok','Y'),('firmware_healthy','1'),('recovery_stop_reason','0')]:
  actual=c('cat '+prefix+name,timeout=3).decode().strip();assert actual==value,(name,actual)
 (out/'result.json').write_text(json.dumps(dict(status='RAM_SELFCHECK_PASS_LONG_INPUT_UNQUALIFIED',candidate_sha256=m['module_sha256'],cold_boot_artifacts_unchanged=True,original_target_module_file_unchanged=True,touch_enabled=False,device_input_tested=False,storage_writes=False),indent=2)+'\n')
 print('PASS: distinct state-1 inactive RAM touch candidate passed existing start/stop selfcheck; idle and restored; long input still unqualified')
if __name__=='__main__':main()
