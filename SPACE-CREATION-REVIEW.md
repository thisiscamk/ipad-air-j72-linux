# Storage space review after the passing RAM recovery test

Prepared 2 November 2026. **Offline design; no snapshot or storage changes are authorized.**

## What is now measured

The exact J72 boots the restricted iOS12 RAM recovery. SSH authentication,
HFS/md0 root-device identity, zero APFS mounts, both GPT copies/CRCs and the
unmounted minimum-size query all pass. The existing partition occupies
127,999,954,944 bytes. Its minimum is 126,357,602,304 bytes, leaving
1,642,352,640 bytes before alignment. It is the same minimum reported in iOS.
The root mount's initial source label really is `root_device`.

The current 3 GiB desktop filesystem has 1,845,407,744 bytes allocated.
`resize2fs -P` estimates a minimum of 2,525,773,824 bytes; that is an estimate,
not a shrink performed. The unchanged ext4 desktop cannot fit the current gap.

## First route to evaluate: compressed local desktop

A gzip SquashFS copy of the existing desktop was built privately from a
read-only host loop mount: **572,002,304 bytes**. Five selected file readbacks
match; the source image is preserved and the host mount was removed. Capacity
and source/tool hashes are recorded locally.
The #34 read-only USB desktop test now passes module load, SquashFS/NBD,
owner-visible desktop/keyboard, Wi-Fi/HTTPS/SSH and normal cleanup. This is
filesystem-format qualification, not a local-storage boot. The #35 kernel has
SquashFS and overlay support configured as modules. Matching SquashFS modules
for #34 and #35 now build and pass 106 import/provider checks. Native-storage integration
and writable-overlay qualification remain later work.

A compressed base can allow an interim local-storage root while retaining the
original iOS snapshot. The first native-storage boot can keep the base read-only
and use RAM for writable runtime directories. This would run without a PC after
Pi-assisted startup, but changes made in RAM would disappear on reboot.
Persistent settings and package updates need a separately qualified writable
store and enough update headroom. Compression does not complete those gates.

### Conditional 1536 MiB layout — arithmetic only

This candidate uses one Linux partition and keeps the kernel/initramfs on the
Pi for the accepted assisted-start milestone. No separate internal boot
partition is required for that milestone. Values use the current 4 KiB geometry:

| Item | Conditional value |
| --- | ---: |
| APFS first LBA, unchanged | 6 |
| APFS proposed byte length | 126,389,035,008 |
| Headroom above currently reported APFS minimum | 31,432,704 bytes |
| Linux first LBA, 1 MiB aligned | 30,856,704 |
| Linux last LBA | 31,249,919 |
| Linux partition capacity | 1,610,612,736 bytes (1536 MiB) |

The partition needs room for filesystem metadata, the compressed base and any
future overlay. The artifact size must be measured before selecting it. The
API minimum is a necessary limit; it does not qualify an actual iOS12 resize.
Fresh geometry/minimum and the exact reviewed write ranges remain prerequisites.

## Larger conventional root remains a separate route

An 8 GiB ext4 root would need a container length around 119.41 GB with this map,
about 6.95 GB below the current minimum. It must not be attempted at that minimum.
It would provide more room for packages and updates once a supported way to
release the space is established.

Hoolock documents an [iOS11–13 snapshot restriction](https://github.com/HoolockLinux/docs/blob/23ebe1fbc375599221553a7e1815e5de182a6b42/tools/README.md#caveats)
and describes deletion/recreation as a possible workaround. That does not prove
this owner's snapshot is the cause or establish a J72 procedure. Its resizer
also requires the SEP/key-storage environment to be initialized and cautions
against a zero-size/max resize on these older systems. None of those mutation
operations were run here.

The [reviewed Amethyst restore path](https://github.com/staturnzz/amethyst/blob/61ce86d7d3f00e5395f4d42bebda0e5dce04946a/Amethyst/Amethyst/jailbreak/remount.c#L184)
renames/reverts/mounts its original snapshot and cleans up jailbreak state.
It is not an export of the snapshot or a proved way to lower the container
minimum. Do not use Restore RootFS or remove that snapshot as an exploratory
step. A GPT metadata copy cannot restore APFS content or the rollback snapshot.

## Remaining work before an installation proposal

1. Capacity passes: the compressed base leaves 1,070,350,336 bytes against the
   reported shrink allowance before partition/filesystem/overlay overhead.
   Budget actual update headroom before choosing a layout.
2. Integrate matching SquashFS and storage modules, private runtime inputs and
   desktop configuration; qualify the compressed desktop over a read-only host
   export before changing internal storage.
3. Qualify the native block read path for a filesystem root and preserve both
   recovery shells. Native write/flush/power-loss behavior remains a later gate
   before any persistent writable overlay.
4. Prepare an exact iOS12 shrink/GPT/image-write proposal against fresh captures,
   including its practical iOS recovery route and rollback limits. Submit it for
   separate approval before executing it.
5. After approved space creation and readback, boot the local compressed base
   read-only, then verify unplugged desktop/touch/Wi-Fi and normal iOS recovery.
6. Qualify persistent writes and charging cooldown restart/sustained net gain.
   Fully PC-free startup after shutdown remains separate from assisted startup.

No new DFU is needed merely to repeat the passing recovery query. The next
DFU should test a concrete native-root integration change once prepared. The
compressed USB test passes; native local root remains unqualified.
