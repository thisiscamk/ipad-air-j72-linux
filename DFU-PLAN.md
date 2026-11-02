# Current: iOS inspection complete; no new DFU needed yet

- [x] Combined #35 desktop, Wi-Fi, input, native read checks and mounted cleanup.
- [x] One-hour charging observation and independent input-limit restoration.
- [ ] Sustained net charge at normal brightness: latest hour lost 97.30mAh.
- [ ] Thermal cooldown/restart: guard held at 38.1°C, restart not observed.
- [x] Build/test a separate bounded recovery-window touch candidate.
- [ ] Next changed RAM session: stage candidate, self-check, then long input/power observation.
- [x] Restore brightness 1604 and governor schedutil; return to iOS charging.
- [x] Owner reapplies Amethyst; root SSH and query-only storage helper pass.
- [x] Refresh APFS minimum: unchanged126357602304 bytes; 4KiB physical blocks.
- [x] Host bounded-map rehearsal, 35 model tests and live checkpoint checks.
- [ ] Qualify iOS12 resize, fenced writer, flush and interruption recovery.
- [ ] Review the exact installation proposal and obtain separate write approval.
- [ ] Install/verify approved layout and image, then changed DFU for local RO root.
- [ ] Later: persistent state, autonomous charging and fully PC-free startup.

No internal writes are authorized or performed. The iPad remains in iOS on the
powered hub. The next RAM test should include a reviewed touch-recovery change;
unchanged charging or DFU retries will not resolve the remaining gates.

[Power measurements](code/charging/maintain35/),
[touch failure](code/touch/LONG-RUN-20261102.md),
[storage transaction plan](INSTALL-TRANSACTION-PLAN.md).

## Earlier preparation

# Owner away: preparation complete; no DFU needed yet

- [x] Keep the combined desktop/Wi-Fi/native-read boot available for the owner.
- [x] Temporarily dim to 401 and run a bounded low-battery return-to-iOS observer.
- [x] Confirm live kernel linear device-mapper target without creating a mapping.
- [x] Prepare bounded native-view planner; current all-APFS map correctly refuses.
- [x] Rehearse future GPT bytes and image hash on host; 13 tests pass, no device writes.
- [x] Prepare #35 RAM desktop and guarded charging adapters; host preflights pass.
- [x] Owner confirms all desktop functions; away observer cancelled, brightness restored1604.
- [x] Normal mounted-container/loop/ext4/NBD/owned-export cleanup passes in this boot.
- [ ] Qualify known RAM workload on #35 and freshly measured hub source before power testing.
- [ ] Qualify iOS 12 resize, fenced image/GPT writer and recovery; review exact install proposal.
- [ ] Separate owner authorization for reviewed writes, then install/verify through qualified backend.
- [ ] Changed DFU: boot local read-only root through a bounded verified partition view.
- [ ] Later: native persistence/flush/update/recovery, autonomous charging and PC-free startup.

The layout rehearsal is not executable or approval-ready. No internal operation
has been authorized. [Prepared source/results](code/storage/native-root-preparation/).

## Previous checkpoint

# Current checkpoint: one-hour net charging pass; combined storage DFU prepared

- [x] Owner confirms RAM desktop, Wi-Fi, menu, keyboard and charging icon on hub.
- [x] Complete one-hour observation: 82% → 88%, estimated net +134.65 mAh.
- [x] Observe three automatic voltage-hold restarts and fault-free final baseline restoration.
- [x] Restore brightness to 1604; cleanly stop desktop, touch and WLAN provider.
- [x] Build/audit matched #35 desktop/storage payload; original kernel/loader/DTB retained.
- [x] Rehearse 1536 MiB ext4 + compressed-base format on host, read-only checks and cleanup pass.
- [x] Direct-Pi DFU: combined #35 boot, both recovery shells and native read-only checks pass.
- [x] Same boot: Wi-Fi association/HTTPS/SSH, USB container-format desktop ready and concurrent native reads pass.
- [ ] Owner checks portrait/menu/Wi-Fi/Foot/keyboard; keep USB connected.
- [ ] Normal mounted-container cleanup, read-only loop/NBD detach and owned host export stop.
- [ ] Finalize bounded native mapping and exact resize/GPT/image-write/recovery proposal.
- [ ] Obtain separate owner approval before internal writes; no install is currently authorized.
- [ ] Install only after procedure qualification and verify image/map before booting.
- [ ] Later changed DFU: local read-only root, Wi-Fi/input, clean USB detachment and unplugged use.
- [ ] Qualify durable writes, persistence and update/recovery handling separately.
- [ ] Finish thermal restart, autonomous source detection and longer charging endurance before unattended use.
- [ ] Investigate on-device startup; Pi-assisted startup remains the interim route.

