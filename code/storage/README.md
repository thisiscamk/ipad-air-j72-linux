# J72 storage preparation (offline only)

**No active J72 storage driver or installer is supplied here.** These tools
prepare metadata review and candidate source changes for later qualification.
See the [morning runbook](../../STORAGE-MORNING-PLAN.md),
[installation gates](../../INTERNAL-STORAGE-PLAN.md) and
[measured host results](PREPARATION-RESULT.json).

## Built Linux observer candidate

The new [J72 Linux ASP observer candidate](linux-asp-observer35/) includes the
actual source, integrated kernel patch, loader recovery patches and host
harnesses: 307 cases pass. Its isolated #35 kernel, five matching modules and
RAM USB recovery image now build successfully. Hardware firmware handoff and
storage reads remain untested. This is a read-only observer, not an installer.

## Captured GPT metadata checker

[j72_storage_preflight.py](j72_storage_preflight.py) uses Python's standard
library. It opens bounded regular host files, refusing device files, symlinks
and FIFOs; it has no device, mount, resize or installation interface. It
requires explicit 512- or 4096-byte logical geometry, validates protective
MBR, both GPT headers/arrays and CRCs, checks usable ranges and non-overlap,
and omits unique GUIDs and names from its report. This is a deliberately
strict subset of [UEFI GPT](https://uefi.org/specs/UEFI/2.10/05_GUID_Partition_Table_Format.html);
unusual metadata requires separate review, not an automatic repair.

The optional planner preserves **every** existing partition, including Linux.
It considers only currently unallocated ranges with unused GPT slots. It
never shrinks APFS or offers replacement. Every result says execution is
unapproved and has an empty list of write operations. Input metadata alone
cannot prove the identity or current state of a connected iPad.

Capture directory format (all files remain private):

- `geometry.json`: `{"logical_block_bytes":4096,"total_blocks":N}`; replace
  `N` with measured Identify geometry, never a guessed or J81 value.
- `mbr.bin`, `primary-header.bin`, `backup-header.bin`: one logical block each.
- `primary-entries.bin`, `backup-entries.bin`: complete entry arrays rounded
  to logical blocks, using the validated header locations/count/stride.

This documents the offline input format; no live capture tool is qualified.
After a separately qualified read-only capture:

```sh
python3 -B code/storage/j72_storage_preflight.py \
  --capture /path/to/private-capture --plan-free-space \
  --boot-mib 1024 --root-mib 8192 --report /path/to/new-private-report.json
```

Sizes are planning inputs, not a selected J72 layout. Exit 0 means valid
metadata (and a fitting geometric proposal if requested); exit 2 means valid
metadata but no fitting free-space plan; exit 1 refuses malformed input or an
existing output file. None permits execution. Partition type/range information
and metadata hashes remain in reports, so keep real captures/reports private.

```sh
python3 -B -m unittest discover -s code/storage \
  -p test_j72_storage_preflight.py -v
```

Sixteen synthetic unit tests cover both logical sizes, corruption, overlap,
identity mismatch, missing space, preserving existing Linux, redaction and
file-type refusal. CLI trials also check valid/free, occupied-APFS, corrupt
backup and refusal to overwrite a report. They use synthetic geometry only.

## Inactive ANS1 loader candidates

Reviewed Orchard commit
[`97dccd13fc4af182a48d4e59198ad72acbfc201c`](https://github.com/OrchardLinux/orchard/tree/97dccd13fc4af182a48d4e59198ad72acbfc201c).
Its [imported ANS1 source](https://github.com/OrchardLinux/orchard/blob/97dccd13fc4af182a48d4e59198ad72acbfc201c/boot/m1n1/patches/hoolock/0032-Add-ANS1-storage.patch)
has the same import SHA as our previous `824bf034` review. The original code
is Nick Chan / Hoolock m1n1, SPDX MIT. Both candidate deltas follow MIT;
Python tools/tests are GPL-2.0-only. Private Apple firmware is not included.

1. [0001 cleanup](0001-ans1-Avoid-freeing-the-command-buffer-twice.patch)
   removes the second `free(cmd)` in normal shutdown.
2. [0002 read guard](0002-ans1-Validate-read-only-commands-and-measured-geometry.patch),
   applied after 0001, admits only Identify and a single bounded user-area
   read at the command submission boundary. It rejects write/unlock/other
   opcodes before mailbox submission; validates Identify geometry; rejects
   LBA narrowing, out-of-range reads and invalid buffer alignment/addressing.

Neither is applied to an active loader. No full loader build or hardware
storage read has run with these candidates. Read the [remaining source audit](ANS1-AUDIT.md)
before considering any device test.

```sh
python3 -B code/storage/verify-j72-ans1-cleanup.py \
  --orchard-tree /path/to/pinned-orchard \
  --candidate code/storage/0001-ans1-Avoid-freeing-the-command-buffer-twice.patch
python3 -B code/storage/verify-j72-ans1-read-guard.py \
  --orchard-tree /path/to/pinned-orchard
```

Each harness verifies the import SHA, extracts actual source, applies the
candidate in a temporary directory and compiles selected functions with host
stubs. The read guard passes 280 cases under UBSan, including all 256 opcode
values and invalid geometry/flags/tags/LBAs/buffers. Directly injecting a
write-unlock header reproduces the baseline executor's lack of an allowlist;
it does **not** demonstrate a reachable write caller in the original loader.
These tests do not execute controller firmware or DMA, prove quiescence, or
qualify the Linux ASP request path. No Orchard PR was changed by this work.
