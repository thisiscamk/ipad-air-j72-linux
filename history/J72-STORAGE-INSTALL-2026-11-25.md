# J72 storage regression to successful Orchard install

This report records the 24–25 November 2026 path from a fresh Orchard `main`
build that could not complete a native storage write to a successful normal
Orchard installation on an iPad Air 1 Cellular (J72/iPad4,2). Dates are in
Asia/Singapore unless a kernel timestamp is quoted.

This is a dated device investigation, not a claim that the local changes are
ready for upstreaming. Apple firmware, device identifiers, credentials, private
keys and raw device logs are deliberately omitted.

## Safety boundary

- Retain the existing iOS APFS partition and keep iOS bootable.
- Install only into the previously released approximately 50 GB area.
- Use one USB boot/install process at a time.
- Qualify a reversible native write, flush and readback before installation.
- Keep write failure handling bounded. An ASP command cannot be safely aborted,
  so an ambiguous timeout must retain its DMA mapping, latch the controller
  failed and require a reboot.
- Do not repeat a DFU attempt without a concrete build or policy change.

## 1. Fresh `main` build: first write timed out

We pulled and built Orchard `main` from scratch for J72:

```sh
git pull
orchard build --device j72
```

The Orchard revision was
`eab974c350978284b69bd3f0951056d77b0f8143`. The RAM recovery booted and
enumerated the 128 GB ASP device and its three partitions. The first reversible
4 KiB qualification write targeted the final block of the disposable p3 area:

- p3-relative 4 KiB block: `11944959`
- driver LBA: `31249919`
- retained p1 and p2: forced read-only

The request was submitted at kernel time `174.031590` and hit the bounded
timeout at `357.348375`, about 183.3 seconds later. The timeout path retained
DMA and required a reboot. We did not run the installer. The device returned to
iOS for charging.

This result showed that including the driver was not sufficient. The current
J72 initialization and queue policy did not reproduce the earlier working
storage configuration.

## 2. Compare with the previously qualified J72 policy

We compared the current storage driver and device-tree configuration with the
earlier J72 build that had completed native writes. The useful differences were
all J72-specific:

1. Limit ASP to one outstanding tag.
2. Limit requests to 4 KiB and one segment.
3. Apply a finite timeout to J72 writes and flushes.
4. On timeout, latch the controller failed and retain the request/DMA mapping
   until reboot instead of pretending the command was cancelled.
5. Start the J72 ANS CPU before RTKit initialization, matching the qualified
   ordering.
6. Remove `apple,always-on` from the J72 ANS DLL power-domain node. Other boards,
   including J85, retain their existing policy.
7. Add metadata-only submit, mailbox, completion and timeout traces. No payload
   data is logged.

The local, unsubmitted patches were:

- `block: asp: Restore bounded J72 write qualification`
- `block: asp: Use the qualified ANS start order on J72`
- `arm64: dts: apple: j72: Use the qualified ANS DLL policy`

The first candidate used one tag, 4 KiB/one-segment requests and a 180-second
write/flush timeout. It produced release `dev-20261124-125347`, whose pinned
index SHA-256 was:

```text
f959cde02fb8fa8cecac6cd311cd20c5d6e13e0553e639dc0c4dbc3f1b1eb839
```

Offline checks confirmed that the release's `asp.ko` contained the diagnostic
markers, the J72 DTB omitted `apple,always-on` from the ANS DLL node, and the J85
DTB still contained it.

## 3. Reversible 4 KiB qualification passed

We RAM-booted the candidate once and verified live limits of 4 KiB and one
segment. Nothing was mounted. The test then:

1. forced the disk and all partitions read-only;
2. enabled writes only on the parent disk and p3;
3. direct-read and retained the original final p3 block in RAM;
4. direct-wrote one 4 KiB test pattern and requested a flush;
5. direct-read and compared the test pattern;
6. restored the saved original block and flushed again;
7. direct-read and compared the restoration; and
8. returned every block device to read-only.

Results:

| Operation | Result |
| --- | --- |
| Test write | success in about 46.592 seconds |
| First flush | success in under 1 ms |
| Test readback | exact match |
| Restore write | success in about 1.5 ms |
| Restore flush | success in under 1 ms |
| Restored readback | exact match |
| ASP timeout or I/O error | none |

The original/restored SHA-256 was
`ff167584959fd04f105e128fa60745ca49d3eb8cd09cc33594e3d1477d3c017b`.
The test-pattern/readback SHA-256 was
`f600eca824e84a43f0691b267bd620e462c50da165c5b80e17aecb7a924f1fa8`.

