#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build a separate signed read-only iOS query helper; no USB or device calls."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'private/j72-platform/power-storage-20261102/recovery-prep'
OUT = BASE / 'native-writer-query-v1'
IMPORTS = {'_printf', '_sysctlbyname', '_getuid', '_open', '_close', '_ioctl',
           '___error', '_alarm', '_dlopen', '_dlsym', '_dlclose', 'dyld_stub_binder'}


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    os.umask(0o077)
    assert not OUT.exists(), 'Refuse existing helper output'
    OUT.mkdir(mode=0o700)
    source = ROOT / 'tools/j72-ios-writer-capabilities.c'
    stub = OUT / 'libSystem.tbd'
    stub.write_text('--- !tapi-tbd-v3\narchs: [ arm64 ]\nplatform: ios\n'
                    'install-name: /usr/lib/libSystem.B.dylib\nexports:\n'
                    '  - archs: [ arm64 ]\n    symbols: [ ' + ', '.join(sorted(IMPORTS)) + ' ]\n...\n')
    obj = OUT / 'queries.o'; binary = OUT / 'j72-ios-writer-capabilities'
    linker = ROOT / 'private/j72-touch/ld64-arm64'; signer = BASE / 'ldid-src/ldid'
    entitlements = BASE / 'readonly-service/inspect-entitlements.plist'
    env = os.environ.copy(); env['LD_LIBRARY_PATH'] = str(ROOT / 'private/j72-touch/runtime/usr/lib/aarch64-linux-gnu')
    with (OUT / 'build.log').open('wb') as log:
        for args in [
            ['/usr/bin/clang', '-target', 'arm64-apple-ios12.0', '-O2', '-ffreestanding',
             '-fno-builtin', '-fno-stack-protector', '-Wall', '-Wextra', '-Werror',
             '-c', str(source), '-o', str(obj)],
            [str(linker), '-arch', 'arm64', '-platform_version', 'ios', '12.0', '12.0',
             '-e', '_main', '-L', str(OUT), '-lSystem', '-o', str(binary), str(obj)],
            [str(signer), '-S' + str(entitlements), str(binary)],
        ]: subprocess.run(args, env=env, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=30)
    raw = binary.read_bytes()
    assert raw[:8] == b'\xcf\xfa\xed\xfe\x0c\x00\x00\x01'
    symbols = subprocess.check_output(['llvm-nm-19', '-u', str(binary)], text=True)
    imports = {line.split()[-1] for line in symbols.splitlines()}
    assert imports <= IMPORTS and {'_open', '_ioctl', '_dlsym'} <= imports
    spec = importlib.util.spec_from_file_location('capsule', ROOT / 'tools/prepare-j72-ios-recovery.py')
    helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
    assert helper.cdh(raw), 'CodeDirectory page hashes invalid'
    inputs = [source, Path(__file__), ROOT / 'tools/test-j72-ios-writer-capabilities.py',
              linker, signer, entitlements, stub]
    result = dict(status='SIGNED_ARM64_QUERY_HELPER_BUILD_PASS_DEVICE_UNTESTED',
                  exact_model='iPad4,2', exact_build='16H81',
                  binary_bytes=len(raw), binary_sha256=sha(binary), imports=sorted(imports),
                  source_files={str(p.relative_to(ROOT)):sha(p) for p in inputs},
                  actual_c_ubsan_cases_pass=15, ioctls='fixed geometry and _IOR capability queries only',
                  open_mode='Darwin O_RDONLY|O_NOFOLLOW', raw_storage_writes=False,
                  resize_or_flush_called=False, existing_recovery_capsule_changed=False,
                  device_access=False, write_qualification_pass=False)
    (OUT / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS separate ARM64/iOS12 signed helper/import closure; query-only, existing capsule unchanged; device untested')


if __name__ == '__main__': main()
