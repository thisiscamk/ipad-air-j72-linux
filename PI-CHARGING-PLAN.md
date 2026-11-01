# Latest result: voltage guard after 27.2 minutes

The reduced-brightness continuous-input run reached **27.2 minutes**, with
768 distinct guard readings: 767 positive, one negative transient, mean
**+449 mA**. At **4.201 V / 37.5°C**, the unchanged **4.2 V voltage guard**
ended charging. Both independent PMIC snapshots confirmed `04c0=02`; the
recorder and source monitor are stopped and logs retained. This was not a
thermal stop or a full-hour pass. [Complete sanitized result](code/charging/hub1050-session/CONTINUOUS-DESKTOP-RESULT.json).

Next: qualify source-aware autonomous charging and the full operating range,
retain battery protections, and repeat a longer usability run with suitable
starting headroom. The existing test ceilings remain unchanged. SOC load
jumps still do not establish charge gained.

# Earlier: continuous-input, lower-brightness hub trial started

The controlled RAM move to the known powered JCH377 returned USB data; the
desktop and input restarted in the same boot. The new-payload helper retains
the exact #33 charging worker, source qualification and all existing guards.
At 802/2047 brightness, initial settled readings were **+449…+469 mA at
36.6 C**, with no guard faults. The owner confirmed the desktop, charging
symbol and input. This bounded test has started; its maximum is one hour,
and a guard can stop it earlier. Full duration and final restoration are
not yet qualified. Keep cables fixed; the host source lease remains required.

The earlier side-bar/keyboard resize loop was stopped before this trial.
That changed workload and brightness mean this is not an isolated comparison
of screen brightness alone. SOC jumps still do not establish charge gained.

# 1 November: temperature test cutoff; owner charging in iOS

The revised continuation ended at **38.1 C**, exceeding its conservative
38.0 C test ceiling. It retained **526 positive readings at +36…+209 mA**.
The worker reported restored=1, restore_failed=0 and a temperature guard
fault. It did not finish an hour. The owner rebooted to iOS for charging
before an independent final PMIC snapshot or remaining RAM logs could be
retrieved. The host monitor and read-only export are stopped.

Next, reduce Linux power use and qualify sustained operation within the
existing limits. Earlier dimmed observations were cooler and had higher
net current, but the conditions were not isolated as a controlled thermal
comparison. Continuous touch is built/offline-tested and awaits a boot
check. No internal-storage installation is authorized.

# 1 November: charging decoupled from the touch-test timer

The dimmed continuation charged for **1,033.724 seconds**, then stopped
when the touch session naturally completed its diagnostic window.
Restoration to `04c0=02` succeeded; no battery guard fault was recorded.
485 unique settled host gauge readings were positive at **+438…+485 mA**,
maximum **37.4 C**. It did not complete a full 30-minute run. Its worker
sample counter retained only the final 295-second window, so that count
remained zero; the host gauge logs provide the stated observations.

A revised [60-minute continuation](code/charging/hub1050-session/) is active,
with sampling timing fixed and charging independent of the touch window.
A controlled touch stop/healthy cleanup/restart preserved charging. Full
duration and restoration on this new worker remain pending. Touch and
normal brightness are owner-confirmed again. The same battery and source
limits remain; autonomous detection and capacity-trend qualification are open.

# 1 November: five-minute desktop charging passed

The desktop-loaded fixed 1,050 mA session completed **300.002214 seconds**
with **140 positive retained readings at +178…+216 mA**, versus a −849 mA
baseline. USB data remained attached, all guards were clear, maximum
recorded temperature was **37.8 C**, and original `04c0=02` restoration
was verified. The owner confirmed the new battery percentage indicator
and charging symbol. [Exact source and validation](code/charging/hub1050-desktop/).

A separate continuation is running with display brightness reduced from
1604 to 802 out of 2047. Initial live gauge reads are approximately
+470 mA net charging at 37.3 C. This longer duration is **not yet qualified**;
it is timed and retains battery, source, USB and restoration guards.
Neither experiment establishes autonomous charger detection or reliable
percentage gain under changing loads. The reviewing Orchard PR is unchanged.

