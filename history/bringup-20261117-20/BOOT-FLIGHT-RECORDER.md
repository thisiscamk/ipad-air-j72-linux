# J72 boot flight recorder

Date: 2026-11-17
Scope: faster diagnosis of iOS/m1n1/Hoolock/Linux warm boots without storage
writes or repeated kernel-wide analysis.

## Goal

Replace the present sequence of bespoke launchers, long blind waits, and later
filesystem-marker inspections with one stable instrumented boot image and one
host observer. A failed attempt should normally answer **which stage was last
entered and why the next stage was not**, without rebuilding the payload.

## Core design

Reserve one 16 KiB, 64 KiB-aligned physical allocation as a flight-recorder
page. Every stage receives its physical address explicitly. It contains:

- a fixed header: magic, schema version, boot nonce, target identity, payload
  hashes and page size;
- an append-only ring of fixed 64-byte events;
- a final snapshot containing the latest stage, error, EL, CPU affinity,
  timestamp/counter, and four stage-specific arguments;
- CRC32C for each event and for the final snapshot;
- no pointers except offsets within the recorder.

Writers use a single CPU and publish `sequence` last after a cache clean. A
stage never parses or rewrites older events. Corrupt or missing records fail
closed and remain distinguishable from a valid stage event.

Suggested event shape:

```text
magic | version | stage | event | sequence | flags | error
counter | current_el | mpidr | arg0 | arg1 | arg2 | arg3 | crc
```

The recorder is diagnostic only. It cannot authorize a boot or weaken an
existing identity, allocation, storage, or restoration gate.

## Stable stage vocabulary

Assign IDs once and do not renumber them:

| Range | Owner | Examples |
|---|---|---|
| `0x01xx` | iOS launcher | allocation, readback, hook commit, sleep returned |
| `0x02xx` | wake bridge | CPU0 entry, CPU1 parked, registers captured |
| `0x03xx` | gather/relocator | descriptor validation, copy, compare, publish |
| `0x04xx` | m1n1 entry | first instruction, ADT accepted, heap ready |
| `0x05xx` | Hoolock | ANS start, storage ready, BLS selected, payload loaded |
| `0x06xx` | kboot | DT prepared, caches cleaned, final branch |
| `0x07xx` | Linux early entry | head.S, MMU on, early initcall milestones |
| `0x08xx` | initramfs | `/init`, storage visible, root mounted, switch-root |
| `0x09xx` | installed system | userspace, USB gadget, boot-complete service |
| `0xExx` | refusal/error | component plus stable reason code |

Each stage records entry before doing work and either success or a specific
error before returning/parking. No generic “failed” event is permitted where a
bounded operation has a concrete failure result.

## Three telemetry layers

### 1. Live USB observer

Run one observer before the terminal call and keep it alive throughout the
attempt. It records monotonic timestamps for topology changes and identities:
DFU, Pongo, first m1n1, second m1n1, Linux gadget, normal iOS, disconnect, and
reconnect. When a proxy exists, it periodically reads only the 16 KiB recorder
and emits newly committed events as JSON Lines.

This replaces separate watcher scripts and prevents a timeout from including
unrelated staging time, as happened in V149.

### 2. On-screen hexadecimal checkpoint

Immediately before any terminal transition, mirror the latest stage and error
to a tiny framebuffer overlay: four colored bars plus the low hexadecimal
digits. It must be a direct bounded write using the already captured framebuffer
geometry, with no font library, allocation, or display reinitialization.

The overlay is valuable after USB disappears and should survive until the next
stage deliberately replaces the framebuffer. Photographing `0620/0000`, for
example, is much more useful than “black screen”. The normal boot path can clear
the overlay once Linux display initialization succeeds.

This sink is optional and must be disabled unless the exact framebuffer range
is validated against the same-boot ADT. It is never a substitute for the binary
record.

### 3. Linux/initramfs export

