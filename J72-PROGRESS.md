# Linux and Omarchy A on an iPad Air 1 Cellular (J72)

Progress report as of 29 October 2026. This is a hardware bring-up report for one iPad, not a general installation guide or an Orchard hardware profile.

## Device and approach

The test device is an iPad Air 1 Cellular (`iPad4,2`, `J72AP`) with an Apple A7 (`CPID 0x8960`, `BDID 0x12`) and iOS 12.5.7. The host is a Raspberry Pi 4 running Debian 13 on aarch64. The experiment uses a **RAM-only, tethered boot**: checkm8/PongoOS → m1n1 → a 4 KiB-page AArch64 Linux kernel and initramfs. The iPad's internal storage and iOS installation have not been changed. The Pi's existing kernel has also been left alone.

The work builds on [Hoolock Linux's A7 documentation](https://github.com/HoolockLinux/docs/blob/master/features/A7.md), its [PongoOS boot method](https://github.com/HoolockLinux/docs/blob/master/tutorials/SETUP_pongoOS.md), and the [Pomme build pipeline](https://github.com/xenoaitham/pomme). [Another J72 Omarchy A experiment](https://github.com/Phoenix2479/ipad-air-linux) provided useful precedent; the results below are measurements from this device.

## Confirmed on the device

| Area | Result |
| --- | --- |
| Boot | PongoOS and m1n1 have booted Linux into RAM on the iPad through the Pi. The USB handoff has occasionally failed on one Pi port, so boot transport still needs hardening. |
| Linux identity | The running system reports `Apple iPad Air (Cellular)`, AArch64, and 4 KiB kernel pages. A rebuilt J72 development kernel reports `7.0.12-j72spi2`. |
| Display | SimpleDRM exposes the panel at 1536 × 2048, 60 Hz. Labwc runs with software rendering. |
| USB access | The Linux USB gadget provides CDC NCM networking and an ACM serial shell. The USB-only network link supports a RAM shell and a host-backed filesystem. |
| Arch and Omarchy A | An Arch Linux ARM root filesystem was served **read-only** over USB NBD. Labwc and Omarchy A's Quickshell ran as an unprivileged tablet user. In the first session, the owner saw the rocket wallpaper, top bar, menu icon, clock, and pointer. The rebuilt-kernel session also started Labwc and Quickshell and reported the correct display mode; a second visual confirmation was not recorded. |
| Home button | The kernel reports Home presses as `KEY_HOMEPAGE`. A temporary userspace bridge opened and closed the Omarchy menu on physical Home presses in the first desktop session. Proper compositor/libinput handling remains to be done. |
| SPI2 foundation | A J72 SPI2 controller-only kernel build and device tree booted with **no touch child**. The measured controller input clock is 60 MHz. A guarded RAM diagnostic brought its Linux power domain from `0x200` to `0x2ff`, read configuration registers, restored automatic power control, and returned it to `0x200`. It sent no SPI transfer. |
| Recovery | After the RAM tests, the graphical processes and read-only NBD mount were stopped, Linux rebooted, and the Pi confirmed the same `iPad4,2` back in normal iOS USB mode. |

## Current limits

This is a host-backed desktop experiment, not a standalone Omarchy installation. Native touchscreen input is not working. Wi-Fi, Bluetooth, charging under Linux, audio, cameras, cellular, GPU acceleration, suspend, and internal storage have not been qualified. The Pi USB connection may not charge the iPad reliably.

The J72 touch hardware is described by Apple's device tree as a SPI-connected controller with separate reset, attention, clock, and PMU resources. The panel's calibration has been read from this device and kept private. The matching iOS firmware format differs from the format accepted by the current Linux `apple_z2` uploader. Touch power/reset order, wire settings, readiness handshake, and firmware upload still need board-specific work. The current test device tree deliberately has no touch child, so it cannot send touch traffic accidentally.

The latest RAM session also found an initramfs ordering issue: `mdev` changed `/dev/null` permissions after they had been set for desktop users. A live permission correction let D-Bus and Quickshell start. The source init script has been corrected, but a new image containing that correction has not yet been built or tested.

## Next development steps

1. Make the RAM boot and graphical startup repeatable, including the initramfs permission fix and clean NBD teardown.
2. Recover and implement J72 touch power, clock, reset, and bounded SPI protocol handling; validate input before enabling it in the desktop.
3. Add an **experimental J72** profile to [OrchardLinux/hardware](https://github.com/OrchardLinux/hardware), with exact board matching, a 4 KiB kernel and matching modules, a RAM boot path, and explicit support limits. The public `devices/` directory currently has several profiles, including J71b and J72b, but no J72 profile. The local J72 worktree is not an upstream port.

## Sharing and attribution

This report is suitable for a public repository. The project workspace also contains private Apple firmware, owner-specific calibration, raw USB/device logs, and local images. Those files are intentionally omitted here. A public PR should contain only original source, build instructions, permitted patches, and evidence that has been reviewed for private data.

Relevant upstream projects: [Hoolock Linux](https://github.com/HoolockLinux/docs), [Pomme](https://github.com/xenoaitham/pomme), [Orchard hardware](https://github.com/OrchardLinux/hardware), and the [J72 Omarchy A precedent](https://github.com/Phoenix2479/ipad-air-linux).
