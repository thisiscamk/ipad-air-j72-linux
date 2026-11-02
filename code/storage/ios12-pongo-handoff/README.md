# Pongo RAM recovery handoff — recovery service reached

**Revision3 passed on J72: authenticated RAM recovery, verified md0 root, zero
APFS mounts, both GPT copies/CRCs and an unmounted APFS minimum-size query.**
The [compact observer](../ios12-pongo-compact/) has now passed on J72 and matched
the loaded kernel UUID to the original iOS12.5.7 image. This candidate uses that
measured ABI/memory map to attempt the prepared restricted recovery image in RAM.
It does not install, resize, remove snapshots, or expose a disk-write command.

## Evidence behind this candidate

The compact observer captured 16 empty map slots, the allocator top, kernel text
range and trust-cache map. A same-session 32-byte trust-cache read revealed a
serialized wrapper: one module at offset 8, version 1, with 1728 records. The stock
component was then retrieved from the exact 16H81 IPSW and checked against Apple's
BuildManifest. Its complete module header matches those live bytes exactly.

A larger RAM dump failed during a later USB transfer. We do not claim the console
problem is solved for every command. The staging client explicitly selects Pongo's
synchronous-stdin/nonblocking-stdout mode, then reads after completion. This
mode passed the actual upload, staging and independent status checks. A timeout
or failed guard stops the procedure; there is no normal-iOS SSH fallback.

## Guarded RAM staging

The authored module has three fixed commands: preflight, stage, and status.
It has **no boot, raw disk, MMIO, kernel patch or installer interface**.

1. Require A7, exact `iPad4,2`, validated DT/RAM views and the original kernel UUID.
2. Hash the **entire existing serialized stock cache in RAM** against the exact
   stock component. This check must pass before the large recovery upload.
3. Require empty reserved slots, no existing RAM disk, a bounded iOS12 command
   line and enough RAM for static allocations plus headroom.
4. Accept only the pinned bundle layout/digest. The module computes SHA-256
   itself, yielding periodically, and validates the serialized cache and HFS
   signature before allocation or DT edits.
5. Allocate/copy/compare the new cache and HFS in Pongo's static RAM region.
   Keep every original stock record, including five identical duplicates, and
   all 181 records from the prepared recovery cache: **1881 records total**.
   Twenty-eight recovery records already occur in stock; 153 are new.
6. Commit only RAM handoff metadata: `RAMDisk`, the `TrustCache` address/length,
   exact `rd=md0 debug=0x2014e -v wdt=-1` arguments and framebuffer ownership.
   The kernel's code bytes are not edited. Existing stock cache bytes remain
   untouched in their original RAM allocation.
7. Check postconditions again. A separate host operation can then request
   `bootux`; it requires the same USB session, unchanged private manifest and a
   completed staging receipt, and rechecks the module's staged state first.

Partial allocations refuse a second staging attempt. The first live test passed
static allocation and comparison of the full bundle; every boot still checks
its current RAM bounds and available slots.
No recovery success is claimed from a USB disconnect or Apple logo.

## Device result

[DEVICE-RESULT.json](DEVICE-RESULT.json) records the passing revision3 test.
The root source label is actually `root_device`, confirming why revision2's
literal `/dev/md0` check failed. Independent stat64 checks prove that `/` is on
the `md0` block device; the root is HFS, its root-filesystem flag is set, and
there are exactly two mounts with **zero APFS mounts**.

The forced inspector opened storage read-only and captured both GPT copies.
The host validated both headers/entry-array CRCs and matching geometry. The disk
still has one APFS partition and no unallocated GPT gap. Raw captures, identifiers
and logs remain private.

`APFSContainerGetMinimalSize` succeeded with no APFS mounted: status0, intact
canaries, **126,357,602,304 bytes**. It exactly matches the earlier normal-iOS
query and leaves only **1,642,352,640 bytes** geometrically releasable. Recovery
boot and mounted-filesystem contention are no longer the measured blocker.
The cause of the high minimum, including the snapshot hypothesis, remains
unproved. There was no resize, snapshot mutation or internal-storage write.

The normal reboot command was authenticated and acknowledged after the test.
USB returned after the initial observation window; normal iOS identity and the
owner's screen confirmation both pass. The paired battery query reports99%.

[Revision2](DEVICE-REV2.json) preserves the authenticated mount-guard refusal;
[revision1](DEVICE-REV1.json) preserves the earlier SSH permission defect.

## Root-device guard and diagnostics

Revision3 accepts only known source labels and requires **all** these checks:

- One HFS root mount with the root-filesystem flag.
- No APFS mounts; bounded, valid mount-table strings and counts.
- `stat64("/")` reports a directory and `stat64("/dev/md0")` a block device.
- Root `st_dev` is nonzero and equals the `md0` node's `st_rdev`.
- Exact board/kernel family and the approved RAM-root boot arguments.

