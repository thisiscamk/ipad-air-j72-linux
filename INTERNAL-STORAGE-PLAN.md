# Latest preparation: first read-only root can use an iOS write backend

The combined #35 desktop/Wi-Fi/native-read boot now passes; owner UI and normal
nested loop/ext4/NBD/export cleanup also pass. This kernel also reports a linear
DM target. The bounded view planner and host-only future GPT rehearsal pass 13
test methods, and the actual current all-APFS capture refuses native mapping.
[Prepared source, exact arithmetic and limits](code/storage/native-root-preparation/).

The first local root may use a separately qualified **iOS native writer** to
install the image, keeping Linux ASP read-only. Linux write/flush qualification
can therefore follow that first read-only milestone. This is a proposed route,
not a tested writer or permission to resize. iOS 12 APFS resize, fenced GPT/image
writes and recovery behavior still need qualification before a reviewable install.
No zero-size resize or snapshot deletion is proposed. The candidate 1536 MiB
ext4/compressed-base format now fits in host rehearsal; it does not yet exist as
a Linux partition on the device.

## Earlier plan, with backend qualification clarified below

# Internal-storage preparation for iPad Air J72

This is a research plan for the iPad Air 1 Cellular (`iPad4,2` / `J72AP`, A7, iOS 12.5.7). **No internal-storage write, partition change, or iOS erase has been authorized.** The current Linux and reduced Omarchy A desktop run from RAM, with internal Wi-Fi and demonstrated unplugged use. Read-only native storage qualification has now passed on the new #35 RAM boot.

## 2 November owner and live-state update

The owner has no backup and states that no personal content needs preserving. A personal-data backup is therefore not a prerequisite they want to pursue. Preserve iOS and recovery metadata by default; this statement does not authorize an unreviewed erase or partition change. The changed #35 RAM boot preserves the firmware reservation and has passed ANS1 Identify and bounded reads. Native charging/source policy, write qualification and iOS 12 space creation remain work in progress.

## Prepared now

See the [morning runbook](STORAGE-MORNING-PLAN.md) for the next actions, the [offline tools and ANS1 audit](code/storage/README.md), and [test receipts](code/storage/PREPARATION-RESULT.json). The metadata checker validates both GPT copies and makes a free-space-only dry run. An inactive loader guard passes 280 host cases; a separate 3 GiB host filesystem copy passes a canary reopening check and read-only e2fsck. None of these is a boot-qualified storage image or an installer.

Fresh read-only #35 results identify a 128,000,000,000-byte disk with 4096-byte logical blocks. Repeated direct 4 KiB reads match. Both GPT copies and their arrays pass CRC and consistency checks: one APFS partition occupies LBAs 6–31,249,994, with **no unallocated gap**. Bounded APFS checkpoint and space-manager metadata checks report 71,745,007,616 free bytes inside the container. This is not a validated shrink minimum. No filesystem was mounted and no internal write or unlock was issued by that observer. See the [measured observer result](code/storage/linux-asp-observer35/RESULT.json).

Subsequent live iOS inspection with the existing Amethyst jailbreak confirms one root snapshot and no data snapshots. Orchard's exact `APFSContainerGetMinimalSize` query reports 126,357,602,304 bytes, leaving only 1,642,352,640 bytes geometrically available for shrink. That is insufficient for the original uncompressed desktop. The later 1536 MiB compressed-container host rehearsal fits the conditional aligned layout; the actual shrink remains unqualified. The original root snapshot supports Amethyst rollback and has not been changed. A snapshot contribution to the high minimum is plausible, not proved. [Measured helpers and result](code/storage/ios12-readonly-inspect/).

Current Orchard uses a boot partition read by m1n1 itself; the latest launch change removes the host fallback reader. Its 1 GiB boot / 8 GiB minimum root policy is a sizing reference, not an approved J72 layout. The original reviewed tree has no Linux ASP implementation to enable for J72. Our subsequently ported and hardened [read-only Linux ASP observer](code/storage/linux-asp-observer35/) now passes initial hardware reads; writable storage remains unqualified.

