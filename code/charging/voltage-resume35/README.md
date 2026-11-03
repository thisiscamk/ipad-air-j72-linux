# Voltage-hold restart candidate — device untested

The [3 November measurement](../maintain35/NINETY-MINUTE-RESULT.json) lost
181.13 mAh across 90 minutes. All five active pauses began at 4.201 V, below
the thermal cutoff. After the fifth pause the pack stayed above the old
36.5°C restart gate. Charging remained off for the rest of the observation.
This differs from the actual thermal hold in the 2 November run.

## Deliberate policy change

Only a voltage/SOC hold after a successful start may resume at 36.6–38.0°C.
It still needs SOC ≤90%, voltage ≤4.1 V, at least 30 seconds since the pause,
a fresh valid gauge vector, independently restored input limit and a qualified
source lease. Initial starts, explicit stop/rearm, expired windows and fault
requalification retain the 36.5°C gate. An actual reading above 38°C latches
thermal history until a successful restart at or below 36.5°C, even if a later
voltage/SOC hold changes the displayed wait reason.

This **relaxes restart eligibility**; it is not a measured charging improvement.
The active 38°C cutoff, current/voltage/SOC limits, nominal 1050 mA input setting,
short source lease, bounded windows and fault/restoration rules remain intact.
The old unused pack-helper declaration is marked `static inline`; its body is
unchanged. Both changes are supplied as patches. The original measured files
and #35 boot payload are unchanged.

## Offline evidence and next device test

- 35 existing actual-core maintenance scenarios and 14 new boundary/fault/latch
  scenarios pass under undefined-behaviour and bounds sanitizers.
- Replaying the recorded pause/restart vectors selects WAIT_COOL with the old
  policy and restart with this candidate. It does not predict physical current,
  temperature or net charge under the new policy.
- Exact-kernel W=1 build has no warnings; strong imports resolve to built-ins.
- Separate host policy-status/refusal tests and observer preflight pass.

[Status and source hashes](RESULT.json). No device execution has occurred.
Keep the qualified touch worker, brightness 802, `schedutil`, Wi-Fi, read-only
ASP and source fixed for the comparison. Include every protective hold in net
charge. Verify thermal-history behaviour, independent restoration and normal
cleanup. An actual thermal restart remains unproved until observed.

This is the same module namespace as the original #35 controller. They must
never be loaded together. Source references are for the exact research kernel,
not an arbitrary installed Linux kernel; the host kernel is unchanged. No Apple
binary or private calibration is included.

Run host core tests from this directory:

```sh
cc -std=c11 -Wall -Wextra -Werror -Wno-unused-function \
  -fsanitize=undefined,bounds -fno-sanitize-recover=all \
  -I. test-maintain.c -o /tmp/j72-maintain-test
/tmp/j72-maintain-test
cc -std=c11 -Wall -Wextra -Werror -Wno-unused-function \
  -fsanitize=undefined,bounds -fno-sanitize-recover=all \
  -I. test-voltage-resume.c -o /tmp/j72-resume-test
/tmp/j72-resume-test
```
