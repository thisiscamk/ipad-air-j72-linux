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
- [x] Build and pin the isolated #35 recovery-only storage image; 307 host cases and matching module imports pass.
- [ ] Next DFU: check live firmware reservation, then explicitly qualify Identify and bounded read-only storage access.
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