The next DFU is a read-only rehearsal, not an installation. The count after that
is conditional on native access, installation-method and recovery qualification.
[Candidate and runbook](code/storage/desktop-storage35/).

## Previous checklist

# Current boot: compressed desktop qualified; RAM desktop ready for hub power test

- [x] Qualify restricted RAM recovery: SSH, md0 root, no APFS mounts, GPT CRCs.
- [x] Measure unmounted minimum: same 1.64 GB release allowance as normal iOS.
- [x] Return normally to iOS; owner confirms screen, paired battery 99%.
- [x] Build 572 MB compressed desktop privately; five file readbacks pass.
- [x] Build matching #34/#35 SquashFS modules; 106 imports resolve to vmlinux.
- [x] Prepare #34 compressed-desktop controller, host export and cleanup; preflight passes.
- [x] Direct-Pi DFU: proven Pongo and --wifi-ram-desktop boot.
- [x] Load matched module; start read-only NBD/SquashFS desktop; ready marker and memory checks pass.
- [x] Owner confirms initial portrait/menu/Foot dragging and keyboard hide → tap → type twice.
- [x] Normal unmount/NBD/export/touch cleanup; Wi-Fi association, HTTPS and Wi-Fi SSH pass in the same boot.
- [x] Resume compressed desktop with Wi-Fi; read-only mount and bar connected-status checks pass.
- [x] Owner verifies restored Wi-Fi window/menu/keyboard.
- [x] Clean up compressed desktop and restore known RAM workload; no export remains.
- [x] Stage maintenance charging worker disabled, with independent baseline unchanged.
- [ ] Owner checks restored RAM input and moves to qualified powered hub; verify source/data path before charging.
- [ ] Observe charging cooldown/restart and sustained net gain under the unchanged protection limits.
- [ ] Integrate native storage reads with the compressed base and review the conditional 1536 MiB layout.
- [ ] Obtain separate approval for exact shrink/GPT/image writes before installation.
- [ ] Qualify local read-only root, then persistent write/flush/overlay behavior.
- [ ] Finish charging cooldown restart and sustained net gain before unattended charging.

The compressed export is detached; the RAM desktop and Wi-Fi are running. No internal storage, resize or
snapshot operation is part of it.
[Compressed candidate/runbook](code/storage/compressed-desktop/),
[space/layout review](SPACE-CREATION-REVIEW.md).

## Earlier checkpoints

# Next DFU: qualify the recovery root-device check and inspect storage

- [x] Pass revision2 RAM stage and independent handoff checks.
- [x] Boot recovery and pass pinned-host/client-key SSH authentication.
- [x] Execute forced inspector; preserve its mount-guard refusal before disk open.
- [x] Build revision3 with root-to-md0 device comparison and structured diagnostics.
- [x] Pass 25 actual-inspector cases and six transport cleanup/refusal cases offline.
- [x] Return to normal iOS on the direct Pi connection.
- [ ] Fresh direct-Pi DFU: boot revision3 and capture the actual mount/device guard.
- [ ] After all guards pass, validate both GPT copies and try the APFS minimum getter.
- [ ] Review space creation if the 1.64 GB shrink allowance persists.
- [ ] Qualify native writes/flush and persistent root before a reviewed installation.
- [ ] Qualify charging cooldown restart and sustained net gain before unattended use.

