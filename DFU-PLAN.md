# Current checkpoint — 31 October 2026

- [x] B01: real native one- and two-finger contacts, matched presses/releases, firmware health and full cleanup. Corrected analog enable is `0x07`; voltage setting is unchanged.
- [x] B02: Linux multitouch slots, evdev and visual orientation passed (owner target/trace confirmation; 21 matched presses/releases). Compositor/libinput, touch menus and launching Foot now pass. Keyboard text entry and the top-bar toggle now pass too. Window dragging also passes. Native Home also opens and closes the menu without the earlier bridge. No new DFU requested.
- [x] B03: automatic self-check, full cleanup, touch restart and read-only desktop startup passed. The owner confirmed repeated keyboard hide/tap/type after the combined image's fresh boot.
- [ ] B04: brightness, Linux power-supply registration/readings and the corrected remaining/full capacity pairing passed. A fresh iOS comparison and battery UI remain; battery-health estimates are unqualified.
- [ ] B04C: brief net charging now passed: one 850 mA / 30-second wall test retained 12 samples at +20…+51 mA, from −766 mA baseline; automatic restoration passed and current returned to −765 mA. iOS recovery and charging are confirmed. Sustained charging, source detection/protections and USB recovery remain open before Wi-Fi.
- [ ] B05–B11: Wi-Fi, persistence/Bluetooth, charging regression with the desktop, audio/rotation, power/remaining hardware, integrated use.
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

## Previous UART-only boot results

- Automatic touch self-check, cleanup, restart and read-only desktop startup passed.
- UART5 registered and the bounded voltage trial returned three matching 3.824 V samples. The gauge identified as BQ27545 (`0x0545`); charge, temperature and cycle data also read successfully.
- Touch stopped on a stale C8 status-query reply. Final health and hardware restoration passed. A revised worker with bounded strict retries restored input in this same boot, then emitted 11,708 frames and stopped cleanly.
- The owner confirmed keyboard hide → tap → type twice in patched Foot; logs independently recorded the tap requests. Combined cold qualification remains open.
- Desktop/root unmounted, NBD detached and the owned export stopped. The owner confirms normal iOS is visible and wall charging.

## Latest combined boot: battery interface and cold input passed

The combined image booted and registered the guarded BQ27545 Linux power supply. Automatic touch/desktop startup passed, and the owner confirmed repeated keyboard hide/tap/type without live repairs. Three initial battery samples reported 78%, about 4.09 V and 34.6°C, with discharge current on the Pi link. The Pi kernel and original desktop image are unchanged.

The desktop/root, NBD export and touch worker were then stopped cleanly. A RAM-only recorder was started before the owner moved to the wall charger. USB failed to enumerate on return to the Pi. During the cable/port move the owner reported that the Pi hung and needed restarting. The wall-charger recording was not retrieved. The iPad is back on its charger; no wall-charging success is claimed. The previous host boot's crash journal is unavailable, so the cause of the host hang is not established.

The completed boot's test sequence was:

1. Verify exact J72 identity and pinned artifacts, then boot the combined image.
2. Check the battery driver identifies `0x0545` and registers a Linux power supply; keep both USB debug paths available.
3. Read voltage, temperature, charge level and current repeatedly. Compare with the prior bounded UART results and an iOS baseline; preserve uncertainty about capacity interpretation.
4. Confirm automatic touch/desktop startup and repeated keyboard hide/tap/type without live repairs. Exercise Home, dragging, release behavior and the existing brightness control.
5. Qualify the combined run with bounded status-read recovery, no stuck contacts or unexpected device loss, and full final hardware restoration.
6. After battery reporting passes, prioritize B04C charging bring-up. Continue in this boot if the recorder and required driver changes can run from RAM; otherwise prepare a concrete changed image for a later DFU. Stop and detach the USB-backed desktop root before any cable change.
7. Stop desktop/input, export evidence, detach the root/export and return to iOS.

**Remaining battery work:** the revised image's compensated remaining/full pairing now agrees with the gauge percentage on the device. Obtain a fresh iOS comparison before displaying health estimates. Signed UPower packages remain staged; their UI trial is deferred. The current image performs no battery NVM or charger-control writes. No iPad storage write is authorized.

