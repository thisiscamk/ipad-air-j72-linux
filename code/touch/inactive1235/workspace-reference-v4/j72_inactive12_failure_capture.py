#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Save stable input evidence before provider shutdown/iOS return.

The caller supplies the existing exact-boot Wi-Fi transport and first stops
its charging owner. No reboot, unload, fault reset or input restart exists here.
An export requires the unchanged kernel guard's stopped/failed session state.
"""
import base64
import importlib.util
import json
from pathlib import Path
from j72_observation_health import fields, scoped_shell

BASELINE = r'''
test "$(cat /sys/block/nbd2/size)" = 0
! busybox grep -Eq '^/dev/(nbd|sd|mmc|nvme|asp|dm|mapper)' /proc/mounts
for p in /sys/module/j72_input_limit*/parameters /sys/module/j72_charge_maintain*/parameters; do
 test -d "$p" || continue
 for value in enabled=0 active=0 armed=0 restore_failed=0; do busybox grep -qx "$value" "$p/status"; done
done
busybox grep -qx reg_04c0=02 /sys/module/j72_wlan_ready_snapshot/parameters/snapshot
echo BASELINE_PASS
'''
STATUS = r'''
p=/sys/module/j72_touch_session/parameters
for k in session_state input_frames input_recoveries input_bad_layouts input_timeouts layout_anomalies wire_anomalies xfer_errors firmware_healthy cleanup_ok hardware_cleanup_ok recovery_stop_reason; do
 printf '%s=' "$k"; cat "$p/$k"
done
if test -r "$p/phase_resync_policy"; then
 for k in contact_state2_policy contact_state2_frames contact_state1_policy contact_state1_frames phase_resync_policy phase_resync_headers phase_resync_frames phase_resync_failures; do printf '%s=' "$k"; cat "$p/$k"; done
fi
'''
STOP_DESKTOP = r'''
if test -f /mnt/omarchy/.j72-ram-root; then
 /sbin/j72-ram-desktop-session stop
else
 /sbin/j72-desktop-session stop
fi
'''
EXPORT = r'''
s=$(cat /sys/module/j72_touch_session/parameters/session_state)
case "$s" in 0|4) ;; *) exit 1;; esac
busybox base64 /sys/kernel/j72_touch_session_anomalies
'''


def analyze(data, layouts, wires):
    spec = importlib.util.spec_from_file_location('failure_ring_analyzer', Path(__file__).with_name('analyze-j72-session-anomalies.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.analyze(data, layouts, wires)


def capture(command, directory):
    """Stop normally and retain evidence; never relabel the original failure."""
    out = Path(directory)
    out.mkdir(mode=0o700)
    result = dict(status='NOT_CAPTURED', input_restarted=False,
                  kernel_export_guard_preserved=True, original_failure_cleared=False)
    try:
        assert command(scoped_shell(BASELINE), timeout=8).strip() == b'BASELINE_PASS'
        result['independent_charge_baseline_verified'] = True
        # Preserve errors from normal APIs. A failed API is not a cleanup pass;
        # it may still leave a stable state-4 ring that the kernel permits reading.
        for name, body, timeout in [('desktop-stop', STOP_DESKTOP, 35),
                                    ('input-stop', '/sbin/j72-touch-session stop', 35)]:
            try:
                (out / (name + '.txt')).write_bytes(command(scoped_shell(body), timeout=timeout))
                result[name + '_api_pass'] = True
            except Exception as exc:
                result[name + '_api_pass'] = False
                result[name + '_error'] = type(exc).__name__ + ': ' + str(exc)
        raw = command(scoped_shell(STATUS), timeout=8)
        (out / 'touch-status.txt').write_bytes(raw)
        status = fields(raw)
        assert status['session_state'] in ('0', '4'), 'Input still active; no export'
        assert int(status['input_bad_layouts']) == int(status['layout_anomalies'])
        data = base64.b64decode(command(scoped_shell(EXPORT), timeout=20), validate=False)
        assert len(data) == 159848, 'Unexpected stable ring size'
        (out / 'touch-anomalies.bin').write_bytes(data)
        result.update(status='STOPPED_RING_CAPTURED', touch_status=status)
        try:
            summary = analyze(data, int(status['layout_anomalies']), int(status['wire_anomalies']))
            (out / 'analysis.json').write_text(json.dumps(summary, indent=2) + '\n')
            result['analysis_pass'] = True
        except Exception as exc:
            result['analysis_pass'] = False
            result['analysis_error'] = type(exc).__name__ + ': ' + str(exc)
    except Exception as exc:
        result['reason'] = type(exc).__name__ + ': ' + str(exc)
    finally:
        (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    return result