The root-label explanation is source-supported, not yet measured on this device.
No resize, snapshot mutation, internal install or erase is authorized.
[Source and separate device/offline evidence](code/storage/ios12-pongo-handoff/).

## Earlier checkpoints

# Next DFU: authenticate to the RAM recovery and inspect storage read-only

- [x] Pass compact inventory, original kernel and entire stock cache checks.
- [x] Stage and independently verify the 130 MB RAM recovery bundle on J72.
- [x] Reach its unique USB service, SSH banner and pinned host key.
- [x] Identify the 0775 root-home permission defect blocking authentication.
- [x] Build revision2 with audited home/.ssh/key ownership and modes.
- [x] Automate recovery-only no-preflight USB transport; cleanup/refusal checks pass.
- [x] Owner returns to iOS; normal model/version/direct-Pi connection verified.
- [ ] Next direct-Pi DFU: proven Pongo loader, revision2 RAM stage and boot.
- [ ] Pass key authentication and forced RAM-root/no-APFS inspector guards.
- [ ] Validate both GPT copies and obtain the optional unmounted APFS minimum.
- [ ] Review space creation if the 1.64 GB shrink allowance persists.
- [ ] Qualify native storage writes/flush and persistent root before a reviewed install.
- [ ] Finish charging cooldown restart and sustained net-charge qualification.

No resize, snapshot mutation, internal installation or erase is authorized.
[Revision2 source/offline checks and revision1 device result](code/storage/ios12-pongo-handoff/).

## Earlier checkpoints

# Next DFU: guarded Pongo RAM recovery handoff

- [x] Compact Pongo inventory: original kernel UUID,16 empty slots and RAM ranges pass.
- [x] Match the live cache header to the exact Apple-manifest stock component.
- [x] Build a serialized cache preserving1728 stock records plus recovery entries:1881 total.
- [x] Build the RAM-only stager and130MB bundle; native imports and offline checks pass.
- [x] Return to normal iOS and verify the direct Pi connection after follow-up USB failure.
- [ ] Fresh DFU: proven Pongo loader, then **handoff module** once; do not reload the observer.
- [ ] Verify entire original RAM trust cache, upload pinned bundle, stage and recheck RAM metadata.
- [ ] Boot the staged RAM image; qualify its unique USB marker, pinned SSH key and guarded inspector.
- [ ] Validate both GPT copies and an optional unmounted-APFS minimum-size query.
- [ ] Review space creation if the1.64GB shrink limit persists; no snapshot/layout change yet.
- [ ] Qualify native storage writes/flush and persistent root before a separately reviewed install.
- [ ] Finish charging cooldown restart and sustained net-charge qualification before unattended Linux charging.

The new test stages RAM and requests a RAM-root boot. No internal installation,
resize, snapshot mutation or erase is authorized. [Candidate and gates](code/storage/ios12-pongo-handoff/).

# Next DFU: compact Pongo recovery inventory

- [x] Boot proven Pongo and load the revised observer.
- [x] Pass allocator/argument metadata guards and the previously blocking DT property.
- [x] Preserve the incomplete verbose capture and USB failure evidence.
- [x] Verify normal iOS and the direct Pi connection after the device returned.
- [x] Build/test a compact observer and a client that reads the console after command completion.
- [ ] Fresh DFU on the current direct Pi cable; load the compact observer once.
- [ ] Verify the original kernel UUID, empty map slots and RAM handoff ranges.
- [ ] Prepare and qualify RAM recovery using a healthy Pongo session where possible.
- [ ] Review safe space creation; qualify native write/flush/root before any install proposal.

There is no internal-storage mutation in this test. Recovery has not booted.
The APFS minimum still leaves only about 1.64 GB shrink allowance.
[New observer and checks](code/storage/ios12-pongo-compact/).

# Next DFU: one corrected Pongo inventory load

