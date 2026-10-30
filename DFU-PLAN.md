# J72 session plan: touch to an internal root filesystem

Updated 31 October 2026. This is a work queue for this exact J72, not a promise of a fixed number of DFUs. Each row groups work that can share a RAM boot. A failed hardware milestone can require more boots; working modules and userspace changes should be tested within the existing boot wherever possible.

**Current position:** Linux, USB debugging and the Omarchy A desktop work. Raw reporting and native packet output are reproducible. C8 = `0x19` enabled 228 valid native frames at idle; a subsequent confirmed owner gesture capture retained 5,297 valid native frames, all with zero fingers. Health and restoration passed. B01 remains open at contact detection; another unchanged gesture test is not planned. The current RAM boot remains available for distinct diagnostics.

## How we will reduce button sequences

- Finish source review, artifact checks and builds before requesting DFU.
- Retain the working boot image and change one hardware variable per comparison.
- Batch separate, guarded modules in one RAM boot, checking cleanup between them.
- Keep both USB debugging paths available. Stop a batch if firmware health or resource restoration fails.
- Prepare userspace, package caches, input parsing, installer simulations and documentation without a DFU.
- Request a new boot when a kernel/DT/loader change or an independent cold-start check actually needs it.
- Record a physical screen/gesture/charger check only when the owner performs it. An automated protocol check is not a substitute.

## Proposed boot batches

IDs identify milestones, not a guaranteed one-DFU-per-row schedule. Batches may combine when their prerequisites are met. Battery, connectivity and desktop preparation can move earlier while touch remains open. GPU, camera and cellular work may each need several separate builds and boots. None of B01–B12 authorizes an internal-storage write.

| Batch | Work within that boot | Pass condition / owner action |
| --- | --- | --- |
| **B01 — current: contact detection** | The reader, raw path and C8 native-output gate are qualified. Confirmed gestures still produce only zero-contact native frames. Review exact J72 acquisition/processing state and current upstream N1 behavior; run distinct guarded comparisons in the existing boot. Corrected N1 control reads now pass an eight-second hardware comparison. | Actual contact counts, coordinates and release states must respond to owner gestures. Ask for another gesture test after a justified configuration change passes automated health and cleanup checks. No unchanged DFU or gesture loop. |
| **B02 — touch in Linux input** | Decode actual finger packets; qualify contact IDs, count, press/move/lift and axes; integrate a J72 input driver. Run evdev/libinput and the unprivileged desktop; integrate Home handling and a software keyboard. | Owner can tap, drag, reach screen edges, enter text and release every contact. Two fingers do not leave stuck contacts. Keep a USB shell for recovery. |
| **B03 — touch cold-start confirmation** | Boot the integrated driver from a clean state; repeat input and desktop checks, then return to iOS. | Independent boot succeeds without live register patches or manual permission fixes. Additional cold starts are validation work, not unchanged attempts at a known failure. |
| **B04 — battery and display controls** | Bring up the J72 UART5/HDQ gauge using exact board wiring; begin with identification and telemetry. Read brightness through the existing PMIC backlight driver, then test bounded changes and restore the starting value. | Plausible battery voltage, temperature, state of charge and current; compare with an iOS baseline. Owner confirms brightness changes. Battery reporting alone does not establish charging. |
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
| Input and desktop | Packet parser, contact-state checks, libinput orientation, Home binding, keyboard, service startup and teardown. | Desktop and temporary Home bridge have worked; native touch is not qualified. |
| Battery and charging | Audit the HDQ UART implementation, J72 clock/pin mapping, read-only gauge commands, charger telemetry and recording tools. | J72 identifies a BQ27540-family HDQ gauge under UART5. Air 2 work is reusable protocol research, with different board wiring. J72's D2089 PMU needs its own charger audit. |
| WLAN and Bluetooth | Map J72 HSIC/PHY/UART power dependencies, audit transport compatibility and privately stage matching firmware/board inputs. | The captured iOS tree places WLAN under EHCI/HSIC; an observed internal device has VID:PID `0a5c:bd1c`. This is not evidence that the current Linux USB WLAN driver supports it. |
| Display and power | Prepare backlight read/restore tools, thermal/idle logging, and display/input rotation configuration. | The existing target kernel builds the PMIC backlight driver. Its behavior on this panel still needs an owner check. |
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
