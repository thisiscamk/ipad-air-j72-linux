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
| Arch and Omarchy A | An Arch Linux ARM root filesystem was served **read-only** over USB NBD. Labwc and Omarchy A's Quickshell ran as an unprivileged tablet user. With the corrected J72 initramfs, the owner again saw the rocket wallpaper, top bar, menu icon, clock, and pointer. The rebuilt kernel reported 1536 × 2048 at 60 Hz. |
| Home button | The kernel reports Home presses as `KEY_HOMEPAGE`. A temporary userspace bridge opened and closed the Omarchy menu on physical Home presses in the first desktop session. Proper compositor/libinput handling remains to be done. |
| SPI2 foundation | A J72 SPI2 controller-only kernel build and device tree booted with **no touch child**. The measured controller input clock is 60 MHz. A guarded RAM diagnostic brought its Linux power domain from `0x200` to `0x2ff`, read configuration registers, restored automatic power control, and returned it to `0x200`. It sent no SPI transfer. |
| Touch power baseline | A one-shot, read-only RAM Linux module read PMU enable registers `0x84 = 0x00`, `0x85 = 0x11` and analog rail setting register `0x398 = 0x14` through the existing I²C regmap. The touch rail enable bits were clear. The setting corresponds to a nominal 6,000 mV code in the matching driver table; the rail was off, so no voltage was measured. No PMU write or touch transfer was made. |
| Touch clock baseline | A guarded RAM module powered the J72 PWM0 domain, read the channel 2 control and capture words at `0x10`, `0x14`, `0x20`, `0x34`, and `0x38`, and let Linux power the domain off again. All five words were zero in this idle state; PMGR actual state returned from `0x2ff` to `0x200`. This did not generate or measure a clock. |
| Touch clock programming | A separate one-shot RAM module checked that reset was low, the candidate touch rails were off, and PWM channel 2 was idle. It programmed two count words to 366 and control to `0x4003` for 250 ms. Readback showed counts of 366 and control `0x4001`; it then restored all three words to zero and PWM0 returned to off. This validates a bounded write and restore path, but the physical output rate was not measured. |
| Touch power sequencing | With reset held low and no SPI traffic, a guarded RAM test enabled the candidate analog rail and then LDO rail for 100 ms, following the order in the matching iOS driver. Their enable bits read back as set, then returned to their original clear values in reverse order. PWM registers and its power domain also returned to idle. Voltage at the touch panel and controller readiness were not measured. |
| SPI transport baseline | With the same short power sequence and reset still low, Linux completed one 16-byte, full-duplex SPI2 transfer at a conservative requested 1 MHz. The first four reply bytes were zero in this reset state. The temporary SPI device, rails, PWM registers, and SPI2/PWM0 domains were cleaned up. This establishes a bounded controller transfer, not a touch-chip response. |
| Touch identification attempt | A separate, guarded, one-shot RAM test repeated the reset-held dummy transfer, released the touch reset pin, waited a provisional 15 ms, and sent one 16-byte HBPP identification frame. Linux completed the transfer, but the first two reply words were `0x0000, 0x0000`, outside the accepted response set. The attention pin read low during the probe. Reset, rail registers, PWM registers, and power domains returned to their prior states. The iPad then returned to normal iOS. Native touch is still unavailable. |
| Recovery | After the RAM tests, the graphical processes and read-only NBD mount were stopped, Linux rebooted, and the Pi confirmed the same `iPad4,2` back in normal iOS USB mode. |

## Current limits

This is a host-backed desktop experiment, not a standalone Omarchy installation. Native touchscreen input is not working. Wi-Fi, Bluetooth, charging under Linux, audio, cameras, cellular, GPU acceleration, suspend, and internal storage have not been qualified. The Pi USB connection may not charge the iPad reliably.

The J72 touch hardware is described by Apple's device tree as a SPI-connected controller with separate reset, attention, clock, and PMU resources. The panel's calibration has been read from this device and kept private. The matching iOS firmware format differs from the format accepted by the current Linux `apple_z2` uploader. The PWM channel 2 register sequence has been exercised and restored, but its source clock and physical output rate remain unverified. Touch power/reset order, wire settings, readiness handshake, and firmware upload still need board-specific work. The current test device tree deliberately has no touch child, so it cannot send touch traffic accidentally.

The unsuccessful identification frame does not tell us which prerequisite is missing. The clock was programmed but its output has not been measured; the physical SPI speed and chip-select behavior are also unverified. Further offline analysis decoded this board's touch SPI settings as mode 0, least significant bit first, whereas the failed test used mode 2, most significant bit first. A related A7 iPad obtained a valid boot-ROM reply after correcting those settings. A new one-shot J72 identification test with the corrected settings is staged; it has not run on this iPad. Repeating the old frame would add no evidence.

An initramfs ordering issue had let `mdev` reset standard device-node permissions after they were set for desktop users. The corrected image was built and booted on the iPad. `/dev/null`, `/dev/zero`, `/dev/tty`, and `/dev/ptmx` were mode `0666` immediately after boot; user D-Bus and Quickshell then started without a live permission repair.

## Next development steps

1. Make the validated RAM boot and graphical startup easier to repeat, including a scripted read-only NBD mount and clean teardown.
2. Recover and implement J72 touch power, clock, reset, and bounded SPI protocol handling; validate input before enabling it in the desktop.
3. Add an **experimental J72** profile to [OrchardLinux/hardware](https://github.com/OrchardLinux/hardware), with exact board matching, a 4 KiB kernel and matching modules, a RAM boot path, and explicit support limits. The public `devices/` directory has no J72 profile. Its [J72b profile](https://github.com/OrchardLinux/hardware/blob/main/devices/j72b/device.toml) is for the iPad 6 Cellular (`iPad7,6`, A10), a different board. The local J72 worktree is not an upstream port. See the [full roadmap](ROADMAP.md) for milestones and pass conditions.

## Sharing and attribution

This report is suitable for a public repository. The project workspace also contains private Apple firmware, owner-specific calibration, raw USB/device logs, and local images. Those files are intentionally omitted here. A public PR should contain only original source, build instructions, permitted patches, and evidence that has been reviewed for private data.

Relevant upstream projects: [Hoolock Linux](https://github.com/HoolockLinux/docs), [Pomme](https://github.com/xenoaitham/pomme), [Orchard hardware](https://github.com/OrchardLinux/hardware), and the [J72 Omarchy A precedent](https://github.com/Phoenix2479/ipad-air-linux).