### Revised next DFU prepared: capacity and recoverable observation

- The revised target kernel pairs compensated remaining/full capacity on J72. The previous working image is retained as a fallback.
- An 8 MiB RAM kernel log retains startup and USB evidence. The proven SPI transfer code and its register accesses are unchanged.
- The manual RAM recorder shows voltage, current, temperature and percentage, with green/red backgrounds for positive/negative battery current. It also retains the full RAM log.
- A local Home press/release may request a guarded USB gadget rebind, at most three separate requests. Desktop, NBD and input must already be stopped. This is an **untested recovery candidate**, not a demonstrated USB fix.
- The kernel, rebuilt touch module and diagnostic assets are packaged. Six capacity-selection cases, eleven Home-event cases, wrong-host refusal, shell checks and pinned-artifact preflight passed. Device qualification remains open.

In the next charged session, first qualify the visible readings and one Home recovery **while still attached to the Pi**. Capture host/target diagnostics before that action. If it fails, stop the batch. If it passes, observe the wall charger from the screen and take readings/photos at intervals. Return the iPad to iOS while it is still on the wall charger **before another Pi connection**; do not repeat the live Linux charger-to-Pi return in this trial. USB/source isolation and the host hang remain separate unresolved work. The Pi kernel stays unchanged.

## Immediately after battery reporting: B04C charging bring-up

**Wall result received:** the owner confirmed both photos were on the wall charger. Displayed uptime advanced by 161.39 seconds, battery fell 88% → 86%, voltage fell 4,046 → 4,037 mV and current remained −743 / −746 mA. Linux was net discharging. No charger controls were changed and the cause is not established. The owner has confirmed iOS is visible and charging on the wall charger. Next: audit J72 charger/source detection and inherited policy before preparing a concrete changed test. No new DFU is requested yet.

**PMIC wall comparison received:** automatic startup, clean desktop/NBD/input teardown and all 18 read-only register captures passed. Owner-confirmed wall photos retain the Pi settings: input suspend clear, nominal input limit about 100 mA, active battery-current setting and ceilings 3,150 mA. Battery current remains −742 / −743 mA. The two photo timestamps are 104.34 seconds apart; a five-minute duration is not claimed. No charger settings were changed. Input-current policy/source detection is now the next test candidate, with cause still unproven. The owner subsequently confirmed iOS is visible and charging; the powerboard USB rating cannot be confirmed. A fixed 425 mA / 30-second comparison has now passed offline preparation; hardware testing and restoration verification are pending.

**Earlier USB observation:** the first Home rebind restored network access, followed by a failed serial check and loss of network responses; cause remains unknown. A second rebind restored four network queries over 30 seconds without serial access. This qualifies that limited network recovery only. Both debugging paths and live Linux charger-to-Pi return remain unqualified.

1. Verify stable Linux voltage, temperature, state-of-charge and current readings, including current sign and units. Record a baseline under a known workload.
2. Audit the exact J72 D2089 charger path, inherited state, USB source detection, current limits and temperature protections. Prepare bounded diagnostics and any required driver changes before hardware testing.
3. Measure the existing Pi USB arrangement first. Determine whether the battery is gaining charge, discharging more slowly, or still discharging; a connected cable or a charging icon does not establish net charging.
4. Prepare a recorder and all its dependencies in RAM. Stop the desktop, unmount its root and detach the host export before asking the owner to switch to a wall charger. Wi-Fi is not a prerequisite for this RAM-only trial.
5. Record charger attach/detach and sustained operation. For the next trial, use the visible readings/photos and return to iOS on the wall charger before connecting to the Pi; live Linux USB return is not yet qualified. If charging requires driver work, qualify the documented control sequence with limits, fault handling and recovery before repeating the measurement.
6. Pass only with measured net charging over a useful interval, a consistent charge trend, temperature/current within the qualified limits, stable Linux operation and successful recovery of USB debugging and iOS.

Reuse the battery-test RAM boot when possible. New kernel/DT requirements may need another DFU; this milestone is not a promise of one boot. B08 remains a later regression of charging and cable transitions with the full desktop and a proven independent root/debug path.

## Subsequent DFUs and dependencies

