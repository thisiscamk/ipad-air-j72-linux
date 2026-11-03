# Contact state 1: separate inactive-contact experiment

**Offline tests/build/preflight and initial device checks pass; long-run unqualified.** The prior resync boot
passed owner menu/Foot/keyboard checks, but the charging gate found one rejected
layout. Normal cleanup and independent baseline checks pass. The actual rejected
report was saved privately before reboot and replayed through the original C
decoder: result -5 (contact state). It has valid wire checksums and the measured
native 0x44 / 24-byte-header / one-contact / 30-byte-stride structure, with state 1.
This identifies that refusal, not the three uncaptured reports from the prior run.

## Narrow change

The [upstream Apple Z2 parser](https://linux.googlesource.com/linux/kernel/git/torvalds/linux/+/81122fba08fa3ccafab6ed272a5c6f2203923a7e/drivers/input/touchscreen/apple_z2.c)
treats only states 3/4 as active. This candidate adds the observed state 1 to the
J72 decoder as **inactive**, without claiming its physical meaning. It releases
that contact slot and emits no position for it. Only 0/1/3/4/5/7 are accepted;
other unknown states still reject the whole report before any input event.
Full packet checksums, native layout bounds/count/stride/image/duplicate-ID
checks, geometry, firmware, SPI timing, rolling recovery budget, timeout and
normal cleanup stay intact. The previous one-extra-transfer policy is retained
unchanged to isolate this contact-state change; it has not proved beneficial.

Read-only policy/frame counters distinguish this worker. The frame counter
increments only after whole-report validation, and resets at session start.

## Checks completed offline

- Compile the actual candidate emitter with controlled Linux input calls:
  all 256 state bytes, active → state-1 slot release without coordinates,
  malformed second-contact atomic rejection, duplicate IDs, every truncated
  length, bad header/count/image/stride and mixed contacts.
- Replay the captured private report through that actual emitter: accepted as
  inactive, no coordinates; original actual decoder rejects it as state -5.
- Retain the 19 actual acquisition scenarios/all 65,536 announced lengths,
  rolling-window tests and actual recovery health-branch tests.
- Exact #35 W=1 module build is warning-free; strong imports/vermagic pass.
  Earlier sealed module, private inputs, host kernel and cold payload are unchanged.
- V3 host orchestration: six failure-capture, two actual collector/policy, five
  same-boot read-receipt and six iOS-return tests pass. The latter cover an absent
  charger module without using a stale prior-boot staging receipt, and actual
  baseline/owner shell refusals. Charging hard limits remain unchanged.

Run the portable emitter tests without private inputs:

```sh
python3 test-emitter.py j72_touch_session.c
```

The optional second argument is a private decoded report file. It is not supplied
here. Source/build helpers reference the private research workspace; Apple firmware
and calibration includes, binaries and raw captures are excluded.
[Source hashes](RESULT.json), [orchestration references](workspace-reference-v3/).

## Next changed boot

Use the unchanged #35 payload over the proven direct Pi path. Before radio/old
touch startup, stage `run-j72-touch-state135.py --stage`. Require the original
self-check, firmware health and physical restoration, then Wi-Fi/RAM desktop,
fresh native read-only storage checks, owner input check and same qualified hub.
Use the separate V3 session/observer and matching iOS-return helper. The zero
layout/SPI/timeout health gate remains; a new failure is captured before shutdown.
No parser fix, charging benefit, long-run reliability or installation is yet proved.
No internal-storage write is authorized.

## Initial device stage

The new worker passed the original start/stop self-check, firmware health and
physical restoration. Wi-Fi/HTTPS/SSH, RAM desktop and fresh native read-only
checks pass. The initial snapshot has 573 valid frames and no layout/SPI/timeout
errors. It has not yet observed a state-1 frame, so that new path is not device
proved. Owner input and longer observation remain pending; no charging started.
[Sanitized device checkpoint](DEVICE-STAGE-RESULT.json).

## Completed device follow-up

Owner menu/typing/keyboard checks passed. Seven state-1 frames were processed,
but seven checksum-valid native state-2 reports were rejected. All seven raw
reports were saved privately. At stop: 14,713 valid frames, one bounded recovery,
zero SPI errors/timeouts, reason 0, firmware/normal cleanup pass. No charging was
started. None of 1,891 extra retries recovered a frame. Independent baseline and
normal iOS charging pass. The [next state-1/2 candidate](../inactive1235/) is host
tested and device untested; the prior failure remains a failure.
