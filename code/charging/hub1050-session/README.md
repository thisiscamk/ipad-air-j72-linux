# Touch-independent guarded charging continuation

## New continuous-input, reduced-brightness trial started

The same pinned charging worker is now running with the new #33 continuous
touch overlay at 802/2047 brightness. The controlled hub data handoff and
desktop/input restart passed. Initial settled battery readings were
+449…+469 mA at 36.6 C with no guard faults, and the owner confirmed the
desktop, charging symbol and input. The maximum is still one hour with the
same source, battery, temperature and rollback guards. This is an
[initial observation](CONTINUOUS-DESKTOP-START.json), not a full-duration
or final-restoration result. Percentage gain remains unqualified.

## Previous normal-brightness continuation

**This continuation ended at the 38.1 C temperature test guard; it did not complete 60 minutes.**
It follows the measured five-minute desktop run. Native build, ABI and
offline policy/rollback/fault/USB tests passed. Charging remained active
through a real touch stop, healthy cleanup and restart. See `VALIDATION.json`
for the observations. The worker reported successful restoration with no
restore failure. The owner rebooted to iOS for charging before an independent
final PMIC snapshot and the remaining RAM logs could be retrieved. There were
526 retained positive readings, +36 to +209 mA. This is a conservative test
cutoff, not an established device overtemperature threshold.

The preceding dimmed-display run charged for 1,033.724 seconds (about 17.2
minutes), then a touch diagnostic timeout caused its host lease to be
withdrawn. Automatic restoration succeeded. 485 unique settled host gauge
readings were positive, +438 to +485 mA; maximum temperature was 37.4 C.
That older worker's retained-sample window had an inherited final-295-second
literal, so its own retained count was zero. This worker fixes sampling to
start five seconds after the actual beginning, for any configured duration.

Battery, USB and PMIC guards are unchanged: nominal 1,050 mA input on the
qualified powered JCH377, original `04c0=02`, 20–38 C, 3.5–4.2 V, SOC
10–95%, battery current within ±1.5 A, 250 ms USB checks and a 2.5-second
host lease. Loading/arming does not change current. The owner-requested
`begin_session` callback queues the same guarded request as Home; it
refuses unarmed, already-used/active, shutting-down or restoration-fault
states. A completed worker cannot be reused.

The host now verifies the known hub, live USB data and read-only desktop
export independently of the finite touch session. This is still an
experimental host-qualified source policy, not autonomous source detection.
It requires the private exact-kernel build and owner-local inputs; this
folder is not an installer or a complete runnable distribution.

New source is GPL-2.0-only. The public offline runner extracts the actual
`begin_set` callback into its synthetic harness, and tests policy timing,
rollback, guard faults and USB lifetime without hardware access.