A label alone cannot allow inspection. Structured diagnostics are saved before
raw disk access; `diagnose` remains a fixed metadata-only command. The host
requires the device-identity guard receipt before accepting inspection success.
Twenty-five actual-inspector native-stub/UBSan cases and six transport cleanup/
refusal cases pass offline. Revision3's device result is recorded separately.

The automatic temporary no-preflight usbmuxd path and cleanup/restoration of the
Pi's normal service also passed. Root/.ssh/key permissions remain audited in
the actual HFS image. The Apple kernel, USB service and keys are unchanged.

## Recovery verification

After boot, the host accepts only the recovery image's unique USB marker and
pinned SSH key. It reuses the already-published restricted inspector from the
[iOS12 recovery source set](../ios12-ram-recovery/), without invoking its gaster
or Apple bootloader upload paths. The forced inspector requires HFS `md0` root
and zero APFS mounts, opens the disk read-only, and takes fixed GPT reads.
It does not expose an interactive shell or a mount/resize/snapshot command.
The only additional revision3 command, `diagnose`, reads root/mount metadata.

Both GPT copies/CRCs and any supported minimum-size result must be reviewed
before proposing space creation. The measured **1.64 GB shrink allowance**
still blocks the conventional root layout. A compressed-root capacity rehearsal
is being evaluated separately; neither layout nor any write is authorized here.

## Recipes and limits

These are the actual lab sources; they expect scripts in `tools/`, the original
capsule-v3 and private lab inputs, and the preceding compact/observer/recovery
source sets. They are not a standalone firmware bundle. Private Apple images,
keys, kernel UUID/config headers, compiled modules, receipts and logs stay local.
The native ARM64 host tools and existing Pi kernel are retained.

```sh
# Build once into a fresh private capsule-v3 (requires the original inputs):
python3 tools/prepare-j72-ios-recovery-v3.py build
python3 tools/prepare-j72-pongo-recovery-handoff.py
python3 tools/test-j72-pongo-recovery-handoff.py
python3 tools/run-j72-pongo-recovery-handoff.py
```

Those commands only build/check local files. Tests bind their result to the exact
private manifest. After a fresh direct-Pi DFU, use one loader process at a time:

```sh
sudo -n python3 tools/j72-pongo-boot.py --require-direct-pi --confirm-pongo
# Wait for success and full loader cleanup:
sudo -n python3 tools/run-j72-pongo-recovery-handoff.py --stage
# Only after stage and status pass, use the private receipt directory it prints:
sudo -n python3 tools/run-j72-pongo-recovery-handoff.py --boot-staged PRIVATE_STAGE_DIR
```

The staging client sends the 130,049,536-byte bundle in bounded chunks. Boot and
staging are device tests; their success is not implied by offline checks.
Do not run the old verbose observer or built-in `bootargs`/`xargs` commands.

## Offline results and source references

[RESULT.json](RESULT.json) records19 actual-source SHA-256 vectors checked against
Python, six serialized-cache refusals, validation of the full real bundle,
11 damaged/truncated bundle refusals, three response refusals, and four invalid
boot-receipt refusals **before USB access**. The native module's imports and
actual export pointer pairs are checked against the pinned Pongo binary.
The existing restricted capsule's signatures, service/source pins and image
readback remain prerequisites. Revision3 adds 25 actual-inspector cases and six
transport cases. Revision3 now passes the device checks recorded separately
above; the offline result remains a record of tests without USB access.

- [XNU4903 initial root mount label](https://github.com/apple-oss-distributions/xnu/blob/xnu-4903.221.2/bsd/vfs/vfs_subr.c#L1017)
- [XNU4903 stat64 ABI](https://github.com/apple-oss-distributions/xnu/blob/xnu-4903.221.2/bsd/sys/stat.h)
- [HFS reports its underlying device ID](https://github.com/apple-oss-distributions/hfs/blob/hfs-407.30.1/core/hfs_vnops.c#L1055)
- [Dropbear home/key permission requirements](https://github.com/mkj/dropbear/blob/main/manpages/dropbear.8)
- [Apple's serialized cache/module declarations](https://github.com/apple-oss-distributions/xnu/blob/xnu-4903.221.2/osfmk/kern/trustcache.h)
- [Pongo static allocator](https://github.com/checkra1n/pongoOS/blob/e98323f8a09abd80fc4cbcd74dee023b91a1ec22/src/kernel/mm.c)
- [Pongo XNU/RAM-disk path](https://github.com/checkra1n/pongoOS/blob/e98323f8a09abd80fc4cbcd74dee023b91a1ec22/src/drivers/xnu/xnu.c)
- [Pongo synchronous stdin and console ring semantics](https://github.com/checkra1n/pongoOS/blob/e98323f8a09abd80fc4cbcd74dee023b91a1ec22/src/shell/usbloader.c)

Host/build helpers and SHA-256 code are MIT; the inspector and its guard
headers are GPL-2.0-or-later as marked in each file. SHA-256 uses the operations/constants in FIPS180-4;
no external crypto source, Apple SDK header or firmware bytes are redistributed.
[PROVENANCE.json](PROVENANCE.json) records the authored source hashes.
