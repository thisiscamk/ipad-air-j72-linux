# J72 session plan: power, Wi-Fi and independent operation

Updated 1 November 2026. **The continuous-input hub run and cleanup are
complete: approximately 34 minutes of input, and 27.2 minutes of charging
before the unchanged voltage guard stopped it. Restoration is independently
verified. HSIC register/domain observation passed in the same boot.** The
owner accepts a Pi-assisted start followed by unplugged use as the first
independence milestone. Fully independent startup remains a later goal.

## Completed on this J72

- [x] RAM Linux and read-only Pi-served desktop; software rendering.
- [x] Native one/two-finger reports, Linux multitouch and owner-confirmed mapping.
- [x] Menus, Foot dragging, keyboard hide/tap/type and Home menu toggle.
- [x] Automatic touch self-check, cleanup/restart and desktop startup after a fresh boot.
- [x] Linux battery reporting, corrected capacity pairing, visible brightness control and top-bar battery/charging indicator.
- [x] Read-only EHCI capability observation and power-domain restoration; no WLAN enumeration yet.
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
- [ ] Correct controller-driver binding after an unresponsive enumeration probe;
  capture the screen error, then qualify USB descriptors, ROM identity and cleanup.
- [x] Compose matched #34 kernel/touch/wireless/vendor payload with a real
  controller driver and phase capture; 83 synthetic API cases pass, unbooted.
- [ ] Boot-qualify #34; enumerate USB and confirm ROM identity with verified
  cleanup; adapt firmware transport, then scan/associate.

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
