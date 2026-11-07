# Current J72 status

Updated 7 November 2026. This page supersedes the dated reports; it separates
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
| Battery UI | Percentage, current, voltage and temperature; external-source reporting | Controller snapshots become stale when supervision stops; calibration is not established |
| Guarded charging | Positive net charge on the tested powered JCH377 port, with restoration and thermal holds | Supervisor failed its timing watchdog under the later browser workload; no unattended/overnight Linux charging claim |
| Charging reconnect | Automatic reconnect admission and later positive current observed in the same boot | Fresh-boot automation and arbitrary sources are not qualified |
| Speakers | Both channel tones heard; ALSA and unchanged PipeWire/WirePlumber playback transfer pass | Enabled startup service has not passed a fresh boot; hot-overlay teardown reference warning remains |
| YouTube/Firefox | Page/player loads | Memory exhaustion, swapping and very slow UI; audible usable browser playback not confirmed |
| Headphones/microphone/Bluetooth/cameras/cellular | No qualification claimed | Future work |
| PC-free startup | None | No demonstrated iOS-app handoff or standalone startup after shutdown |

## Charging: measured results and present failure

The tested policy used a nominal **1,050 mA USB input limit** on the marked
powered JCH377 data/charging port, whose paired iOS checks reported 5 V / 1,500 mA.
That is not battery charging current or authorization for every hub/charger.

- Bounded qualification: 7,200.06 seconds, **+366.693 mAh net**, maximum 37.0°C.
- Separate continuous-mode observation: 2,736.663 seconds, **+255.8135 mAh net**,
  maximum 37.2°C.
- Restoration/stop, hold/restart, source-loss and supervisor-failure checks were
  exercised. Reusable profile code requires each installation's own evidence.
- Later, during the browser session, the supervisor reported a slow status
  read and hit its watchdog. Charging stopped and baseline restoration passed.
  This failure was not cleared or bypassed.
- The iPad subsequently restarted unexpectedly. The owner found the iOS battery
  very low and confirmed iOS charging; depletion is plausible, not a proven reset cause.

**Do not interpret “connected” or an old positive current snapshot as live
charging.** Fresh direct battery readings, controller/service state and signed
current matter. Do not rely on this Linux setup for unattended charging yet.
Current failure/low-battery protection takes priority over raising current limits.

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