# 1 November: five-minute powered-hub charging passed

The fixed 1,050 mA test completed **300.006 seconds**, retaining **140 positive
samples at +153..+209 mA**, from -830 mA baseline. USB data stayed connected;
the host made 529 active-phase status reads. Maximum recorded temperature was
37.2 C and guard voltage 4.139 V. No battery/source faults occurred. Automatic
rollback passed with independent 0x04c0=0x02 readback, and the recorder stopped.

This qualifies the five-minute diagnostic workload on the source-qualified
powered JCH377 port. Autonomous charger detection, source transitions and
full desktop charging remain open. Battery percentage jumped under load
changes, so a percentage increase is not claimed as charge gained.

The [measured five-minute worker source](code/charging/hub1050-long/) is now
included beside the [short worker](code/charging/hub1050/). Both are also in
Orchard PR #43 for interim implementation review. Wi-Fi will be a separate
follow-up once it works. No internal-storage write is authorized.

# 1 November: 1,050 mA / 30-second powered-hub test passed

All **12 retained worker samples** were positive at **+177..+213 mA** battery
current, from **-809 mA** baseline. The measured active duration was 30 seconds.
USB data stayed connected. Battery guards reported no faults; the last guard
sample was 74%, 36.8 C and 4.126 V. Original input-limit restoration passed:
inactive, disarmed, restored=1, restore_failed=0, error=0, and independent
PMIC 0x04c0=0x02 readback. The RAM recorder was stopped and logs retained.

The last host lease renewal raced normal completion and was refused by the
terminal target. The watcher exited with an error; independent target status
and timestamps establish successful duration and restoration. The later
candidate checks terminal state on this race and still propagates errors
while a trial is active.

The [actual short-test source](code/charging/hub1050/) is published with tests
and sanitized validation. A separate **1,050 mA / five-minute** worker is
staged unarmed in the same RAM boot, gated on the actual successful short
result and restoration. It retains all battery/source/USB guards. Sustained
charging and automatic source detection are still unqualified.

# 1 November: brief net charging with hub data; pack guard stopped trial

The source-qualified nominal **1,250 mA / 30-second** comparison started in
the working #33 RAM image after direct boot and controlled transfer to the
powered JCH377 marked charging/data port. The host continuously verified the
qualified USB port and renewed a 2.5-second lease. USB data stayed available.

- Baseline battery current: **−771 mA**.
- RAM recorder readings during the short active interval: **+373, +368 and
  +201 mA**, with voltage **4.196, 4.200 and 4.200 V**.
- The worker stopped after **5.43 seconds**, reporting `-ERANGE` from its pack
  guard. The original worker did not record which pack field failed. The
  voltage boundary is a hypothesis supported by the recorder, not a proven
  identification of the exact failed reading.
- Automatic restoration passed: inactive, disarmed, `restored=1`,
  `restore_failed=0`, and independent `0x04c0=0x02` readback.
- The first five seconds are excluded from retained worker statistics;
  **zero retained worker samples** passed before the stop. The five-minute
  1,250 mA trial remains **blocked**. Brief positive recorder readings do not
  establish sustained charging.

The subsequent **1,050 mA / 30-second** comparison passed as described above.
It ran in the same RAM boot. It retains the same source, voltage, temperature, SOC, current and
rollback guards and records the exact failed guard values. No safety bound
has been raised. Sustained qualification is pending.

The #33 target kernel cannot unload modules. The completed 1,250 mA worker
remains resident, disarmed and permanently used; the new worker has a distinct
module identity. A planned same-name module replacement was refused before
any hardware change. Future batch planning must account for this constraint.

# Charging while connected to the Pi

## 31 October: powered-hub trial completed; back in iOS

