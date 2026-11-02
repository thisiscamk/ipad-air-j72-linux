# Current checkpoint: owner UI and mounted cleanup pass

The owner confirms all desktop functions. The away observer was cancelled and
reaped, brightness restored to1604, and normal nested loop/ext4/NBD/owned-export
cleanup passed. The known RAM desktop now stages/starts on #35 with Wi-Fi and
NBD detached. The #35 maintenance module loads disabled with no input-limit
change. The next physical gate is the same marked powered-hub port and fresh
source-path qualification; no new DFU is needed for that continuation.

## Preparation details

# Native-root preparation after the combined #35 boot

**Preparation only: no internal resize, GPT write, Linux partition, mapping or
installation has been executed.** [Sanitized results](RESULT.json).

## Bounded read-only root view

The current #35 kernel already includes device-mapper and its linear target.
A private ARM64 dmsetup closure passes a native host help smoke test. It was
staged in target RAM and `dmsetup targets` confirmed `linear` on the live iPad.
This queries supported targets; it creates no mapping and opens no internal
block device. The temporary `/dev` and `/proc` binds were removed afterward.
The first query refused because `/proc/devices` was unavailable in the isolated
chroot; binding existing proc for the query resolved that userspace requirement.

This gives a candidate alternative to the recovery BusyBox loop tool, which
has no size-limit option. A future native view must have **both offset and
length bounded**, must be read-only over an already read-only backing device,
and must re-read its actual table, size, read-only flag and backing identity.
No future view has yet been created or mounted on native storage.

[j72_native_view_plan.py](../j72_native_view_plan.py) first validates both captured
GPT copies/CRCs using the existing parser, then accepts only the conditional
J72 geometry with separate APFS and Linux partitions. **It refuses the actual
current single-APFS layout**, as verified against the private captured metadata.
It cannot reinterpret an APFS tail as a Linux partition.

Device-mapper tables use **512-byte sectors even though J72 logical blocks are
4096 bytes**. The conditional 1536 MiB view would have 3,145,728 table sectors
at offset 246,853,632 sectors. The planner does not invoke dmsetup or any ioctl.
Thirteen test methods across mapping and layout rehearsal pass, covering unit
conversion, endpoint errors, overlap, wrong type/geometry, extra partitions,
corrupt original CRCs, null/duplicate IDs and applying a proposal twice.

## Actual captured-layout rehearsal — host files only

[j72_rehearse_layout.py](../j72_rehearse_layout.py) validates the original private
metadata and creates new **host files** representing a possible future map.
It preserves the protective MBR and existing disk/Apple identity, name, flags
and start; it changes the proposed APFS endpoint, adds one Linux entry and
recomputes both arrays/header CRCs. The resulting metadata passes the GPT audit
and bounded view planner. The actual 1536 MiB image was hashed read-only.
Generated identifiers, raw original/proposed metadata and image hashes remain
in the private receipt directory; they are not an independent backup.

- Current APFS: 127,999,954,944 bytes.
- Observed minimum: 126,357,602,304 bytes, to be refreshed before any operation.
- Conditional APFS target: 126,389,035,008 bytes.
- Margin above that observed minimum: 31,432,704 bytes.
- Conditional Linux: logical LBAs 30,856,704..31,249,919, exactly 1536 MiB.

There is no write interface in either planner. `approval_ready=false`: the
actual iOS 12 resize, transaction/recovery handling and extent-fenced writer
remain unqualified. The future buffers are **not** a generic repair image and
must never be restored blindly after a partial resize.

## First install route to qualify

The first read-only local root could be written using **iOS's native storage
stack**, then read by the already read-only Linux ASP driver. That separates
first-root bring-up from later Linux write/flush/persistence qualification;
it does not qualify the iOS writer. A new reviewed helper must bind exact disk,
GPT state, image and extent, reject ambiguous/changed state, flush and verify
readback. APFS internal relocation remains the framework's operation and needs
its own failure/recovery audit.

[Hoolock's helper](https://github.com/HoolockLinux/docs/blob/master/tools/resize.c)
is an API reference, not a ready J72 installer. Its
[documentation](https://github.com/HoolockLinux/docs/blob/master/tools/README.md)
describes online filesystem freezing, separate GPT handling and SEP/gigalocker
requirements, and warns about zero-size requests on older iOS. Our proposed
byte target is explicit and nonzero. Snapshot removal is not part of this plan;
the measured minimum does not establish snapshot causation.
[Orchard's current app](https://github.com/OrchardLinux/resize-apfs#requirements)
still targets iOS 16+, so it is not a J72/iOS 12 implementation to run directly.

## Next same-boot actions once the owner returns

1. Cancel `watch-j72-away-battery.py --cancel`; wait for its observer to exit.
   Restore brightness from the temporary 401 to 1604, then request the pending
   portrait/menu/Wi-Fi/Foot hide-tap-type screen check. **Keep USB attached.**
2. Normal `run-j72-compressed-desktop.py --container35 --stop`: actual nested
   loop/ext4/NBD unmount and owned export cleanup now pass.
3. If continuing power qualification, restore the known RAM workload with
   `run-j72-ram-desktop35.py stage --storage35`, then `start --storage35`. This
   adapter retains the original guards and uses the pinned static HTTP
   helper; stage/start now pass on #35. It is not the USB container workload.
4. The [#35 charging adapter](../../charging/maintain35/) requires a new source
   receipt after the hub move. The #35 module loads disabled with unchanged limits; it is not armed.
5. Return to iOS and qualify the resize/write/recovery route before any exact
   installation authorization. A successful capacity proposal is not that gate.

The away observer keeps the current UI/export available, dimmed, while checking
battery. At <=30%, >=40 C or its two-hour deadline it requests normal desktop,
touch and radio cleanup and an iOS reboot. It preserves the export on an
uncertain health read or failed cleanup. It performs no charger override.
