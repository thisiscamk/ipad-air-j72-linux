# Roadmap to a usable J72 Omarchy A tablet

This is a staged research plan, not an installation procedure. The current desktop runs from RAM and has passed its first owner-confirmed unplugged test with internal Wi-Fi; the Pi is still needed to start Linux after shutdown. iOS and the iPad's internal storage remain intact. Each stage needs real-device evidence before it can be called working.

The [DFU session plan](../DFU-PLAN.md) expands these milestones into proposed boot batches, work to prepare without the device, owner checks and installation dependencies. Several comparisons can share one RAM boot. The [independent-operation plan](../INDEPENDENCE-PLAN.md) now tracks the accepted first goal: Pi-assisted startup followed by unplugged use. Wi-Fi and continuous input now work in the unplugged desktop. Repeatability, autonomous power policy and internal storage still need engineering work.

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
- [x] Capture repeated finger frames and verify their layout and checksums (1,801 valid native reports, including one and two fingers).
- [x] Run the first owner tap-and-swipe capture: only startup status, no finger reports.
- [x] Compare polling both attention levels and alternating counters: no additional packets; owner participation in this second window is unconfirmed.
- [x] Trace the missing J72 display-sync setup, validate a guarded idle test, and observe an active sync-pad signal with full cleanup.
- [x] Test owner gestures with display sync enabled: 180-second capture, zero packets.
- [x] Validate application health with six known-query checks over ten seconds.
- [x] Validate a candidate BF setting across three delayed wake/readback cycles and an idle recorder with final application-health check.
- [x] Test owner gestures with the verified candidate setting and display sync: 180 seconds, zero packets; firmware information remains valid at the end.
- [x] Verify all 1,152 calibration bytes by checksum-valid SRAM reads before and after firmware upload.
- [x] Verify all five N1 setup register values immediately after writing and after calibration.
- [x] Build and run eight distinct reader comparisons in one RAM boot, with final firmware health and full restoration verified; the initial synthetic parser/transfer checks pass.
- [x] Compare 0/10/1,000-microsecond CS timing, success-only read tags, display sync, candidate BF setting and query priming; none establishes finger reporting.
- [x] Run corrected no-sync reader during confirmed owner gestures: one valid startup status frame, no finger packets, no malformed frames or transfer errors.
- [x] Compare the corrected reader with display sync enabled during confirmed owner gestures: zero packets, final firmware health and restoration passed.
- [x] Run targeted read-only status comparisons: report7f is `0x00040000` without sync and zero with sync; final health and restoration passed.
- [x] Select the audited alternative RAM report path: 106 checksum-valid raw result frames in eight seconds, with healthy firmware and full restoration.
- [x] Retain full tap/swipe and steady-hold captures: 833 and 1,089 valid raw frames, no overwritten data, final health and restoration passed.
- [x] Compare raw/native/raw modes in one power cycle: raw reporting resumes; no native finger frames.
- [x] Read processing counters: capture advances in native mode even while native report submission and USB output remain absent.
- [x] Test the verified candidate BF setting with the corrected reader during confirmed owner gestures: zero native frames; capture counter advances, health and restoration pass.
- [x] Identify active C8 report mask separately from BF and enable contact/periodic output: 228 valid empty native frames at idle, with advancing submission count and clean teardown.
- [x] Test confirmed owner gestures with C8 enabled: all 5,297 valid native frames contain zero fingers; health and restoration pass.
- [x] Review current Orchard touch PRs and add bounded classic-layout analysis; 18 offline checks pass.
- [x] Identify a missing shared analog-control dependency through the A7 J86 reference and independently verify it in the exact J72 iOS driver.
- [x] Correct analog enable to `0x07`: owner gestures produce contacts; firmware health and full cleanup pass.
- [x] Establish actual native finger reporting under the corrected analog power and C8 settings.
- [x] Decode bounded native contacts into Linux MT slots; owner confirms full-screen mapping and multi-finger traces.
- [x] Verify touch menus, launching Foot and on-screen keyboard typing/toggle in the unprivileged desktop.
- [x] Confirm window dragging in the integrated session.
- [x] Confirm native Home menu open/close in the integrated session.
- [x] Qualify the combined touch/keyboard image after a fresh RAM boot and verify final touch cleanup.
- [ ] Repeat longer integrated sessions and qualify USB reconnect and return to iOS with the new battery image.

