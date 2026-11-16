# Current J72 status

Updated 16 November 2026. This page supersedes the dated reports; it separates
physical-device results from host preparation. [Start guide](QUICKSTART.md).

## Device and working system

- iPad Air 1 Cellular: iPad4,2, J72AP, A7/S5L8960X, CPID `0x8960`, BDID `0x12`.
- Retained iOS 12.5.7 / 16H81; Amethyst supplies temporary root SSH when needed.
  Jailbreak root access does not survive a normal restart without reapplication.
- Installed Omarchy-A with `7.3.0-rc1-j72-pw1-orchard-apple-4k`, 4 KiB pages.
- Internal ext4 root and FAT boot, with the original iOS APFS partition retained.
  Approximately 50 GB was released for Linux; the earlier 9 GiB stage is history.
- Pi-assisted direct USB boot, then the powered hub for the qualified charging
  tests. The desktop has also worked unplugged after startup.

## Support matrix

| Feature | Physical evidence | Remaining limitation |
| --- | --- | --- |
| Display/brightness | Portrait desktop, menu, terminal and brightness changes confirmed | Software rendering; demanding pages are slow |
| Touch/Home | Native touch, menu/Home and terminal interaction confirmed | Earlier long-session stops needed recovery; preserve diagnostics |
| On-screen keyboard | Manual icon and terminal-tap reopening confirmed | Test against the exact desktop/client combination |
| Storage | Native read/write/flush, installed ext4 root and mounted FAT boot demonstrated | Native bare-loader launch has a heap failure; recovery-to-installed startup is the working route |
| Wi-Fi | BCM43241 rev 6, association, HTTPS and SSH demonstrated | Private matching firmware and J72 HSIC startup required |
| Battery UI | Percentage, current, voltage, temperature and physically qualified external-source reporting | Pack calibration is not established |
| Guarded charging | On-device autonomous controller sustained +279 to +423 mA, restored on unplug and resumed after reconnect | Service is installed and enabled; verify automatic startup on the next natural Omarchy boot |
| Charging reconnect | Physical unplug restored 0x02; transitional source/PMIC states stayed stopped; reconnect resumed automatically | Arbitrary sources and other devices are not qualified |
| Speakers | Both channel tones heard; ALSA and unchanged PipeWire/WirePlumber playback transfer pass | Enabled startup service has not passed a fresh boot; hot-overlay teardown reference warning remains |
| YouTube/Firefox | Page/player loads | Memory exhaustion, swapping and very slow UI; audible usable browser playback not confirmed |
| Headphones/microphone/Bluetooth/cameras/cellular | No qualification claimed | Future work |
| PC-free startup | None | No demonstrated iOS-app handoff or standalone startup after shutdown |

## Charging: autonomous on-device qualification

The tested policy uses a nominal **1,050 mA USB input limit** on the marked
powered JCH377 data/charging port, whose paired iOS checks reported 5 V /
1,500 mA. That is not battery charging current or authorization for every
hub, charger, battery or iPad.

- The earlier host-lease supervisor passed long charging runs but later stopped
  on a slow status read under browser load. It is now disabled.
- The replacement controller runs on the iPad and does not depend on Pi uptime,
  USB enumeration or a host lease. It retains the one-hour window, independent
  250 ms restoration deadline, PMIC ceiling checks and pack safety limits.
- A ten-minute live run stayed at **+279 to +423 mA**, raised the gauge from
  60% to 63%, and held 35.8–36.1 C with zero controller/restoration faults.
- Physical cable removal restored PMIC `0x04c0` to `0x02`. Transitional reporter
  `ENODATA` and reconnect PMIC-settle `EPERM` both keep charging stopped. Exact
  online, valid PMIC invariants, fresh safe battery data and cooldown are all
  required before automatic resume.
- Explicit stop/restoration passed. The exact qualified module and service are
  installed; the service is enabled and active. The next natural Omarchy boot
  still needs to confirm automatic startup, so iOS remains retained as fallback.

Source and sanitized results are under
[`code/current/charging/autonomous`](code/current/charging/autonomous/).

## Audio: exactly what passed

The CS42L81 codec is reused; A7 needs MCA-v1 and SmartIO adaptations. Both
48 kHz stereo S16 channel tones were audible. The owner thought they came from
different sides, but separation was difficult to judge. PipeWire discovered
stereo output and a normal `pw-play` transfer completed. PCM closed and MCA
suspended when idle. No microphone or headphone result is claimed.

Audio was installed and enabled on the development iPad. **That is not proof
of automatic startup:** a fresh boot and audible browser playback remain open.
Source and build-only instructions: [audio](code/current/audio/README.md).

## Reproducibility scope

[Current source](code/current/README.md) now includes pinned Orchard/kernel
patch snapshots and reusable Wi-Fi/charging/audio pieces. The older 7.0.12 lab
code is retained for research, not mixed into the current build.

A clean-checkout build/deploy of the complete installed configuration has not
been qualified. Private inputs and installation/source-admission gaps are
listed in the [replication guide](QUICKSTART.md). No single DFU count or promised
installation duration is justified. Upstream PR status is not a support claim.
