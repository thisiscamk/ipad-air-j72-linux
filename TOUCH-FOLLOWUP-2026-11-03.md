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
lead from prior private J72 captures and Orchard's J71b fix. Its initial device checks now pass, but it may not fix the three layout
rejections. The original complete
wire/contact checks remain unchanged.

## Next changed DFU

Use the unchanged #35 cold payload, stage the new touch candidate first, then
Wi-Fi/desktop/fresh read-only storage and owner input checks. The new driver
uses `--touch-resync35`, requires its policy/counters and retains the zero-layout
health gate. If input passes, continue the guarded charging test in that same
boot. If it fails, capture the actual rejected packets before iOS return.
No internal write or storage installation is authorized.

## New boot: initial checks pass

The distinct touch worker passed its existing start/stop self-check, firmware
health and physical restoration. Wi-Fi, HTTPS, pinned SSH, RAM desktop and fresh
native read-only checks pass. The initial snapshot has 706 valid frames with
zero rejected layouts, SPI errors or timeouts. It also has 84 eligible headers,
zero recovered resync frames and 84 resync failures: the extra retry has not
proved useful. Owner input verification and the longer guarded test are pending.
Charging has not started in this boot.

## Owner check passed; actual refusal captured

The owner confirmed menu, Foot typing and keyboard reopening, then moved to the
powered hub. The next input health check found one rejected layout. No charging
module was loaded and no current override occurred. The test stopped before
charging. The stopped-ring capture now works: the sole rejected report was
retained and its checksum/layout checks reproduced the refusal. It is a native
`0x44` report, header 24, one contact, stride 30, **contact state `1`**. Our decoder
accepts only 0/3/4/5/7, so it rejects this state before emitting any event.

Final input counts: 4,502 valid frames, one layout rejection, zero recoveries,
SPI errors or timeouts. There were 495 eligible extra retries and zero recovered
resync frames. This boot does not establish a benefit from that transport change.
Normal desktop/input/provider cleanup and independent baseline `02` pass. A
normal iOS reboot completed; the owner unlocked and confirmed charging. Two
fresh diagnostic samples independently confirm charging on the hub.

The [upstream Apple Z2 parser](https://linux.googlesource.com/linux/kernel/git/torvalds/linux/+/81122fba08fa3ccafab6ed272a5c6f2203923a7e/drivers/input/touchscreen/apple_z2.c)
reports states 3/4 as active and other states as inactive. That is a reference
for a narrow follow-up experiment, **not proof of the meaning of state 1 on J72**.
We will retain complete packet/bounds/duplicate-ID validation and reject other
unknown states. No parser change is yet qualified. The three uncaptured reports
from the prior attempt remain unexplained. Raw packets stay private.

The [separate state-1 inactive candidate](code/touch/state135/) now passes actual
emitter/private-report replay, exhaustive state tests, warning-free build/import
checks and V3 host preflight. It is device untested. The device remains in iOS
charging; use the new runbook selector for the next changed DFU.

## State-1 worker: remaining reports are state 2

The owner confirmed menu, Foot typing and keyboard reopening. The worker processed
seven state-1 frames, then the hub health gate found seven other rejected layouts.
All seven were captured before shutdown. They have valid wire checksums and the
same native structure, with contact state **2**. At stop: 14,713 valid frames, one
bounded recovery, zero SPI errors/timeouts and stop reason 0. Normal cleanup,
firmware health and independent baseline pass. No charging module/current override
was used. None of 1,891 extra retries recovered a frame.

A read-only same-boot replacement precheck found CONFIG_MODULE_UNLOAD disabled
in this exact kernel. No unload, force operation or kernel modification occurred.
The selected V3 iOS-return helper now handled the absent charging module normally;
iOS returned, the owner unlocked and two fresh diagnostic samples confirm charging
at 70% on the qualified hub.

The [next inactive-state-1/2 candidate](code/touch/inactive1235/) preserves active
states 3/4 and all other packet/layout/refusal/cleanup rules. Actual C emitter
replay of the earlier state-1 report plus all seven state-2 reports, exhaustive
state/malformed-report checks, original acquisition/recovery tests, warning-free
build/import checks and V4 host preflight pass. It is device untested. Another
DFU is needed because this kernel cannot replace the loaded module.
