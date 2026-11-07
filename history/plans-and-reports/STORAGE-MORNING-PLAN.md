> **Historical report / superseded plan.** Start with the [current status](../../J72-PROGRESS.md) and [replication guide](../../QUICKSTART.md). Statements below describe their original session, not current support.

# 2 November: RAM recovery passes; compressed desktop starts on device

RAM recovery now passes SSH authentication, HFS/md0 device identity, zero APFS
mounts and both GPT copies/CRCs. The actual mount source is `root_device`. The
unmounted APFS minimum query succeeds and matches iOS: 126,357,602,304 bytes,
leaving 1,642,352,640 bytes geometrically releasable. No resize, snapshot change
or internal write occurred. Normal iOS return is confirmed; battery reports 99%.

A private compressed copy of the desktop is 572,002,304 bytes. Five selected
file readbacks pass. Matching #34/#35 SquashFS modules build; 106 strong imports
resolve to vmlinux, with the original kernels/configs/exports unchanged.
The compressed desktop now reports ready on the proven #34 RAM boot. The
matched SquashFS module loaded; the read-only NBD block size and SquashFS mount
checks pass. A post-start sample has 535,568 KiB memory available and no swap.
The owner confirmed the initial GUI/menu/Foot/keyboard checks. Normal cleanup
and firmware-health checks pass. Wi-Fi was then initialized in the same boot:
association, HTTPS 200 and Wi-Fi SSH pass. The compressed desktop resumes with
474,240 KiB available and bar status connected; the owner confirms Wi-Fi/menu/
keyboard work. A second normal cleanup passed, and the proven RAM desktop
was restored for power testing. No host export remains. The maintenance worker
is loaded disabled while the hub move is pending. No internal disk access.

A 1536 MiB partition is a candidate within the reported minimum, subject to a
reviewed resize/write procedure. The compressed base may avoid snapshot removal
for an interim local-root milestone. Native storage/root qualification, durable
writes and unattended charging remain open.
[Recovery result](../../code/storage/ios12-pongo-handoff/),
[compressed test/source](../../code/storage/compressed-desktop/),
[space review](SPACE-CREATION-REVIEW.md).

## Earlier checkpoints

# 2 November: recovery SSH authentication passes; mount identity check is next

Revision2 passed RAM staging, recovery boot, pinned SSH identity and client-key
authentication. The forced inspector now executes. It stopped at its RAM-root/
mount safety check with exit 5, before opening the disk; no GPT/minimum-size
result or storage change occurred. The owner has returned to iOS.

Matching XNU source uses an initial `root_device` mount label, while the old
inspector requires `/dev/md0`. The actual label remains unobserved. Revision3
adds detailed guard output and checks root/device numbers, HFS/root flags and
zero APFS mounts before permitting read-only inspection. It retains the fixed
SSH commands and adds a metadata-only `diagnose` command. 25 actual-inspector
cases and six transport cleanup/refusal cases pass offline; device test pending.
[Updated code and measured result](../../code/storage/ios12-pongo-handoff/).

## Earlier checkpoints

# 2 November: RAM recovery boots; SSH permission fix ready for its next test

The guarded Pongo stager passed on J72: exact original kernel and full stock
trust-cache hashes,130MB upload, verified RAM copies and independent handoff
checks. The RAM recovery's unique USB marker, SSH banner and pinned host key
were reached. No broad kernel patch was used.

Public-key authentication stopped at a confirmed image-permission defect:
root's home was 0775, which the bundled Dropbear rejects. The forced inspector
has not executed, so recovery GPT reads and the unmounted minimum-size query
remain pending. The owner returned to iOS; no storage change occurred.

Revision2 sets/audits the home and key directory permissions in the actual HFS
image. It also automates the temporary no-preflight usbmuxd transport that
reached SSH in the first test, with proxy cleanup and host-service restoration.
Offline checks, including five transport cleanup/refusal cases, pass. The next
DFU tests authentication and read-only storage inspection; it is not an install.
[Code, separate device evidence and next candidate](../../code/storage/ios12-pongo-handoff/).

## Earlier checkpoints

# 2 November: compact Pongo inventory passes; actual RAM handoff candidate built

