# J72 internal storage: morning runbook

Prepared 1 November 2026. **Preparation is ready; an on-device installer is not.**
The original overnight preparation made no device changes. On 2 November, the
iPad is running the RAM desktop on its powered hub while a longer charging test
runs and a new storage observer is built. No internal write has been performed.
Preserve iOS by default. The host kernel stays unchanged.

## Ready on the host

- [GPT checker and free-space planner](code/storage/j72_storage_preflight.py):
  validates both table copies, geometry, CRCs, ranges and overlaps; preserves
  every existing partition. It operates on captured regular files only and
  generates no write commands. Sixteen synthetic unit tests pass.
- [ANS1 loader candidates and audit](code/storage/README.md): duplicate-free
  fix plus a positive command allowlist, measured geometry and read bounds.
  The second candidate passes 280 cases using actual extracted source with
  host stubs and UBSan. No complete loader build or hardware qualification.
- A private, separate 3 GiB ext4 host image: canary survives reopening and
  read-only `e2fsck` passes. The original image hash is unchanged. This is a
  filesystem rehearsal, not a bootable internal-root release.
- Pinned Orchard/J81 reference material, historical J72 controller facts,
  synthetic accepted/blocked/corrupt GPT captures and [sanitized results](code/storage/PREPARATION-RESULT.json).
- Existing proven RAM boot, desktop, Wi-Fi and USB recovery path retained as
  the rescue baseline. Private firmware and image contents stay local.

## 2 November observer build

A new [Linux ASP observer](code/storage/linux-asp-observer35/) is fully built
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

## Next iOS checks

Use the owner's existing jailbreak to restore root SSH after restarting.
Confirm the method rather than assuming an unpatched iOS boot enables SSH.
The [read-only iOS helper](code/storage/ios12-readonly-inspect/) is built for
this model/iOS 12 but not yet run. It checks framework/symbol availability and
bounded snapshot listing only. No resize API is called and no snapshot is
created, renamed or deleted. A snapshot workaround or resize would need its
own qualified plan and explicit review before changing storage.

Hoolock's [support-tool notes](https://github.com/HoolockLinux/docs/blob/master/tools/README.md)
describe an iOS 11–13 snapshot obstacle. This is a research lead, not proof of
a safe J72 method. A [separate author's resize helper](https://gist.github.com/iarchiveml/47946a79c0412a38f3e5f1872f040183)
explicitly excludes iOS 12. Current tool names alone do not establish ABI or
behavior on this device. Do not run either resize tool as an experiment.

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