- [x] Use the proven direct-Pi checkra1n → Pongo path successfully.
- [x] Register the original observer and pass exact model/RAM/DT guards.
- [x] Capture the full memory map: 16 unused slots and an existing trust cache.
- [x] Correct handling of the 4-byte handle, zero-length flag and doubled newlines.
- [x] Test the actual property callback; avoid repeat module uploads and built-in boot-argument commands.
- [ ] Owner returns to normal iOS on the current direct Pi cable.
- [ ] Fresh DFU: load the revised observer once; verify original kernel UUID and allocator bounds.
- [ ] Prepare/qualify the RAM recovery handoff with that evidence, retaining a healthy Pongo session.
- [ ] Review a concrete space-creation proposal before any internal changes.

The recovery image has not booted and the 1.64 GB shrink allowance remains a
separate installation blocker. [Measured result and code](code/storage/ios12-pongo-probe/).

# Next DFU: read-only recovery inventory through proven Pongo

- [x] Observe gaster's A7 PATCH/reconnect boundary; stop before any image upload.
- [x] Confirm that two cable cycles did not restore USB; do not resume or repeat the same exploit.
- [x] Compare Legacy iOS Kit's gaster fork: its A7 payload and reconnect logic are unchanged.
- [x] Return to iOS; verify iPad4,2 / 12.5.7 on the direct Pi connection.
- [x] Build a read-only Pongo handoff probe; 8 memory-span, 143 Mach-O and 8 response-refusal cases plus fragmented transport checks pass.
- [ ] Next DFU: use the already proven checkra1n → Pongo 2.6.3 launcher.
- [ ] Load the probe in RAM; match the loaded Apple kernel UUID and inventory boot arguments/memory-map slots.
- [ ] Use that evidence to prepare the RAM recovery handoff; reuse a healthy Pongo session for compatible work.
- [ ] Qualify the recovery boot before any space-creation or installation proposal.

The changed test bypasses gaster and inspects the existing XNU handoff.
It has no boot, kernel-patch, DeviceTree-edit or disk-access command.
The iOS recovery image has still not booted. [Probe source/results](code/storage/ios12-pongo-probe/).

# Recovery DFU follow-up: A7 reconnect handling

- [x] First changed DFU: exact J72/direct Pi verified; gaster timed out before any image upload.
- [x] Reap the loader group and inspect USB; two cable cycles did not restore enumeration.
- [x] Add/test line-buffered live logs and interception of gaster's A7 reconnect prompt.
- [x] Add/test a saved-attempt resume gate requiring the same ECID, capsule and gaster marker; partial image uploads refuse resume.
- [ ] Confirm normal iOS after a manual Top+Home restart; keep the direct Pi cable.
- [ ] New DFU for the revised manual-step handling, then use cable cycles only when its live prompt is reached.
- [ ] Qualify the actual recovery image and storage reads. Neither has run yet.

The first attempt's exact exploit stage is unknown because stdout was buffered.
No bootloader, recovery image or storage inspector was uploaded. The functional
change for the next DFU is handling A7's manual reconnect boundary and resuming
that same attempt without a repeated exploit. [Source/results](code/storage/ios12-ram-recovery/).

# Next DFU: iOS 12 RAM recovery qualification

- [x] Build a separate recovery capsule with the original J72 iOS 12.5.7 kernel.
- [x] Restrict startup to one guarded USB service; key-only SSH permits only inspection/reboot.
- [x] Pass boot-argument guards, CodeDirectory/cache checks, image readback and native launcher checks.
- [x] Publish the actual authored service, inspector, stubs and build/boot/test recipes.
- [ ] Move only the iPad cable directly to the Pi and enter the next DFU.
- [ ] Boot the new recovery capsule once; verify its unique USB marker and pinned SSH host key.
- [ ] Confirm RAM root/no APFS mounts; validate both GPT copies and try the read-only minimum-size getter.
- [ ] Return to normal iOS and confirm charging. Review results before proposing snapshot or layout changes.

