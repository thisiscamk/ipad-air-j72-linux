#!/usr/bin/python3
"""J72-only hardware ordering before the unchanged NetworkManager service.

The exact kernel provider owns PHY/reset/EHCI and checks the measured ROM.
This unit does not associate, configure addresses, or manage credentials.
"""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time

P=Path('/sys/module/j72_wlan_transport_v3/parameters')
assert os.getuid()==0
assert b'apple,j72\0' in Path('/proc/device-tree/compatible').read_bytes()
def fields():
 return dict(l.split('=',1) for l in (P/'status').read_text().splitlines() if '=' in l)
def checked_active():
 v=fields()
 assert (P/'session_active').read_text().strip()=='Y'
 assert v['result']=='0' and v['rom_result']=='0'
 assert v['rom_identity']=='00004324,00000006,00090000,60000000,00000000,00000000'
 return v
def wireless():
 return [p for p in Path('/sys/class/net').iterdir() if (p/'phy80211').exists()]
def command(argv,bound=45):
 p=subprocess.run(argv,capture_output=True,timeout=bound)
 if p.returncode:
  sys.stderr.write(p.stderr.decode(errors='replace')[-1000:])
 assert p.returncode==0,argv[0]
mode=sys.argv[1];assert mode in ('start','stop')
if mode=='stop':
 if not P.exists():raise SystemExit(0)
 if (P/'session_active').read_text().strip()=='Y':(P/'stop').write_text('1\n')
 v=fields()
 assert v['retain_controller']=='0'
 for key in ('restored','consumer_removed','gpio_released','phy_restored','reset_restored','hcd_stopped','controller_restored'):
  assert v[key]=='1',(key,v[key])
 print('J72 Wi-Fi transport stopped and restored')
 raise SystemExit(0)
meta=json.loads(Path('/etc/orchard/j72-hardware.json').read_text())
assert os.uname().release==meta['kernel_release']
assert hashlib.sha256(Path('/usr/lib/firmware/brcm/brcmfmac43241-j72-usb.bin').read_bytes()).hexdigest()==meta['wifi_firmware_sha256']
if P.exists():
 checked_active()
else:
 assert not Path('/sys/module/brcmfmac').exists(),'Do not retry an earlier partial probe'
 command(['modprobe','j72_wlan_transport_v3','confirm_native=1','keep_active=1'])
 checked_active()
if not wireless():
 devices=[p for p in Path('/sys/bus/usb/devices').iterdir() if (p/'idVendor').is_file() and (p/'idVendor').read_text().strip()=='0a5c' and (p/'idProduct').read_text().strip()=='bd1c']
 assert len(devices)==1
 interface=devices[0].name+':1.0'
 command(['modprobe','brcmfmac_wcc'])
 assert (Path('/sys/module/brcmfmac/parameters/j72_bind')).read_text().strip()=='N'
 Path('/sys/module/brcmfmac/parameters/j72_bind').write_text('1\n')
 Path('/sys/bus/usb/drivers/brcmfmac/bind').write_text(interface+'\n')
 until=time.monotonic()+50
 while not wireless():
  assert time.monotonic()<until,'No WLAN after firmware; do not reset or retry'
  time.sleep(1)
assert len(wireless())==1
print('J72 Wi-Fi interface ready for NetworkManager')
