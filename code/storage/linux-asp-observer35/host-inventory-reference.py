#!/usr/bin/env python3
"""Check observer pins, or capture only live firmware metadata over USB."""
import argparse
import ast
import base64
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT/'private/j72-platform/power-storage-20261102/storage-observer35'


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT/'tools'/filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['preflight', 'inventory'])
    args = parser.parse_args()
    os.umask(0o077)
    host = load('h', 'j72-wifi-v3-host.py')
    manifest = json.loads((WORK/'manifest.json').read_text())
    assert manifest['profile'] == 'storage-observer35'
    assert not manifest['storage_autoload'] and not manifest['internal_write_support']
    assert not manifest['loader_storage_init']
    for name, digest in manifest['inputs'].items():
        assert host.sha(ROOT/name) == digest, name
    for name, digest in manifest['files'].items():
        assert host.sha(WORK/name) == digest, name
    assert host.sha(Path(manifest['payload'])) == manifest['payload_sha256']
    tree = ast.parse((ROOT/'tools/j72-pongo-pmic-boot.py').read_text())
    pins = [ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == 'STORAGE35_SHA256' for t in n.targets)]
    assert pins == [manifest['payload_sha256']]
    if args.action == 'preflight':
        print('PASS: exact #35 observer inputs/image pins; no device contacted')
        return
    command = load('lock', 'run-j72-input-limit-hub1050-desktop.py').locked_ram(host.ram())
    check = ('test "$(uname -v)" = '+shlex.quote(manifest['uts_version'])+
             ' && test "$(cat /proc/device-tree/model)" = "Apple iPad Air (Cellular)"'+
             ' && test "$(cat /run/j72/storage-observer-ready)" = storage-observer35-recovery-only'+
             ' && test ! -d /sys/module/asp')
    command(check, timeout=5)
    capture = WORK/('inventory-'+time.strftime('%Y%m%d-%H%M%S'))
    capture.mkdir()
    boot = command('cat /proc/sys/kernel/random/boot_id', timeout=4).decode().strip()
    raw = command('busybox base64 /sys/firmware/fdt', timeout=8)
    fdt = capture/'live.dtb'
    fdt.write_bytes(base64.b64decode(raw, validate=False))
    assert 40 <= fdt.stat().st_size <= 1024*1024
    (capture/'kernel.txt').write_bytes(command('uname -a; cat /proc/mounts; cat /proc/modules; dmesg', timeout=5))
    (capture/'boot-id.txt').write_text(boot+'\n')
    # fdtget's child walker can stop at NOP tokens in the loader's valid FDT.
    # Validate/canonicalize a host copy; retain the original captured bytes.
    original_fdt = fdt
    fdt = capture/'canonical.dtb'
    subprocess.run(['dtc', '-I', 'dtb', '-O', 'dtb', '-o', str(fdt), str(original_fdt)],
                   check=True, capture_output=True)

    def get(node, prop, kind='x'):
        return subprocess.check_output(['fdtget', '-t', kind, str(fdt), node, prop], text=True).strip()

    def cells(node, prop):
        return [int(x, 16) for x in get(node, prop).split()]

    def pairs(values):
        assert len(values) % 4 == 0
        return [((values[i]<<32)|values[i+1], (values[i+2]<<32)|values[i+3]) for i in range(0, len(values), 4)]

    assert get('/', 'model', 's') == 'Apple iPad Air (Cellular)'
    assert get('/aliases', 'asp', 's') == '/soc/block@208040000'
    assert get('/soc/block@208040000', 'status', 's') == 'okay', 'Loader kept storage disabled; inspect private handoff diagnostics'
    fw = '/reserved-memory/ans-firmware'
    assert cells('/soc/block@208040000', 'memory-region') == cells(fw, 'phandle')
    assert get('/soc/block@208040000', 'memory-region-names', 's') == 'firmware'
    properties = subprocess.check_output(['fdtget', '-p', str(fdt), fw], text=True).splitlines()
    assert 'no-map' in properties
    regions = pairs(cells(fw, 'reg'))
    assert len(regions) == 1
    address, size = regions[0]
    assert address and 0 < size <= 64*1024*1024 and not ((address|size)&4095)
    assert address < (1<<40) and size <= (1<<40)-address
    nodes = subprocess.check_output(['fdtget', '-l', str(fdt), '/'], text=True).splitlines()
    memories = [n for n in nodes if n.startswith('memory@')]
    ram = [region for node in memories for region in pairs(cells('/'+node, 'reg'))]

    # /memory describes Linux's usable span, not all physical DRAM. The
    # firmware can be deliberately carved out above that span. Get the
    # loader's actual DRAM extent from its separately reserved RAM log only.
    reserved = subprocess.check_output(['fdtget', '-l', str(fdt), '/reserved-memory'], text=True).splitlines()
    log_nodes = []
    for node in reserved:
        path = '/reserved-memory/'+node
        result = subprocess.run(['fdtget', '-t', 's', str(fdt), path, 'label'],
                                capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip() == 'm1n1_stage2.log':
            log_nodes.append(path)
    assert len(log_nodes) == 1
    log_regions = pairs(cells(log_nodes[0], 'reg'))
    assert len(log_regions) == 1
    log_address, log_size = log_regions[0]
    assert log_size == 16384 and not (log_address & 4095)
    assert any(base <= log_address and log_address+log_size <= base+length for base, length in ram)
    assert not (log_address < address+size and address < log_address+log_size)
    body = ('busybox dd if=/dev/mem of=/run/j72-loader-log.bin bs=4096 skip='+
            str(log_address//4096)+' count=4 2>/run/j72-loader-log-dd.txt; '+
            'test "$(busybox stat -c %s /run/j72-loader-log.bin)" = 16384; '+
            'busybox base64 /run/j72-loader-log.bin')
    guard = 'test "$(cat /proc/sys/kernel/random/boot_id)" = '+shlex.quote(boot)+' && '
    log = base64.b64decode(command(guard+'busybox sh -ec '+shlex.quote(body), timeout=8))
    assert len(log) == log_size
    (capture/'m1n1-log-ram.bin').write_bytes(log)
    dram = re.findall(rb'FDT: DRAM at (0x[0-9a-f]+) size (0x[0-9a-f]+)', log)
    assert len(dram) == 1, 'Inspect the private loader log before storage probe'
    dram_base, dram_size = (int(x, 16) for x in dram[0])
    assert dram_base <= address and address+size <= dram_base+dram_size
    kernel = (capture/'kernel.txt').read_text()
    regions = re.findall(r'OF: reserved mem: (0x[0-9a-f]+)\.\.(0x[0-9a-f]+).*nomap.*ans-firmware', kernel)
    assert any(int(start, 16) == address and int(end, 16)+1 == address+size for start, end in regions)
    result = {'boot_id': boot, 'uts_version': manifest['uts_version'],
              'live_fdt_sha256': host.sha(original_fdt), 'firmware_metadata_valid': True,
              'loader_dram_extent_verified': True, 'kernel_nomap_reservation_verified': True,
              'firmware_bytes_read': False, 'asp_loaded': False,
              'storage_commands_submitted': False, 'internal_writes': False}
    (capture/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print('PASS: live J72 firmware fits physical DRAM and matches the kernel no-map reservation; ASP remains unloaded')
    print('Private inventory saved:', capture)


if __name__ == '__main__':
    main()