The recovery capsule is **not device-qualified yet**. It does not install,
resize, mount APFS or remove the rollback snapshot. The measured 1.64 GB
shrink allowance still blocks the intended Linux layout. This replaces the
previous “no new recovery payload ready” preparation status.
[Source and offline results](code/storage/ios12-ram-recovery/).

# 2 November: leave-on power candidate and storage qualification

- [x] Requalify the powered JCH377 using current paired iOS diagnostics.
- [x] Try DFU through the hub as requested: checkm8 reached; download handoff failed, no Linux.
- [x] Bypass the hub for boot: exact J72 Pongo and proven RAM desktop boot pass.
- [x] Restore internal Wi-Fi, HTTPS, pinned SSH and RAM desktop; owner confirms menu/keyboard.
- [x] Return to the same hub with Wi-Fi alive; same-UDC USB rebind restores data.
- [x] Build/load the new maintenance controller disabled; direct Pi source refusal passes.
- [x] Observe full-pack hold, held-source lease loss, fault latch and explicit requalification.
- [x] Observe positive charging, active-source lease withdrawal/restoration in 2.27 seconds, explicit restart and automatic voltage/cool holds.
- [x] Complete 3600.6 seconds of controller observation without faults and independently verify final restoration.
- [ ] Qualify automatic cooldown restart and sustained net charge gain; native source detection remains open.
- [x] Return to iOS and confirm locked-screen hub charging: 42% → 44% over three minutes, all sampled currents positive. This is an iOS result.
- [x] Build and pin the isolated #35 recovery-only storage image; 307 host cases and matching module imports pass.
- [x] Boot #35; verify live firmware, both recovery shells, Identify and repeated direct reads.
- [x] Capture/validate both GPT copies and APFS checkpoint/space manager; no free partition gap exists.
- [x] Reapply existing Amethyst; verify root SSH, snapshot counts and the exact APFS minimum-size query.
- [ ] Resolve the measured minimum-size limit: only 1.64 GB can currently be released; retain the original root snapshot until recovery is reviewed.
- [ ] Capture fresh layout, qualify safe space creation and native root, then review exact install changes.

The owner has no backup and does not need the device's personal content.
iOS preservation remains the layout default; erasure is not implied. Recovery
metadata and exact write-plan review are still required. Internal installation
is not enabled by this checklist. [Power candidate](code/charging/maintain34/).

# J72 session plan: power, Wi-Fi and independent operation

Updated 1 November 2026. **The first unplugged RAM desktop test passed:**
terminal, menu, touch and keyboard work, with Wi-Fi SSH and verified HTTPS.
The host disk export is stopped. Wi-Fi plus guarded hub charging also passed
a fifteen-minute continuation with verified restoration. Startup after a
shutdown still requires the Pi; autonomous power policy remains open.

## Next storage preparation

The [morning runbook](STORAGE-MORNING-PLAN.md) lists the read-only inventory, implementation, backup, coexistence, rehearsal and later installation batches. Offline checks pass; no fully built ANS1 observer or installer is ready yet. Leave the iPad in iOS charging until a concrete changed test is ready. No storage writes are authorized.

## Latest Wi-Fi session

