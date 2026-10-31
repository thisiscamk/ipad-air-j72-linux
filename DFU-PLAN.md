# Current checkpoint — 31 October 2026

- [x] B01: real native one- and two-finger contacts, matched presses/releases, firmware health and full cleanup. Corrected analog enable is `0x07`; voltage setting is unchanged.
- [x] B02: Linux multitouch slots, evdev and visual orientation passed (owner target/trace confirmation; 21 matched presses/releases). Compositor/libinput, touch menus and launching Foot now pass. Keyboard text entry and the top-bar toggle now pass too. Window dragging also passes. Native Home also opens and closes the menu without the earlier bridge. No new DFU requested.
- [ ] B03: automatic self-check, full cleanup, touch restart and read-only desktop startup passed a fresh boot. Same-worker reuse also passed. Revised automatic keyboard startup still needs independent cold confirmation.
- [ ] B04: visible brightness dim/restore passed. Battery gauge telemetry remains open.
- [ ] B05–B11: Wi-Fi, persistence/Bluetooth, charging, audio/rotation, power/remaining hardware, integrated use.
- [ ] B12–B15: storage read-only qualification, installer rehearsal, separately authorized installation, installed-system verification.

Earlier zero-contact results below are historical. The corrected-power gesture test now passes B01.

# J72 session plan: touch to an internal root filesystem

Updated 31 October 2026. This is a work queue for this exact J72, not a promise of a fixed number of DFUs. Each row groups work that can share a RAM boot. A failed hardware milestone can require more boots; working modules and userspace changes should be tested within the existing boot wherever possible.

**Current position:** native multitouch, full-screen mapping, desktop menus, launching Foot, on-screen typing and keyboard show/hide have passed owner checks. The analog enable correction is `0x07`; the voltage setting is unchanged. The completed RAM session passed automatic touch self-check, full cleanup, restart and desktop startup using the same kernel. The owner confirmed menus, window dragging and keyboard reopening/typing after live keyboard changes. A revised keyboard startup bundle is prepared; native Home and visible brightness dim/restore have also passed in this boot.

## How we will reduce button sequences

- Finish source review, artifact checks and builds before requesting DFU.
- Retain the working boot image and change one hardware variable per comparison.
- Batch separate, guarded modules in one RAM boot, checking cleanup between them.
- Keep both USB debugging paths available. Stop a batch if firmware health or resource restoration fails.
- Prepare userspace, package caches, input parsing, installer simulations and documentation without a DFU.
- Request a new boot when a kernel/DT/loader change or an independent cold-start check actually needs it.
- Record a physical screen/gesture/charger check only when the owner performs it. An automated protocol check is not a substitute.

## Completed in this boot

- Automatic touch self-check, full cleanup, restart and read-only desktop startup passed.
- Owner checks passed: menus, window dragging, on-screen typing/reopening, keyboard icon, native Home open/close, and visible brightness dim/restore.
- A longer cycle and another same-boot restart passed. The final cycle emitted 38,237 frames with zero layout rejects, timeouts, recoveries or SPI errors; common rejected wire replies remained filtered. Final firmware health and full cleanup passed.
- Desktop teardown exposed an executable-symlink check issue; it was fixed and verified in this boot. The original root was unmounted, NBD detached and the host export stopped.

## Next DFU: keyboard cold confirmation and first battery voltage trial

The next private image adds the exact J72 UART5 description to the device tree. It preserves the kernel and includes the automatic keyboard mode and corrected teardown script. UART5 is absent from the running tree used in the completed boot, so this test needs a fresh boot. No battery command runs automatically.

1. Verify exact J72 identity and pinned image, then boot the integrated touch/desktop session.
2. Confirm automatic startup and the revised keyboard behavior without live repairs.
3. Inspect UART5 registration at its exact J72 address/interrupt and confirm external USB debugging still works.
4. Take a passive pad/domain snapshot. Refuse the voltage trial unless the inherited GPIO44 state and UART5 tty provider match the verified guards; leave the separate PMU GPIO control untouched.
5. Run one bounded diagnostic for three voltage samples. It sends only the two voltage register read addresses, checks command echo and response layout, and restores/readback-checks UART settings. No gauge reset, Control subcommand, firmware or data-flash write is implemented.
6. If successful, use this same boot to prepare further read-only telemetry checks. Voltage alone does not identify the exact gauge or qualify battery reporting or charging. A failed trial saves its evidence and stops without automatic retries.
7. Finish with orderly desktop/root teardown, touch health/restoration checks and a return to iOS.

