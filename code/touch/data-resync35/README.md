# Bounded data-phase resynchronisation — device untested

The next candidate addresses a measured transport pattern: 20 of 32 retained
J72 data-phase anomalies contain a checksum-valid 16-byte E1 length header.
[Orchard's J71b change](https://github.com/OrchardLinux/orchard/commit/ec1a4e1ad1d76ff60f3576df9573ec6ec7f30566)
provides the mechanism reference. This is a J72 adaptation of that idea, not a
claim that the J71b patch works unchanged here.

The later J72 precharge attempt recorded three rejected layouts, with touch
still active and no SPI errors/timeouts. Their raw reports were lost before
reboot. **Their cause is unknown; this candidate may not fix them.** The next
session also adds [capture before shutdown](../../charging/voltage-resume35/workspace-reference-v2/j72_input_failure_capture.py).

## Exact change

`j72-data-phase.h` implements the acquisition function used by the real worker:

- Keep the measured GetData request, checksum construction and queue tag 1/2.
- When its reply starts with E1, require the full 16-byte header checksum and
  a positive payload length of 2–2454 before admitting **one** extra transfer.
- Retain that first reply in the private wire-anomaly ring before overwriting it.
- A second header, invalid checksum, empty/oversized length or transfer error
  gets no further retry. Existing rejection/recovery paths remain.
- Verify the final complete wire checksum and original native contact decoder
  before any input event. Neither validator was relaxed or changed.

Original firmware/calibration, SPI clock/CS/word-delay settings, GPIO/power
ownership, rolling/finite recovery budgets, input timeout and cleanup guards
remain intact. The extra transfer deliberately changes bus work; this is not
an identical workload for causal comparisons with the earlier power run.
New read-only counters report policy, headers, emitted resync frames and failures.

## Offline evidence

- 19 acquisition scenarios, including all 65,536 advertised lengths, pass with
  undefined-behaviour/bounds sanitizers. The tests exercise the same acquisition
  function compiled into the worker, both tags, transfer faults, buffer bounds,
  checksum failures and the one-retry limit.
- Original rolling-window and actual recovery-health branch tests pass.
- Exact #35 kernel W=1 build is warning-free; strong imports resolve to built-ins.
- The actual C header guard recognises 20 of 32 retained private J72 data-phase
  records. This classifies old replies; it does not prove a real follow-up frame.

[Source hashes and result](RESULT.json). No new candidate has run on the iPad.
The old qualified candidate, #35 kernel and cold payload are preserved.

## Next device sequence

Load this distinct module before radio/old touch startup on a fresh #35 RAM
boot, using `run-j72-touch-resync35.py --stage` in the private workspace.
Require the existing start/stop self-check, firmware health and physical cleanup.
Then start Wi-Fi/RAM desktop, perform fresh native read-only checks and owner
input verification, and move to the same qualified powered-hub port.

The session driver uses `--touch-resync35`. The strict zero-layout/SPI/timeout
health rules remain. A precharge failure stops progression and normally stops
input to export its stable ring **before** provider shutdown/reboot. Failed APIs
remain failures even when evidence export succeeds; no reset/restart/forced
unload is used to continue testing.

If checks pass, the existing voltage-hold charging candidate can be observed in
this same boot. A net-gain result would qualify that stated combined workload;
it would not isolate the effect of charging policy from the touch change.

Host acquisition test:

```sh
cc -std=c11 -O1 -g -Wall -Wextra -Werror \
  -fsanitize=undefined,bounds -fno-sanitize-recover=all \
  test-data-phase.c -o /tmp/j72-data-phase-test
/tmp/j72-data-phase-test
```

Private firmware/calibration includes are required for the kernel module and
are intentionally absent. Builder/stager references expect the existing private
workspace. No Apple binary, raw packet, private include or calibration is published.
