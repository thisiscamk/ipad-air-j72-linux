> **Historical report / superseded plan.** Start with the [current status](../../J72-PROGRESS.md) and [replication guide](../../QUICKSTART.md). Statements below describe their original session, not current support.

# Plan from the current RAM desktop to an installed J72 tablet

Updated 3 November 2026. This is the current project plan; dated session reports
hold the measurements. Today's [input/storage/power session](SESSION-2026-11-03.md)
completed: input and restoration pass, but net charge fails. iOS charging
is confirmed after PIN entry by the owner and two diagnostic readings.

## Milestones

| Milestone | What the owner can do | Remaining dependency |
| --- | --- | --- |
| RAM desktop — demonstrated | Use touch, Home/menu, Foot, keyboard, Wi-Fi and battery display; run unplugged after startup. | Long input reliability and power qualification. RAM changes disappear on reboot. |
| Internal read-only base — next storage milestone | Start using the Pi, then use the locally stored desktop without a Pi-served filesystem. | iOS12 resize/writer engineering, exact first-trial approval and verified installation. Runtime changes still live in RAM. |
| Persistent local system | Keep files/settings and update the installed system. | Bounded native Linux writes, flush/error handling, writable state and update/recovery qualification. |
| Independent daily operation | Use and charge the iPad without a Pi maintaining a source lease. | J72 autonomous source detection, withdrawal/protection and endurance. |
| PC-free startup | Start Linux after shutdown without another machine. | A separate, demonstrated A7/iOS12 on-device handoff and startup route. |

The owner accepts Pi-assisted startup as an interim milestone. Internal storage
does not establish persistence, autonomous charging or PC-free startup by itself.

## 1. Measured input/power result and next comparison

- [x] One direct-Pi DFU; unchanged #35 cold payload.
- [x] Touch self-check and owner menu/typing/keyboard check.
- [x] Wi-Fi/HTTPS/SSH; native read-only inventory/six matching reads; both idle captures.
- [x] Complete 90 minutes at brightness 802, `schedutil`, Wi-Fi, touch and ASP active.
- [x] Analyse fresh vectors including every hold: **−181.13 mAh; net-charge failure**.
- [x] Input: 221,923 frames, eight recoveries, no SPI/layout/timeout errors; normal stop.
- [x] Five voltage pauses/four restarts; final restart blocked above 36.5°C.
- [x] Independent final baseline restoration, normal cleanup and iOS reboot request.
- [x] Confirm iOS charging at 81% after PIN entry; USB/identity and two diagnostics pass.
- [x] Prepare isolated voltage-hold restart candidate and host/build tests.
- [ ] Measure the candidate on the same workload, retaining qualified input.
- [ ] Natural actual-thermal-trip cooldown/restart, repeatability and longer endurance.

The [candidate](../../code/charging/voltage-resume35/) deliberately relaxes only
voltage/SOC-hold restart eligibility to 36.6–38°C. Initial starts and actual
thermal recovery retain 36.5°C; hard active limits, source lease, current,
restoration and fault guards remain intact. **Host-tested, device untested**.
There is no net-charge improvement claim. Neither this proposal nor safe
restoration qualifies autonomous or unattended charging.

### Later precharge abort and revised next batch

The owner UI and fresh storage checks passed again, but three touch layout
rejections stopped the idle/precharge gate. The charging candidate only loaded
disabled: no current override or net-charge observation occurred. Normal cleanup
and iOS charging after unlock pass. [Follow-up diagnosis](TOUCH-FOLLOWUP-2026-11-03.md).

The later bounded-resync boot passed the owner input check, then stopped before
charging on one rejected layout. This time the report was captured: checksum-valid
native structure with contact state 1, outside our whitelist. None of 495 extra
retries recovered a frame. Cleanup and iOS charging pass.

