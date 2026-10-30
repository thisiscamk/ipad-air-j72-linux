# Deferred internal-storage plan for iPad Air J72

This is a research plan for the iPad Air 1 Cellular (`iPad4,2` / `J72AP`, A7, iOS 12.5.7). **No internal-storage write, partition change, or iOS erase has been authorized.** The current Linux and Omarchy A work boots into RAM and uses a read-only root filesystem served by a Raspberry Pi over USB.

## When to start

Offline source audits, recovery design, image building and installer simulations can proceed now. Begin device-side storage qualification only after repeated RAM boots demonstrate native touch, usable Wi-Fi, reliable battery reporting and charging, the other services the owner needs, and clean return to iOS. A host-backed writable root can test persistence first. Any feature deferral needs owner agreement; storage installation must not bypass the usability gate.

The [DFU session plan](DFU-PLAN.md) places storage qualification after the integrated tablet tests and groups the installation work into later boot batches. Those are planning milestones, not a fixed DFU estimate.

## Current blockers

1. **J72 storage is unproved.** A7/A8 devices use Apple's ANS1 storage processor. [Orchard's m1n1 patch](https://github.com/OrchardLinux/hardware/blob/main/boot/m1n1/patches/hoolock/0032-Add-ANS1-storage.patch) contains ANS1 support, and [experimental J81/A8X work](https://github.com/mattonik/ipad-nixos/blob/main/research/j81-ans1-storage-bringup.md) has demonstrated read-only Linux access on a different board. Neither establishes a safe J72 Linux write path.
2. **The current installer does not support this device.** [Omarchy A's installation instructions](https://github.com/OrchardLinux/omarchy-a#install) list J71b/iPad 6 as supported and require iPadOS 16 or later. They describe creating a Linux-data partition while preserving iOS, with a host `orchard launch` still required after a cold restart. The exact J72 layout remains to be designed from measured geometry.
3. **The current APFS resizer does not support iOS 12.** [Resize APFS](https://github.com/OrchardLinux/resize-apfs#requirements) requires iOS/iPadOS 16 or later; its documented hardware resize test is on J71b. We must establish a separate, verified J72/iOS 12 coexistence procedure before considering a dual-boot layout.

## Proposed gates

| Gate | Evidence required before advancing |
| --- | --- |
| 0. Usable RAM Linux | Touch, chosen connectivity and power features, desktop, repeated boot, and recovery pass on this J72. No storage operation is part of this gate. |
| 1. Read-only ANS1 bring-up | Preserve the iBoot-loaded ANS firmware through Pongo/m1n1; identify the J72 ANS1 controller and block size; enumerate namespace metadata and the partition map read-only; read a few bounded, aligned blocks and compare repeated hashes. Audit loader and Linux initialization as well as the block request path: refuse write-unlock, writes, discard, format and writable passthrough. Do not mount with journal replay. Confirm normal iOS boot afterward. |
| 2. Recovery design | Make and verify an encrypted iOS backup on a separate computer, inventory owner data that the backup may omit, record the partition map and firmware/restore path privately, and rehearse a non-destructive recovery boot. Check which restore image Apple will currently accept for this exact model before any write. Do not publish backup contents or identifiers. |
| 3. Layout choice | Decide whether iOS must remain. For coexistence, first prove a supported iOS 12 APFS shrink and partition-table update on this model; the current Resize APFS release is not that proof. If this cannot be established, stop. A full-device replacement would be a separate owner decision and recovery plan. |
| 4. Write-capable ANS1 driver | Audit and harden the J72-specific Linux ANS1 path: firmware handoff, tag bounds before queue access, complete SGL construction, DMA address limits, measured block geometry, submission/completion errors, cache flush, timeouts, power-loss behavior and protection of auxiliary Apple areas. Test destructive cases away from the owner's only iPad first. Host simulations and repeated read-only tests do not qualify hardware writes. |
| 5. Installer rehearsal | Build an exact-J72 installer that shows the intended partition map, refuses Apple/unknown regions, checks available space and image hashes, and has an explicit stop point before writes. Rehearse its decision logic on synthetic disk images and a disposable test target. Require a fresh backup and a separate owner authorization for the reviewed write plan. |
| 6. First install | Create only the approved Linux partitions, write and verify a small boot/system image, keep a USB recovery shell, and boot the internal root through the already validated DFU/Pongo path. Check filesystem integrity, touch, Wi-Fi, charging, updates, and repeated iOS/Linux transitions before copying user data. |
| 7. Maintenance and rollback | Provide update and repair procedures, space monitoring, boot-selection instructions, and a tested rollback to the preserved iOS layout or a documented full restore. Maintain the host RAM boot as a rescue path. |

## What “installed” would mean

The first realistic outcome is **Linux stored on the iPad but launched from a host after each cold restart**. Orchard's current supported-device flow works this way. Internal storage removes the Pi-hosted root filesystem; it does not by itself remove the DFU/Pongo host requirement. A truly untethered power-on boot would need a separate, proven boot-chain design and is not included in this plan.

The current [Omarchy A README](https://github.com/OrchardLinux/omarchy-a#supported-devices) describes automatic login and unrestricted passwordless sudo in its experimental image. Before storing personal data on a J72 install, choose and validate login/access controls and a data-protection design. Encryption support and performance on this J72 remain unqualified; do not infer them from another device's image.

## Concrete preparation before the write decision

1. Keep the original host root image immutable and qualify an isolated writable host copy. Test persistence and package updates there first.
2. Produce an ANS1 command allowlist and failure-path audit. The [J81 submission audit](https://github.com/mattonik/ipad-nixos/blob/main/research/j81-ans1-submission-audit.md) reproduces SGL and tag-check gaps using synthetic requests; it is useful evidence to address, not write-path qualification.
3. Collect geometry and layout only through the qualified read-only path. Save the map and bounded metadata privately. Determine real free space and required image/update headroom; do not reserve an invented fixed partition size.
4. Establish the iOS 12 resize/coexistence mechanism independently of the iOS 16+ app. Preserve iOS by default. If the mechanism is not demonstrated, retain host persistence and stop before partition changes.
5. Build a proposed image with pinned kernel/modules, locally supplied firmware, a rescue shell and a root identifier that does not depend on discovery order. Test first boot, repair and update behavior against disposable disk images.
6. Produce a dry-run report listing the exact target, changed ranges, preserved regions, image hashes, backup checks and rollback limits. Refuse ambiguous identity, unknown maps, insufficient space, missing backups or an unsupported resize path.
7. Review that concrete report with the owner. Only a later explicit authorization can allow the approved writes. Recheck target identity and backups immediately before execution.

No step in this document authorizes changing storage. The detailed partition layout, commands, backup checks, and rollback criteria should be reviewed with the owner only after gates 0–5 have produced evidence on this exact device.