The compact probe passed: original kernel UUID matched, all16 reserved slots
were empty, and allocator/text/trust-cache ranges were validated. A same-session
32-byte read identified the serialized cache wrapper. The exact stock component
matches Apple's manifest and the entire live module header. A larger read then
failed USB; iOS has returned and normal direct-Pi identity is verified.

The next candidate stages the restricted recovery image and merged trust cache
in RAM. It preserves all1728 stock records, including five identical duplicates,
and incorporates the181 recovery-cache records:1881 total. It requires the
entire original RAM cache hash to match before upload, validates the full bundle,
checks RAM copies and handoff metadata, and separates staging from boot.
All offline checks pass; hardware staging and recovery boot remain untested.
[Code and checks](../../code/storage/ios12-pongo-handoff/). No disk writes occurred.

# 2 November: compact Pongo observer prepared after partial second capture

The second proven Pongo boot and revised module load passed. The observer read
allocator/argument metadata and passed the previously blocking 4-byte property,
but USB failed during verbose output. Kernel UUID verification and recovery
boot remain incomplete. The iPad returned to iOS; exact normal USB/direct Pi
identity is verified. No disk or snapshot writes occurred.

The next candidate emits a fixed compact summary and waits for command completion
before reading the full console ring. Smaller reads were rejected as a design:
Pongo discards leading output, rather than preserving it for later short reads.
Eleven real C callback cases, eight frame refusals and idle-before-read transport
checks pass offline. Runtime remains untested; this is a changed test, not a
claimed fix. [Actual code/results](../../code/storage/ios12-pongo-compact/).

# 2 November: Pongo inventory captured; corrected probe needs a fresh session

The proven loader and first probe registration passed. Model, RAM and DeviceTree
guards passed; the observer stopped at legitimate non-map metadata. A built-in
DT read captured 16 unused reserved slots and an existing trust-cache mapping.
The kernel UUID is not yet verified and the recovery image has not booted.

Repeated module loads failed before execution. A later built-in boot-argument
read lost console access; an incompatible pointer conversion is suspected from
source. The next test uses one corrected observer load in fresh Pongo and avoids
those built-ins. Six real-source property cases and twelve malformed-frame
refusals now pass, alongside the existing span/Mach-O/transport checks.
[Actual source and separate device/offline results](../../code/storage/ios12-pongo-probe/).
No disk or snapshot writes occurred. Normal iOS return is pending owner confirmation.

# Current recovery gate: inspect the proven Pongo handoff

The gaster route did not restore a pwned USB endpoint after its A7 reconnect
prompt. It uploaded no bootloader or recovery image. The owner has returned the
iPad to iOS. A different, read-only test is now built using the checkra1n/Pongo
path already proven on this J72: identify the loaded XNU kernel, boot arguments
and reserved memory-map slots. [Actual observer source/results](../../code/storage/ios12-pongo-probe/).

The next DFU establishes that inventory; it is not an installation or a claim
that the recovery image boots. A healthy Pongo session can be reused while the
next RAM handoff is prepared. Space creation, driver write/flush qualification
and the reviewed write proposal remain later gates. No snapshot change or
internal install is authorized by this preparation.

# Recovery candidate built; device qualification is next

A separate iOS 12.5.7 RAM recovery capsule is now built and pinned. The original
Apple kernel is unchanged. The restricted service/inspector, native ARM64
launcher and image readback checks pass offline; both authored tools rebuild
byte-for-byte. Normal iOS refusal tests pass. Recovery boot remains untested.

The next DFU qualifies read-only USB recovery, both GPT copies and an optional
minimum-size query without mounted APFS. It will not create space or install.
The original snapshot remains intact; its effect on the high shrink minimum
is still unproved. After recovery qualification we can prepare a concrete
space-creation proposal, including recovery limits, for separate review.
[Actual source and checks](../../code/storage/ios12-ram-recovery/).

# J72 internal storage: morning runbook

Prepared 1 November 2026. **Preparation is ready; an on-device installer is not.**
The original overnight preparation made no device changes. On 2 November, the
read-only #35 storage boot and live iOS API checks have passed. The iPad is
back in iOS on the powered hub. No raw storage write, resize, snapshot mutation
or partition change has been performed.
Preserve iOS by default. The host kernel stays unchanged.

## Ready on the host

- [GPT checker and free-space planner](../../code/storage/j72_storage_preflight.py):
  validates both table copies, geometry, CRCs, ranges and overlaps; preserves
  every existing partition. It operates on captured regular files only and
  generates no write commands. Sixteen synthetic unit tests pass.