The current driver correction starts every explicit transfer before queuing bytes, enables AUTO_TX only for receive-only transfers, drains the receive side within the FIFO window, and fixes the reversed Linux bit-order flag mapping. The GPIO path is a working upload fallback. Several distinct modules can run in one RAM session; these milestones are not necessarily one DFU each. Native touch input and text entry now reach the desktop. The reusable worker and automatic touch/desktop startup passed a cold RAM boot and same-boot reuse. The combined keyboard focus and touch retry fixes also passed an owner check after a fresh boot.

**Pass:** repeated cold RAM boots give usable touch in an unprivileged Omarchy A session, with clean return to iOS.

## 2. Make the tethered desktop dependable

- Script the Pi-to-iPad RAM boot, read-only root handoff, graphical startup and teardown with exact board and artifact checks.
- Integrate Home button handling into the input stack, then test menu behavior without the temporary bridge.
- Measure memory, frame rate and responsiveness on the A7 software-rendered desktop; trim the session where needed.

**Pass:** repeatable desktop sessions with touch, Home and USB recovery.

## 3. Bring up platform services individually

- Battery readings and the top-bar indicator work. Five-minute powered-hub desktop charging passed, and later runs measured positive current but ended before their planned duration. The latest stopped at the conservative temperature guard. Reduce Linux power use and qualify autonomous source/protection policy; retain the current guards. See [power results](../PI-CHARGING-PLAN.md).
- Prepare Wi-Fi in parallel with power work: the #34 wireless kernel and matched modules/owner-local firmware inputs are built and staged offline. J72 HSIC/reset sequencing, USB transport adaptation and networking are unfinished. See [the source review and Wi-Fi plan](../WIFI-PLAN.md). Bluetooth is a separate transport/firmware task. Keep USB networking available for recovery.
- Qualify audio, brightness, cameras, cellular, GPU acceleration and suspend separately. There is no evidence yet that all will be available.

**Pass:** each service works in use and survives repeated boot and shutdown cycles.

## 4. Integrate and share the port

- Turn the local experimental J72 worktree into a reproducible build with a 4 KiB-page kernel, matching modules, exact `iPad4,2`/`J72AP` identification and a documented RAM boot path.
- [Orchard PR #43](https://github.com/OrchardLinux/orchard/pull/43) is ready for review of measured SPI, touch, battery and bounded charging code. Native profile integration remains open; working Wi-Fi is intended for a separate contribution.
- Publish original code and sanitized evidence. Keep Apple firmware, calibration and raw device logs local.

**Pass:** another owner can build and test the RAM-only path on the exact model, with recovery instructions.

## 5. Prepare independent operation and persistent storage

A small RAM-resident root may permit an earlier unplugged demonstration once Wi-Fi works, subject to measured memory headroom. Persistent host-backed Linux can test updates first. Internal installation needs qualified J72 ANS1 access, iOS 12 coexistence, backup/recovery evidence and separate write authorization. Current Orchard now documents an experimental Air 2 internal-root success; its code is a useful reference. See [the active offline storage preparation](../INTERNAL-STORAGE-PLAN.md). The current standard installer/resizer does not support this J72/iOS 12 combination.

Native touch and text entry are demonstrated. The current input work is to remove the diagnostic lifetime limit safely and qualify long sessions. The larger remaining dependencies are HSIC Wi-Fi, autonomous power policy and local root storage. Internal storage would remove the Pi-served filesystem; fully independent startup is a separate boot-chain goal.

## Readiness for internal installation

- [ ] All required tablet services pass together in RAM/host-backed Linux, including Wi-Fi and power. Any feature deferral needs owner agreement.
- [ ] A host-backed writable image proves settings persistence, updates and recovery without iPad storage.
- [ ] J72 ANS1 works read-only with initialization and request-path write refusal.
- [ ] An iOS 12-compatible coexistence procedure, qualified write path and verified backup/recovery route exist.
- [ ] The exact installer plan passes a dry run and receives separate owner authorization.
- [ ] Internal root, host-assisted cold launch, updates and rescue are verified.

Internal installation is a separate engineering milestone. It does not remove the host required for cold boot, and the current iOS 16+ Orchard installation flow cannot simply be applied to this iOS 12 device.