- **B04:** Linux battery registration, repeated telemetry, current sign and a raw capacity comparison passed. Correct the exported capacity pairing and obtain a fresh iOS comparison. Brightness already passed.
- **B04C, next after B04:** bring up and measure Linux charging using a RAM-only diagnostic environment, before Wi-Fi work. The current image adds reporting only; charging diagnostics/control still need preparation and qualification.
- **B05–B06:** build and qualify the A7 internal HSIC/EHCI bus, enumerate the WLAN device, then validate matching firmware and the USB driver protocol, association and traffic. These are separate risks and may need several boots.
- **B07–B11:** host persistence and Bluetooth, full-desktop charging/cable regression, audio and rotation, power and remaining hardware, then integrated daily-use tests. Reuse a boot for userspace and runtime changes wherever possible.
- **B12–B15:** only after the required hardware/usability gates: storage read-only qualification, installer rehearsal, a separately authorized installation, then cold installed-system and recovery checks. No internal-storage write is currently authorized.

The full pass conditions and owner actions remain in the batch table below. Batch IDs are milestones, not a promise of one DFU each.

## Proposed boot batches

IDs identify milestones, not a guaranteed one-DFU-per-row schedule. Batches may combine when their prerequisites are met. Battery, connectivity and desktop preparation can move earlier while touch remains open. GPU, camera and cellular work may each need several separate builds and boots. None of B01–B12 authorizes an internal-storage write.

| Batch | Work within that boot | Pass condition / owner action |
| --- | --- | --- |
| **B01 — passed: contact detection** | Corrected the missing shared analog enable. Native one- and two-finger reports, coordinates and matched release lifecycles now pass. | Owner gesture capture, final firmware health and full hardware restoration passed. |
| **B02 — passed: Linux input** | Linux MT slots, screen mapping, menus, Foot launch, typing and the keyboard toggle passed. | Window dragging and native Home menu open/close passed. |
| **B03 — passed: integrated cold start** | Automatic self-check, full cleanup, touch restart and desktop startup passed. The combined image includes the touch retry and Foot focus fixes. | Owner confirmed repeated keyboard hide/tap/type after the fresh boot. Final touch health/cleanup and desktop/export teardown also passed. |
| **B04 — partly passed: battery and display controls** | Owner confirmed PMIC brightness dim/restore. Bring up the J72 UART5/HDQ gauge using exact board wiring; begin with identification and telemetry. Read brightness through the existing PMIC backlight driver, then test bounded changes and restore the starting value. | Plausible battery voltage, temperature, state of charge and current; compare with an iOS baseline. Owner confirms brightness changes. Battery reporting alone does not establish charging. |
| **B04C — next after battery reporting: charging bring-up** | Audit J72 charger/source detection and limits; measure the Pi arrangement, then use a fully RAM-resident recorder for wall-charger attach/detach. Qualify any required charger-driver changes. This precedes Wi-Fi work. | Sustained measured net charging, consistent charge trend, qualified temperature/current limits and recovery of USB debugging/iOS. Owner changes cables only after the desktop root/export is detached. |
| **B05 — Wi-Fi bus and device** | Qualify the internal EHCI/HSIC host, PHY, clocks, rails and reset without disturbing the external USB gadget. Read descriptors before selecting a WLAN transport driver. | The internal WLAN USB device enumerates and remains stable; external USB debug still works. Firmware startup and association are separate checks. |
| **B06 — Wi-Fi firmware and networking** | Use the matching local WLAN firmware and board data, validate the driver protocol, then test scan, association, DHCP, DNS and traffic. Keep credentials and identifiers private. | Owner's network works reliably under load; reconnect after a controlled disconnect. No driver-probe-only success claim. This is a separate driver risk from touch. |
| **B07 — persistence and Bluetooth** | Test a separate writable root/home image stored on the host, retaining the original image. Once Wi-Fi is stable, exercise the root/debug path over Wi-Fi. Bring up Bluetooth's UART transport and matching firmware with separate power guards. | Settings survive Linux sessions in the host image; Bluetooth discovery and a real keyboard/mouse connection work. No iPad storage is used. |
| **B08 — desktop charging and cable regression** | Repeat B04C charging qualification under the intended desktop workload, using a proven independent root/debug path before disconnecting USB data. Exercise the intended charger/data arrangement and transitions. | Net charging under the required workload, qualified temperature/current limits, stable desktop operation and recovery of USB debug. Owner changes cables. Never disconnect an active USB-backed root and assume cached files will suffice. |
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
| Battery and charging | Audit the HDQ UART implementation, J72 clock/pin mapping, read-only gauge commands, charger telemetry and recording tools. | The guarded BQ27545 Linux frontend now runs on J72. Voltage, current, charge level and temperature read successfully; capacity pairing needs correction. Charger observation needs log recovery after USB re-enumeration failed. No charger-control write was made. |
| WLAN and Bluetooth | Map J72 HSIC/PHY/UART power dependencies, audit transport compatibility and privately stage matching firmware/board inputs. | The captured iOS tree places WLAN under EHCI/HSIC; an observed internal device has VID:PID `0a5c:bd1c`. This is not evidence that the current Linux USB WLAN driver supports it. |
| Display and power | Prepare backlight read/restore tools, thermal/idle logging, and display/input rotation configuration. | The existing PMIC backlight driver passed a visible three-second dim/restore check and restored the original value. Battery voltage and temperature were read through the UART diagnostic; the Linux battery interface is ready for device qualification. CPU thermal and wider power management remain open. |
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