- [ANS1 loader candidates and audit](../../code/storage/README.md): duplicate-free
  fix plus a positive command allowlist, measured geometry and read bounds.
  The second candidate passes 280 cases using actual extracted source with
  host stubs and UBSan. No complete loader build or hardware qualification.
- A private, separate 3 GiB ext4 host image: canary survives reopening and
  read-only `e2fsck` passes. The original image hash is unchanged. This is a
  filesystem rehearsal, not a bootable internal-root release.
- Pinned Orchard/J81 reference material, historical J72 controller facts,
  synthetic accepted/blocked/corrupt GPT captures and [sanitized results](../../code/storage/PREPARATION-RESULT.json).
- Existing proven RAM boot, desktop, Wi-Fi and USB recovery path retained as
  the rescue baseline. Private firmware and image contents stay local.

## 2 November observer build

A new [Linux ASP observer](../../code/storage/linux-asp-observer35/) is fully built
in isolation: #35 kernel, matching storage/recovery modules, new loader and
RAM USB shells. All strong imports resolve; 307 actual-source host cases and
payload/archive checks pass. The storage module is not loaded automatically.
The loader leaves ANS initialization to Linux and keeps recovery available
when firmware metadata is missing. The first J72 hardware boot, firmware reservation check, Identify, repeated
direct reads, both GPT copies and bounded APFS checkpoint/space-manager reads
now pass. Raw captures remain private. The disk has one APFS partition with
no unallocated gap. Free blocks inside APFS do not validate a shrink minimum.

## Sequence from here

These are test batches, not a promise of one DFU each. Complete offline gates
before requesting buttons. Compatible checks share a running boot.

| Batch | Work | Gate before continuing |
| --- | --- | --- |
| 0 — iOS inventory and recovery | Confirm exact model/current layout, available space and backup status. If a new privileged iOS observation is needed, explain its temporary jailbreak/boot separately. Existing cached inventory needs no DFU to analyze. | Current private records, recorded personal-data backup waiver and a known normal-iOS return path. No resizing. |
| 1 — finish read-only storage implementation | Audit init failure ownership, timeout/late completions and DMA quiescence; integrate exact J72 firmware/ADT handoff and build in isolation. Retain both recovery shells and the known RAM desktop. | Full build and injected-failure tests pass. Current loader candidates alone do not meet this gate. |
| 2 — first storage DFU, only when batch 1 passes | Boot the changed read-only observer directly from the Pi. Identify namespace geometry; perform a few bounded aligned reads, repeat hashes, then capture both GPT headers/entry arrays and protective MBR privately. | Only Identify and bounded user-area reads reach command submission; no unlock, writes, auxiliary access, discard, flush or filesystem mount. Stop on the first error. Return to iOS on a fault or charging need; reuse a healthy boot for compatible checks. |
| 3 — map and coexistence decision | Run the offline checker on the captured metadata. Measure image/update headroom. Investigate an iOS 12 supported capacity/shrink route without invoking resize. | A real unallocated gap or independently demonstrated iOS 12 coexistence method. If neither exists, installation stays blocked. |
| 4 — persistent-root and driver qualification | Integrate the ANS1 Linux driver with this kernel/DT, initramfs and PARTUUID root. Qualify tag/SGL/DMA bounds, completion, timeout, flush and recovery. Add persistent desktop/network services and credentials handling. Exercise updates, reboot and recovery with disposable images/test media first. | Boot-tested native root, known failure behavior, protected Apple ranges and passing persistence/update checks. No owner-device write test is implied. |
| 5 — concrete write proposal | Produce exact target identity, unchanged/changed ranges, both GPT backups/hashes, image hashes, backup checks, rollback limits and failure recovery. Review with the owner. | Separate explicit authorization for that exact proposal. This preparation request authorizes no installation or erase. |
| 6 — later install and qualification | Write only the approved Linux areas, verify readback and filesystem integrity, boot internal root, check desktop/touch/Wi-Fi/power, then repeat cold starts and iOS recovery. | Persistent files, updates, normal recovery and agreed independent-use features pass. Keep the RAM rescue boot. |

## iOS checks passed; next recovery work

