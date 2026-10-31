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
- [ ] Obtain Pi supply rating and any existing powered hub's model/rating.
- [ ] Select and qualify the power/data path; prepare guarded test artifacts.
- [ ] Request a changed, prepared DFU and measure current plus stable data.
- [ ] Qualify sustained net charging, source transitions and desktop workload.

The iPad remains charging in iOS. No DFU is requested yet. The host kernel
and iPad internal storage remain unchanged.