### Prepared current DFU batch: one 425 mA comparison

1. Reuse the existing RAM image; confirm automatic startup, then stop desktop, input and the USB-backed root/export cleanly.
2. Load the fixed-register observer and the experimental input-limit module into RAM. Loading and arming perform no PMIC writes. Confirm the new screen is visible and the original nominal 100 mA setting remains unchanged.
3. Move to the charging powerboard USB socket and confirm the display still advances. Only after this confirmation, one physical Home press starts the single 425 mA attempt. No higher-current step or repeat is enabled.
4. Record battery current, voltage, temperature and PMIC readback. A separate kernel workqueue schedules restoration after 30 seconds and verifies the original setting. Gauge reads cannot hold its policy lock. Photograph the active phase if possible and the retained result afterward. Software rollback still depends on a functioning kernel and PMIC bus; a restoration failure requires return to iOS on the charger.
5. Return to iOS while staying on the charger and confirm charging before any Pi attachment. Do not repeat the live Linux charger-to-Pi return.

The exact-kernel module build, 46 imported-symbol checks, 15 tests of the actual policy core, 10 battery-guard cases, syntax checks and pinned-artifact preflight passed. **The control experiment is not yet device tested.** The comparison may only reduce discharge: a higher input-limit setting alone does not establish actual USB input power or net charging. B04C remains open.

Current batch checklist:

- [x] Reuse verified J72 DFU; boot existing image.
- [x] Save battery baseline; stop desktop/input/root/export cleanly.
- [x] Load both modules unarmed; verify the original input setting.
- [x] Owner confirms the new screen and ready/unarmed/unused values.
- [x] Wait for battery at or below 95%; arm with all guards passing. The owner paused before the wall move; the test was disarmed without a control write. The same boot later resumed at 83%, the recorder restarted, and arming passed again with the original input setting unchanged.
- [x] Owner confirms wall attachment, then triggers one Home press.
- [x] Compare current response and photograph verified restoration: 12 trial samples at −423…−400 mA versus −764 mA before; final `restored=1`, `restore_failed=0`, `error=0` and original input-limit readback.
- [x] Return to iOS on the charger and confirm charging.

These steps use one RAM boot; no extra DFU is needed between them.

### Completed charging DFU: fixed 850 mA comparison

The single 425 mA comparison is complete, and the owner confirmed return to iOS and charging. A separate charger photo and the owner's explicit 5 V / 1 A rating now identify the next source. Its actual capacity has not been independently measured. The earlier powerboard will not be used for this test.

- [x] Obtain the separate source's stated rating.
- [x] Build and pin an isolated fixed 850 mA variant, preserving the measured 425 mA artifacts.
- [x] Pass native build/import, actual policy/failure, battery-guard, source-flag refusal, syntax and artifact checks.
- [x] New charged DFU; reuse the existing target RAM image.
- [x] Pass startup, capture battery baseline and stop desktop/input/root/export cleanly.
- [x] Stage the 850 mA module unarmed, confirm its screen and arm after battery checks pass.
- [x] Move to the specific 5 V / 1 A charger; confirm advancing uptime and allow a baseline.
- [x] One Home press: fixed 850 mA for 30 seconds, then automatic restoration to 100 mA. Photograph the active and restored phases.
- [x] Return to iOS while remaining on the charger; confirm charging before any Pi attachment.

