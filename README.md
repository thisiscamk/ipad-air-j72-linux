# Omarchy-A on iPad Air 1 Cellular (J72)

Experimental Linux bring-up for **iPad4,2 / J72AP / Apple A7**, using Orchard
and Omarchy-A. Updated **7 November 2026**.

**The installed desktop now boots from internal storage.** Touch, the on-screen
keyboard, Wi-Fi, battery reporting and speaker output have been demonstrated.
iOS is retained and remains the charging fallback. Startup still requires a
computer; this is not a supported-device image or a one-command installer.

## Start here

1. **[Current status](J72-PROGRESS.md)** — what actually works, what was only
   prepared, and the failures still open.
2. **[Replication guide](QUICKSTART.md)** — prerequisites, pinned sources,
   the shortest useful path and explicit gaps before the installed milestone.
3. **[Current source and build instructions](code/current/README.md)** —
   Orchard/kernel patch snapshots, Wi-Fi startup, charging tools and audio code.
4. **[How we got here](PROCESS.md)** — the successful sequence and lessons
   that avoid repeating weeks of hardware investigation.
5. **[Remaining work](ROADMAP.md)** and **[historical reports](history/README.md)**.

| Milestone | Current evidence |
| --- | --- |
| Installed Omarchy-A | Internal ext4 root and FAT boot partition; PIN login and working desktop |
| Input/display | Touch, Home/menu, Foot, on-screen keyboard and brightness checks pass |
| Wi-Fi | Internal BCM43241 connected; HTTPS, SSH and unplugged desktop demonstrated |
| Battery/charging | Telemetry and guarded positive charging measured; reliability under load still open |
| Speakers | Both channels heard; normal PipeWire transfer passes; fresh-boot autostart unverified |
| Browser video | YouTube loads, but Firefox is too slow and has run out of memory; usable playback unqualified |
| PC-free boot | Not working; Pi-assisted startup is the accepted interim workflow |

## Reuse the work

Use unchanged Orchard/Omarchy-A where possible and keep J72 hardware
adaptations explicit. **J72 is not J72b**: these instructions do not cover the
A10 iPad 6 Cellular. The tested host is a Raspberry Pi 4 with native aarch64
userspace; replacing the host kernel was not required.

Start with RAM boot. Internal installation changes APFS/GPT and is a separate,
reviewed operation; this repository does not ship an unattended resize/install
script. Source availability does not establish another device's qualification.
Apple firmware, device calibration, credentials and raw logs are not published.
See [contribution rules](CONTRIBUTING.md).

Upstream projects: [Orchard](https://github.com/OrchardLinux/orchard),
[Omarchy-A](https://github.com/OrchardLinux/omarchy-a),
[Apple Linux kernel](https://github.com/OrchardLinux/linux).
