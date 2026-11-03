#!/usr/bin/env python3
"""Build an isolated, DEVICE-UNTESTED #35 voltage-hold restart candidate.

Initial starts, thermal-trip cooldown and expired-window restarts still require
36.5 C. Only a verified voltage/SOC hold may restart at 36.6..38.0 C, without
an intervening thermal trip. This changes restart eligibility, not the 38 C
active cutoff, source lease, nominal input current, voltage/SOC/current limits,
window deadline, independent restoration or fault-latching rules.
"""
import difflib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'private/j72-platform/power-storage-20261102'
BASE = WORK / 'maintain35'
OUT = WORK / 'voltage-resume35'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def replace_once(text, before, after):
    assert text.count(before) == 1, before
    return text.replace(before, after, 1)


def main():
    os.umask(0o077)
    assert not OUT.exists(), 'Refuse an existing candidate; preserve measured inputs'
    host = load('voltage35_host', 'j72-desktop-storage35-host.py')
    boot = host.preflight(verify_desktop=False)
    original = json.loads((BASE / 'manifest.json').read_text())
    for name, digest in original['files'].items():
        assert sha(ROOT / name) == digest, name
    OUT.mkdir()
    mod = OUT / 'module'
    mod.mkdir()
    for name in ('j72_charge_maintain35.c', 'j72-maintain-core.h', 'j72-limit-core.h', 'Makefile'):
        shutil.copyfile(BASE / 'module' / name, mod / name)
    # The maintenance policy uses its own pack guard. Keep the legacy helper
    # body intact, but make its declaration inline in this candidate so an
    # unused static definition does not obscure W=1 warnings.
    limit = mod / 'j72-limit-core.h'
    limit_before = limit.read_text()
    limit_after = replace_once(limit_before, 'static int j72_limit_pack_guard(',
                               'static inline int j72_limit_pack_guard(')
    limit.write_text(limit_after)
    (OUT / 'helper-declaration.patch').write_text(''.join(difflib.unified_diff(
        limit_before.splitlines(True), limit_after.splitlines(True),
        fromfile='a/j72-limit-core.h', tofile='b/j72-limit-core.h')))
    core = mod / 'j72-maintain-core.h'
    before = core.read_text()
    text = replace_once(before, ' unsigned int cycles, pauses;',
                        ' unsigned int cycles, pauses;\n unsigned int last_pause, warm_full_resumes;\n bool thermal_latched;')
    text = replace_once(text, ' if (was_active) {m->pauses++; m->stopped_at_ms=now;}',
                        ' if (was_active || mode==J72_OFF || fatal) m->last_pause=mode;\n'
                        ' if (was_active) {m->pauses++; m->stopped_at_ms=now;}')
    text = replace_once(text, ' if (m->sample[2]>380)\n  return j72_maintain_pause(m,p,io,now,J72_WAIT_COOL,0,false);',
                        ' if (m->sample[2]>380) {\n'
                        '  m->thermal_latched=true;\n'
                        '  return j72_maintain_pause(m,p,io,now,J72_WAIT_COOL,0,false);\n }')
    text = replace_once(text, '   m->pauses++;m->stopped_at_ms=now;',
                        '   m->pauses++;m->stopped_at_ms=now;m->last_pause=J72_WAIT_WINDOW;')
    text = replace_once(text, ' if (m->sample[2]>J72_RESUME_TEMP_TENTHC) {',
                        ' /* A voltage/SOC hold alone is not a thermal trip. The active\n'
                        '  * 38 C cutoff was checked above. Keep 36.5 C for every initial\n'
                        '  * start, expired window, stop/fault/requalification and any\n'
                        '  * actual thermal trip, even if a later voltage hold masks it. */\n'
                        ' if (m->sample[2]>J72_RESUME_TEMP_TENTHC &&\n'
                        '     (!m->cycles || m->last_pause!=J72_WAIT_FULL || m->thermal_latched)) {')
    text = replace_once(text, ' m->cycles++;m->mode=J72_RUNNING;return 0;',
                        ' if (m->sample[2]>J72_RESUME_TEMP_TENTHC) m->warm_full_resumes++;\n'
                        ' m->thermal_latched=false;\n'
                        ' m->cycles++;m->mode=J72_RUNNING;return 0;')
    core.write_text(text)
    (OUT / 'restart-policy.patch').write_text(''.join(difflib.unified_diff(
        before.splitlines(True), text.splitlines(True), fromfile='a/j72-maintain-core.h', tofile='b/j72-maintain-core.h')))
    source = mod / 'j72_charge_maintain35.c'
    text = source.read_text()
    text = replace_once(text, ' mutex_unlock(&policy_lock);\n return n;\n}',
                        ' n += scnprintf(buf+n,PAGE_SIZE-n,\n'
                        '  "resume_policy=1\\nlast_pause=%u\\nthermal_latched=%u\\nwarm_full_resumes=%u\\n",\n'
                        '  maintain.last_pause,maintain.thermal_latched,maintain.warm_full_resumes);\n'
                        ' mutex_unlock(&policy_lock);\n return n;\n}')
    source.write_text(text)
    shutil.copyfile(ROOT / 'tools/charge-voltage-resume35/test-voltage-resume.c', OUT / 'test-voltage-resume.c')
    shutil.copyfile(ROOT / 'tools/charge-voltage-resume35/replay-restart.c', OUT / 'replay-restart.c')
    shutil.copyfile(Path('/home/pi/ipad-air-j72-linux/code/charging/maintain34/test-maintain.c'), OUT / 'test-maintain.c')
    with (OUT / 'host-tests.log').open('wb') as log:
        for name in ('test-maintain', 'test-voltage-resume'):
            subprocess.run(['cc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                            '-Wno-unused-function', '-fsanitize=undefined,bounds', '-fno-sanitize-recover=all',
                            '-I' + str(mod), str(OUT / (name + '.c')), '-o', str(OUT / name)],
                           check=True, stdout=log, stderr=subprocess.STDOUT)
            subprocess.run([str(OUT / name)], check=True, stdout=log, stderr=subprocess.STDOUT)
        for label, include, expected in [('baseline', BASE / 'module', '0'), ('candidate', mod, '1')]:
            binary = OUT / ('replay-' + label)
            subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                            '-Wno-unused-function', '-fsanitize=undefined,bounds', '-fno-sanitize-recover=all',
                            '-DEXPECT_RESUME=' + expected, '-I' + str(include),
                            str(OUT / 'replay-restart.c'), '-o', str(binary)], check=True, stdout=log, stderr=subprocess.STDOUT)
            subprocess.run([str(binary)], check=True, stdout=log, stderr=subprocess.STDOUT)
    with (OUT / 'build.log').open('wb') as log:
        subprocess.run(['make', '-C', str(WORK / 'storage-kernel/src'),
                        'O=' + str(WORK / 'storage-kernel/out'), 'ARCH=arm64', 'M=' + str(mod),
                        '-j2', 'W=1', 'modules'], check=True, stdout=log, stderr=subprocess.STDOUT)
    exports = {line.split()[1] for line in (WORK / 'storage-kernel/out/Module.symvers').read_text().splitlines() if line.split()[2] == 'vmlinux'}
    imports = {line.split()[1] for line in subprocess.check_output(['nm', '-u', str(mod / 'j72_charge_maintain35.ko')], text=True).splitlines() if line.split()[0] == 'U'}
    assert not imports - exports, imports - exports
    assert 'warning:' not in (OUT / 'build.log').read_text().lower()
    assert subprocess.check_output(['modinfo', '-F', 'vermagic', str(mod / 'j72_charge_maintain35.ko')], text=True).strip() == '7.0.12-j72spi2 SMP preempt aarch64'
    for name, digest in original['files'].items():
        assert sha(ROOT / name) == digest, name
    host.preflight(verify_desktop=False)
    files = [Path(__file__).resolve(), ROOT / 'tools/run-j72-voltage-resume35.py',
             ROOT / 'tools/run-j72-voltage-observation35.py', ROOT / 'tools/charge-voltage-resume35/test-voltage-resume.c',
             ROOT / 'tools/charge-voltage-resume35/replay-restart.c', *mod.glob('*.[ch]'), mod / 'Makefile',
             mod / 'j72_charge_maintain35.ko', OUT / 'restart-policy.patch', OUT / 'helper-declaration.patch']
    manifest = dict(status='OFFLINE_BUILD_TESTS_PASS_DEVICE_UNTESTED', uts_version=boot['uts_version'],
                    nominal_mA=1050, unchanged_active_limits=True, strong_imports_resolved=True,
                    active_cutoff_tenthC=380, initial_and_thermal_resume_tenthC=365,
                    voltage_only_restart_may_use_active_temperature_range=True,
                    restart_policy_changed=True, active_limits_source_lease_and_fault_guards_unchanged=True,
                    thermal_trip_latched_until_cool_restart=True, original_artifacts_unchanged=True,
                    strong_imports=len(imports), device_tested=False, physical_net_gain_proved=False,
                    files={str(p.relative_to(ROOT)): sha(p) for p in files})
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('PASS: isolated candidate tests/build/import closure; restart permission changed; no device contacted')


if __name__ == '__main__':
    main()
