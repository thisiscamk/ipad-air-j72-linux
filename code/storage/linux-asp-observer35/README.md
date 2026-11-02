# J72 Linux ASP observer candidate

**Experimental, read-only, not hardware qualified. No installer is included.**
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

The first hardware sequence is USB recovery, live firmware reservation review,
explicit Identify, a few repeated aligned reads, then private GPT capture.
Stop on the first controller fault. No filesystem mount or internal write is
part of that sequence. See the [storage runbook](../../../STORAGE-MORNING-PLAN.md).