The direct Pi RAM boot and controlled transfer to the powered JCH377's
marked charging/data port passed. The desktop, USB-backed root, NBD and
touch worker were stopped before the cable move. Native NCM data remained
available throughout the subsequent fixed 850 mA / 30-second trial and
rollback: 49 successful host reads over about 101 seconds, with no read
errors.

Battery current was −773 mA before the trial. The worker retained 12 trial
samples spanning **−10 to +37 mA**. This is near break-even with brief
positive readings, **not sustained net charging**. Host gauge snapshots use
a different sampling schedule and can retain an older reading; they must
not replace the worker's mixed-current range.

Automatic restoration passed: `used=1`, `active=0`, `armed=0`, `restored=1`,
`restore_failed=0`, `error=0`, and separate PMIC readback confirmed
`0x04c0=0x02`. Data remained usable after restoration. The recorder was
stopped and a normal reboot returned the device to iOS on the same hub.
iOS diagnostics confirmed external power and `BatteryIsCharging=true`.
No further DFU is planned tonight. Internal storage and the Pi kernel are
unchanged.

Next: finish J72 source/controller mapping and adapt the existing
[Orchard charging architecture](ORCHARD-POWER-PLAN.md), then qualify source
transitions, sustained positive current and charging with the desktop.
A new DFU will be requested only after a concrete changed test is prepared.

Goal: keep USB networking, shell and the desktop root available while the
iPad charges, without moving between the Pi and wall charger. This is a plan;
no Pi-powered charging test has been performed.

## Constraints found on 31 October 2026

