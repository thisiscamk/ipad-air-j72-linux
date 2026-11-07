# Native Orchard J72 CLI candidate

Source for the first native `orchard build` / `orchard run` test on the iPad
Air 1 Cellular. **One native USB console boot passes.** This is a review bundle against Orchard
`6b5fca68c56868651113ede0063a3061d0b22914`, not a supported-device release.
Apply the four numbered patches with `git am` in a clean checkout of that
base. The runtime test used `e9946443f4901125fc24a5895aa3c9a70629d665`; the later
result/feature metadata commit is `6ae6dfc` (no runtime-code change).

The patches contain:

1. A verified public firmware recipe identifying the Apple iOS 12.5.7 IPSW
   and logical J72 touch-properties input. Outputs remain empty for the
   console build. The existing Orchard remote extractor already works.
2. An experimental J72 descriptor, explicit checksum-checked A7 bootstrap,
   dynamic Pi 4 direct-port check and a RAM console using standard serial,
   NCM and SSH. Native desktop features remain unqualified; install is disabled.
3. Shared build tooling to reuse source-key/checksum verified nightly tools
   in RAM builds, reuse the prepared BusyBox and exclude cache metadata from
   the payload. This is a separate upstream tooling topic, replayed alone as
   `8480fd2` on the same base.

The normal checkout `bin/orchard build examples/usb-console --device j72`
path has produced a real 11.9 MB image using coherent verified nightly kernel,
loader and tools plus an explicit known Pongo 2.6.3 image. The device booted that image with `orchard run ... --no-build --yes`.
Serial/SSH, `orchard exec`, RAM-only file transfer and normal iOS USB return
pass. See the [measured result](../../../history/plans-and-reports/NATIVE-CLI-BOOT-2026-11-03.md).

A source build can use `--kernel-tree`; the prepared first image instead
uses the normal `--kernel-dir`, `--busybox`, `--loader`, `--pongo` and `--cache`
component overrides. The exact published component base is
`nightly-20261103-6b5fca68c568`, kernel 7.3.0-rc1-orchard-apple-4k. Its J72 DTB,
image and 71 matching modules were checked. No lab 7.0.12 modules are reused.

This console test supplies no touch, Wi-Fi, desktop or charging policy. The
existing lab stack demonstrated those features separately; they still need
native driver/DT/firmware integration and exact-revision hardware tests.
The new native SPI source topic is not in this published first-test kernel.
Internal storage remains untouched.

4. The measured first native console result and qualification of USB serial
   and NCM/SSH only. Installation stays disabled; desktop hardware is unqualified.

## Validation

- Eight A7 bootstrap/process-ownership tests pass.
- Firmware extraction matches the privately decoded logical input; the full
  official IPSW hash and exact board identity were verified locally.
- Ten published-component tests and three focused RAM packaging tests pass.
- Actual image component hashes, CPIO contents, init, standard USB helper,
  Dropbear and SSH permissions pass inspection. No private key, firmware,
  optional modules or cache metadata is included.
- Final complete Orchard unit suite: **510 tests pass, no skips** (task umask022).
- Hardware qualification: one direct-Pi RAM boot, serial and SSH execution,
  4 KiB SSH push/pull and forced serial pull pass. iOS USB returned after
  normal reboot. Owner and two diagnostic reads confirm iOS charging on the powered hub;
  display and desktop hardware remain unqualified.

Only source and public recipe metadata are included. Apple firmware,
calibration, credentials, raw device logs and binary boot images stay local.
Kernel topics will be exported through Orchard's prescribed workflow only
after their hardware gates pass; these files are CLI/recipe source patches.

## Upstream drafts

- [Orchard #58](https://github.com/OrchardLinux/orchard/pull/58): shared RAM tools reuse/staging fix.
- [Orchard #59](https://github.com/OrchardLinux/orchard/pull/59): experimental J72 native console, depending on #58.

Both are drafts. They contain the implementation, tests and measured result;
they do not submit the unqualified native touch/Wi-Fi/power topics.
