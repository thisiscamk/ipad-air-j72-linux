# How we reached the installed J72 desktop

Current summary: 7 November 2026. For commands and prerequisites use
[the replication guide](QUICKSTART.md); for claims use [current status](J72-PROGRESS.md).
This summary replaces the original RAM-only narrative; its full text remains
in [history](history/pre-cleanup-2026-11-07/PROCESS.md).

1. **Identify and boot a control.** Confirm J72/A7, 4 KiB pages and exact DFU
   identity. Establish one serialised, bounded checkra1n/Pongo RAM console boot
   with native ARM64 host tools. Verify Linux itself, not just loader output.
2. **Fix SPI before interpreting controller codes.** Touch replies initially
   looked like controller rejection. The A7 explicit PIO transfer ordering was
   wrong. Correct transport sequencing let the unchanged firmware upload.
3. **Supply the right N1 startup and unit calibration.** Firmware upload ACK is
   not a working touchscreen. Validate device info, checksums, coordinates,
   contact/release states and real finger captures before claiming input.
4. **Use standard desktop pieces.** Move from diagnostic framebuffer/RAM
   experiments to the native Orchard kernel, Omarchy-A desktop, Foot and on-screen
   keyboard. Check portrait coordinates, Home and repeated keyboard reopening.
5. **Identify the actual Wi-Fi ROM.** J72 uses a USB/HSIC BCM43241 rev-6 radio.
   Retain measured reset/clock/PHY ownership and use matching private firmware.
   Let unchanged NetworkManager handle the resulting interface.
6. **Separate power presence from charging.** The inherited input limit was too
   small. Bounded 425/850/1,050 mA experiments showed progressively improved pack
   current, followed by positive net-charge endurance on one qualified powered
   hub. Preserve restoration and thermal/timing limits. Later browser pressure
   stopped supervision; this is an unresolved reliability issue.
7. **Qualify storage before resizing/installing.** Prove recovery access, disk
   inventory, reads and native writes/flushes. Investigate the snapshot/shrink
   limit on the actual device. The owner approved snapshot retirement and shrink;
   approximately 50 GB was freed while iOS remained bootable.
8. **Use the normal installed-system flow.** Install the native base, boot the
   existing ext4 root and FAT boot, fix the ASP partition-device integration and
   confirm PIN login, desktop, Wi-Fi and input. Recovery-to-installed startup
   works; the direct bare-loader heap failure remains a separate issue.
9. **Bring up audio by layers.** Confirm CS42L81 identity, A7 SmartIO protocol,
   DMA and MCA-v1 clocks/frames, then muted PCM, quiet channel tones and normal
   PipeWire discovery/playback. Enabled service is not yet a cold-boot result.

## Lessons that save the most time

- A same-model name or register layout from another SoC is not proof of compatibility.
- Batch read-only diagnosis and reversible driver tests into one RAM session;
  request a new DFU only for a concrete new boot artifact or necessary recovery.
- Use standard producers and components. Keep justified J72 hardware differences
  separate from generic desktop experiments and from the private firmware inputs.
- Record fresh boot, exact source/build and actual read/write/cleanup results.
  Host tests do not establish physical-device behaviour.
- Keep iOS bootable for charging. A cached battery percentage or “connected” icon
  is insufficient to leave a long test unattended.

[Detailed historical notes](history/README.md) retain failed approaches and
measurements. They explain why choices were made; they are not today's runbook.
