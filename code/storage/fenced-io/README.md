# Portable C fenced I/O — host tested; native adapter unqualified

This is one component of the proposed iOS12 writer. It contains **no disk-open,
APFS resize, formatting, GPT transaction, approval or device-execution interface**.
It cannot select a storage target. A future adapter must prove the owned media,
opened-descriptor identity, geometry and operation state before supplying I/O.
The exact internal installation remains unapproved.

## What is implemented

- A caller-specified, aligned byte fence, exclusive end, signed-offset ceiling
  and bounded maximum transfer. Every operation checks the same identity callback.
- Aligned short-transfer completion and at most three EINTR retries per exact
  transfer. Zero, oversized, negative or unaligned progress latches failure.
- Flush once, followed by exact readback of the whole submitted range. A failed
  flush, including EINTR, stops progression; it is never automatically retried.
- Separate aligned readback memory; overlap with source data is refused.
- Sticky errors and progress counters. After failure, no further I/O proceeds.

Callbacks are an engineering boundary, not identity proof. The future native
adapter must bind them to the same opened descriptor and independent registry/
media/session evidence. Transaction ordering, metadata freshness, approved job/
image hashes, detached-operation lifecycle and no automatic resume still need
implementation above this core. Do not reinitialize a failed transaction or
report unflushed/unverified bytes as installed.

## Actual checks completed

1. **34 C scenarios** run the real header with a bounded memory fixture. They
   cover aligned short I/O, retry exhaustion, read/write errors, invalid partial
   progress, failed flush, identity loss before/during/after writes, corrupt
   readback, overlap, bad geometry and overflow/fence refusals.
2. The same core writes a **new, immediately unlinked host regular file**, calls
   host `fsync`, verifies its range and outside sentinels, then refuses a real
   file-size identity mutation. It accepts no caller path or existing file.
3. A compile-only probe emits an **arm64 iOS12 Mach-O object** with warnings
   treated as errors. It is not a linked/signed executable or a native runtime test.

[Machine-readable result and hashes](RESULT.json). No iPad was contacted.
Host `fsync` and a compiled ABI object do not establish native iOS flush support,
NAND durability, encrypted APFS resizing or recovery after interrupted writes.
The [RAM ownership harness](../../../RAM-APFS-REHEARSAL-PLAN.md) is still unbuilt.

Run locally from this directory:

```sh
cc -std=c11 -O1 -g -Wall -Wextra -Werror \
  -fsanitize=undefined,bounds -fno-sanitize-recover=all \
  test-fenced-io.c -o /tmp/j72-fenced-core-test
/tmp/j72-fenced-core-test
cc -std=c11 -O1 -g -Wall -Wextra -Werror \
  -fsanitize=undefined,bounds -fno-sanitize-recover=all \
  test-host-file.c -o /tmp/j72-fenced-host-test
/tmp/j72-fenced-host-test
clang -target arm64-apple-ios12.0 -O1 -ffreestanding -fno-builtin \
  -fno-stack-protector -Wall -Wextra -Werror \
  -c compile-probe.c -o /tmp/j72-fenced-ios12.o
```
