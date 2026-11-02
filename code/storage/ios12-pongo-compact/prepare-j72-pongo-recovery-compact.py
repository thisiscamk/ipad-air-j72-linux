#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build and pin the compact observer offline; no device or system changes."""
import hashlib, importlib.util, json, os, struct, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'private/j72-platform/power-storage-20261102/recovery-prep/pongo-route/compact-v2'
def main():
    os.umask(0o077);WORK.mkdir(exist_ok=True)
    s=importlib.util.spec_from_file_location('legacy',ROOT/'tools/run-j72-pongo-recovery-probe.py')
    legacy=importlib.util.module_from_spec(s);s.loader.exec_module(legacy)
    original=legacy.check()
    source=ROOT/'tools/j72-pongo-recovery-compact.c';obj=WORK/'j72-recovery-compact.o';module=WORK/'j72-recovery-compact.kext'
    linker=ROOT/'private/j72-touch/ld64-arm64';libs=ROOT/'private/j72-touch/runtime/usr/lib/aarch64-linux-gnu'
    env=os.environ.copy();env['LD_LIBRARY_PATH']=str(libs)
    with (WORK/'build.log').open('wb') as log:
        for argv in [
          ['/usr/bin/clang','-target','arm64-apple-ios12.0','-O2','-ffreestanding','-fno-builtin','-fno-stack-protector','-Wall','-Wextra','-Werror','-c',str(source),'-o',str(obj)],
          [str(linker),'-arch','arm64','-kext','-static','-ios_version_min','12.0','-o',str(module),str(obj)]]:
            subprocess.run(argv,stdout=log,stderr=log,env=env,check=True,timeout=45)
    imports=legacy.module_imports(module)
    # Check actual flat-image export pointer pairs, not string presence alone.
    image=legacy.PONGO.read_bytes()
    for name in imports:
        offset=image.find(name.encode()+b'\0');assert offset>=0
        pair=image.find(struct.pack('<Q',0x100000000+offset));assert pair>=0
        pointer=struct.unpack_from('<Q',image,pair+8)[0]
        assert 0x100000000<=pointer<0x100100000
    files=dict(original['files'])
    additions=[source,ROOT/'tools/j72_pongo_control.py',ROOT/'tools/run-j72-pongo-recovery-compact.py',
               ROOT/'tools/prepare-j72-pongo-recovery-compact.py',ROOT/'tools/test-j72-pongo-recovery-compact.py',
               module,Path('/lib/aarch64-linux-gnu/libusb-1.0.so.0')]
    for p in additions:files[str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)]=legacy.sha(p)
    raw=additions[-1].read_bytes();assert raw[:6]==b'\x7fELF\x02\x01' and struct.unpack_from('<H',raw,18)[0]==183
    manifest={'profile':'j72-pongo-readonly-recovery-compact-v2','files':files,
              'expected_kernel_uuid':original['expected_kernel_uuid'],'module_imports':imports,
              'device_output_bound':2047,'pongo_ring_capacity':4095,
              'console_control_read_length':4096,'read_stdout_while_command_active':False,
              'automatic_boot':False,'kernel_patch_interface':False,'raw_storage_interface':False,
              'runtime_tested':False}
    (WORK/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('PASS offline compact native build, actual Pongo export pointers and input pins')
if __name__=='__main__':main()