The state-1 worker then passed owner input checks and processed seven state-1
frames, but seven captured state-2 reports stopped progression before charging.
Normal cleanup and iOS charging pass. The [next inactive-state-1/2 candidate](../../code/touch/inactive1235/)
passes actual eight-report/emitter tests, build and V4 preflight; device execution
remains untested. Input gates remain strict. A fresh DFU is required because the
current kernel disables module unloading. Continue guarded charging in that boot
only if input passes. This does not isolate a power-policy effect.

## 2. Finish the storage qualification tools offline

The next storage DFU should carry prepared tools and a precise experiment, not
be used to discover which helper to build. Existing recovery capsule v3 remains
the proven inspect/diagnose/reboot rescue image.

### Q1 — Separate disposable-RAM experiment

Build a new, separately pinned recovery variant with:

1. The existing exact J72/build, HFS/md0 root and zero internal APFS-mount checks.
2. A read-only pre-existing-media inventory, registry identities/ancestry and
   measured memory budget. Determine the real allocation units and geometry;
   do not assume a `ram://` argument or APFS block size describes media geometry.
3. A no-mount attach of one bounded RAM object. Prove it was created by this
   invocation and is RAM-backed; reject internal/root/pre-existing media,
   ambiguous identities and symlink/device substitution before formatting.
4. Only after that proof, bounded APFS format, minimum query, explicit nonzero
   shrink and independent resulting-size/checkpoint checks. An optional grow
   must remain within the owned RAM backing. Never use the size-zero shortcut.
5. Owned-object detach and independent reread of original internal metadata.

Host tests must reject malformed inventories, multiple new media, missing backing
proof, stale invocation identity, swapped device nodes, insufficient memory,
wrong geometry, size overflow and every attempt to select an internal/root path.
The helper must expose no generic caller-supplied format target.

This harness is **not built or device ready yet**. A successful RAM experiment
would establish API/mechanism evidence, not encrypted internal APFS shrink or
flash durability. [Detailed scratch design](RAM-APFS-REHEARSAL-PLAN.md).

### Q2 — Native writer and interrupted-operation handling

Finish an iOS12-native implementation of the already rehearsed transaction:

- Bind the opened descriptor to the exact device identity, 4096-byte geometry,
  original metadata, fresh filesystem state and approved image/job hashes.
- Keep internal APFS unmounted for raw GPT/image operations. A separate normal
  iOS route is proposed for the explicit APFS resize with SEP state initialized.
- Complete aligned short writes and bounded `EINTR` handling; reject zero or
  unaligned partial progress, overflow, changed metadata and out-of-range chunks.
- Write the backup GPT array/header before the primary array/header, with native
  flush and exact readback at each boundary. Any failed flush ends progression.
- Stream only inside the approved Linux extent, then flush and hash the entire
  image readback. Never mount a partially verified image.
- Use a detached operation identity and an explicit release gate. Record intent
  on the host before release. Online resize can freeze iOS filesystem I/O; lost
  SSH or an unresponsive UI is not permission to kill, reboot or repeat it.
- Keep inspection/classification separate from repair. An unknown, torn or
  foreign state stops progression; no automatic resume or generic GPT repair.

The [portable C fenced-I/O core](../../code/storage/fenced-io/) now passes 34 actual
C scenarios, a new unlinked host-file write/fsync/readback/fence check, and an
arm64 iOS12 compile-only probe. Native descriptor/media identity, the native
flush adapter, full transaction owner and detached resize operation are still
unimplemented/unqualified. This is component preparation, not a ready writer.

Exercise remaining actual C paths with fake native I/O, then owned RAM/disposable fixtures.
Reuse the 44 existing host tests and full 1.5 GiB host write/readback result.
Do not count those tests as a native media flush or first encrypted-resize pass.
The current query-only helper must remain query-only; do not add a resize or
write switch to its already measured interface.

## 3. Prepare the exact first internal-trial proposal

