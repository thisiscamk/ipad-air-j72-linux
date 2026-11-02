# Current: normal-iOS read-only capability queries pass

The owner reapplied Amethyst after the power test. Exact-device root SSH and
the signed query-only helper pass, without DFU. iOS reports writable media,
4096-byte physical blocks and maximum read/write transfers of1,048,576 bytes.
The APFS minimum is unchanged at 126357602304 bytes, with intact canaries.
Feature mask `0x16` advertises barrier, priority and unmap, as defined in
[Apple's XNU4903 disk header](https://raw.githubusercontent.com/apple-oss-distributions/xnu/xnu-4903.241.1/bsd/sys/disk.h).
No feature operation was invoked.
The helper opened the disk read-only; no resize, flush or storage write was
issued. These capabilities do not establish successful writes or durability.

The first temporary `/tmp` location was denied by System Policy. The identical
binary passed from a unique temporary `/usr/bin` location, as earlier probes
did. All temporary helpers were removed; no signing or global policy changed.
[Sanitized device result](IOS-QUERY-RESULT.json).

The power hour has finished with net loss during a thermal hold; touch also
reached its cumulative recovery limit. The iPad is back in iOS and charging.

## Earlier checkpoint

# Current: checkpoint and interrupted-install preparation pass

The #35 desktop and guarded charging are active on the powered hub; the owner
confirms the charging icon, menu and keyboard. The prior source-path gate has
passed; the full one-hour charging result is still pending.

New preparation completed in this boot:

- **35 host test methods pass** across layout, bounded mapping, interrupted-install
  classification and checkpoint validation. The actual captured-layout model
  classifies 22 memory-only interruption outcomes without repair or device writes.
- Read-only ASP reads over pinned Wi-Fi captured the 280-block descriptor area:
  140 valid NX candidates, no malformed candidates. The selected mapping chain
  and all five mapped ephemeral objects pass headers/checksums. Container size
  remains 127,999,954,944 bytes. This does not validate full filesystem semantics.
- A new disposable **host file** rehearses the 128 GB proposed layout, 4096-byte
  read-only loop, offset/length-fenced read-only DM map, ext4 `ro,noload`, base
  hash readback, and normal unmount/map removal/loop detach. Original image and
  host kernel stay unchanged. No native iPad map or filesystem was created.

The host tool initially assumed `/dev/mapper` contained symlinks; this host
creates direct block nodes. The revised check uses the actual major/minor and
sysfs DM name. A transient busy removal was inspected and normally cleaned;
the successful second rehearsal also waits for udev and uses normal retry.
The host swap loop was untouched. This is not a device-root boot result.

See [the transaction and recovery plan](../../../INSTALL-TRANSACTION-PLAN.md),
[interruption model](../j72_install_state.py),
[checkpoint checker](../j72_apfs_checkpoint_plan.py), and
[host rehearsal reference](rehearse-j72-host-native-view.py).
All raw metadata, framework binaries, disassembly, identifiers and image hashes
remain private. The reference tool expects this research workspace's private
inputs; it is not a portable installer.

## Earlier preparation checkpoint

# Current checkpoint: owner UI and mounted cleanup pass

The owner confirms all desktop functions. The away observer was cancelled and
reaped, brightness restored to 1604, and normal nested loop/ext4/NBD/owned-export
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

## Prepared next normal-iOS query (no DFU required)

A separate signed ARM64/iOS12 [query helper](j72-ios-writer-capabilities.c) is
ready after normal iOS return and owner reapplication of Amethyst/root SSH.
It pins iPad4,2 and build16H81, opens only `/dev/rdisk0` read-only with no-follow,
requires the measured geometry, and issues only fixed read queries for media
writability, advertised features, physical block size and maximum I/O sizes.
It repeats the already measured APFS minimal-size query. No resize, raw write,
mount, snapshot or flush operation is exposed. Capability replies do not prove
write/flush durability. Fifteen actual-C/UBSan fake-iOS cases pass; native build,
strict imports and CodeDirectory page hashes pass. Device execution is pending.
The existing read-only recovery capsule and running Linux payload stay intact.
