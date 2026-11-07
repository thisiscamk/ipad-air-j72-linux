> **Historical report / superseded plan.** Start with the [current status](J72-PROGRESS.md) and [replication guide](QUICKSTART.md). Statements below describe their original session, not current support.

# J72 installation transaction and recovery preparation

**Preparation, 2 November 2026. No internal installation or resize is authorized
or performed.** Preserve iOS by default. The owner's decision not to back up
personal content is recorded; it does not authorize an unspecified disk change.

## What is now demonstrated

- The combined #35 RAM desktop, touch, keyboard and Wi-Fi work together. Native
  storage is read-only and repeated bounded reads match. Normal mounted desktop
  and export cleanup passes. The later power hour lost net charge during thermal
  hold; continuous touch hit its lifetime recovery limit. Those issues remain open.
- The conditional layout and bounded-view planners pass against captured metadata.
  A new disposable host disk rehearses 4096-byte read-only backing, an exact
  offset/length read-only DM map, ext4 `ro,noload`, compressed-base hash readback,
  and normal unmount/map removal/loop detach. This is not an internal-root boot.
- A read-only APFS descriptor capture contains 140 valid NX candidates. The
  selected checkpoint mapping and all five ephemeral objects pass headers and
  checksums, reporting the original 127,999,954,944-byte container. Full filesystem
  semantic validation is not claimed. Raw captures and identifiers remain private.
- 35 host test methods cover the layout, mapping, interruption and checkpoint
  checks. The actual captured-layout model examines 22 memory-only interruption
  outcomes. It has no device writer or automatic repair interface.

Sources and sanitized results: [native-root preparation](code/storage/native-root-preparation/).

The fresh normal-iOS query helper also passes with no writes: 4096-byte physical
blocks, 1MiB read/write transfer limits, media-writable capability and unchanged
126357602304-byte APFS minimum. No flush was issued. This is capability evidence,
not writer, resize or durability qualification.
[Device query result](code/storage/native-root-preparation/IOS-QUERY-RESULT.json).

## New host I/O rehearsal and qualification boundary

A new disposable host disk now rehearses the actual ordered GPT writes and
1.5 GiB image stream, with host fsync, exact metadata/full-image readback and
outside-fence sentinels. Nine I/O failure tests bring the storage model/I/O total
to 44 methods. This exercises host regular-file mechanics; APFS size is simulated,
and no native iOS writer, actual resize or flash durability is qualified.
[Result](code/storage/native-root-preparation/HOST-WRITE-RESULT.json).

The first internal operation will remain an explicit reviewed trial. Host and
potential RAM scratch tests cannot prove the first encrypted internal shrink in
advance. Complete the engineering/recovery review, disclose that uncertainty,
and obtain the exact write authorization before that trial. No trial is ready
or requested by the new host preparation.

See [the batched session plan](NEXT-SESSION-PLAN.md) and
[proposed RAM APFS rehearsal](RAM-APFS-REHEARSAL-PLAN.md).

## Conditional layout for review

All disk LBAs below are **4096-byte logical blocks**. DM table sectors are
separately measured in **512-byte units**.

| Region | Conditional disposition |
| --- | --- |
| Protective MBR, original identities, Apple partition name/flags/start | Preserve exactly. |
| APFS partition beginning at LBA 6 | Resize to an explicit **126,389,035,008 bytes**, then change only its GPT endpoint. |
| Linux slot 2, LBAs 30,856,704..31,249,919 | New **1536 MiB** extent for the verified ext4 container/compressed base. |
| Both GPT arrays and headers | Update their exact reviewed bytes and CRCs, with independent readback. |
| Space outside those regions, snapshots and auxiliary namespaces | No proposed changes. |

The observed minimum is 126,357,602,304 bytes, only 31,432,704 bytes below the
conditional APFS target. **Refresh the minimum immediately before any proposal
is approved/executed**; refuse if the current minimum no longer fits. No zero-size
resize, snapshot deletion or full-device replacement is proposed.

## Native iOS writer still to qualify

The first local root can use the native iOS storage stack for installation while
the Linux ASP driver remains read-only. That avoids requiring Linux writes before
the first read-only root; it does not qualify an iOS writer by itself.

The existing owner-local probe already established that `APFSContainerResize`
and the minimal-size query exist on this iOS 12 device. Further private inspection
of the exact restore framework confirms a real resize wrapper, not an absent
symbol or obvious unsupported stub. It forwards a size request to the container
user client and returns its result. Successful mutation, encryption prerequisites,
failure recovery and hardware durability remain unproved.

