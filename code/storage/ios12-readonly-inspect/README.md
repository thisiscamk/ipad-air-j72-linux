# J72 iOS 12 read-only inspection helper

**Built and statically checked; not yet run on the iPad.** Use the owner's
existing jailbreak and authorized root SSH. An ordinary iOS reboot does not
restore jailbreak SSH services.

The helper refuses machines other than `iPad4,2` and Darwin 18. It reports
whether APFS.framework loads and whether a small set of candidate symbols
exists. It never calls those APFS functions. Symbol presence does not validate
their ABI, behavior or a supported resize minimum.

It also calls the documented `fs_snapshot_list` interface for `/` and
`/private/var`, using one bounded 64 KiB buffer per path. Output includes only
the first batch's entry count and numeric errors. It does not output snapshot
names or UUIDs, and does not claim that a first batch is a complete inventory.
No resize, snapshot mutation, mount, raw-disk write or `fsctl` occurs.

The ABI declarations follow Apple's
[snapshot interface](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/sys/snapshot.h)
and [attribute-list layout](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/sys/attr.h).
The minimal linker stub is authored here; no Apple SDK or firmware is included.

Build with Clang and LLVM's Mach-O linker:

```sh
clang -target arm64-apple-ios12.0 -O2 -ffreestanding -fno-builtin \
  -fno-stack-protector -Wall -Wextra -Werror \
  -c j72-apfs-inspect.c -o j72-apfs-inspect.o
ld64.lld-19 -arch arm64 -platform_version ios 12.0 12.0 -e _main \
  -adhoc_codesign -L . -lSystem j72-apfs-inspect.o -o j72-apfs-inspect
```

Static inspection confirms an ARM64 Mach-O executable, an ad-hoc signature
and only the expected basic library imports. Native execution, jailbreak
signing requirements and snapshot-list permissions remain to be checked.
If either listing reports an error, it does not establish that no snapshots
exist. This helper contains no resize or deletion action to fall back to.
