#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Prepare a compressed desktop test on the proven #34 RAM boot; no device I/O."""
import hashlib, json, os, shutil, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'private/j72-platform/power-storage-20261102/compressed-root-prep'
OUT=WORK/'desktop-test34'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def main():
 os.umask(0o077)
 if OUT.exists():raise RuntimeError('Refuse existing compressed desktop candidate')
 capacity=json.loads((WORK/'result.json').read_text());module=json.loads((WORK/'module34-result.json').read_text())
 olddir=ROOT/'private/j72-platform/wifi-ram-desktop';old=json.loads((olddir/'manifest.json').read_text())
 image=WORK/'desktop-capacity.squashfs';ko=WORK/'squashfs-module34/squashfs.ko'
 assert capacity['status']=='OFFLINE_CAPACITY_PASS' and sha(image)==capacity['compressed_sha256']
 assert module['strong_imports_unresolved']==0 and sha(ko)==module['module_sha256']
 assert capacity['source_desktop_sha256']==old['desktop_sha256'] and capacity['compressed_bytes']==image.stat().st_size and image.stat().st_size%512==0
 pins=json.loads((WORK/'module34-inputs.json').read_text())['base_files']
 for name,value in pins.items():assert sha(ROOT/name)==value,name
 source=olddir/'overlay/sbin/j72-desktop-session'
 assert sha(source)==old['overlay_files']['sbin/j72-desktop-session']
 script=source.read_text()
 replacements={'busybox nbd-client 10.0.0.1 10811 /dev/nbd2':'busybox nbd-client 10.0.0.1 10831 /dev/nbd2',
  '= 6291456 ]':f'= {image.stat().st_size//512} ]',
  'mount -t ext4 -o ro,norecovery /dev/nbd2 "$root"':'mount -t squashfs -o ro /dev/nbd2 "$root"\n [ "$(busybox stat -f -c %T "$root")" = squashfs ] || return 1',
  'LANG=C.UTF-8 LC_ALL=C.UTF-8':'LANG=C.utf8 LC_ALL=C.utf8',
  'cp /etc/j72-session/autostart ':'cp /opt/j72-compressed/autostart '}
 for a,b in replacements.items():
  assert script.count(a)==1,a
  script=script.replace(a,b)
 OUT.mkdir(mode=0o700)
 (OUT/'controller.sh').write_text(script);(OUT/'controller.sh').chmod(0o755)
 (OUT/'autostart').write_text('''#!/bin/bash
set -eu
wlr-randr --output Unknown-1 --scale 2 --transform normal
omarchy-keyboard run > "$XDG_RUNTIME_DIR/keyboard-start.log" 2>&1 &
qs -p /opt/omarchy-ipad/shell/shell.qml > "$XDG_RUNTIME_DIR/quickshell.log" 2>&1 &
foot -d info --title='J72 compressed desktop' /bin/bash --noprofile --norc > "$XDG_RUNTIME_DIR/foot.log" 2>&1 &
printf 'started\\n' > "$XDG_RUNTIME_DIR/j72-shell-started"
''');(OUT/'autostart').chmod(0o755)
 shutil.copyfile(ko,OUT/'squashfs.ko');subprocess.run(['strip','--strip-debug',str(OUT/'squashfs.ko')],check=True)
 for name in ['controller.sh','autostart']:subprocess.run(['sh','-n',str(OUT/name)],check=True)
 sources=[Path(__file__),ROOT/'tools/run-j72-compressed-desktop.py',ROOT/'tools/prepare-j72-compressed-root.py',ROOT/'tools/run-j72-wlan-enumeration-v2.py',ROOT/'tools/j72-wifi-host.py',ROOT/'tools/run-j72-reader-audit.py',ROOT/'tools/run-j72-input-limit-hub1050-desktop.py',ROOT/'tools/preflight-j72-wifi-ram-boot.py',olddir/'manifest.json',source,WORK/'result.json',WORK/'module34-result.json']
 manifest={'profile':'j72-compressed-desktop34-v1','status':'OFFLINE_PREPARED_DEVICE_UNTESTED','kernel_build':old['uts_version'],'kernel_sha256':old['kernel_sha256'],'boot_payload':old['payload'],'boot_payload_sha256':old['payload_sha256'],'image':str(image),'image_bytes':image.stat().st_size,'image_sha256':sha(image),'nbd_port':10831,'nbd_device':'/dev/nbd2','nbd_read_only':True,'internal_storage_access':False,'charging_control_started':False,'writable_state':'RAM only','requires_usb_cable_until_stop':True,'files':{str(p.relative_to(ROOT)):sha(p) for p in sources+[image,OUT/'controller.sh',OUT/'autostart',OUT/'squashfs.ko']},'base_kernel_files':pins,'offline_imports_checked':module['strong_imports_checked'],'device_boot_tested':False}
 (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('PASS prepared compressed desktop: exact #34 module/kernel pins, read-only NBD image, portrait/locale runtime and shell syntax; no device accessed')
if __name__=='__main__':main()
