# Captured inactive states 1 and 2 — next device candidate

**Host tests/build/preflight pass; device untested.** The preceding state-1
worker passed owner menu/typing/keyboard checks and processed seven state-1
reports. Its charging gate then stopped on seven other rejected layouts. All
seven were captured privately: checksum-valid 0x44 native packets with header
24, one contact, stride 30 and state 2. No charging module or current override
was used. Normal cleanup and iOS charging pass.

The [upstream Apple Z2 parser](https://linux.googlesource.com/linux/kernel/git/torvalds/linux/+/81122fba08fa3ccafab6ed272a5c6f2203923a7e/drivers/input/touchscreen/apple_z2.c)
uses only 3/4 as active. This candidate handles the two captured states 1/2 as
inactive, releasing their contact slots and emitting no positions. It does not
claim their physical meaning. Only 0/1/2/3/4/5/7 are accepted; state 6 and values
8..255 still reject the whole report. Packet checksums and header/count/stride/
image/bounds/duplicate-ID checks remain intact. SPI, firmware, rolling recovery,
timeout and cleanup are unchanged. The preceding one-extra-transfer policy is
retained for a controlled contact-state comparison, without a benefit claim.

The actual candidate emitter passes all 256 state-byte tests, active-to-1/2
release without coordinates, whole-report atomic refusals and malformed bounds
checks under sanitizers. All eight privately captured reports replay as inactive
with zero positions. Original acquisition/recovery tests and exact #35 warning-free
W=1 build/import/vermagic checks pass. V4 host capture/collector/receipt/iOS-return
tests and source-pin preflight pass. Prior sealed inputs are preserved.

The attempted same-boot replacement stopped at a read-only precheck: this exact
kernel has CONFIG_MODULE_UNLOAD disabled. No module unload or kernel modification
was attempted. A fresh DFU is needed to load this changed worker.

Next: unchanged #35 cold payload, `run-j72-touch-inactive1235.py --stage` before
old touch/radio, original self-check/physical restore, Wi-Fi/RAM desktop, fresh
read-only storage, owner input and qualified hub. Then use the separate V4
session/observer and iOS-return helper. Zero-layout/SPI/timeout health gates
remain. A failure is captured before provider shutdown. No internal writes are
authorized. No long-run reliability or charging improvement is yet proved.

```sh
python3 test-emitter.py j72_touch_session.c
```

Optional report arguments are private decoded captures and are not included.
[Source hashes/results](RESULT.json), [V4 host references](workspace-reference-v4/).
Firmware/calibration includes, binaries and raw device logs remain private.
