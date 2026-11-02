# J72 Linux ASP observer candidate

**Experimental, read-only. The first J72 hardware qualification passed; no installer is included.**
This is a candidate for our Linux 7.0.12 J72 development base. It is not a
drop-in Orchard 7.3 port and must not be used as a generic Apple storage driver.

## Source and reuse

The integration starts from the A7/ASP/mailbox/RTKit portions of
[micro23's J81 observation patch at e2203b8](https://github.com/micro23/ipadair2-omarchy/blob/e2203b83f45726c825b39dd17fbab405c2a90e5b/experimental/j81-storage/patches/Orchard-J81-ANS1-ReadOnly-v1.patch).
The original ASP implementation is by Nick Chan. J72 addresses and interrupts
are checked against cached inventory from this A7 device; J81 partition offsets
and A8X device nodes are not copied. Existing source license headers apply.
The new bounds header and host tests use GPL-2.0-only.

[kernel-integration.patch](kernel-integration.patch) contains the selected
integration plus J72 hardening relative to our existing 7.0 development source.
The complete candidate [asp.c](src/drivers/block/asp.c) and shared
[bounds header](src/drivers/block/j72-asp-bounds.h) are included for review.
This folder excludes firmware, compiled images/modules and device logs.

## First observer restrictions

- Exact `apple,j72` machine check and explicit module opt-in; the module is
  packaged outside module indexes and is never loaded automatically.
- Submission allows only Identify and bounded user-area reads. Write unlock,
  writes, auxiliary namespaces, flush and discard cannot reach the mailbox.
- Only the user namespace is exposed, read-only. Automatic partition scanning
  is disabled. The first queue limits each read to one 4096-byte block.
- Linux's 512-byte sector units are converted explicitly to 4096-byte ASP LBAs.
  Tags, capacity, alignment, DMA addressing and every SGL segment are checked
  before command-buffer access/submission. Invalid SGLs do not write any PFNs.
- The firmware address/size must match a `no-map` region recognized by Linux's
  reserved-memory subsystem before remap/start writes are allowed.
- A timeout, crash or ambiguous delivery latches failure and retains DMA
  resources until a platform reset. This deliberately has no live recovery,
  unload or rebind path. It is unsuitable for an installed writable root.

The accompanying loader patches disable loader storage initialization. Missing
or invalid firmware metadata disables the ANS device while preserving the RAM
USB recovery boot. An actual live firmware handoff still needs qualification.

## Offline verification

These harnesses extract functions from the supplied candidate, compile them
with host stubs and run under UBSan:

```sh
python3 -B code/storage/linux-asp-observer35/test-asp-guards.py
python3 -B code/storage/linux-asp-observer35/test-asp-firmware.py
```

289 submission/SGL/queue/geometry cases and 18 firmware/shutdown cases pass.
They do not demonstrate firmware boot, hardware DMA correctness, reliable reads
or persistence. The full target build and hardware status are recorded in
[RESULT.json](RESULT.json).

## First J72 hardware result — 2 November

The changed image cold-booted and both NCM and ACM recovery shells responded.
The live firmware reservation matched the loader's physical DRAM extent and
Linux's `no-map` reservation. Linux's usable `/memory` span deliberately
excludes the firmware; it must not be mistaken for the complete DRAM extent.
The host canonicalizes a copy of the valid FDT before child traversal because
`fdtget -l` can stop at its NOP tokens. The original capture remains private.

Manual driver load negotiated RTKit 10.2, endpoint 6, and Identify exposed a
128 GB namespace read-only. Repeated direct 4096-byte reads of the protective
MBR and both GPT headers matched. Both complete GPT copies passed CRC and
consistency checks. Bounded APFS metadata reads found a checksum-valid latest
checkpoint and space manager.

The disk has one APFS partition and no unallocated gap. Free blocks inside
APFS do not establish a valid shrink minimum. Internal storage installation,
write/flush/recovery qualification, iOS 12 coexistence and native-root boot
remain open. No internal writes, unlock, format, auxiliary access, discard or
filesystem mount occurred. Raw metadata, device identities and logs stay local.

See the [storage runbook](../../../STORAGE-MORNING-PLAN.md) for remaining gates.

[host-inventory-reference.py](host-inventory-reference.py) is the actual workspace
helper, intended at `tools/run-j72-storage-observer.py` alongside the workspace
USB shell helpers and private manifests. It is not standalone. Its inventory
mode reads firmware metadata and the separately reserved 16 KiB loader RAM log;
it never reads firmware bytes or loads the ASP module.