**Offline readiness:** the new DT variant changes only the UART5 node and a reference to its existing power domain; all original properties compare byte for byte. The actual reader passes 256 encode/decode cases and pseudo-terminal tests for leading noise, bad echo, malformed or short responses, disallowed commands and bounded timeouts with runtime bounds checks. Its loader/self-test and wrong-controller refusal also passed in the existing Arch RAM environment without opening a UART. The first real UART5/HDQ result remains pending.

## Subsequent DFUs and dependencies

- **B04:** finish exact J72 HDQ pin/clock validation, build the read-only gauge path, compare plausible battery readings with iOS and qualify backlight controls. Brightness passed. The UART5 DT variant and bounded voltage-only diagnostic are built and checked; actual gauge communication remains untested.
- **B05–B06:** build and qualify the A7 internal HSIC/EHCI bus, enumerate the WLAN device, then validate matching firmware and the USB driver protocol, association and traffic. These are separate risks and may need several boots.
- **B07–B11:** host persistence and Bluetooth, measured charging/cable changes, audio and rotation, power and remaining hardware, then integrated daily-use tests. Reuse a boot for userspace and runtime changes wherever possible.
- **B12–B15:** only after the required hardware/usability gates: storage read-only qualification, installer rehearsal, a separately authorized installation, then cold installed-system and recovery checks. No internal-storage write is currently authorized.

The full pass conditions and owner actions remain in the batch table below. Batch IDs are milestones, not a promise of one DFU each.

## Proposed boot batches

IDs identify milestones, not a guaranteed one-DFU-per-row schedule. Batches may combine when their prerequisites are met. Battery, connectivity and desktop preparation can move earlier while touch remains open. GPU, camera and cellular work may each need several separate builds and boots. None of B01–B12 authorizes an internal-storage write.

