#!/usr/bin/python3
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
BASE=Path('/usr/local/lib/orchard/j72-audio')
def run(argv):subprocess.run(argv,check=True,timeout=20)
def main():
 assert os.uname().release=='7.3.0-rc1-j72-pw1-orchard-apple-4k', 'kernel ABI differs'
 assert b'apple,j72' in Path('/proc/device-tree/compatible').read_bytes().split(b'\0'), 'not J72'
 manifest=json.loads((BASE/'manifest.json').read_text())
 for name,digest in manifest.items():assert hashlib.sha256((BASE/name).read_bytes()).hexdigest()==digest, name
 if '--mute' in sys.argv:
  if 'J72 Audio Test' in Path('/proc/asound/cards').read_text():run(['python3',str(BASE/'mute-controls.py')])
  return
 assert not Path('/sys/module/j72_audio_overlay').exists(), 'audio already loaded'
 firmware=Path('/lib/firmware/apple/s5l8960x-smartio.bin')
 assert firmware.is_symlink() and firmware.resolve()==BASE/'s5l8960x-smartio.bin', 'firmware path differs'
 for module in ('snd-soc-cs42l81','snd-soc-simple-card'):run(['modprobe',module])
 loaded=[]
 try:
  for module in ('virt-dma','apple-sio-core','apple-sio-dma','j72_mca','j72_audio_overlay'):
   if Path('/sys/module',module.replace('-','_')).exists():
    assert module=='virt-dma', 'unexpected preloaded driver: '+module
    continue
   argv=['insmod',str(BASE/(module+'.ko'))]
   if module=='j72_audio_overlay':argv.append('confirm_transport_only=1')
   run(argv);loaded.append(module.replace('-','_'))
  end=time.monotonic()+12
  while 'J72 Audio Test' not in Path('/proc/asound/cards').read_text():
   assert time.monotonic()<end,'ALSA card timeout'
   time.sleep(.1)
  run(['python3',str(BASE/'mute-controls.py')])
 except BaseException:
  for module in reversed(loaded):subprocess.run(['rmmod',module],timeout=15)
  raise
 print('J72 speakers ready; muted initial hardware volume -30dB',flush=True)
if __name__=='__main__':main()
