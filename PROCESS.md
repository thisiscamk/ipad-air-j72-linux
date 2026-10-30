# How we brought up RAM Linux and Omarchy A on J72

This records the path followed on one iPad Air 1 Cellular (`iPad4,2` / `J72AP`, Apple A7) through 30 October 2026. It is a **method and measured workflow**, not a ready-made installer. The iPad still has iOS 12.5.7, and every Linux boot in this project has used RAM. Read [J72-PROGRESS.md](J72-PROGRESS.md) for the current support status.

## What can be reproduced from this report

| Part | Availability today |
| --- | --- |
| Hoolock A7 boot documentation, PongoOS setup, and Pomme v0.1.0 4 KiB kernel/m1n1 release | Public upstream sources linked below. |
| Exact J72 DFU identity, boot order, RAM checks, USB networking and read-only NBD procedure | Recorded below from the physical device. |
| The supervisor used to serialize and time out our USB attempts, the revised J72 kernel/DTB, and the Arch/Omarchy A root build | Local development artifacts; they are not yet packaged in this repository as a reproducible release. |
| Apple's firmware, this panel's calibration, raw device logs and the 3 GiB root image | Kept local and omitted from the public repository. They are not required to understand the baseline boot method. |

Someone using another device must obtain its correct device tree, boot components and page-size requirements. **J72b is a different iPad**: Orchard's [J72b profile](https://github.com/OrchardLinux/hardware/blob/main/devices/j72b/device.toml) describes the iPad 6 Cellular (`iPad7,6`, A10).

## 1. Identify the exact device and choose a RAM baseline

We recorded the normal iOS product as `iPad4,2`, then checked DFU with `irecovery -q` before each boot. Our expected fields were:

```text
PRODUCT: iPad4,2
MODEL: j72ap
CPID: 0x8960
BDID: 0x12
MODE: DFU
```