| Batch | Work within that boot | Pass condition / owner action |
| --- | --- | --- |
| **B01 — passed: contact detection** | Corrected the missing shared analog enable. Native one- and two-finger reports, coordinates and matched release lifecycles now pass. | Owner gesture capture, final firmware health and full hardware restoration passed. |
| **B02 — passed: Linux input** | Linux MT slots, screen mapping, menus, Foot launch, typing and the keyboard toggle passed. | Window dragging and native Home menu open/close passed. |
| **B03 — partly passed: integrated cold start** | Automatic self-check, full cleanup, touch restart and desktop startup passed a fresh boot; a longer cycle and another same-boot restart also passed. | Confirm the revised automatic keyboard startup independently after a later cold boot; Revised teardown passed after fixing a symlink check; return to iOS has been requested. |
| **B04 — partly passed: battery and display controls** | Owner confirmed PMIC brightness dim/restore. Bring up the J72 UART5/HDQ gauge using exact board wiring; begin with identification and telemetry. Read brightness through the existing PMIC backlight driver, then test bounded changes and restore the starting value. | Plausible battery voltage, temperature, state of charge and current; compare with an iOS baseline. Owner confirms brightness changes. Battery reporting alone does not establish charging. |
| **B05 — Wi-Fi bus and device** | Qualify the internal EHCI/HSIC host, PHY, clocks, rails and reset without disturbing the external USB gadget. Read descriptors before selecting a WLAN transport driver. | The internal WLAN USB device enumerates and remains stable; external USB debug still works. Firmware startup and association are separate checks. |
| **B06 — Wi-Fi firmware and networking** | Use the matching local WLAN firmware and board data, validate the driver protocol, then test scan, association, DHCP, DNS and traffic. Keep credentials and identifiers private. | Owner's network works reliably under load; reconnect after a controlled disconnect. No driver-probe-only success claim. This is a separate driver risk from touch. |
| **B07 — persistence and Bluetooth** | Test a separate writable root/home image stored on the host, retaining the original image. Once Wi-Fi is stable, exercise the root/debug path over Wi-Fi. Bring up Bluetooth's UART transport and matching firmware with separate power guards. | Settings survive Linux sessions in the host image; Bluetooth discovery and a real keyboard/mouse connection work. No iPad storage is used. |
| **B08 — charging and cable transitions** | Use a RAM-resident diagnostic environment, or a proven Wi-Fi root, before disconnecting USB data. Record gauge readings under load, charger attach/detach and return to the Pi. Qualify the exact charger/data arrangement. | Measured net charging, sensible temperature/current limits, stable operation and recovery of USB debug. Owner changes cables. Never disconnect an active USB-backed root and assume cached files will suffice. |
| **B09 — audio and tablet controls** | Qualify codec/clock/amplifier sequencing, speakers, headphones and microphone separately; integrate volume buttons. Test orientation sensors, display/input rotation and desktop controls. | Owner verifies audio and screen behavior; input coordinates follow rotation. Each feature needs its own evidence. |
| **B10 — power management and remaining hardware** | Qualify idle power, thermal behavior, CPU frequency changes, screen blanking and wake before system suspend. Investigate GPU, cameras and cellular as distinct driver projects. | Stable power and wake behavior; explicit support findings for every remaining feature. GPU, cameras and cellular cannot be promised from current evidence. Any deferral needs owner agreement before installation readiness is declared. |
| **B11 — integrated daily-use qualification** | Soak the intended desktop workload using host persistence; exercise input, Wi-Fi, charging, audio, Bluetooth, rotation, shutdown and return to iOS. Repeat cold boots using pinned artifacts. | All required features pass together, with usable memory/performance, no stuck contacts or repeated USB/network loss, and a working recovery image. This is the owner's usability gate before internal-storage work. |
| **B12 — ANS1 read-only qualification** | Only after B11: use a separate RAM image with writes and write-unlock commands disabled throughout the storage path. Preserve the required inherited firmware, identify storage geometry, enumerate namespaces and perform bounded aligned reads. Repeat hashes and inspect the partition map read-only. | Exact J72 read access, stable results and iOS recovery. No mounting with journal replay, no formatting, no partition edits, no firmware/auxiliary-area writes. Read success does not qualify writes. |
| **B13 — installer rehearsal** | After the storage and layout research gates below: boot the proposed installer in mandatory dry-run mode, inspect the actual target and produce the exact proposed changes. Recheck backups and rescue boot. | A concrete reviewed write plan, tested installer decisions and target refusal rules. Still no internal write. |
| **B14 — first approved installation** | Requires separate owner authorization. Perform only the approved layout and Linux filesystem writes; verify them, then boot that root through the existing host-assisted route. | Internal root works with the same validated drivers; iOS is preserved as agreed. USB rescue stays available. |
| **B15 — installed-system verification** | Cold-launch the installed system, test updates/recovery, return to iOS and confirm persistence and filesystem integrity. Document the validated repair and rollback procedure. | Repeatable launch and maintenance without the Pi serving the root filesystem. A host is still needed to start Linux after a cold restart. |

## Work that does not need to wait for touch

| Workstream | Prepare before the relevant DFU | Current evidence / unresolved work |
| --- | --- | --- |
| Input and desktop | Packet parser, contact-state checks, libinput orientation, Home binding, keyboard, service startup and teardown. | Native touch, menus, window dragging and keyboard entry work; native Home passed; revised keyboard cold startup remains open. |
| Battery and charging | Audit the HDQ UART implementation, J72 clock/pin mapping, read-only gauge commands, charger telemetry and recording tools. | J72 identifies a BQ27540-family HDQ gauge under UART5. Air 2 work is reusable protocol research, with different board wiring. J72's D2089 PMU needs its own charger audit. |
| WLAN and Bluetooth | Map J72 HSIC/PHY/UART power dependencies, audit transport compatibility and privately stage matching firmware/board inputs. | The captured iOS tree places WLAN under EHCI/HSIC; an observed internal device has VID:PID `0a5c:bd1c`. This is not evidence that the current Linux USB WLAN driver supports it. |
| Display and power | Prepare backlight read/restore tools, thermal/idle logging, and display/input rotation configuration. | The existing PMIC backlight driver passed a visible three-second dim/restore check and read back the original value. Battery and thermal telemetry remain absent. |
| Root filesystem | Preserve the existing image; prepare an isolated host-backed writable copy, package cache, service definitions and reproducible image recipe. | This can establish persistence and update behavior before internal storage. |
| Orchard | Split general SPI/input fixes from exact J72 activation, retain build hashes and module ABI, prepare an experimental profile and recovery instructions. | A focused contribution can be reviewed before an internal installer exists. Do not present the experimental worktree as a completed port. |
| Storage | Audit ANS1 command submission and write refusal; model layouts on disposable disk images; research the iOS 12 APFS APIs and recovery requirements. | Existing sources contain real protocol and error-path gaps. No storage driver or resizer has been qualified on this J72. |