- [x] Boot #34 and pass its initial touch self-check.
- [x] Repair matching NCM/FunctionFS/NBD/evdev recovery modules and indexes in RAM; both USB shells respond.
- [x] Enumerate the internal radio: high-speed USB `0a5c:bd1c`.
- [x] Read a complete ROM identity: chip `0x4324` (BCM43241), revision 6, 576 KiB RAM.
- [x] Review current Orchard main, PRs and the P105-pinned Cascadia USB transport.
- [x] Use standard-driver shutdown to verify halt before removing the USB bus in the same boot.
- [x] Return to iOS to release the previous boot’s retained owners; qualify the revised provider’s complete cleanup in the next boot.
- [x] Build a new candidate with the complete recovery closure, earlier power-domain attachment, synchronized stop and brighter display; cold qualification pending.
- [x] Build the exact USB/chip/revision transport candidate and validate private J72 TRX/NVRAM offline.
- [x] Stage separate RAM Wi-Fi/DHCP/HTTPS/SSH tools and pass native localhost SSH, DHCP/configuration and bundle-transfer checks.
- [x] Build Orchard’s port-authorization fix for exact #34; 16 actual-source offline combinations pass. Runtime update is ready before first driver load.
- [x] Fresh boot: recovery, brighter startup, RAM tools, firmware loading/re-enumeration and wlan0.
- [x] Scan, WPA2 association, DHCP, DNS, HTTPS and pinned-key Wi-Fi SSH.
- [x] Deliberate disconnect/reconnect, explicit DHCP renewal and desktop-user HTTPS.
- [x] Owner confirms brighter desktop, menu and keyboard with Wi-Fi active; new Wi-Fi bar popup works.
- [x] Qualify Wi-Fi with guarded charging: five-minute interactive and fifteen-minute continuation pass.
- [x] Qualify new provider full stop/restoration and both USB recovery shells.
- [x] Repeat Wi-Fi firmware startup, association and HTTPS/SSH after another DFU.
- [ ] Qualify longer traffic and integrated recovery/charging policy.

No new DFU is needed for the current RAM desktop work. Radio firmware has
been loaded successfully in RAM; it remains private.
See [Wi-Fi findings and reuse plan](WIFI-PLAN.md).

## Current Wi-Fi and charging batch

- [x] Move the running #34 system to the qualified hub; Wi-Fi SSH survives.
- [x] Recover USB data with a same-UDC software rebind; no extra DFU.
- [x] Trace an initial early stop to an HDQ flags-read timeout; baseline restored.
- [x] Build/test a bounded fresh-gauge retry worker without changing guard limits.
- [x] Complete 300.273 seconds of Wi-Fi/interactive-desktop charging: time-weighted +211.332 mA, one -140 mA sample, verified restoration.
- [x] Owner confirms menu, keyboard and charging indication; HTTPS passes during charging.
- [x] Complete 900.447 seconds of continuation: 424 settled samples, all +239..+397 mA, time-weighted+306.965 mA, verified restoration.
- [x] Qualify complete Wi-Fi provider stop, independent hardware restoration and both USB recovery shells.
- [x] Repeat radio startup, association, HTTPS and Wi-Fi SSH in a fresh boot.
- [x] Start the corrected RAM desktop with Foot/Bash and valid UTF-8 locale; no NBD export.
- [x] Owner confirms menu, typing and keyboard in the fresh RAM desktop.
- [x] Test serial respawn across a real cable cycle; ACM and NCM recover without a manual shell restart.
- [x] Complete five minutes of RAM-desktop/Wi-Fi hub charging: mean +296.8 mA, two negative readings, independent restoration.
- [x] Owner confirms iOS visible and charging on the same hub for the overnight break.
- [x] Start the reduced desktop from RAM; verify NBD/export detached, live processes, Wi-Fi HTTPS and about 235 MiB available.
- [x] Owner confirms terminal, menu, touch and keyboard unplugged; same-boot Wi-Fi SSH and desktop-user HTTPS pass with the host USB device absent.

The short result includes a brightness change from 1604 to 1203; it does not
qualify SOC gain, autonomous charging policy or timeout recovery. See the
[actual worker, tests and bounded result](code/charging/wifi34-refresh/).

## Completed on this J72

- [x] RAM Linux and read-only Pi-served desktop; software rendering.
- [x] Native one/two-finger reports, Linux multitouch and owner-confirmed mapping.
- [x] Menus, Foot dragging, keyboard hide/tap/type and Home menu toggle.
- [x] Automatic touch self-check, cleanup/restart and desktop startup after a fresh boot.
- [x] Linux battery reporting, corrected capacity pairing, visible brightness control and top-bar battery/charging indicator.
- [x] Read-only EHCI capability observation and power-domain restoration; later USB/ROM results and separate cleanup limit are recorded above.
- [x] Powered-hub USB data and five-minute desktop charging: 140 positive readings, +178…+216 mA, verified rollback.
- [x] Charging remained active through a controlled touch stop/restart after removing the monitor's touch dependency.
- [x] Return to iOS for charging; host export and monitor stopped.
- [x] Interim measured-code Orchard PR #43 submitted for review.

