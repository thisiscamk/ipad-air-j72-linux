# Pongo RAM recovery handoff — recovery service reached

**Revision1 passed RAM staging and booted the restricted recovery SSH service.
Client authentication was blocked; revision2 is built and checked offline.**
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

## First device result and revision2

[DEVICE-RESULT.json](DEVICE-RESULT.json) separates the observed revision1 result
from the new offline candidate. All live kernel/cache guards, the 130 MB upload,
RAM copies and independent handoff checks passed. The custom USB marker, SSH
banner and pinned host key were observed. The forced inspector did **not** run,
so neither its RAM-root/no-APFS guards nor recovery GPT/minimum-size reads have
passed on device yet. No disk was opened by the inspector.

The uploaded HFS catalog showed root's home as 0775. The bundled Dropbear checks
home permissions before accepting a public key and rejects group-writable
directories. Revision2 sets root's home and the host-key directory to 0700,
retains .ssh 0700/key 0600, and audits actual HFS ownership and modes after build.
The same kernel, service and key identities are retained. This fixes a confirmed
permission defect; successful authentication remains a device gate.

The normal host usbmuxd preflight expected lockdownd, which this minimal recovery
does not run. A temporary no-preflight daemon reached SSH successfully. Revision2
automates that transport only after the exact recovery marker/direct-Pi checks,
reaps its proxy/daemon groups and restores the host service. Five simulated
success/failure/refusal cases verify cleanup without USB access.

## Recovery verification

After boot, the host accepts only the recovery image's unique USB marker and
pinned SSH key. It reuses the already-published restricted inspector from the
[iOS12 recovery source set](../ios12-ram-recovery/), without invoking its gaster
or Apple bootloader upload paths. The forced inspector requires HFS `md0` root
and zero APFS mounts, opens the disk read-only, and takes fixed GPT reads.
It does not expose an interactive shell or a mount/resize/snapshot command.

Both GPT copies/CRCs and any supported minimum-size result must be reviewed
before proposing space creation. The currently measured **1.64GB shrink allowance**
still blocks the intended layout. No internal change is authorized by this test.

## Recipes and limits

These are the actual lab sources; they expect scripts in `tools/`, the original
capsule-v2 and private lab inputs, and the preceding compact/observer/recovery
source sets. They are not a standalone firmware bundle. Private Apple images,
keys, kernel UUID/config headers, compiled modules, receipts and logs stay local.
The native ARM64 host tools and existing Pi kernel are retained.

```sh
# Build once into a fresh private capsule-v2 (requires the original inputs):
python3 tools/prepare-j72-ios-recovery-v2.py build
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
readback remain prerequisites. Revision2 adds actual HFS permission auditing
and five host-transport cleanup/refusal cases. Revision2 has not run on device;
revision1 reached the recovery SSH service as recorded separately above.

- [Dropbear home/key permission requirements](https://github.com/mkj/dropbear/blob/main/manpages/dropbear.8)
- [Apple's serialized cache/module declarations](https://github.com/apple-oss-distributions/xnu/blob/xnu-4903.221.2/osfmk/kern/trustcache.h)
- [Pongo static allocator](https://github.com/checkra1n/pongoOS/blob/e98323f8a09abd80fc4cbcd74dee023b91a1ec22/src/kernel/mm.c)
- [Pongo XNU/RAM-disk path](https://github.com/checkra1n/pongoOS/blob/e98323f8a09abd80fc4cbcd74dee023b91a1ec22/src/drivers/xnu/xnu.c)
- [Pongo synchronous stdin and console ring semantics](https://github.com/checkra1n/pongoOS/blob/e98323f8a09abd80fc4cbcd74dee023b91a1ec22/src/shell/usbloader.c)

Authored code is MIT. SHA-256 uses the operations/constants in FIPS180-4;
no external crypto source, Apple SDK header or firmware bytes are redistributed.
[PROVENANCE.json](PROVENANCE.json) records the authored source hashes.