## Internal installation has separate research gates

These must be completed between B11 and B14; they are not automatic consequences of fixing touch.

1. **Recovery and backups:** verify a restorable owner backup, account for device-specific data it omits, preserve the observed map privately, and verify the then-current restore route for this exact model. Establish what recovery preserves and what a full restore would erase.
2. **Read-only ANS1:** B12 must demonstrate the actual board path. Audit both loader and Linux initialization: a read-only block flag does not undo an initialization command that unlocks writes. The [Air 2 audit](https://github.com/mattonik/ipad-nixos/blob/main/research/j81-ans1-storage-bringup.md) specifically identifies this issue in the unmodified experimental driver.
3. **iOS 12 coexistence:** preserve iOS by default. Establish a supported resize/layout mechanism for J72/iOS 12, or stop at host persistence. Current [Resize APFS requirements](https://github.com/OrchardLinux/resize-apfs#requirements) target iOS/iPadOS 16 and later; its J71b tests do not qualify this device. Replacing iOS would be a different project requiring an explicit owner decision.
4. **Writes, flushes and failures:** qualify ANS1 request bounds, DMA addresses, completion/tag handling, timeout recovery, flush/durability and region protection. Use synthetic tests and disposable media for destructive cases. Those tests still do not establish hardware behavior on J72.
5. **Layout and image:** choose space from measured geometry and real free-space requirements. Specify every changed range, filesystem, alignment, preserved Apple region and recovery artifact. Decide the storage/access-protection policy; an automatically logged-in development desktop is not a finished personal-data setup.
6. **Rehearsal and authorization:** B13 must emit a concrete dry-run plan. The owner approves that plan only after the prerequisites pass. No planning document authorizes a write.
7. **Installation and maintenance:** B14–B15 must verify persistence, the chosen iOS coexistence arrangement, updates, rescue and rollback. Keep the known RAM boot usable independently of the new root.

The first intended installation stores Linux on the iPad and retains a **host-assisted cold boot**. Untethered power-on boot is a separate boot-chain research project. Orchard's current [Omarchy A instructions](https://github.com/OrchardLinux/omarchy-a#start-linux-after-a-restart) also use a host launch; their supported-device installer is not yet a J72 installer.

## Checklist to update after each session

- [x] RAM Linux, USB debugging and graphical desktop demonstrated.
- [x] SPI upload, N1 firmware startup, calibration retention and setup-register readback verified.
- [x] Eight short reader comparisons completed on hardware with health and restoration verified.
- [x] Corrected no-sync reader tested during confirmed owner gestures; no finger packets.
- [x] Corrected reader with display sync tested during confirmed owner gestures; no packets, health and restoration passed.
- [x] Continuous raw result frames captured and checksum-validated; firmware health and restoration passed.
- [ ] Raw sensor contents correlated with deliberate owner touches.
- [x] Enable the active C8 native-report gate; validate 228 empty native frames at idle.
- [x] Test gestures with C8 enabled: 5,297 valid native frames, all zero fingers; contact detection remains unresolved.
- [ ] Actual finger reports and native desktop touch.
- [ ] Repeatable input/desktop boot and Home/keyboard integration.
- [ ] Battery, brightness, Wi-Fi, Bluetooth and charging qualified.
- [ ] Audio, rotation, power management and remaining hardware assessed and qualified as required.
- [ ] Integrated daily-use and recovery gate passed.
- [ ] ANS1 read-only access and stable hashes on J72.
- [ ] iOS 12 coexistence, backup/recovery and write path qualified.
- [ ] Installer rehearsal and separate owner approval.
- [ ] Internal installation, cold-launch, updates and rescue verified.

There is no reliable total DFU count or completion date yet. Touch reporting, HSIC Wi-Fi, ANS1 writes and iOS 12 partitioning are distinct open engineering problems. The aim is to resolve their offline dependencies early and make each physical boot answer several prepared questions.