The dimmed continuation lasted 17.2 minutes, not its planned 30 minutes.
The later nominal one-hour continuation stopped at the conservative 38.1 C
test cutoff after 526 positive readings (+36…+209 mA). The worker reported
restoration; reboot prevented retrieval of an independent final PMIC snapshot.
Neither full duration passed. Percentage jumps under load are not a qualified
charge-level trend. Battery health, autonomous source policy, long-session
input and sustained charging remain open.

## Offline work now complete

- [x] Build opt-in continuous touch for #33 and #34, retaining fault/manual-stop paths.
- [x] Build isolated #34 Wi-Fi kernel with rfkill/cfg80211/USB brcmfmac.
- [x] Stage matched wireless/vendor/touch modules, dependency indexes and private firmware inputs; check hashes, exports and TRX CRC.
- [x] Identify missing USB match and unresolved BCM4324B5 HSIC transport; no forced bind.
- [x] Review Orchard main at 824bf034 and J81 native-root contributor sources.
- [x] Reproduce the imported ANS1 shutdown double-free with host stubs; prepare a one-line candidate and passing regression check.
- [x] Expand local-root, internal installation and cold-start independence plans.
- [x] Package N1 continuous touch, its five-second self-check, reduced initial
  brightness and automatic battery widget. Original #33 kernel/DT/loader and
  read-only desktop are retained.
- [x] Fresh N1 boot: continuous mode active beyond its three-second fallback;
  explicit stop/firmware health/cleanup and automatic restart pass. Desktop
  startup and battery-widget IPC pass at 802/2047 brightness.
- [x] Owner confirms battery/dimmer startup and repeated keyboard hide/tap/type
  after restoring a changed side-bar setting to top; no new DFU.
- [x] Clean input shutdown after about 26 minutes and 47,598 frames; firmware
  health and cleanup pass. Longer reliability remains open.
- [x] Prepare new-payload charging helper with unchanged worker/guards; actual
  direct-Pi source refusal passes. Clean teardown and RAM hub handoff prepared.
- [x] Powered-hub data return, desktop/input restart and owner UI confirmation.
- [x] Start guarded lower-power charging with the unchanged worker/guards:
  initial settled +449…+469 mA, 36.6 C, no faults. Full duration is not claimed.
- [x] Retain the 27.2-minute voltage-guard endpoint and independently verify
  original-limit restoration. Full hour remains unqualified.
- [x] Observe HSIC PHY registers through the existing Linux power owner, with
  automatic clock gating handled and both domains restored. No radio enable.
- [x] Bounded native PHY transition with exact baseline restoration.
- [x] Radio reset and GPIO-owned HOST_READY handshake; DEVICE_READY response
  measured and all state/ownership restored, in the same RAM boot.
- [x] Read halted EHCI registers during the ready handshake; all state restored.
- [x] Audit remap `0x108` and live OF DMA range, noncoherent DMA and AIC translation.
- [x] Correct controller-driver binding and capture USB descriptors/ROM identity on #34.
- [ ] Integrate the measured standard-shutdown repair and qualify full cleanup.
- [x] Compose matched #34 kernel/touch/wireless/vendor payload with a real
  controller driver and phase capture; 83 synthetic API cases pass; now booted with USB/ROM success and teardown failure recorded above.
- [x] Boot #34 and confirm USB/ROM identity; recovery packaging needed a same-boot repair.
- [ ] Qualify a corrected cold-boot payload, full cleanup and adapted firmware transport, then scan/associate.

## Remaining boot batches

Several checks may share one boot. Kernel, DT or loader changes, and fresh
cold-start qualification, can require another DFU. These are expected batches,
not a fixed number of DFUs. N1–N5 involve no iPad storage writes. S1–S2 are
read-only/rehearsal; S3 alone represents a later separately approved install.