The device tree is `s5l8960x-j72.dtb`. A7 needs a **4 KiB-page AArch64 kernel** in this boot path. We started with the published [Pomme v0.1.0 release](https://github.com/xenoaitham/pomme/releases/tag/v0.1.0): its 4 KiB kernel with embedded initramfs, matching modules, J72 DTB, and m1n1. We checked the release hashes, ARM64 Image header, page-size flag, DTB model/compatible strings and payload layout before touching USB. We retained this released image as a known-good control when rebuilding the kernel later.

The working handoff was the [Hoolock PongoOS route](https://github.com/HoolockLinux/docs/blob/master/tutorials/SETUP_pongoOS.md), using native aarch64 host tools on the Raspberry Pi 4. We used checkra1n 0.1337.3 with Hoolock PongoOS 2.6.3. An older Pongo 2.5.1 pairing was abandoned after a compatibility mismatch. No Apple restore image was sent during the successful Pongo → m1n1 → Linux boot.

## 2. Get a bounded DFU → PongoOS handoff

The owner entered DFU with the cable connected and released both buttons. The host checked **all** identity fields above and required exactly one matching DFU device. We then ran one USB boot process at a time under a lock. Our supervisor imposed a timeout, reaped the entire checkra1n process group, and checked the resulting USB state. A loader exit code or “Checkmate” message alone was not treated as a successful boot.

The evidence gate was a new `05ac:4141` PongoOS USB device whose serial string still identified `CPID:8960 BDID:12`, followed by a responsive Pongo console. The Pi USB port mattered: one path intermittently failed at the USB handoff even after checkra1n appeared successful. Moving the cable to another Pi USB-A port led to a confirmed Pongo connection. We did not repeat unchanged failed attempts.

Our local supervisor and pinned binaries are not in this public repo yet. Use the upstream boot documentation to prepare your own host tools. If you write a wrapper, preserve the exact-device check, exclusive USB access, timeout and process-group cleanup. Do not launch two DFU/Pongo clients simultaneously.

## 3. Send m1n1, the J72 DTB and the RAM kernel

The baseline combined image was assembled in this order:

```text
m1n1.bin
chosen.bootargs=console=tty0 loglevel=7 rdinit=/init
s5l8960x-j72.dtb
gzip-compressed 4 KiB ARM64 kernel Image with embedded initramfs
```

The boot arguments are a real newline-terminated text record, not a shell command. The baseline Image already contained its initramfs. We verified the gzip round trip and the byte-for-byte component order before sending it. In a single native `pongoterm` session, `/send <combined-image>` uploaded the image, then `bootm` transferred control to m1n1/Linux. The Pongo USB disconnect at this point was expected; the success condition was the **new Linux gadget**, `1d6b:0104`, with CDC NCM networking and USB ACM serial.

On this device the live RAM kernel reported `Apple iPad Air (Cellular)`, AArch64, `KernelPageSize: 4 kB`, and a 1536×2048 simpledrm framebuffer. Both USB shell paths responded. These checks established an actual Linux boot, beyond the loader's status message.

## 4. Establish a local USB shell

The initramfs set the iPad's NCM interface to `10.0.0.2/24` and exposed a RAM shell on port 23. On the Pi we disabled NetworkManager control of that *temporary* interface and set `10.0.0.1/24`:

```sh
sudo nmcli device set usb0 managed no
sudo ip addr add 10.0.0.1/24 dev usb0
ping 10.0.0.2
nc 10.0.0.2 23
```

The host address sometimes disappeared after USB re-enumeration; restoring it recovered the shell. The gadget also exposed an ACM console at `/dev/ttyACM0`. We checked model, kernel release, page size and bidirectional USB networking before mounting any larger root filesystem. `usb0` and `/dev/ttyACM0` are observed names on this Pi; discover the actual interface names on another host.

## 5. Run Arch and Omarchy A without using iPad storage

We first tested a small software-rendered desktop, then built an Arch Linux ARM root with signed packages and an unprivileged `tablet` user. We added Labwc, Quickshell, Qt6, fonts, D-Bus, seatd and the [Omarchy A shell](https://github.com/OrchardLinux/omarchy-a). A minimal J72 shell configuration enabled a menu and clock while hiding controls for unverified hardware services. The root was packed as ext4, checked offline with `e2fsck -fn`, and exported **read-only** from the Pi over the USB-only address:

```sh
qemu-nbd --persistent --read-only --format=raw \
  --bind=10.0.0.1 --port=10811 omarchy-shell.ext4
```

On the iPad RAM shell, BusyBox's `nbd-client` attached that export to `/dev/nbd2`. We waited for `/sys/block/nbd2/size` to become nonzero before mounting:

```sh
busybox nbd-client -b 4096 10.0.0.1 10811 /dev/nbd2
cat /sys/block/nbd2/size  # wait until this is nonzero
mkdir -p /mnt/omarchy
mount -t ext4 -o ro,noload /dev/nbd2 /mnt/omarchy
```

Our first mount attempt raced the NBD capacity announcement; a later attempt succeeded. The paths and port are examples from this test, not reserved names.

For the chroot session we bound `/dev`, `/dev/pts`, `/dev/shm`, `/proc` and `/sys`; `/run`, `/tmp` and `/home` were tmpfs in RAM. The `tablet` user had access to `seat`, `video` and `input`. Seatd supplied the DRM seat. Labwc ran on simpledrm with `WLR_BACKENDS=drm` and `WLR_RENDERER=pixman`; a user D-Bus session and Quickshell then started on its Wayland socket. The rebuilt-kernel session reported Labwc's output at 1536×2048@60. The owner confirmed the Omarchy rocket wallpaper, top bar, clock, menu icon and pointer on screen.

The initramfs needed `/dev/pts` with usable `ptmx`, `/dev/shm`, `/dev/fd`, and standard device nodes accessible to the non-root user. `mdev -s` recreated `/dev/null` at mode 0660 in one test, so the permission adjustment has to run **after** mdev. We rebuilt and booted the corrected image. The four standard nodes checked at boot were mode 0666, and user D-Bus and Quickshell started without a live chmod. The owner again confirmed the wallpaper, bar, menu icon, clock, and pointer. The public repo does not yet contain the full root-build recipe or the root image, so these desktop steps are a reproducible design and test record, not a one-command build.

## 6. Measure input and stage touch work separately

The physical Home button generated `KEY_HOMEPAGE` (172). A normal Labwc binding did not receive it in the first session. A temporary RAM-only evdev-to-Omarchy-menu bridge did, and the owner confirmed that repeated Home presses opened and closed the menu. Native libinput/compositor integration is still pending.

For touch, we compared the J72 Apple DeviceTree, a private owner calibration read, the matching iOS driver metadata and the Linux controller source before enabling anything. The J72 touch device sits under SPI2, with separate chip-select, reset, attention, PWM clock and PMU dependencies. We first booted an SPI2 **controller-only** DTB with no touch child. A later guarded RAM diagnostic held the Linux SPI2 power domain on just long enough to read six controller configuration words, then returned it to automatic power control. It sent no SPI word or firmware. The measured input clock is 60 MHz; that value alone does not establish touch wire speed. Touch firmware and power sequencing remain open work.

The next RAM-only session measured a touch-power baseline without enabling any rail. The existing I²C PMU driver exposed a regmap at address `0x3c`; an exact-board, read-only module sampled two candidate enable registers (`0x84 = 0x00`, `0x85 = 0x11`). Their candidate enable bits were clear. The first module build had an overly strict device-tree path comparison and stopped before reading; a corrected build used an exact node lookup and produced the snapshot. We transferred that corrected module through the RAM USB shell, verified its hash on both ends, and rebooted back to iOS. The register-to-touch mapping and safe power sequence still require independent verification.

A subsequent read-only RAM boot also sampled register `0x398 = 0x14`, the voltage-setting field associated with the candidate analog rail. The matching driver's table maps this code to a nominal 6,000 mV setting, but the rail was disabled and we did not measure an output voltage. The owner confirmed that iOS came back on screen after the RAM reboot and moved the iPad to a wall charger. The Pi did not see normal iOS USB before it was unplugged.

### Follow-up: resolve the SPI upload blocker

The initial driver could report completed transfers while the touch controller had not accepted the packet. Repeating packet sizes and checksum variations did not establish that the intended bytes reached the wire. We therefore observed the SPI pads through their existing GPIO input buffers while sending a slow, known pattern, with touch reset asserted and rails off. This required no board access.

Those measurements showed that AUTO_TX generated clocks with constant MOSI, and that the S5L bit-order flag mapping was reversed. A temporary GPIO SPI implementation then uploaded the original private packet and received `0x4bc1`. A direct-register hardware probe reproduced acceptance by disabling AUTO_TX for explicit commands, starting RUN before queuing every byte, draining RX and limiting outstanding data to the receive FIFO depth. Applying those rules to every explicit transfer in the normal Linux SPI driver also passed: readiness advanced to `0x4879`, all 57,016 bytes transferred in about 745 ms, ACK was `0x4bc1`, and the four-byte C4 command returned `0x4879, 0x4f81` with an attention change.

The firmware packet itself was unchanged. These results identify a transport problem; they do not establish the precise ROM meaning of every earlier failure status. Each probe restored reset, chip select, rails, PWM and power domains, and normal iOS USB was verified after reboot. Follow-up queries showed that the four-byte C4 reply was not proof of firmware startup. We traced the N1-specific calibration override beyond the earlier disassembly range, checked its defaults against the live iOS properties, uploaded private proximity and panel calibration, and used the proper address-bearing Z2 execute frame. Device-info checksums then passed with interface version 1 and maximum packet size 2,454; screen metrics matched iOS. An initial application result frame passed header and payload checksums. These distinct probes ran in one RAM session. Continuous reading and real finger capture remain before evdev or desktop touch can be claimed.


### Validated N1 startup in the RAM diagnostics

These are observations from this J72, not a general driver or a completed touch port. Power, PWM, reset and CS guards surround the sequence, and every probe restores them. The packet framing was recovered from the matching driver; [Corellium's public hx-touchd](https://github.com/corellium/projectsandcastle/blob/03db9c6ae04141eb940f3b9f56d446f50d57fadf/hx-touchd/mtfw/mtfw.c) supplied a useful comparison. Its other board values must not replace J72's measured properties.

1. Require the boot-ROM readiness exchange to advance to `0x4879`.
2. Upload the private proximity calibration, then panel calibration, using chunks capped at 1,008 data bytes and requiring `0x4bc1` after each. This panel's calibration is 1,024 bytes; its data stays private.
3. Upload the original 57,016-byte preconstructed firmware packet and require `0x4bc1`.
4. Read the chip version through the ROM register protocol, validate the response checksum, and require the observed C1F15 ID before N1 setup.
5. Apply the matching N1 register sequence below. Each write uses mask `0xffffffff` and requires `0x4ad1`.

| Controller address | Value | Evidence |
| --- | --- | --- |
| `0x10003060` | `6089` | J72 FLL personality value |
| `0x1000305c` | `0x20` | Matching N1 reference-divider default |
| `0x10003058` | `6` | Matching N1 routine |
| `0x10003000` | `3` | Matching N1 default for this chip version |
| `0x10003518` | `1` | Live iOS clock-enable property; the static default alone was insufficient |

6. Read the controller's SPI APU status, request calibration with `1f 01`, wait 65 ms, and query ACK. The matching method checks transfer success at this step; the observed `0x4969` has no assigned meaning here.
7. Send the 12-byte Z2 execute frame addressed to the J72 personality's `0x10003400`. This supersedes the earlier four-byte C4 test.
8. Send the application wake frame, then validate device information and screen metrics. Interface 1, maximum packet size 2,454 and the screen descriptor match iOS.
9. Confirm operating-mode readback, then qualify result reading with actual gestures. An idle check captured one checksum-valid startup status frame. The first owner tap-and-swipe capture produced no finger frames. Attention-low gating was an inference from startup, not proven finger polarity; a separate comparison polled both levels with alternating counters and found no additional packets. Do not interpret a quiet queue or a valid startup packet as working touch.

The next comparison adds a missing board lifecycle step **before step 1**, during reset-held startup. Its J72 startup enables display sync on GPIO119 after the pre-reset wake and before reset release. A guarded RAM idle test has validated the corresponding mux readback and full restoration. A separate GPIO-only sample observed transitions only with this mux enabled, then restored the original pad. The owner completed a 180-second gesture capture with this setting and no packets arrived. Display sync alone is insufficient.

Known application queries then passed six times over ten seconds. For the next candidate configuration, report BF is written with `95 81 09 00`. Validate the E1 reply checksum and its command/report/status fields at bytes 6/7/8, then wait, wake the application and read BF back. Three independent delayed readbacks now match, followed by a checked normal-mode write. A two-second idle recorder passed with no packets or malformed frames and valid application information at its end. The owner then performed gestures during a 180-second recording: no packets arrived, and the final device-info checksum was valid. This configuration has not established finger reporting or evdev input.

Follow-up ROM reads checked every calibration word before and after uploading firmware: all 1,152 bytes matched the private expected data. Each N1 setup register was also read immediately after its write and again after calibration; all five retained their intended values with valid checksums. These checks distinguish acknowledged commands from actual retained contents. They still do not establish that the application is scanning.

Several distinct probes ran in this one RAM session without another DFU. The live capture module is bounded in time and record count, exports data only through a root-readable RAM file, and resets and powers down the controller after capture. Firmware, calibration and raw traces remain local.

## 7. Cleanly return to iOS

For the USB-backed desktop, we stopped Quickshell, Labwc, D-Bus and seatd, then unmounted the chroot's bind/tmpfs mounts. An earlier root unmount briefly returned “busy” while chroot parent processes exited; a later normal unmount succeeded. In the corrected-image session, every chroot mount and the read-only ext4 root unmounted normally before `/dev/nbd2` was detached and the Pi's qemu-nbd server stopped. From the RAM shell we requested `sync; reboot -f`. The Pi subsequently saw the Linux gadget disconnect and normal iOS USB `05ac:12ab`; `ideviceinfo` again returned `iPad4,2`.

The Pi USB connection did not reliably charge the iPad, so we returned to iOS and used a wall charger between sessions. No internal-storage write, partitioning, iOS erase or Pi kernel replacement was part of this workflow.

## Reusing the method for another board

1. Record exact product/board/CPID/BDID and source the **matching** device tree. Refuse a boot if identity differs.
2. Determine that SoC's kernel page size and obtain a matching Image, initramfs and module set. Keep a published baseline separate from development builds.
3. Prove each boundary separately: DFU → exact Pongo USB → responsive Pongo console → m1n1 handoff → Linux gadget → model/page-size check → bidirectional USB shell.
4. Bring up display and a read-only host root before attempting native peripherals. Keep USB debugging available.
5. Probe board-specific power, clocks, pins and firmware in small guarded stages. A controller that registers is not proof that its attached device works.
6. Preserve recovery evidence and return to the original OS after each bounded session. Publish reviewed source and sanitized results; keep owner calibration, Apple firmware and raw identifiers local.

This sequence can guide other A7–A11 experiments, but its J72 addresses, GPIO numbers, DTB, page-size selection and touch assumptions must not be copied to a different board without fresh evidence.
