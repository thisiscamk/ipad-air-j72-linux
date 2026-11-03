# #35 touch recovery-window — bounded device run passes

The [long-run failure](../LONG-RUN-20261102.md) reached the old six-recovery
lifetime budget. This separate candidate retains that cumulative limit for
finite diagnostic sessions. For explicit continuous sessions it permits at
most **six recoveries in a rolling 60-second window**. A seventh within that
window stops input; sparse healthy recoveries no longer exhaust a lifetime quota.
The interval is a conservative test policy, not a measured controller specification.

Every admitted recovery still releases contacts and checks device information,
zero status flags and native-report gate 0x19. SPI/layout checks, contact decoding,
firmware, calibration, timing and cleanup stay unchanged. Failures remain latched
in state 4; the existing stop wrapper is unchanged. New read-only diagnostics name
the recovery stop reason and separately report physical hardware restoration.
They do not turn a failed acquisition into a successful cleanup API result.

The separate module builds without warnings with W=1 against the unchanged #35
kernel. Strong imports resolve to its built-in exports. UBSan/bounds checks cover
burst limits, exact expiry, clock reversal, ring rotation,1,000 sparse recoveries,
finite-session refusal and failures of the actual recovery branch's health gates.
The 3 November run completed with 221,923 valid frames and eight recoveries,
zero SPI/layout/timeout errors, and normal stop/firmware/physical cleanup.
The owner checked input at startup; no end-of-run gesture check was performed.
Wire anomalies remain under investigation. This is bounded-run evidence,
not an all-day reliability claim. [Measured result](DEVICE-RESULT-20261103.json).

`j72_touch_session.c` is the complete candidate; the patch is against the pinned
measured #35 source, whose digest is in [RESULT.json](RESULT.json). Owner firmware
and calibration includes stay private; generate them using the existing recipe
and supply `J72_PRIVATE_INCLUDES` when building. No binary or Apple input is included.

Host references expect the private research workspace. For a proven #35
boot, before any touch/radio/desktop start, the new stage tool verifies exact
boot/board/source hashes, loads this candidate from RAM, and runs the existing
start/stop self-check. It preserves the original cold payload/module files.
A failed check stops progression; do not bypass the failure or retry startup.
After a pass, existing Wi-Fi/desktop tools can reuse the loaded, idle worker.

Run standalone host tests:

```sh
cc -std=c11 -Wall -Wextra -Werror -fsanitize=undefined,bounds \
  -fno-sanitize-recover=all test-recovery-window.c -o /tmp/j72-window-test
/tmp/j72-window-test
python3 test-integration.py j72_touch_session.c
```