Pass the recorder as an explicit `/reserved-memory` node in the J72 DTB, marked
`no-map`. The earliest practical Linux hook appends entry/MMU milestones. The
diagnostic initramfs reads the page through a small dedicated driver or reserved
mapping and exports the complete record over the first Linux USB gadget as a
single framed response. It also includes the boot nonce in the USB serial.

Do not use a filesystem marker for the primary result. A filesystem receipt may
remain a later durability check, after storage and root mounting are already
known to work.

## Recovering a record after a terminal stall

Whether DRAM contents survive the exact controlled recovery path is not yet
qualified. Test this separately with a harmless canary before relying on it:

1. A returning diagnostic writes a random nonce and CRC to an owned, documented
   physical page.
2. Perform the same controlled recovery used after a stalled boot.
3. In fresh Pongo, read only that exact page before large uploads or memory
   initialization.
4. Repeat once with a different nonce to exclude stale or fabricated data.

If both pass, add a first-command `flightrec read` path to Pongo/m1n1 and obtain
the last record before loading another payload. If retention fails, the live USB
log and framebuffer code remain the authoritative post-terminal signals. Do not
add raw-storage writes merely to compensate.

## Stop gates: several boundaries, one image

Build the diagnostic payload once with numbered stop gates. A host-selected,
hash-covered configuration chooses `continue`, `return`, or `park/proxy` after
each major stage. The code and payload hashes remain unchanged between trials;
only the small configuration and boot nonce differ.

Examples:

- stop after relocated ADT validation and remain in m1n1 proxy;
- stop after ANS initialization but before storage reads;
- stop after BLS payload loading but before `kboot_boot`;
- stop immediately before the final Linux branch;
- continue through initramfs USB export.

This converts trial-and-error source edits into a binary search over known stage
IDs. A later gate is attempted only after all earlier gates have receipts from
the same immutable build.

## Host-side automatic classifier

One command should produce one directory containing:

- `manifest.json`: exact input hashes, stop gate, boot nonce and device identity;
- `events.jsonl`: USB and recorder events on one monotonic timeline;
- `console.log`: first and second m1n1 output;
- `result.json`: last valid stage, first missing expected stage, error meaning,
  USB outcome, elapsed times and recommended next gate;
- `framebuffer-code.txt`: owner-entered/photo-derived code when needed.

Classification must be table-driven. Examples:

- second m1n1 USB plus `0x04xx`, no `0x05xx`: Hoolock did not start;
- `ANS_READY` but no `STORAGE_READY`: inspect only the bounded ANS/storage call;
- `KBOOT_BRANCH` plus no `LINUX_ENTRY`: Linux entry contract or earliest head.S;
- `LINUX_ENTRY` plus no `INITRAMFS_INIT`: kernel early boot/initramfs handoff;
- `ROOT_MOUNTED` plus no `SWITCH_ROOT`: installed-root userspace boundary.

Timeouts start at the event they supervise, not at process launch. The observer
reaps the entire process group and never starts a second USB boot process.

## Fast implementation sequence

1. Implement the recorder schema and host decoder with fixture tests only.
2. Add recorder writes to the already proven returning wake bridge; prove exact
   readback and cleanup without a terminal boot.
3. Add the unified USB observer and automatic classifier. Replay historical V149
   and V151 timelines as regression fixtures.
4. Add m1n1/Hoolock stop gates and proxy reads. First live discriminator stops in
   the persistent second proxy; it does not enter Linux or access storage.
5. Add the validated framebuffer mirror.
6. Qualify post-recovery DRAM retention with the two-nonce canary.
7. Add the reserved-memory DT node and initramfs USB exporter, then instrument
   the minimum bounded Linux early-entry locations.

The next terminal boot should not run until steps 1-4 pass offline and in the
returning path. Its purpose should be to demonstrate the complete recorder from
wake entry through a selected m1n1 stop gate, not to attempt another blind full
desktop boot.

## Expected improvement

Most failures become one attended attempt followed by automatic classification,
rather than: attempt, wait, recover, DFU again, mount a partition, inspect a
marker, modify a launcher, and repeat. Stop gates also let one reviewed binary
answer multiple questions without accumulating V-numbered code variants.
