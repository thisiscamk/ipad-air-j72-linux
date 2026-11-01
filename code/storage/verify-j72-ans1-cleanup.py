#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Reproduce an imported ANS1 cleanup defect with host stubs, never hardware.

Original ANS1 code: Nick Chan / Hoolock m1n1, SPDX MIT, imported by Orchard.
The tested function is extracted from the public pinned patch at runtime.
This does not qualify initialization, DMA, storage reads, or an entire loader.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import resource
import subprocess
import tempfile

IMPORT = 'boot/m1n1/patches/hoolock/0032-Add-ANS1-storage.patch'
IMPORT_SHA = '9522985e68957b0906d8ef1b7b0fb224ec54cb4e7132ab2bb6cad110b7548b40'
PRELUDE = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
static int a, b, c, sleep_calls, rtkit_free_calls, power_off_calls, free_calls;
static bool ans1_initialized = true, ans1_ready = true;
static void *cmd = &a, *ans1_akf = &b, *ans1_rtkit = &c;
static void *freed[2];
static void tracked_free(void *ptr) {
    for (int i = 0; i < free_calls; i++) assert(ptr != freed[i]);
    assert(free_calls < 2);
    freed[free_calls++] = ptr;
}
static void rtkit_sleep(void *ptr) { assert(ptr == &c); sleep_calls++; }
static void rtkit_free(void *ptr) { assert(ptr == &c); rtkit_free_calls++; }
static void pmgr_adt_power_disable(const char *path) { assert(path); power_off_calls++; }
#define free tracked_free
'''
MAIN = r'''
int main(void) {
    ans1_shutdown();
    assert(free_calls == 2 && freed[0] == &a && freed[1] == &b);
    assert(sleep_calls == 1 && rtkit_free_calls == 1 && power_off_calls == 1);
    assert(!ans1_initialized && !ans1_ready);
    ans1_shutdown();
    assert(free_calls == 2 && sleep_calls == 1 && rtkit_free_calls == 1 && power_off_calls == 1);
    return 0;
}
'''


def no_core_dump():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def function(text):
    found = re.search(r'^void ans1_shutdown\(void\)\n\{.*?^\}', text, re.S | re.M)
    if not found:
        raise ValueError('ANS1 cleanup function missing')
    return found.group() + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--orchard-tree', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    args = parser.parse_args()
    data = (args.orchard_tree / IMPORT).read_bytes()
    if hashlib.sha256(data).hexdigest() != IMPORT_SHA:
        parser.error('changed upstream import: review the candidate against the new source')
    part = data.decode().split('diff --git a/src/ans1.c b/src/ans1.c\n', 1)[1].split('\ndiff --git ', 1)[0]
    source = '\n'.join(line[1:] for line in part.splitlines()
                       if line.startswith('+') and not line.startswith('+++')) + '\n'
    results = {}
    with tempfile.TemporaryDirectory(prefix='j72-ans1-cleanup-') as temporary:
        directory = Path(temporary)
        (directory / 'src').mkdir()
        path = directory / 'src/ans1.c'
        path.write_text(source)
        subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-i', str(args.candidate.resolve())],
                       cwd=directory, check=True, capture_output=True, timeout=30)
        for name, text in (('imported', source), ('candidate', path.read_text())):
            test = directory / f'{name}.c'
            test.write_text(PRELUDE + function(text) + MAIN)
            binary = directory / name
            subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                            '-fsanitize=undefined', str(test), '-o', str(binary)],
                           check=True, capture_output=True, timeout=60)
            result = subprocess.run([str(binary)], capture_output=True, timeout=5,
                                    preexec_fn=no_core_dump)
            results[name] = result.returncode
            if name == 'imported' and not (result.returncode == -6 and
                                          b'ptr != freed[i]' in result.stderr):
                raise ValueError('baseline did not reproduce the expected duplicate-free assertion')
            if name == 'candidate' and result.returncode != 0:
                raise ValueError('candidate cleanup failed')
    print(json.dumps({'baseline_duplicate_free_reproduced': True,
                      'candidate_frees_each_allocation_once': True,
                      'repeat_shutdown_returns_without_extra_cleanup': True,
                      'ubsan_candidate_pass': True, 'hardware_tested': False,
                      'return_codes': results}, indent=2))


if __name__ == '__main__':
    main()