- Raspberry Pi 4 has **1.2 A total across its USB ports**, per the
  [Raspberry Pi hardware documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#maximum-power-output).
- This host has a bus-powered SSD whose descriptor declares **896 mA**.
  That is a declared maximum, not measured draw. An additional 850 mA iPad
  ceiling would exceed the shared budget when compared with that declaration;
  spare current must not be assumed. Host undervoltage history currently
  reports zero; that does not qualify a new combined load.
- A USB 2.0 device is limited to **500 mA on a standard downstream port**,
  including when plugged into a USB 3 port. The Pi's aggregate electrical
  budget does not grant the iPad a larger USB allocation. See
  [USB-IF peripheral power policy](https://compliance.usb.org/index.asp?Format=Standard&UpdateFile=Policies).
- The separate-wall 850 mA test produced only +20 to +51 mA net battery
  current with desktop/input stopped. Lower standard-port power may reduce
  discharge without charging. Battery current and USB input current are
  different measurements; do not equate them or infer a precise threshold.

## Software clue

The measured target kernel sets `CONFIG_USB_GADGET_VBUS_DRAW=500`.
Configfs initializes `MaxPower` from that value, and the composite driver
calls `usb_gadget_vbus_draw` when configured. The init script does not
change `MaxPower`. Actual enumeration descriptors must be checked next boot.

In that source tree, DWC2 forwards the current request only to the legacy
USB PHY (`uphy`). The S5L8960 device tree supplies a generic `usb2-phy`, whose
AUSB driver does not implement charger-current forwarding. With that generic
PHY selected, the legacy pointer remains absent and the draw callback returns
`-ENOTSUPP`. This is a concrete candidate for why gadget enumeration did not
raise the inherited 100 mA PMIC ceiling, but the running callback path has not
yet been traced. Advertising a larger descriptor does not program the PMIC
or prove that a host can provide the power.

## Two paths to qualify

### Direct Pi port: bounded standard-current operation

1. Confirm Pi supply rating and account for SSD/other USB loads; qualify the
   total budget before any higher load. Do not unplug the host's mounted SSD.
2. In one fresh RAM boot, verify live descriptors, host topology, target
   configuration and PMIC/gauge baseline while NCM stays connected.
3. Prepare a separate Pi-source experiment with a fixed current no greater
   than the valid configured USB allocation (initially a conservative
   425 mA ceiling within a verified 500 mA configuration), independent rollback,
   battery guards and a host-health monitor. The existing **wall-only**
   850 mA worker is not authorized for a direct Pi port.
4. Measure net battery current and stable USB shell/network operation.
   Reduce display/idle power in separately measured comparisons if needed;
   restore each setting. Repeat under the desktop load only after idle passes.
5. Integrate configured/reset/suspend/disconnect limits through proper
   charger/USB ownership; a userspace configured-state poll is insufficient.

Net charging from the direct port is a goal, not a promised result.

### Powered hub with a charging-and-data port

Use a hub with its own power supply and a documented **BC1.2 Charging
Downstream Port (CDP)** or another explicitly supported simultaneous
charging/data mode. CDP supports data plus charging; a Dedicated Charging
Port does not carry data. See [Microchip's port definitions](https://developerhelp.microchip.com/xwiki/bin/view/applications/usb/power-delivery/battery-charging/).

```text
Pi USB data ── powered hub ── charging + data port ── iPad
                    │
               hub power supply
```

A plain powered hub may still limit each data port to 500 mA. A port marked
charge-only does not meet this goal. Check the exact model's per-port and
total ratings, simultaneous operation, source signalling and upstream power
isolation before selecting it. No splitter cable or connection joining two
power sources is part of this plan.

First qualify DFU/Pongo/Linux data through the selected hub using the existing
exact-device launcher. Then identify its charging capability on J72 and
prepare a bounded test that keeps the data cable attached. Initially retain
the previously tested 850 mA ceiling, only after source qualification; a
1.5 A port rating is not permission to raise the target limit to 1.5 A.
Record current/temperature, USB errors, restoration and iOS recovery before
longer or desktop-loaded trials.

## Current checklist

- [x] Audit Pi power specification, attached SSD descriptor and target source.
- [x] Identify the generic-PHY/current-request integration gap as a candidate.
- [x] Confirm official Pi 4 supply, JCH377 model photo and owner-rated 5 V / 4 A hub adapter.
- [x] Verify self-powered hub, paired iOS data and repeated iOS charging/source reports; build/check a separate guarded hub trial.
- [x] Direct RAM boot, controlled hub transfer, bounded current trial and stable NCM data.
- [ ] Qualify sustained net charging, source transitions and desktop workload.

The iPad is back in iOS and machine diagnostics confirm charging through the hub. The bounded trial is complete; the next automatic-policy test is not ready yet. The host kernel
and iPad internal storage remain unchanged.

## Owner's available hub: JCH377 confirmed

The owner supplied a photo confirming **j5create JCH377**, confirmed the
marked charging port and reports a **5 V / 4 A** adapter. The Pi uses its
official Pi 4 supply. The [manufacturer specification](https://en.j5create.com/pages/jch377-specifications)
lists one 2.4 A fast-charging USB-A port plus six other data ports; the
[quick guide](https://download.j5create.com/qig/JUH377_JCH377_qig.pdf) identifies
the marked charging port. Raw owner photos and identifying label data stay
private.

The connected hub enumerates as self-powered. The iPad enumerates through
its marked port at 480 Mbit/s, pairing validates, and three repeated normal
iOS diagnostic reads report `IsCharging=true`, `ExternalConnected=true`,
`ExternalChargeCapable=true` and adapter details of **5 V / 1.5 A**. This
establishes simultaneous iOS charging reports and working data access;
it does not measure physical USB input current or independently identify the
charging protocol. The iOS USB descriptor still declares 500 mA, distinct
from its reported charging-source allowance.

The owner reported a Pi hang while changing only the hub/iPad cables; the
SSD was not moved. After restart the hub/iPad enumerate and diagnostic reads
work. Only the current boot's journal is available, so the hang's cause is
unresolved. The SSD remains attached directly and holds the Pi's running root
filesystem. Keep the current cables fixed for the next test.

The verified topology is Pi data -> powered JCH377 -> marked charging port
-> iPad, with the hub's own adapter and the Pi's own official supply.

Before requesting a DFU:

1. Identify the exact model, marked charging port and matching adapter.
2. Connect the empty powered hub using its proper data lead; inspect its
   enumeration and self-powered reporting without moving the mounted SSD.
3. With iOS running, verify that the intended port supports data enumeration
   while the iPad reports charging. That does not measure net charge or
   prove BC1.2/CDP negotiation; retain that distinction.
4. Resolve the port's simultaneous charging mode and current entitlement,
   then prepare a separate guarded **hub-source** trial. The existing
   wall-only 850 mA module must not be reused unchanged for the hub.
5. Qualify a bounded current comparison with NCM active and host/target
   logging, followed by restoration and USB/iOS recovery. Only then extend
   duration or add the desktop workload.

No new hardware purchase is proposed before checking the available hub.

## Prepared next DFU: direct boot, RAM handoff, then charging

The separate hub-source worker keeps the measured 850 mA ceiling, 30-second
independent rollback and battery guards. It changes the source arming token
and parameter, preserving the measured wall variant. It performs no current
write at load or arm; one instructed physical Home press triggers one trial.
The host checks the dynamically discovered, iOS-qualified physical port, hub
identity/revision, self-powered descriptor and current host boot before
staging or arming. Rebooting the host requires source requalification. These
checks are not continuous electrical source detection.

Native ARM64 `W=1` build/modpost, 15 policy fault/normal cases, ten battery
guards, 12 synthetic topology tests and three invalid CLI/source refusals
passed. The policy core and kernel import list match the wall-tested worker.
The original #33 target image and host kernel are unchanged. **The hub Linux
trial is not yet device tested.**

In the next RAM boot, verify baseline configuration/current and clean desktop
input/root teardown, then monitor USB and battery before/during/after the
bounded test without moving cables. If the inherited PMIC ceiling differs
from the worker's required 100 mA baseline, preserve that boot and inspect it
read-only instead of forcing a setting. Require final restoration, stable
data and iOS recovery before extending duration or adding desktop load.

## Boot-path update: direct Pi boot before the hub transfer

Two isolated boot attempts through the JCH377 reached exploit setup and
Checkmate but did not reappear in download mode. The second used the
launcher’s existing exact-iPad-port power reconnect; port off/on completed
and power was restored, but Pongo still did not start. No Linux charging
trial ran. This does not invalidate the observed iOS charging/data path.

The next test changes the boot transport to the previously working direct
Pi connection. After automatic startup, the desktop/root, NBD and touch are
stopped and health/restoration checked. A separate one-shot RAM script
unbinds the gadget before the owner moves the iPad cable to the marked hub
port. One Home press there rebinds USB. The script restores the original UDC
on error where possible; its Home wait is bounded to 20 minutes.

Only after live NCM, the qualified hub port, exact kernel/model and completed
transfer-handler exit are verified can the separate charging worker be
staged. The USB-reconnect Home press and charging-test Home press are
distinct instructed steps. No charging worker runs on the direct Pi port or
during the move. If the transfer fails, inspect the screen and return to iOS
on the hub; no repeated reconnects are planned.

Shell syntax, wrong-host refusal before state creation, the existing source
guards and artifact preflight pass. **The new RAM USB transfer has not yet
been device tested.** It requires one new direct-connected DFU for the whole
transfer/current batch, if the transfer succeeds. This is one initial cable
move to qualify the hub path, followed by fixed cabling during charging.

## Earlier checkpoint: RAM handoff and unarmed worker

The direct Pi boot passed. After healthy desktop/root/NBD/input teardown,
the one-shot gadget handoff reached the JCH377 marked port: native NCM
enumerated at 480 Mbit/s, the RAM shell responded, transfer state reported
`REBOUND` and its handler exited. Battery read 89%, 4.091 V, -750 mA and
37.1 degrees C before the current trial. The visible 850 mA trial is staged
**unarmed**, with input limit still `0x04c0=0x02`; no hub charging result is
claimed yet.

The [Orchard power integration review](ORCHARD-POWER-PLAN.md) identifies
existing generic-PHY current reporting, source-event ownership, early BC1.2
detection and PMIC readback handling to reuse after verifying J72 mappings.