| Batch | Checklist | Owner check / exit condition |
| --- | --- | --- |
| **N1 — continuous input and lower-power operation** | Package a matched payload and battery widget; five-second continuous-mode check against a three-second finite fallback; explicit stop/health/cleanup/restart; longer touch and lower-power charging tests. | Touch remains usable beyond the old timer; charging, temperatures, rollback and recovery pass within unchanged guards. |
| **N2 — internal WLAN bus** | Audit and implement exact J72 HSIC PHY, clocks, reset and ready signals; compose DT/module changes; inspect descriptors before binding the WLAN driver. | Stable WLAN enumeration and external USB debugging; clean failure/rollback. |
| **N3 — radio and networking** | Adapt exact USB firmware/download/re-enumeration behavior; private board data, vendor helper and signed regulatory database; scan, association, DHCP, DNS, HTTPS, traffic/reconnect and Wi-Fi SSH. | Owner network and sustained traffic pass; recovery USB survives. May share N2 if transport changes are already prepared. |
| **N4 — optional unplugged RAM-root demonstration** | Build and measure a minimal fully local root/desktop; verify all dependencies fit RAM and cleanly detach every USB-backed mount/export. | Owner confirms usable desktop after unplug, managed over Wi-Fi. No persistence across reboot. If memory is insufficient, wait for qualified internal storage. |
| **N5 — integrated tablet qualification** | Host-backed persistence/updates; power/source withdrawal, repeated boots, required audio/Bluetooth/rotation and other agreed hardware; charging and network regression. | The owner's required feature set works together with stable memory/performance and rescue/iOS recovery. Feature deferrals need agreement. |
| **S1 — read-only J72 ANS1** | After usability gates: reviewed loader/driver, inherited firmware, mailbox/DMA, write-unlock/output denial, geometry/GPT and bounded repeated reads. | Stable hashes, both GPT copies inspected privately and normal iOS recovery; no journal replay or storage write. |
| **S2 — installer rehearsal** | Verified backups/recovery; proven iOS 12 coexistence; hardened bounded write path; synthetic layout/failure tests; exact dry-run report. | Concrete preserved/changed ranges and hashes reviewed. No device write yet. |
| **S3 — separately approved installation** | Requires new explicit authorization for S2's exact plan. Install only approved ranges; filesystem/readback checks and rescue remain available. | Local root boots with validated drivers; agreed iOS layout preserved. |
| **S4 — installed-system qualification** | Fresh Pi-assisted launches, persistent marker/identity, unplugged desktop, autonomous charging, updates, filesystem checks and recovery. | Pi no longer serves root or maintains a charging lease; it is needed only for Linux startup after shutdown. |
| **U1 — fully independent startup** | Separate exact-A7/iOS 12 boot-chain investigation, recovery and boot selection. | Demonstrated start after shutdown without another computer; no working route established yet. |

Legacy milestone mapping: B01–B03 are the demonstrated touch/desktop work;
B04/B04C continue in N1/N5; B05–B06 are N2–N3; B07–B11 are N5; B12–B15
are S1–S4. The older detailed test history is retained in
[the previous plan](https://github.com/thisiscamk/ipad-air-j72-linux/blob/74ba0fc/DFU-PLAN.md).

## Rules for each new DFU

1. Prepare and pin the concrete changed kernel/DT/loader/modules/root overlay first.
2. Explain what changed and what the next boot will answer; do not repeat an unchanged failed attempt.
3. Use one exact-device USB launcher/process group; keep the host kernel unchanged.
4. Run compatible independent diagnostics in the same session and verify cleanup between them.
5. Stop on failed health/restoration; preserve private evidence and the known-good rescue path.
6. Do not disconnect a USB-backed root. Keep charging within the qualified source and existing test guards.
7. Record screen/gesture/charger observations only after the owner performs them.
8. Keep firmware, calibration, raw metadata, credentials and identifying logs private.

No internal installation, partition change or iOS erase is authorized by this plan.
