#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build the read-only Pongo probe locally. No USB calls or system installs."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'private/j72-platform/power-storage-20261102/recovery-prep'
WORK=BASE/'pongo-route'

def load(name,file):
    spec=importlib.util.spec_from_file_location(name,file)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def run(argv,env=None):
    p=subprocess.run(list(map(str,argv)),capture_output=True,timeout=45,env=env)
    with (WORK/'build.log').open('ab') as log:log.write(p.stdout+p.stderr)
    if p.returncode:raise RuntimeError('Offline build command failed; inspect private build.log')

def main():
    os.umask(0o077);WORK.mkdir(exist_ok=True)
    builder=load('image_builder',ROOT/'tools/prepare-j72-ios-recovery.py')
    fw=builder.firmware() # Exact J72/16H81 Apple BuildManifest digest checks.
    probe=load('probe_host',ROOT/'tools/run-j72-pongo-recovery-probe.py')
    assert probe.sha(probe.PONGO)=='1e5543fd8e6dbd84c334b87d71aa473f4d347c2ba8a5e863b6e10f18461c7575'
    assert probe.sha(ROOT/'tools/host/aarch64/bin/checkra1n-0.1337.3')=='078053c11e9a301f0e71b87b6b854e6c8a69c87972325dd0c90deeeba1c3cb70'
    with tempfile.TemporaryDirectory(prefix='kernel-dec-',dir=WORK) as tmp:
        run([ROOT/'tools/host/aarch64/bin/ipsw','kernel','dec',fw['KernelCache'],'-o',tmp])
        outputs=list(Path(tmp).iterdir());assert len(outputs)==1 and outputs[0].is_file()
        probe.kernel_uuid(outputs[0]);shutil.copyfile(outputs[0],WORK/'kernel.original.dec')
    source=ROOT/'tools/j72-pongo-recovery-probe.c';obj=WORK/'j72-recovery-probe.o'
    run(['/usr/bin/clang','-target','arm64-apple-ios12.0','-O2','-ffreestanding','-fno-builtin',
         '-fno-stack-protector','-Wall','-Wextra','-Werror','-c',source,'-o',obj])
    ld=ROOT/'private/j72-touch/ld64-arm64'
    libs=ROOT/'private/j72-touch/runtime/usr/lib/aarch64-linux-gnu'
    env=os.environ.copy();env['LD_LIBRARY_PATH']=str(libs)
    # LLVM 19's -kext is unimplemented; use the already tested native Apple linker.
    run([ld,'-arch','arm64','-kext','-static','-ios_version_min','12.0','-o',probe.MODULE,obj],env=env)
    imports=probe.module_imports(probe.MODULE)
    sources=[source,ROOT/'tools/j72-pongo-recovery-bounds.h',Path(__file__).resolve(),
             ROOT/'tools/run-j72-pongo-recovery-probe.py',ROOT/'tools/test-j72-pongo-recovery-probe.py',
             ROOT/'tools/j72-pongo-boot.py',ROOT/'tools/j72_usb_path.py']
    binaries=[probe.PONGOTERM,probe.PARENT,ROOT/'tools/host/aarch64/bin/checkra1n-0.1337.3',
              ROOT/'tools/host/aarch64/bin/ipsw',Path('/usr/bin/clang'),ld,
              libs/'libcrypto.so.1.1',libs/'libBlocksRuntime.so.0']
    def relative(p):return str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)
    files={relative(p):probe.sha(p) for p in sources+binaries+[
        probe.MODULE,probe.PONGO,WORK/'kernel.original.dec',fw['KernelCache']]}
    native=[]
    for p in binaries:
        raw=p.read_bytes()[:64]
        assert raw[:6]==b'\x7fELF\x02\x01' and struct.unpack_from('<H',raw,18)[0]==183
        native.append(relative(p))
    manifest={'profile':'j72-pongo-readonly-recovery-probe-v1','pongo_source_pin':'e98323f8a09abd80fc4cbcd74dee023b91a1ec22',
              'product':'iPad4,2','cpid':0x8960,'bdid':0x12,'ios_build':'16H81',
              'expected_kernel_uuid':probe.kernel_uuid(WORK/'kernel.original.dec'),
              'files':files,'host_elf':native,'module_imports':imports,
              'raw_storage_interface':False,'automatic_boot':False,'kernel_patch_interface':False,
              'runtime_tested':False}
    (WORK/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    probe.check()

if __name__=='__main__':main()