Refresh normal-iOS model/build, both GPT copies, APFS size/minimum, snapshots,
recovery limitations and image hash. The owner's backup waiver is recorded.
Before the installation decision, confirm that the required usability/power
features pass or the owner explicitly accepts the named remaining limitations.
Acceptance of Pi-assisted startup does not silently waive autonomous charging
or other requested features.

The present **conditional** proposal retains iOS and its rollback snapshot:

- APFS target: **126,389,035,008 bytes**.
- New Linux extent: **1536 MiB**, 4096-byte LBAs **30,856,704–31,249,919**.
- First base: the verified 572 MB compressed image in the 1.5 GiB container;
  root changes remain in RAM initially.

The last measured APFS minimum leaves only about 31.4 MB below that target.
Recompute it immediately before the proposal and execution. If it no longer
fits, revise the layout/image or retain the host-backed route; do not silently
delete a snapshot or replace iOS to recover space.

The review must show exact changed/preserved ranges, approved artifacts, helper
revision, interruption classifications and realistic recovery limits. Engineering
and host/RAM tests inform the first internal trial; they cannot prove that first
encrypted internal resize in advance. **The exact internal trial still requires
separate owner approval. No internal install/resize/write is currently authorized.**

## 4. Execute an approved installation in distinct phases

Only after the proposal is ready and separately approved:

1. In normal jailbroken iOS, issue the one explicit resize using the reviewed
   detached procedure. Establish actual resulting state before another action.
2. Boot the qualified RAM recovery with internal APFS unmounted. Confirm shrink
   and original identities before the approved GPT/image transaction.
3. Verify both complete proposed GPT copies, the full image hash and unchanged
   outside ranges. Preserve original and new metadata privately.
4. Return to iOS and verify its normal boot/coexistence before testing local Linux.

Do not retry a partial operation merely because its transport disconnected.
[Exact transaction and recovery states](INSTALL-TRANSACTION-PLAN.md).

## 5. First internal-base boot and acceptance

Prepare a new pinned Linux payload with a guarded local-base selector and rescue
fallback. Discover storage by verified identity/geometry and the approved GPT,
not by assuming a discovery-order device name. Bind a read-only view to exactly
the Linux extent; ext4 must not replay its journal. Read the compressed base
through that bounded view and keep the first runtime upper layer in RAM.

Required evidence:

- Full expected base hash and boot/root provenance from the internal drive.
- No host NBD/export or USB filesystem dependency.
- Owner check of touch, Home/menu, keyboard, Wi-Fi and readable display.
- Same-boot native reads, memory/temperature and normal mount cleanup.
- Controlled unplugged use over Wi-Fi and normal iOS return.
- A later repeat cold launch using the same pinned artifacts.

The USB or RAM rescue path must remain available if the installed base fails.
This milestone is an internally stored **read-only base**, not writable persistence.

## 6. Persistent state and system updates

Prototype writable upper/state behaviour against a disposable host-backed image
first. Measure space and RAM needs for settings, home data, logs, packages and an
update/rollback copy. The 1536 MiB extent is tight; do not assume it fits the full
Omarchy A application set or a second system image.

Native persistence then requires a separately audited Linux ASP write path:
request/tag/SGL bounds, alignment, DMA/error/timeout ownership, range fences,
flush ordering and recovery. A native iOS image writer does not provide Linux
writes. Test faults on disposable media/fixtures before an approved iPad trial.

After qualification, test persistence across normal reboot, updates with adequate
free space, failed update rollback, read-only rescue and filesystem recovery.
Decide the desired installed-system login, lock and data protection before
storing personal data; these are not established by the RAM desktop demo.

## 7. Autonomous charging and USB transitions

Current charging depends on the Pi's short source lease. First implement a
read-only J72 source/withdrawal observer using known-safe, audited paths.
The stock evidence identifies CBTL1610 revision 137 and D2089; event, mux and ADC
handling still need J72-specific qualification.

