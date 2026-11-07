# Omarchy-A on iPad Air 1 Cellular (J72)

Experimental Orchard/Omarchy-A support for **iPad4,2 / J72AP / Apple A7**.
Current as of **7 November 2026**. The desktop runs from internal storage;
iOS is retained as a bootable charging fallback.

## What works now

| Feature | Status |
| --- | --- |
| Installed desktop | Internal ext4 root and FAT boot; PIN login, menu and Foot terminal |
| Display and input | Portrait display, brightness, touchscreen, Home button and on-screen keyboard |
| Wi-Fi | Internal BCM43241 connected; HTTPS, SSH and unplugged desktop use demonstrated |
| Battery reporting | Percentage, voltage, current, temperature and external-power indication |
| Speaker audio | Both channels heard; normal PipeWire output works |
| Guarded charging | Positive net charging measured on the qualified powered hub; reliability under load remains open |

**Important limits:** startup still needs a computer. The working installed
startup goes through RAM recovery; direct bare-loader launch has an unresolved
heap error. Audio startup is enabled but not yet verified after a fresh boot.
Linux charging is not dependable for unattended use: a supervisor timeout
stopped charging during the browser test. Firefox/YouTube remains too slow and
has exhausted memory; usable video playback is not qualified. Use iOS for
reliable overnight charging.

[Detailed current support and measurements](J72-PROGRESS.md).

## How to replicate

1. **Use the exact target.** iPad Air 1 Cellular, iOS 12.5.7 / 16H81;
   DFU identity CPID `0x8960`, BDID `0x12`. J72b and other iPads are different
   devices. The tested host is a Pi 4 running native aarch64 Linux.
2. **Prepare the source.** Clone this repo and follow the
   [replication guide](QUICKSTART.md) and
   [pinned Orchard/kernel build instructions](code/current/README.md).
   Use the checkout's `bin/orchard`, matching 4 KiB kernel/modules and native
   ARM64 host tools. Keep upstream components unchanged except for the stated
   J72 hardware differences.
3. **Prove RAM boot first.** Use a known data cable directly to the Pi.
   Verify Linux, serial access and a normal return to iOS before adding the
   desktop, native touch and Wi-Fi. Supply your own verified private firmware
   and panel calibration.
4. **Add the current hardware pieces.** Source and instructions are included
   for [Wi-Fi startup](code/current/wifi/README.md),
   [guarded charging](code/current/charging/README.md) and
   [speaker audio](code/current/audio/README.md).
5. **Treat installation as a separate operation.** Measure your own APFS/GPT
   layout, retain iOS recovery/charging, and review the exact resize/install
   plan. Do not copy another device's partition identifiers or shrink limits.

This repo includes source snapshots, build instructions and qualification
checks. **It is not yet a turnkey installed release:** complete clean-checkout
release/deployment, private-input provisioning and the remaining reliability
checks are listed explicitly in the [replication guide](QUICKSTART.md#what-is-not-yet-a-one-command-recipe).
Apple firmware, unit calibration, credentials, raw logs and binary images are
not distributed.

Upstream projects: [Orchard](https://github.com/OrchardLinux/orchard),
[Omarchy-A](https://github.com/OrchardLinux/omarchy-a),
[Apple Linux kernel](https://github.com/OrchardLinux/linux).