## When to start

Offline source audits, recovery design, image building and installer simulations can proceed now. Begin device-side storage qualification only after repeated RAM boots demonstrate native touch, usable Wi-Fi, reliable battery reporting and charging, the other services the owner needs, and clean return to iOS. A host-backed writable root can test persistence first. Any feature deferral needs owner agreement; storage installation must not bypass the usability gate.

The [DFU session plan](DFU-PLAN.md) places storage qualification after the integrated tablet tests and groups the installation work into later boot batches. Those are planning milestones, not a fixed DFU estimate.

The owner now accepts a Pi-assisted start followed by unplugged use as the
first independence milestone. See [the independent-operation plan](INDEPENDENCE-PLAN.md)
for RAM-root and internal-root options. Offline preparation is active; the
device-side usability and write-authorization gates below still apply.

## 1 November source review: useful starting points

Reviewed Orchard at
[`97dccd13fc4af182a48d4e59198ad72acbfc201c`](https://github.com/OrchardLinux/orchard/tree/97dccd13fc4af182a48d4e59198ad72acbfc201c).

| Source | What to reuse or investigate | J72 gap |
| --- | --- | --- |
| [m1n1 ANS1 import](https://github.com/OrchardLinux/orchard/blob/97dccd13fc4af182a48d4e59198ad72acbfc201c/boot/m1n1/patches/hoolock/0032-Add-ANS1-storage.patch) | A7/A8/A8X mailbox/AKF startup, preloaded firmware and user-area reads. | Exact J72 firmware handoff, power/DMA, read bounds and cleanup need qualification. |
| [Firmware handoff patch](https://github.com/OrchardLinux/orchard/blob/97dccd13fc4af182a48d4e59198ad72acbfc201c/boot/m1n1/patches/hoolock/0034-kboot-Pass-ANS1-firmware-information-to-Linux.patch) | Loader fills the `asp` firmware reserved-memory information for Linux. | Subsequently integrated in #35; firmware reservation, physical DRAM containment and first Linux ASP reads now pass. |
| [J81 follow-up merged through PR #34](https://github.com/OrchardLinux/orchard/blob/97dccd13fc4af182a48d4e59198ad72acbfc201c/docs/integration/j81-2026-10-29-followup/NATIVE-ROOT.md) | Experimental internal ext4, systemd/desktop, Wi-Fi and persistence after a fresh host-assisted boot. | Different A8X board and kernel. Orchard's standard J81 profile still has `install=false`. |
| [Pinned J81 contributor code](https://github.com/micro23/ipadair2-omarchy/tree/e2203b83f45726c825b39dd17fbab405c2a90e5b/experimental/j81-storage) | Read-only ASP overlay, write-range checks, GPT parser/tests, explicit native-tool selection, root guards and PID 1 handoff. | Do not copy its partition boundaries, 4096-byte assumptions, board identity, approvals or resize target. Its patch is for its pinned prepared source. |
| [Orchard layout planner](https://github.com/OrchardLinux/orchard/blob/97dccd13fc4af182a48d4e59198ad72acbfc201c/src/orchard/install_layout.py) and [boot contract](https://github.com/OrchardLinux/orchard/blob/97dccd13fc4af182a48d4e59198ad72acbfc201c/docs/boot-contract.md) | Pure planning logic, preserving Apple ranges, pinned table hashes, PARTUUID roots and platform/kernel separation. | A future J72 layout must be based on measured geometry and a qualified installer. Existing allocation defaults are not our approved layout. |
| [Latest boot-from-host fix](https://github.com/OrchardLinux/orchard/blob/97dccd13fc4af182a48d4e59198ad72acbfc201c/boot/m1n1/patches/orchard/0006-storage-Release-the-NVMe-boot-from-host-strap-after-.patch) | Account for differences between normal and USB-started iBoot. | This patch addresses PCIe NVMe/J71b, not a J72 ANS1 solution. Do not copy the strap writes. |

**Audit result:** the imported `ans1_shutdown()` frees its command buffer
twice. No later patch in the reviewed series changes that function. The
[one-line candidate and host reproducer](code/storage/README.md) reproduce
the duplicate-free assertion in the extracted original function and pass
with the candidate, including repeat shutdown and UBSan checks. The full
loader has not been rebuilt or hardware tested with it. Review error-path
ownership as well before selecting any ANS1 loader for J72.

The J81 framework-based resizer source is a starting point for a later
**probe-only** iOS 12 API/capacity investigation. Finding an APFS entry point
does not prove that shrinking is supported or safe. The current Resize APFS
application explicitly requires iOS 16 or later; do not run its installation
flow on J72/iOS 12.

### Initial J72 read-only command policy to implement and audit

This policy is now implemented by the #35 read-only Linux observer and has passed first hardware reads. The earlier inactive loader candidate remains a separate host-tested reference.
ANS1 commands are not the newer PCIe NVMe admin command set.

| Path | Initial policy |
| --- | --- |
| Identify `0x00` | Permit only bounded expected metadata with validated completion/tag handling. |
| USERAREA read `0x10` | Permit only measured-geometry, aligned, bounded reads to private RAM buffers. |
| Mailbox/queue/power setup | Permit only the reviewed volatile setup needed for the read path; audit firmware behavior and rollback. |
| USERAREA write `0x11`, WRITE_UNLOCK `0x19` | Deny, including during initialization. A read-only block flag alone is insufficient. |
| Format/clear, auxiliary writes, discard, flush and arbitrary passthrough | Deny. The first observer does not need them. |
| Auxiliary reads and unknown opcodes | Deny initially; any private recovery inventory needs a separate scoped audit. |
| Filesystem access | Raw reads only for initial qualification; no mount that can replay a journal. |

Before any first read: prove allowed operations in both loader and Linux,
check tag bounds before indexing, complete SGL/DMA construction, error and
timeout cleanup, and inherited firmware ownership. Before any later write:
add namespace/extent fences, flush/durability and failure tests separately.
The J81 contributor's WRITE_UNLOCK is global; its range protections are
software guards, not hardware locks on each namespace.

## Current blockers

1. **Writable J72 storage remains unqualified.** A7/ANS1 firmware handoff, Identify, repeated reads, GPT verification and bounded APFS capacity reads now pass on J72. Write fences, flush/durability and native-root operation still need separate qualification.
2. **The current installer does not support this device.** [Omarchy A's installation instructions](https://github.com/OrchardLinux/omarchy-a#install) list J71b/iPad 6 as supported and require iPadOS 16 or later. They describe creating a Linux-data partition while preserving iOS, with a host `orchard launch` still required after a cold restart. The exact J72 layout remains to be designed from measured geometry.
3. **The current APFS resizer does not support iOS 12.** [Resize APFS](https://github.com/OrchardLinux/resize-apfs#requirements) requires iOS/iPadOS 16 or later; its documented hardware resize test is on J71b. We must establish a separate, verified J72/iOS 12 coexistence procedure before considering a dual-boot layout.

## Proposed gates

| Gate | Evidence required before advancing |
| --- | --- |
| 0. Usable RAM Linux | Touch, chosen connectivity and power features, desktop, repeated boot, and recovery pass on this J72. No storage operation is part of this gate. |
| 1. Read-only ANS1 bring-up | Preserve the iBoot-loaded ANS firmware through Pongo/m1n1; identify the J72 ANS1 controller and block size; enumerate namespace metadata and the partition map read-only; read a few bounded, aligned blocks and compare repeated hashes. Audit loader and Linux initialization as well as the block request path: refuse write-unlock, writes, discard, format and writable passthrough. Do not mount with journal replay. Confirm normal iOS boot afterward. |
| 2. Recovery design | The owner has waived preserving personal content and has no backup. Record the partition map and firmware/restore path privately, preserve iOS by default, and rehearse a non-destructive recovery boot. A metadata capture on the same host disk is not an independent backup. Check which restore image Apple will currently accept for this exact model before any write. Do not publish backup contents or identifiers. |
| 3. Layout choice | Decide whether iOS must remain. For coexistence, first prove a supported iOS 12 APFS shrink and partition-table update on this model; the current Resize APFS release is not that proof. If this cannot be established, stop. A full-device replacement would be a separate owner decision and recovery plan. |
| 4. Write backend qualification | For the first read-only root, qualify an iOS 12 native resize/GPT/image writer with exact extent fences and recovery verification. If using Linux writes, audit and harden the J72-specific Linux ANS1 path: firmware handoff, tag bounds before queue access, complete SGL construction, DMA address limits, measured block geometry, submission/completion errors, cache flush, timeouts, power-loss behavior and protection of auxiliary Apple areas. Test destructive cases away from the owner's only iPad first. Host simulations and repeated read-only tests do not qualify hardware writes. |
| 5. Installer rehearsal | Build an exact-J72 installer that shows the intended partition map, refuses Apple/unknown regions, checks available space and image hashes, and has an explicit stop point before writes. Rehearse its decision logic on synthetic disk images and a disposable test target. Record the owner's backup waiver and require separate owner authorization for the exact reviewed write plan. |
| 6. First install | Create only the approved Linux partitions, write and verify a small boot/system image, keep a USB recovery shell, and boot the internal root through the already validated DFU/Pongo path. Check filesystem integrity, touch, Wi-Fi, charging, updates, and repeated iOS/Linux transitions before copying user data. |
| 7. Maintenance and rollback | Provide update and repair procedures, space monitoring, boot-selection instructions, and a tested rollback to the preserved iOS layout or a documented full restore. Maintain the host RAM boot as a rescue path. |

## What “installed” would mean

The first realistic outcome is **Linux stored on the iPad but launched from a host after each cold restart**. Orchard's current supported-device flow works this way. The RAM desktop already avoids a Pi-hosted root during unplugged use; internal storage would localize the base and reduce RAM pressure; persistent changes still need separately qualified writes. It does not by itself remove the DFU/Pongo host requirement. A truly untethered power-on boot would need a separate, proven boot-chain design and is not included in this plan.

The current [Omarchy A README](https://github.com/OrchardLinux/omarchy-a#supported-devices) describes automatic login, an installation password for sudo, a six-digit screen-lock PIN, and no disk encryption. Our experimental RAM image has not been migrated to that installed-system setup. Before storing personal data, validate the chosen login, lock and data-protection configuration on J72; encryption support and performance remain unqualified.

## Concrete preparation before the write decision

1. Keep the original host root image immutable and qualify an isolated writable host copy. Test persistence and package updates there first.
2. Produce an ANS1 command allowlist and failure-path audit. The [J81 submission audit](https://github.com/mattonik/ipad-nixos/blob/main/research/j81-ans1-submission-audit.md) reproduces SGL and tag-check gaps using synthetic requests; it is useful evidence to address, not write-path qualification.
3. Collect geometry and layout only through the qualified read-only path. Save the map and bounded metadata privately. Determine real free space and required image/update headroom; do not reserve an invented fixed partition size.
4. Establish the iOS 12 resize/coexistence mechanism independently of the iOS 16+ app. Preserve iOS by default. If the mechanism is not demonstrated, retain host persistence and stop before partition changes.
5. Build a proposed image with pinned kernel/modules, locally supplied firmware, a rescue shell and a root identifier that does not depend on discovery order. Test first boot, repair and update behavior against disposable disk images.
6. Produce a dry-run report listing the exact target, changed ranges, preserved regions, image hashes, backup checks and rollback limits. Refuse ambiguous identity, unknown maps, insufficient space, missing backups or an unsupported resize path.
7. Review that concrete report with the owner. Only a later explicit authorization can allow the approved writes. Recheck target identity and backups immediately before execution.

No step in this document authorizes changing storage. The detailed partition layout, commands, backup checks, and rollback criteria should be reviewed with the owner only after gates 0–5 have produced evidence on this exact device.
