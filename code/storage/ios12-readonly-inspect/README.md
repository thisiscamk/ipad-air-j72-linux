# J72 iOS 12 read-only inspection helpers

**Device tested on iPad4,2 / iOS 12.5.7 with the owner's existing Amethyst
jailbreak active.** Root SSH returned after the owner reapplied Amethyst.
No DFU was needed for these checks. No partition, APFS container or snapshot
was changed; temporary helper files were removed after execution.

## Measured result

The [result](RESULT.json) records these initial checks:

- APFS.framework loads; `APFSContainerResize`, `APFSContainerGetMinimalSize`
  and `APFSContainerGetSpaceInfo` are present. The helpers never call resize.
- The snapshot helper reports one root snapshot and zero data snapshots in
  its bounded first batch. The already installed `snaputil -l` separately
  completed with matching counts. Snapshot names stay private.
- `APFSContainerGetMinimalSize("disk0s1", ...)` returns success and
  **126,357,602,304 bytes**. The output fits the measured container, is
  4096-byte aligned and passes output-buffer canaries.
- Against the 127,999,954,944-byte container this allows at most
  **1,642,352,640 bytes** geometrically, before layout alignment/headroom.
  This cannot fit the 1 GiB boot + 8 GiB root sizing reference. About
  71.7 GB of free APFS blocks does not override the API's reported minimum.

This is a successful minimum-size query, not a successful shrink or an
installation proposal. A snapshot contribution is plausible, not proved.
Hoolock's [iOS 11–13 caveat](https://github.com/HoolockLinux/docs/blob/23ebe1fbc375599221553a7e1815e5de182a6b42/tools/README.md)
mentions snapshots preventing shrink. Amethyst's
[restore implementation](https://github.com/staturnzz/amethyst/blob/main/Amethyst/Amethyst/jailbreak/remount.c)
uses its original root snapshot for rollback. Deleting that snapshot would
change recovery behavior and is not part of these helpers or authorized tests.

## Source and ABI

`j72-apfs-inspect.c` refuses any model other than `iPad4,2` and Darwin 18.
It checks candidate symbols without invoking them, and calls the documented
`fs_snapshot_list` interface for `/` and `/private/var` with one 64 KiB buffer
each. It outputs counts/errors only; a first batch alone is not a complete
snapshot inventory. The mask is `ATTR_BULK_REQUIRED` (`0x80000001`), including
`ATTR_CMN_RETURNED_ATTRS`. The initial name-only mask returned EINVAL; this
was corrected before the passing v3 result.

`j72-apfs-minimum.c` uses the exact `APFSContainerGetMinimalSize` spelling
and `int(const char *, CFIndex *)` ABI recorded by
[Orchard's wrapper](https://github.com/OrchardLinux/resize-apfs/blob/ac1658923378dcb800523d7dcd45002fc2bc5862/Sources/NativeSystem/NativeSystem.c)
and the [palera1n declaration](https://github.com/palera1n/jbinit/blob/df653b8a4cc30cdc3bcec65d4aff0ed7b598da22/apple-include-private/APFS/APFS.h).
On ARM64, CFIndex is a signed 64-bit long. The query is restricted to the
freshly measured single APFS physical store `disk0s1`; there is no writable
raw-disk open or fallback mutation operation.

Snapshot ABI declarations follow Apple's
[snapshot interface](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/sys/snapshot.h)
and [iOS 12-era attribute layout](https://github.com/apple-oss-distributions/xnu/blob/xnu-4903.241.1/bsd/sys/attr.h).
The minimal linker stub is authored here; no Apple SDK or firmware is included.

## Building and execution

Build either source with Clang and LLVM's Mach-O linker, substituting its name:

```sh
clang -target arm64-apple-ios12.0 -O2 -ffreestanding -fno-builtin \
  -fno-stack-protector -Wall -Wextra -Werror \
  -c j72-apfs-inspect.c -o j72-apfs-inspect.o
ld64.lld-19 -arch arm64 -platform_version ios 12.0 12.0 -e _main \
  -adhoc_codesign -L . -lSystem j72-apfs-inspect.o -o j72-apfs-inspect
```

The temporary data-volume path was denied by iOS process-execution policy
and the process was killed before output. Executing the same binary from a
unique temporary `/usr/bin` path worked, without new entitlements, signing
packages or a different jailbreak. That path was removed after each check.
Do not overwrite an existing executable. This observation applies to the
owner's current jailbreak and is not a generic execution-policy guarantee.

No resize, snapshot creation/deletion/rename/revert, mount, or raw-disk write
is present. An error never authorizes one as a fallback.