These steps completed in **one RAM boot**. No host kernel or internal-storage changes are included. The same physical charging source must be used for all three comparison phases. A short positive battery-current result alone will not complete B04C: sustained positive current and charge-level trend, source policy/protections and desktop charging regression remain required.

### Remaining charging tests before Wi-Fi

- [x] Short positive net-current test and automatic rollback; owner-confirmed iOS recovery.
- [ ] Prepare source-aware policy and a longer bounded test with battery/current/temperature guards and independent rollback. New build and DFU only after offline preparation.
- [ ] Measure sustained positive current and charge trend; verify restoration and iOS recovery.
- [ ] Qualify USB recovery and later full-desktop charging/cable regression; do not return live Linux from wall to Pi before that path is resolved.

No next test image or DFU is requested yet.

## Added priority: charging with the Pi data link attached

See [the Pi charging plan](PI-CHARGING-PLAN.md). Audit the source and host USB
budget before the next current test. A separate powered charging/data hub
may be required: ordinary USB 2 standard-port allocation is at most 500 mA,
and the attached SSD declares 896 mA against the Pi 4's shared 1.2 A budget.
The wall-only 850 mA trial must not be run unchanged on a direct Pi port.

- [x] Static gadget/PHY/current-request audit and host descriptor inventory.
- [ ] Confirm Pi supply and any powered hub; select a qualified source.
- [ ] Prepare one guarded RAM boot for live USB configuration/current-path
  checks, a source-limited test and stable-data measurements.
- [ ] Qualify sustained charge and desktop operation without cable moves.

This work precedes another longer wall-only test where practical. No new
DFU is requested until a concrete source-qualified test is ready.

### Next DFU ready: verified powered JCH377, data retained

- [x] Owner model/marked port confirmed; adapter 5 V / 4 A, official Pi supply.
- [x] Paired iOS data and repeated charging reports pass; iOS reports 5 V / 1.5 A source.
- [x] Separate fixed 850 mA / 30-second worker built, source-gated and tested offline; original wall assets unchanged.
- [ ] Boot the unchanged RAM image through this hub and verify baseline, startup and clean teardown.
- [ ] Run one guarded current/data comparison without any cable move; verify automatic restoration and USB stability.
- [ ] Return to iOS on the same connection and confirm charging/data recovery.

The hub/iPad-only cable-move hang remains unexplained; previous-boot logs are
unavailable. Keep the present wiring fixed. This short data-retained test
precedes longer charging qualification. One new DFU is required for the batch.

**First hub boot attempt:** exploit setup/Checkmate passed, but download-mode
USB did not return. No Pongo/Linux or charging trial ran. Recover iOS first,
then use the prepared exact-iPad-port reconnect control during the loader
handoff, with all other wiring unchanged. This is a new transport control,
not another unchanged attempt. Charging and stable Linux data remain untested
on the hub.

### Revised next DFU: direct boot -> controlled RAM hub handoff

- [x] Archive the second hub boot failure: exact-port off/on completed but download mode did not return. No charging result.
- [x] Prepare and check a one-shot RAM UDC unbind/Home-rebind script with root/input/identity guards and no charger writes.
- [x] Make charging staging refuse an incomplete or still-running transfer handler.
- [ ] Connect the iPad directly to the Pi in iOS, verify it, then enter a new DFU.
- [ ] Boot through the known direct path; finish startup and clean root/NBD/input teardown.
- [ ] Follow the blue transfer screen: move to the powered hub’s marked port, then one Home press to rebind data.
- [ ] Verify live NCM and completed transfer, then perform the separate guarded 850 mA comparison and restoration.
- [ ] Return to iOS and confirm charging/data on the same hub connection.

The hub boot attempts will not be repeated unchanged. This prepared batch
uses one new DFU and one initial cable handoff; subsequent charging stays
on the hub with data connected.