This qualified that exact p3 block and the J72 policy. It did not prove that
every address or firmware garbage-collection state would complete within the
same time.

## 4. First normal installer attempt exposed a second bound

We ran Orchard's normal installer with the qualified release and selected only
partition 3 (`ext4`, `omarchy-a`, 45.6 GiB). Partitions 1 and 2 were not offered
as installation targets.

The first backup-GPT-area write was a 4 KiB request at driver LBA `31249995`.
It exposed two mismatched limits:

- Orchard's host-side `dd` wait: 120 seconds
- J72 kernel write timeout: 180 seconds

The kernel trace was:

```text
42.645232   submit write at LBA 31249995
226.275462  J72 timeout; DMA retained, reboot required
228.720196  firmware completion, status 0
230.438329  firmware report: GC took 51 seconds
```

The timeout fired about 183.630 seconds after submission. Firmware reported
successful completion about 2.445 seconds later, or about 186.075 seconds after
submission. Because the driver had already latched failure, the following
queued GPT writes were rejected with I/O errors. We issued no further storage
operation, returned all block devices to read-only, captured evidence and
rebooted to iOS.

This was not evidence that the write was corrupt. It was evidence that a valid
J72 firmware operation, including garbage collection, could exceed both the
host's 120-second wait and the kernel's 180-second bound.

## 5. Evidence-based timeout adjustment

We retained the one-tag, 4 KiB, one-segment and failed-latch protections. Only
the two finite waits changed:

- J72 write/flush timeout: 180 seconds -> 240 seconds
- Orchard host wait for each GPT `dd`: 120 seconds -> 300 seconds

The 240-second kernel limit gives roughly 54 seconds of headroom over the
observed 186.075-second completion. The 300-second host limit is deliberately
longer so a kernel failure is reported first. Neither timeout is unbounded.

We rebuilt with:

```sh
orchard build --device j72
```

The rebuilt release was `dev-20261124-210645`; its pinned index SHA-256 was:

```text
45b093c0da78f73949b52248251badab4943c23c8b009d0adaef368274f52c7b
```

The release audit passed for 84,857 members. We extracted the packaged
`asp.ko` and checked its AArch64 instructions: `apple_asp_queue_rq` constructs
the immediate `0x3a980`, which is 240,000 ms. This verified the packaged module,
not merely the source patch.

## 6. Successful normal installation

With one fresh DFU, we ran the normal Orchard installer against the explicit
rebuilt manifest. It again offered only partition 3. The formerly failing GPT
write completed within the new bound, and Orchard reported `Partitions
created`.

The installer then transferred a 726 MiB root image. Throughput was deliberately
limited by the conservative one-tag/4 KiB policy and averaged roughly 300–400
KiB/s, with occasional longer individual requests. The transfer and final
synchronous flush completed without an ASP timeout.

Orchard reported, in order:

- system files written;
- firmware installed;
- old boot entries removed;
- user set up;
- kernel and drivers installed;
- boot entry written;
- installed; and
- `Omarchy A is ready`.

Post-install read-only verification found:

| Check | Result |
| --- | --- |
| Kernel | `7.3.0-rc1-orchard-apple-4k`, AArch64 |
| systemd state | `running` |
| Failed systemd units | 0 |
| J72 ASP timeouts | 0 |
| Kernel I/O errors | 0 |
| Root | `/dev/asp0n1p3`, ext4, read-write |
| Boot | `/dev/asp0n1p2`, vfat, mounted at `/boot` |
| Retained iOS | `/dev/asp0n1p1`, APFS, unmounted |

The only extended first-boot job was normal pacman keyring initialization. It
completed, after which systemd reached `running` with no failed units.

## What actually fixed the install

The successful path required two separate corrections:

1. Restore the previously qualified J72 ANS initialization, power-domain and
   conservative queue policy. That changed the first tested p3 write from an
   indefinite/timeout result to a reversible qualification pass.
2. Increase, but keep bounded, the J72 kernel and host GPT-write waits based on
   the measured 186.075-second firmware completion. That allowed the normal
   installer to survive a legitimate long garbage-collection event.

The timeout increase is not proof that the underlying latency is ideal or that
240 seconds is universally sufficient. It is a bounded compatibility policy
supported by this device's measured behavior. The one-tag/4 KiB constraints and
DMA-retention failure path remain important safeguards until the ASP driver's
J72 behavior is better understood.

## Publication status

These changes were local device-bring-up changes. This report does not submit,
approve or propose an upstream Orchard PR. Any upstream submission should first
separate the generic installer wait from J72-specific driver/device-tree policy
and include the exact reviewed patch set and device evidence.
