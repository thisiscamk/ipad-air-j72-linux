# 3 November follow-up: charging stopped at the input gate

The owner confirmed menu, Foot typing and keyboard reopening, then moved the
running RAM desktop to the same powered-hub port. Wi-Fi survived. The known
same-UDC rebind restored both USB shells after a stale configured state.
Fresh native storage inventory and six read-only checks passed; no internal
filesystem was mounted or written.

At fixed brightness 802, the five-minute idle recording completed. The new
charging module loaded **disabled**, with baseline unchanged. The precharge
health check then found **three rejected touch layouts** at 24,512 valid frames.
Input was still active, with zero recoveries, SPI errors, timeouts or stop reason.
The rejected reports were not emitted as valid input. The guard stopped the
trial before arming: charging `used=0`, cycles=0 and active=0. **No 90-minute
charging observation or current override occurred.**

Normal desktop/input/radio cleanup and independent baseline `02` pass. iOS
returned. Diagnostics initially could not confirm charging; the owner unlocked
with the PIN and confirmed it. Two later iOS diagnostic samples confirm charging
on the qualified hub. The iPad remains charging in iOS.
[Sanitized result](code/charging/voltage-resume35/DEVICE-STAGE-RESULT.json).

## Evidence gap and preparation

The main driver saved active health and kernel text. A separate stopped-ring
collector lost the race with shutdown/reboot and timed out. The three raw
layout reports were not captured, so their subtype/cause remains unknown.

A new failure path now stops the charging owner, verifies baseline, normally
stops desktop/input and exports the stable ring **before** provider shutdown.
It preserves API failure/state-4 status and never relaxes the kernel export
guard. Six host tests cover successful classification of a synthetic invalid
type, unrestored baseline refusal, active-session refusal, failed stop APIs,
wrong export size and shell syntax. The synthetic type is not evidence of the
actual rejected report type.

The [separate data-phase resync candidate](code/touch/data-resync35/) builds
warning-free and passes acquisition/recovery tests, including every advertised
16-bit length. It addresses checksum-valid E1 headers in data replies, a known
lead from prior private J72 captures and Orchard's J71b fix. It is **device
untested** and may not fix the three layout rejections. The original complete
wire/contact checks remain unchanged.

## Next changed DFU

Use the unchanged #35 cold payload, stage the new touch candidate first, then
Wi-Fi/desktop/fresh read-only storage and owner input checks. The new driver
uses `--touch-resync35`, requires its policy/counters and retains the zero-layout
health gate. If input passes, continue the guarded charging test in that same
boot. If it fails, capture the actual rejected packets before iOS return.
No internal write or storage installation is authorized.
