# J72 iOS 12 RAM recovery candidate

**Image built and checked offline; the first attempt stopped in the exploit before any image upload.** This is recovery preparation,
not an installer. The current storage blocker is the measured APFS minimum:
only 1.64 GB can be released, despite about 71.7 GB free inside the container.
We retain the existing Amethyst rollback snapshot. Its contribution to that
minimum is not proved.

## What this candidate does

- Uses the original, unpatched iOS 12.5.7 / 16H81 J72 Apple kernel.
- Patches iBSS/iBEC for a temporary RAM boot, with exactly
  `rd=md0 debug=0x2014e -v wdt=-1`. No NVRAM unlock or restore/reformat arguments.
- Keeps all 174 original restore trust-cache records and adds the staged
  executable CodeDirectory hashes. Whether the stock kernel accepts the
  augmented cache remains a device-test question.
- Replaces the restore daemon with our guarded USB service, disables the
  other three stock launch jobs and enables one recovery job.
- Starts password-disabled Dropbear with unique private host/client RSA keys.
  The authorized key forces the inspector; forwarding and PTYs are disabled.
- Exposes only `inspect` and `reboot`. Inspection requires this exact model,
  Darwin 18, HFS `/dev/md0` as root and zero mounted APFS filesystems.
- Opens `/dev/rdisk0` read-only and performs 13 fixed, aligned 4 KiB reads
  for the measured 128 GB / 4096-byte geometry. The host checks both GPT
  headers, CRCs and entry copies. Raw captures remain private.
- Tries the read-only `APFSContainerGetMinimalSize` getter. It may be
  unavailable or fail in unmounted recovery; there is no resize fallback.

No automatic APFS mount, snapshot change, raw write or installer is included.
Factory restore utilities still present in the original Apple image are not
made available through the restricted SSH command. Apple images, keys,
compiled programs and private logs are deliberately excluded from this repo.

## Checks completed

[RESULT.json](RESULT.json) records 16 cases against the actual boot-argument
guard, signed code-page/cache verification for six staged Mach-O files,
13 RAM-image file readbacks, seven unchanged stock loader/library files and
all six IMG4 component types. The original compressed kernel is unchanged.
Both authored executables rebuild byte-for-byte with the commands below.

On normal jailbroken iOS, the service refused before IOKit/child-process
actions, and the inspector refused before raw-disk access. Its separate mount
ABI probe correctly saw three mounts, including two APFS mounts and a
non-RAM root. These are negative guard tests, not recovery-boot qualification.
The launcher timeout check stopped a deliberately spawned child process group.

The first device attempt verified exact J72/direct Pi, then timed out in gaster
after 120 seconds. Its stdout was buffered, so the exact exploit stage is
unknown. Two cable cycles did not restore USB. No iBSS, iBEC or RAM image was
uploaded, and the inspector did not run. The revised launcher saves line-buffered
live exploit output and stops/reaps its group at gaster's explicit A7 cable
prompt. A saved attempt can resume without another exploit only if its original
ECID, unchanged capsule and `PWND:[gaster]` USB marker all match. Six invalid
resume-state cases and the live-prompt/process-group checks pass offline. This
revised handling is not hardware-tested yet.

## Building the authored tools

Requires Clang, LLVM's Mach-O linker and a native `ldid`. No Apple SDK is
needed: the minimal linker stubs here contain authored ABI declarations.
From this directory, build each source, substituting its name:

```sh
clang -target arm64-apple-ios12.0 -O2 -ffreestanding -fno-builtin \
  -fno-stack-protector -Wall -Wextra -Werror \
  -c j72-usb-recovery.c -o j72-usb-recovery.o
ld64.lld-19 -arch arm64 -platform_version ios 12.0 12.0 -e _main \
  -adhoc_codesign -L . -lSystem -F . \
  -framework CoreFoundation -framework IOKit \
  j72-usb-recovery.o -o j72-usb-recovery
ldid -Sservice-entitlements.plist j72-usb-recovery
```

For `j72-recovery-inspect`, omit the two `-framework` options and use
`inspect-entitlements.plist`. Keep compiled outputs outside this repository.

The Python files preserve the actual lab recipes. They expect the lab workspace
layout: scripts in `tools/`, authored sources and owner-supplied inputs in the
private `recovery-prep` directory. They are not a standalone download-and-boot
distribution. The private input manifest, signing material and launcher pins
must be generated and reviewed before use. Adapt model/geometry guards only
after measuring a different device; this candidate is restricted to J72.

`prepare-j72-ios-recovery.py` builds/checks without USB access.
`test-j72-ios-recovery.py` checks the prepared private capsule offline.
`boot-j72-ios-recovery.py` defaults to offline preflight; `--boot` makes one
bounded attempt, requires root, a direct Pi connection and one exact J72 in
DFU. Uploads target the same ECID. It does not retry failed uploads or change
NVRAM. Each subprocess group is parent-bound and reaped.
`--resume-pwned-dfu /private/saved-attempt` uses the strict resume gate above;
it never repeats the exploit or accepts a partially uploaded boot chain.

The native HFS tool reports `BTree inconsistent!` when deleting one stock
launch job. That failed image was discarded. The accepted recipe starts from
the untouched image, uses a directory-only tar, and overwrites regular files
through `add_hfs`/`writeToHFSFile`. It never uses the failing catalog-deletion
path. All staged files are read back and compared.

## Primary sources and licensing

- USB initialization derives from xerub's GPL service as retained in
  [sshrd_SSHRD_Script](https://github.com/verygenericname/sshrd_SSHRD_Script/blob/1a0c0e034b687ffbad7675a88fac8772c0e80185/restored_external.c).
  The C service, inspector and common guard are GPL-2.0-or-later.
- [Legacy iOS Kit's pinned recipe](https://github.com/LukeZGD/Legacy-iOS-Kit/blob/23622f8fe72c09952089d5145a7b008cfcc90d9b/restore.sh)
  supplies the ARM64 tooling and A7 boot sequence as references.
- [SSHRD's pinned script](https://github.com/verygenericname/SSHRD_Script/blob/d99ec4a19172b87d80fd9dea25eabf39291425a0/sshrd.sh)
  uses x86-64 tools on Linux by default and adds A7 restore/reformat arguments;
  it is not run as our read-only preset.
- [Kairos](https://github.com/dayt0n/kairos) supplies the bootloader patcher.
- Functional `statfs64`, disk-ioctl and open-flag declarations follow
  [Apple XNU 4903](https://github.com/apple-oss-distributions/xnu/tree/xnu-4903.241.1/bsd/sys).
- The minimum-size getter follows
  [Orchard's wrapper](https://github.com/OrchardLinux/resize-apfs/blob/ac1658923378dcb800523d7dcd45002fc2bc5862/Sources/NativeSystem/NativeSystem.c)
  and the iOS-era ABI cited in the [earlier inspection helper](../ios12-readonly-inspect/).

The new Python recipes and authored `.tbd` stubs are MIT; the copied GPT
checker retains GPL-2.0-only. Referenced third-party tools keep their own
licenses and are not redistributed here. Source pins and hashes are in
[PROVENANCE.json](PROVENANCE.json).
