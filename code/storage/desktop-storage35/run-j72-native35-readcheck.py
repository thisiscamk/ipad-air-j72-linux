#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Opt-in #35 ASP probe after a same-boot firmware inventory, or bounded reads."""
import argparse
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import time

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'private/j72-platform/power-storage-20261102/desktop-storage35'


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['preflight', 'probe', 'check'])
    p.add_argument('--receipt', type=Path, help='Same-boot inventory directory for probe, completed probe directory for check')
    a = p.parse_args()
    os.umask(0o077)
    h = load('h35', 'j72-desktop-storage35-host.py')
    manifest = h.preflight(verify_desktop=False)
    if a.action == 'preflight':
        print('PASS: fixed read-only ASP input and explicit same-boot receipt required; no device contacted')
        return
    assert a.receipt, 'Explicit same-boot receipt is required'
    receipt = a.receipt.resolve()
    assert receipt.is_relative_to(WORK) and receipt.is_dir(), 'Receipt must stay in the private candidate directory'
    previous = json.loads((receipt / 'result.json').read_text())
    assert previous['uts_version'] == manifest['uts_version']
    if a.action == 'probe':
        for key in ('firmware_metadata_valid', 'loader_dram_extent_verified', 'kernel_nomap_reservation_verified'):
            assert previous[key] is True, key
        assert previous['asp_loaded'] is False and previous['internal_writes'] is False
    else:
        assert previous['probe_pass'] is True and previous['device_read_only'] is True
    raw = load('lock', 'run-j72-input-limit-hub1050-desktop.py').locked_ram(h.ram())
    guard = ('test "$(uname -v)" = ' + shlex.quote(manifest['uts_version']) +
             '; test "$(cat /proc/sys/kernel/random/boot_id)" = ' + shlex.quote(previous['boot_id']) +
             '; test "$(cat /proc/device-tree/model)" = "Apple iPad Air (Cellular)"; ')

    def c(body, timeout=5):
        return raw('busybox sh -ec ' + shlex.quote(guard + body), timeout=timeout)

    # A fresh directory and fixed /run names cannot overwrite internal files.
    out = WORK / (('probe-' if a.action == 'probe' else 'readcheck-') + time.strftime('%Y%m%d-%H%M%S'))
    out.mkdir()
    ram = '/run/j72-native35-' + out.name
    c('test "$(busybox stat -f -c %T /run)" = tmpfs; mkdir -m 700 ' + ram)
    if a.action == 'probe':
        c('test ! -d /sys/module/asp; '
          'test ! -d /sys/module/j72_charge_maintain35; '
          'test "$(busybox stat -f -c %T /run)" = tmpfs', 5)
        digest = c('busybox sha256sum /opt/j72/asp-readonly.ko').decode().split()[0]
        assert digest == manifest['overlay_files']['opt/j72/asp-readonly.ko']
        body = ('insmod /opt/j72/asp-readonly.ko confirm_j72_readonly=1 enable_reformat=0; '
                'rc=$?; echo "$rc" > ' + ram + '/probe.result')
        # Do not kill/unload a timed-out kernel probe: retained DMA needs reboot.
        spawn = ('busybox setsid busybox sh -c ' + shlex.quote(body) +
                 ' </dev/null >' + ram + '/probe.log 2>&1 & echo $! >' + ram + '/probe.pid')
        c(spawn)
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            state = c('if test -f ' + ram + '/probe.result; then cat ' + ram + '/probe.result; else echo WAIT; fi').strip()
            if state != b'WAIT':
                assert state == b'0', 'Probe failed: retain USB/logs and reboot; never unload or retry'
                break
            time.sleep(.5)
        else:
            raise RuntimeError('Probe timeout: retain USB/logs and DMA, then reboot; no unload or retry')
        for _ in range(30):
            if c('if test -b /dev/asp0n1; then echo READY; else echo WAIT; fi').strip() == b'READY':
                break
            time.sleep(.5)
        else:
            raise RuntimeError('Namespace did not appear; retain current boot for diagnosis')
    c('test "$(cat /sys/block/asp0n1/ro)" = 1; '
      'test "$(cat /sys/module/asp/parameters/enable_reformat)" = N; '
      'test "$(cat /sys/block/asp0n1/queue/logical_block_size)" = 4096; '
      'test "$(cat /sys/block/asp0n1/size)" = 250000000; '
      'test "$(cat /sys/block/asp0n1/queue/max_hw_sectors_kb)" = 4; '
      '! busybox grep -Eq "^/dev/asp" /proc/mounts')
    (out / 'kernel.txt').write_bytes(c('dmesg', 8))
    (out / 'result.json').write_text(json.dumps({
        'uts_version': manifest['uts_version'], 'boot_id': previous['boot_id'],
        'probe_pass': True, 'device_read_only': True, 'logical_block_bytes': 4096,
        'device_bytes': 128000000000, 'internal_writes': False,
        'mounted_internal_filesystem': False,
    }, indent=2) + '\n')
    if a.action == 'probe':
        print('PASS: exact #35 ASP namespace appears read-only; repeat-read qualification still required')
    else:
        hashes = {}
        for lba in (0, 1, 31249999):
            pair = []
            for repetition in range(2):
                target = ram + '/read.bin'
                body = ('busybox dd if=/dev/asp0n1 of=' + target + ' bs=4096 count=1 skip=' + str(lba) +
                        ' iflag=direct 2>' + ram + '/read.log; '
                        'test "$(busybox stat -c %s ' + target + ')" = 4096; busybox base64 ' + target)
                data = base64.b64decode(c(body, 12))
                assert len(data) == 4096
                if lba in (1, 31249999):
                    assert data[:8] == b'EFI PART'
                (out / ('lba-' + str(lba) + '-' + str(repetition) + '.bin')).write_bytes(data)
                pair.append(hashlib.sha256(data).hexdigest())
            assert pair[0] == pair[1], 'Repeated aligned reads differ: preserve boot for diagnosis'
            hashes[str(lba)] = pair
        (out / 'reads.json').write_text(json.dumps({'bytes_each': 4096, 'repeated_hash_pairs': hashes,
                                                   'internal_writes': False}, indent=2) + '\n')
        print('PASS: six bounded native reads, equal repeated hashes and both GPT signatures; no writes/mounts')
    print('Private evidence:', out)


if __name__ == '__main__':
    main()
