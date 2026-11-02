#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Stage pinned networking on #35 using its known bundled BusyBox for HTTP."""
import importlib.util
import json
import os
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    os.umask(0o077)
    h = load('h35', 'j72-desktop-storage35-host.py')
    manifest = h.preflight(verify_desktop=False)
    n = load('network', 'j72_network_userspace.py')
    network = n.preflight()
    c = load('lock', 'run-j72-input-limit-hub1050-desktop.py').locked_ram(h.ram())
    assert c('uname -v', timeout=4).decode().strip() == manifest['uts_version']
    assert c('cat /proc/device-tree/model', timeout=4).rstrip(b'\0\n') == b'Apple iPad Air (Cellular)'
    # BusyBox dispatches by argv[0]; retain the exact basename "busybox".
    target = '/run/j72-fetch/busybox'
    c('test "$(busybox stat -f -c %T /run)" = tmpfs && test ! -e /run/j72-fetch && mkdir -m 700 /run/j72-fetch', timeout=4)
    # The regular bundle BusyBox is dynamically linked and cannot bootstrap
    # an empty recovery root. Use the separately prepared static ARM64 helper.
    source = n.WORK / 'bootstrap-busybox'
    digest = '999cb969d09093a71716cfc747bb53cdada3f332c05eb5046c56e0f66a4d6d22'
    assert h.sha(source) == digest
    load('upload', 'run-j72-wlan-enumeration-v2.py').upload(c, h, source, target)
    c('chmod 700 ' + target + '; ' + target + ' wget --help >/run/j72-fetch-help.txt 2>&1', timeout=4)

    def fetch_command(body, timeout=15):
        # Replace only the fixed HTTP invocation; all original staging gates,
        # archive hashes, extraction, RAM mounts and executable checks remain.
        if body.startswith('busybox wget '):
            body = target + ' wget ' + body[len('busybox wget '):]
        return c(body, timeout=timeout)

    n.stage(fetch_command, network)
    out = ROOT / 'private/j72-platform/power-storage-20261102/desktop-storage35' / ('network-stage-' + time.strftime('%Y%m%d-%H%M%S'))
    out.mkdir()
    (out / 'result.json').write_text(json.dumps({
        'network_archive_sha256': network['archive_sha256'],
        'fetcher_sha256': digest,
        'kernel_build': manifest['uts_version'], 'original_stage_checks_preserved': True,
        'root_busybox_replaced': False, 'internal_storage_access': False,
        'network_tools_staged': True,
    }, indent=2) + '\n')
    print('PASS: pinned networking staged in RAM using separately pinned HTTP helper; system BusyBox retained')
    print('Private evidence:', out)


if __name__ == '__main__':
    main()