[Hoolock's helper](https://github.com/HoolockLinux/docs/blob/master/tools/resize.c)
is a useful API reference. Its [documentation](https://github.com/HoolockLinux/docs/blob/master/tools/README.md)
requires explicit handling of old-iOS zero-size behavior, online filesystem freezing
and SEP/gigalocker state. Another [helper author's iOS 12 caveat](https://gist.github.com/iarchiveml/47946a79c0412a38f3e5f1872f040183)
is conflicting portability evidence; symbol availability does not settle that caveat.
The [current Orchard app](https://github.com/OrchardLinux/resize-apfs#requirements)
is not an iOS 12 installer to run unchanged.

The implementation must bind the exact board, firmware/boot, disk geometry,
both original GPT copies, fresh filesystem size/minimum and image hash. The
qualified RAM-recovery identity guard and absence of APFS mounts should remain
mandatory for raw GPT/image operations. APFS resize prerequisites need their own
qualification; do not mount internal filesystems simply to bypass that question.

## Ordered transaction and stop points

1. **Preflight and exact approval:** fresh identity/layout/minimum, private metadata
   copies and image hash; qualified helper and recovery limitations; concrete owner
   approval of the exact resize, GPT and Linux-extent writes.
2. **Explicit APFS resize:** record request/result. A nonzero return or lost connection
   does not prove nothing changed. Re-read actual checkpoint/container state and both
   GPT copies before deciding anything further.
3. **GPT commit:** after confirmed filesystem shrink, proposed order is backup array,
   backup header, primary array, primary header, with real media flush/readback at
   each durability boundary. This is not an atomic transaction and is not yet a
   qualified device writer. Neither old nor proposed GPT is a generic repair image.
4. **Image:** only after both exact future GPT copies validate, stream aligned bounded
   chunks inside the Linux extent. Refuse wrong units, overlap, zero length, excessive
   chunk sizes, changed disk/metadata or image hashes. Flush and verify the entire
   image readback before any native mount.
5. **First local-root test:** Pi-assisted launch, exact read-only bounded map over the
   read-only ASP device, ext4 without journal replay and the compressed base. Runtime
   remains in RAM initially. Confirm the base really comes from internal storage and
   no host export is needed; test touch, keyboard, Wi-Fi, charging and iOS return.
6. **Later persistence/startup:** separately qualify writable state, updates, power-loss
   recovery and PID 1/root handoff. Fully PC-free power-on remains a distinct boot-chain
   goal. A read-only container mounted by a RAM system is not all of those milestones.

## Interruption classification

| Fresh observation | Required response |
| --- | --- |
| Original filesystem size and both exact original GPTs | Original layout; still no write permission. |
| Confirmed shrunk filesystem, both original GPTs | Shrink completed; GPT not committed. Do not blindly undo the shrink. |
| Confirmed shrink, proposed backup, original primary | Interrupted commit. Preserve evidence; explicit recovery review. |
| Proposed primary but original backup | Unexpected order; stop. |
| Torn copy, foreign valid identity, changed MBR or uncertain filesystem size | Stop; no automatic repair or image write. |
| Confirmed shrink, both exact proposed GPTs, full verified image | Candidate for a separately guarded read-only root test. |

The [state model](code/storage/j72_install_state.py) never turns classification
into write authorization. The [checkpoint checker](code/storage/j72_apfs_checkpoint_plan.py)
rejects unsupported layouts and bounded-read overflows. Its selected checkpoint
checks cover mapping/object headers and checksums, not a general APFS repair engine.

## Recovery limits to settle before approval

The proven RAM recovery and normal iOS return are retained. Metadata copies on
the same host are not an independent data backup. A full restore can erase the
device and change its installed version.

A catalog lookup on 2 November reports iPad4,2 iOS 12.5.8/16H88 as signed and
12.5.7/16H81 as unsigned. This is catalog evidence, **not a device-specific Apple
TSS acceptance test**, so returning to exactly 12.5.7 must not be promised.
[Apple documents iOS 12.5.8](https://support.apple.com/en-us/118387), including its
activation-certificate extension; no update or restore is requested here.
Fresh device-specific restore acceptance, the chosen native writer and partial-
resize recovery procedure remain gates before the installation proposal is ready.
