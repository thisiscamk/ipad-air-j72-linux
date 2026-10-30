# Roadmap to a usable J72 Omarchy A tablet

This is a staged research plan, not an installation procedure. The current boot runs from RAM with a read-only root filesystem served by a Raspberry Pi. iOS and the iPad's internal storage remain intact. Each stage needs real-device evidence before it can be called working.

The [DFU session plan](DFU-PLAN.md) expands these milestones into proposed boot batches, work to prepare without the device, owner checks and installation dependencies. Several comparisons can share one RAM boot. The number of DFUs remains open because touch, HSIC Wi-Fi and internal-storage support still need engineering work.

## 1. Finish native touch

- [x] Identify SCLK/MOSI through software pad sampling and measure SPI bit-order polarity.
- [x] Receive firmware ACK `0x4bc1` through GPIO SPI using the original private packet.
- [x] Receive firmware ACK `0x4bc1` through direct S5L hardware-controller PIO.
- [x] Validate corrected normal Linux SPI driver upload with ACK `0x4bc1`.
- [x] Distinguish the earlier C4 command from the proper address-bearing Z2 execute path.
- [x] Upload this panel's private calibration and proximity calibration with checked ACKs.
- [x] Apply the exact N1 setup and validate running firmware device information against iOS.
- [x] Read checksum-valid screen metrics and normal operating mode matching iOS.
- [x] Validate a bounded attention-gated reader at idle: one initial status frame passed both checksums, with no malformed frames.
- [ ] Capture repeated finger frames and verify their layout and checksums.
- [x] Run the first owner tap-and-swipe capture: only startup status, no finger reports.
- [x] Compare polling both attention levels and alternating counters: no additional packets; owner participation in this second window is unconfirmed.
- [x] Trace the missing J72 display-sync setup, validate a guarded idle test, and observe an active sync-pad signal with full cleanup.
- [x] Test owner gestures with display sync enabled: 180-second capture, zero packets.
- [x] Validate application health with six known-query checks over ten seconds.
- [x] Validate a candidate BF setting across three delayed wake/readback cycles and an idle recorder with final application-health check.
- [x] Test owner gestures with the verified candidate setting and display sync: 180 seconds, zero packets; firmware information remains valid at the end.
- [x] Verify all 1,152 calibration bytes by checksum-valid SRAM reads before and after firmware upload.
- [x] Verify all five N1 setup register values immediately after writing and after calibration.
- [x] Build and run eight distinct reader comparisons in one RAM boot, with final firmware health and full restoration verified; eleven synthetic parser/transfer checks pass.
- [x] Compare 0/10/1,000-microsecond CS timing, success-only read tags, display sync, candidate BF setting and query priming; none establishes finger reporting.
- [x] Run corrected no-sync reader during confirmed owner gestures: one valid startup status frame, no finger packets, no malformed frames or transfer errors.
- [x] Compare the corrected reader with display sync enabled during confirmed owner gestures: zero packets, final firmware health and restoration passed.
- [x] Run targeted read-only status comparisons: report7f is `0x00040000` without sync and zero with sync; final health and restoration passed.
- [x] Select the audited alternative RAM report path: 106 checksum-valid raw result frames in eight seconds, with healthy firmware and full restoration.
- [ ] **Current RAM session:** compare raw contents during deliberate owner touches, then qualify contact decoding.
- [ ] Establish actual scan/report enablement and attention behavior from finger packets.
- [ ] Read bounded touch reports and implement evdev input, including contact tracking, orientation and edges.
- [ ] Verify touch in the unprivileged desktop with owner screen checks.
- [ ] Repeat cold RAM boots and verify cleanup and return to iOS.

The current driver correction starts every explicit transfer before queuing bytes, enables AUTO_TX only for receive-only transfers, drains the receive side within the FIFO window, and fixes the reversed Linux bit-order flag mapping. The GPIO path is a working upload fallback. Several distinct modules can run in one RAM session; these milestones are not necessarily one DFU each. Native touch input remains unproven until reports reach the desktop.

**Pass:** repeated cold RAM boots give usable touch in an unprivileged Omarchy A session, with clean return to iOS.

## 2. Make the tethered desktop dependable

- Script the Pi-to-iPad RAM boot, read-only root handoff, graphical startup and teardown with exact board and artifact checks.
- Integrate Home button handling into the input stack, then test menu behavior without the temporary bridge.
- Measure memory, frame rate and responsiveness on the A7 software-rendered desktop; trim the session where needed.

**Pass:** repeatable desktop sessions with touch, Home and USB recovery.

## 3. Bring up platform services individually

- Establish battery reporting and safe charging under Linux. The Pi USB port has not provided reliable charging in these experiments.
- Bring up Wi-Fi and Bluetooth using the J72 buses, power controls and required firmware. Keep USB networking available for recovery.
- Qualify audio, brightness, cameras, cellular, GPU acceleration and suspend separately. There is no evidence yet that all will be available.

**Pass:** each service works in use and survives repeated boot and shutdown cycles.

## 4. Integrate and share the port

- Turn the local experimental J72 worktree into a reproducible build with a 4 KiB-page kernel, matching modules, exact `iPad4,2`/`J72AP` identification and a documented RAM boot path.
- Propose an experimental J72 profile to [OrchardLinux/hardware](https://github.com/OrchardLinux/hardware) once core desktop and touch are reproducible. State support limits clearly; J72 differs from existing Orchard profiles.
- Publish original code and sanitized evidence. Keep Apple firmware, calibration and raw device logs local.

**Pass:** another owner can build and test the RAM-only path on the exact model, with recovery instructions.

## 5. Consider independent operation later

A persistent root filesystem on an external host can come before internal-storage work. A host-launched internal install would need J72 ANS1 write support, an iOS 12-compatible layout procedure, backup and recovery evidence, and explicit owner authorization. The current Orchard installer and APFS resizer do not support this J72/iOS 12 combination. See the [deferred internal-storage plan](INTERNAL-STORAGE-PLAN.md). Internal storage would not by itself eliminate the host needed for DFU/Pongo after a cold restart. That work is outside the current RAM-only scope.

Native touch is the main uncertainty. Firmware upload, calibration acceptance and application startup now pass; a reliable completion date still depends on scan/report enablement, report handling and real input validation.

## Readiness for internal installation

- [ ] All required tablet services pass together in RAM/host-backed Linux, including Wi-Fi and power. Any feature deferral needs owner agreement.
- [ ] A host-backed writable image proves settings persistence, updates and recovery without iPad storage.
- [ ] J72 ANS1 works read-only with initialization and request-path write refusal.
- [ ] An iOS 12-compatible coexistence procedure, qualified write path and verified backup/recovery route exist.
- [ ] The exact installer plan passes a dry run and receives separate owner authorization.
- [ ] Internal root, host-assisted cold launch, updates and rescue are verified.

Internal installation is a separate engineering milestone. It does not remove the host required for cold boot, and the current iOS 16+ Orchard installation flow cannot simply be applied to this iOS 12 device.