The owner reapplied the existing Amethyst jailbreak and root SSH returned.
The [device-tested read-only helpers](../../code/storage/ios12-readonly-inspect/)
confirm one root snapshot and no data snapshots. The exact
`APFSContainerGetMinimalSize` spelling used in Orchard returns success and
126,357,602,304 bytes, leaving only 1,642,352,640 bytes against the measured
container. This is too little for the 1 GiB boot + 8 GiB root reference.
No resize, snapshot mutation or GPT change was run.

Before the next storage DFU or write proposal:

1. Review a recovery route that preserves normal iOS boot and the existing
   Amethyst restore snapshot. The personal-data backup waiver does not make
   that snapshot disposable; it supplies a different rollback function.
2. Investigate Hoolock's [iOS 11–13 snapshot caveat](https://github.com/HoolockLinux/docs/blob/23ebe1fbc375599221553a7e1815e5de182a6b42/tools/README.md).
   Its deletion/recreation approach is a lead, not a qualified J72 procedure.
   The live minimum is now measured; snapshot causation remains unproved.
3. Establish an exact J72/iOS 12 rescue environment, SEP/key access and a
   reviewed snapshot-preservation/rollback strategy before any snapshot change.
   Build and inspect that environment before requesting another DFU.
   Source review has identified concrete preparation work: the pinned
   [SSHRD script](https://github.com/verygenericname/SSHRD_Script/blob/d99ec4a19172b87d80fd9dea25eabf39291425a0/sshrd.sh)
   downloads an x86_64 gaster binary on Linux and adds
   `nand-enable-reformat=1 -restore` for A7. Do not execute that preset as our
   read-only recovery test. [Legacy iOS Kit](https://github.com/LukeZGD/Legacy-iOS-Kit/blob/23622f8fe72c09952089d5145a7b008cfcc90d9b/restore.sh)
   provides ARM64 host tools and an A7/iOS 12 producer to audit. No recovery
   script has been executed and no such payload is ready for DFU yet.
4. Resolve the capacity limit, then generate an exact layout from fresh
   measurements. Do not select a size below the reported minimum or treat
   APFS free blocks as a partition gap.
5. Continue the fenced Linux write, flush/durability and native-root work on
   disposable images. No existing read-only observer can install Linux.

A [separate author's resize helper](https://gist.github.com/iarchiveml/47946a79c0412a38f3e5f1872f040183)
explicitly excludes iOS 12. A present API symbol and successful size query do
not prove that a destructive operation from another OS version will work.

## Before any storage write

1. The owner states there is no backup and the personal contents are not needed.
   This waives the personal-data backup task; do not keep requesting it. It does
   not authorize an unspecified erase or partition change. Preserve iOS by
   default and present the concrete installation proposal before any write.
2. Check the currently accepted restore image for this exact model and a
   practical recovery route. Acceptance has not been verified tonight. A
   backup of user data is not a raw partition rollback or jailbreak backup.
3. Save fresh layout metadata privately and a second offline copy. Do not
   treat a GPT backup as a substitute for APFS data recovery.
4. Preserve iOS. The cached 128 GB inventory reports almost the whole disk
   allocated to APFS. Its free capacity cannot be treated as a Linux gap.
5. Finish autonomous charging/source protection before an installed daily-use
   milestone. Guarded hub charging and battery reporting work, but unattended
   Linux charging remains unqualified. Storage will not fix that dependency.

## Boundaries and likely blockers

- Orchard's [current resizer](https://github.com/OrchardLinux/resize-apfs#requirements)
  requires iOS 16 or later; this iPad runs iOS 12.5.7. Do not run its install or
  resize flow here. J81/A8X success is a reference, not J72/A7 qualification.
- The source snapshot contains an ANS1 loader import, not a drop-in Linux ASP
  driver for our current build. More integration work is required before DFU.
- The first installation goal is a persistent internal root with Pi-assisted
  startup, followed by unplugged use. Internal storage alone does not provide
  PC-free startup after shutdown.
- No Linux partition size has been chosen. Planner defaults (1 GiB boot,
  8 GiB root) follow current Orchard policy only; full application space,
  update headroom and the measured map determine the eventual proposal.

**Next action:** leave iOS intact, review fresh layout/recovery status and
the implementation gates above. A new DFU is requested only once there is a
changed, fully built read-only observer with its recovery checks ready.