Then add one native source owner with conservative grants, unchanged pack guards,
independent limit readback and immediate withdrawal on lost/uncertain identity.
Coordinate charger detection and USB data roles; never sample an active mux
blindly. Test the known hub and wall source separately, both cable orientations,
source replacement, data reconnect, host loss, controller faults and restoration.
Only then broaden duration/source support and retire the Pi lease.

[Fresh Orchard source review](UPSTREAM-REVIEW-2026-11-03.md) includes new USB-role
work useful for this design. It does not fix pre-Linux hub DFU handoff, and its
different-board PMIC register values are not J72 settings.

## 8. Tablet features and daily-use qualification

| Feature | Current evidence / next action |
| --- | --- |
| Touch, Home, keyboard | Usable and owner checked; finish revised-worker endurance and clean stops. |
| Display and brightness | Working; qualify idle dim/wake and orientation separately from fixed-load tests. |
| Wi-Fi | Association, HTTPS, SSH, reconnect/renewal and unplugged use pass; repeat boot/long traffic and power transitions. |
| Battery/power | Readings and widget work; current net-charge run pending, autonomous charging and suspend remain open. |
| Internal base and persistence | Read-only storage reads pass; installation and durable writes remain open. |
| Audio / Bluetooth | Not qualified; map exact resources/firmware and test independently. |
| Rotation / suspend / wake | Not qualified; preserve recovery access while adding these. |
| GPU acceleration | Desktop currently uses software rendering; A7 support needs separate evidence. |
| Cameras / cellular / other sensors | Not qualified. Agree priority/deferral with the owner before calling the tablet complete. |

Each service must survive the integrated desktop workload and normal stop/restart.
Do not let a feature experiment silently consume another owner's DFU window.

## 9. PC-free startup research

Keep the proven Pi-assisted path while researching the exact A7/iOS12 handoff.
First assess a local iOS launcher with locally available inputs, jailbreak state,
CPU/memory/firmware ownership and a working route back to iOS. Root SSH or a
successful RAM recovery does not prove a Linux handoff from running iOS.

An on-device launcher requiring reapplication of Amethyst is one possible
intermediate research route. Its availability/signing and cold/low-battery
behaviour remain to be demonstrated. Direct power-on into Linux needs an
additional persistent early-boot route. No working route is established here.
Older kloader arm64 support is documented for iOS7–8, not this iOS12 device;
see the [source project's stated support](https://github.com/axi0mX/ios-kexec-utils).
No downgrade, boot-variable change or persistent boot-chain modification is
included in this preparation.

## 10. Upstream integration and reproducibility

The [concrete integration plan](UPSTREAM-INTEGRATION-PLAN.md) maps current producer
contracts, ownership, focused PRs and clean-checkout acceptance. A small optional
keyboard patch passes 113 Omarchy host tests; real Wayland qualification is open.

Keep measured original sources and sanitized tests/results in this repository.
Orchard PR #43 merged documentation; its experiment code is preserved in a
history tag outside the active build tree. Draft #53 carries the private-firmware
converter and measured Wi-Fi configuration. Native J72 profile,
resource ownership, DT and production driver integration remain further work.

Pin an Orchard revision and port each component with an independent reproduction
step. Review its current producer/build contract before exporting changes;
nightly or branch names must not silently replace the measured inputs. Keep the
host kernel unchanged and Apple firmware/calibration private.

## DFU budget and what can be done without the owner

The remaining ledger is in [DFU-PLAN.md](DFU-PLAN.md). Three future boot stages
are the best-case route to the first internal read-only desktop: recovery
qualification, approved recovery installation, then Linux local-base boot.
Allow **4–6 DFUs while qualifying those stages**, not a guaranteed count or cap.
Repeat endurance, persistence, autonomous power and PC-free startup add work
whose boot counts are not yet established.

While the owner is away: analyse the running test, prepare/review host code,
build isolated recovery candidates, test failure handling and update plans.
Do not start another DFU attempt, interrupt the fixed workload, install to
internal storage or change the running charging policy.
