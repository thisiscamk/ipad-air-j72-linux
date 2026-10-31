# Charging while connected to the Pi

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
- [ ] Request a changed, prepared DFU and measure current plus stable data.
- [ ] Qualify sustained net charging, source transitions and desktop workload.

The iPad remains charging in iOS through the hub. The next guarded hub test is prepared. The host kernel
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

## Prepared next DFU: short Linux test with data retained

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
