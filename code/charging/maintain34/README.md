# Opt-in J72 charging maintenance candidate

2 November 2026. **Live observation is in progress. This is not unattended
charging qualification or general charger detection.** [Measured status](RESULT.json).

The old diagnostic worker ended after one session or a battery guard. This
candidate can remain enabled on the **same owner-qualified powered JCH377
charging/data port**, wait without a current override when the pack is full
or warm, then begin another bounded window after conservative restart checks.
It is an intermediate Pi-supervised implementation; removing the host lease
would remove a source check and is not supported.

## Preserved limits and new states

- Only PMIC register `0x04c0` is writable: original `0x02` or the previously
  measured nominal 1050 mA setting `0x4e`. No write occurs at module load/arm.
- The existing active limits remain: SOC 10..95%, temperature 20..38 C,
  voltage 3.5..4.2 V, battery current within +/-1.5 A. Hardware PMIC ceiling
  and configuration checks are retained. Pack current is not USB input current.
- High SOC/voltage/temperature cause a verified return to `0x02` and a hold.
  Starting/resuming requires SOC <=90%, voltage <=4.1 V and temperature
  <=36.5 C. Waiting outside active limits never permits a current override.
- Every current window retains the original one-hour deadline. A new window
  requires verified restoration, a fresh pack vector, qualified source,
  matching PMIC state and a minimum 30-second pause after a completed cycle.
- Gauge I/O stays outside the policy mutex on a separate queue. A six-second
  snapshot-age bound and the independent high-priority 250 ms source/deadline
  checks prevent a blocked gauge read from indefinitely extending a grant.
- The Pi must verify the exact physical hub path, revision, self-powered
  descriptor, current host boot and high-speed configured gadget before
  renewing the 2.5-second source lease. This is not charger classification on
  the iPad. A direct Pi connection is refused before arming.
- Missing/invalid battery data, excessive current, source loss, unexpected
  register state or a restoration failure latch the controller off. A renewed
  source lease alone cannot restart it. A root-only requalification operation
  requires fresh source/battery checks and verified `0x02`; it leaves the
  controller disabled and cannot clear failed restoration.
- Manual stop, Top button, suspend preparation and reboot stop the controller.
  Home continues to control the menu and cannot start charging. The target
  has no module unload support, so fault recovery is explicit requalification
  or a later reboot, not an assumed unload/reload cycle.

Mode values: `0` off, `1` charging window, `2` waiting for full-pack headroom,
`3` waiting to cool, `4` between windows, `5` starting, `6` latched fault.
A controller enabled in a hold is not actively charging. Positive current,
charge gained and endurance must be measured separately.

## Host regression check

The test compiles the actual shared policy header with fake register I/O;
it does not model controller firmware, GPIO events or real HDQ timing.

```sh
cc -std=c11 -Wall -Wextra -Werror -Wno-unused-function \
  -fsanitize=undefined -fno-sanitize-recover=all \
  code/charging/maintain34/test-maintain.c -o /tmp/j72-test-maintain
/tmp/j72-test-maintain
```

35 scenarios pass: full/warm holds, restart thresholds/delay, stale/missing
readings, source/PMIC loss, write/readback faults, failed restoration, finite
window expiry, fault latching and explicit requalification. The module builds
against the exact #34 target kernel and all strong imports resolve.

[host-reference.py](host-reference.py) is the actual workspace orchestration
reference, intended at `tools/run-j72-charge-maintain34.py` alongside the existing
workspace helpers and private manifests. It is not a standalone installer.
It records bounded observations and verifies restoration when they end.
Private source receipts, network credentials, firmware and logs are excluded.

## Remaining live gates

The module has loaded disabled with unchanged input limits. Real direct-Pi
source refusal, full-pack waiting, lease withdrawal during a hold, fault
latching and explicit requalification passed. A longer observation with the
RAM desktop and Wi-Fi is underway at brightness 1203/2047.

Still to measure: a positive-current cycle on this controller, restoration
and restart at a hold, withdrawal during an active-current window, longer
interactive operation and final independent restoration. Temperature/voltage
stops remain possible; a one-hour wall clock is not one hour charging. Do not
infer all-day/overnight safety or standalone charging from the shorter tests.

## Orchard reuse

Current Orchard's Tristar driver offers native source classification and
source-change handling, using a D2365-family PMIC and CBTL1610. J72 also has a
CBTL1610 according to cached iOS device-tree inventory, but uses the older
Anya/D2089 PMIC path. The bank/ADC/event mappings need a J72-specific audit;
the D2365 register writes must not be copied onto Anya. That port is the route
to removing this candidate's Pi qualification dependency.
