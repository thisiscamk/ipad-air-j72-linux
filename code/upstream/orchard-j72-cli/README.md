# Native Orchard J72 CLI candidate

Source for the first native `orchard build` / `orchard run` test on the iPad
Air 1 Cellular. **Device untested.** This is a review bundle against Orchard
`6b5fca68c56868651113ede0063a3061d0b22914`, not a supported-device release.
Apply the three numbered patches with `git am` in a clean checkout of that
base. The integrated source is `e9946443f4901125fc24a5895aa3c9a70629d665`.

The patches contain:

1. A verified public firmware recipe identifying the Apple iOS 12.5.7 IPSW
   and logical J72 touch-properties input. Outputs remain empty for the
   console build. The existing Orchard remote extractor already works.
2. An experimental J72 descriptor, explicit checksum-checked A7 bootstrap,
   dynamic Pi 4 direct-port check and a RAM console using standard serial,
   NCM and SSH. Native feature flags remain unqualified; install is disabled.
3. Shared build tooling to reuse source-key/checksum verified nightly tools
   in RAM builds, reuse the prepared BusyBox and exclude cache metadata from
   the payload. This is a separate upstream tooling topic, replayed alone as
   `8480fd2` on the same base.

The normal checkout `bin/orchard build examples/usb-console --device j72`
path has produced a real 11.9 MB image using coherent verified nightly kernel,
loader and tools plus an explicit known Pongo 2.6.3 image. The first test will
use that image with `orchard run ... --no-build`, then check serial, SSH,
`orchard exec`, RAM-only file transfer and normal return to iOS.

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

## Validation

- Eight A7 bootstrap/process-ownership tests pass.
- Firmware extraction matches the privately decoded logical input; the full
  official IPSW hash and exact board identity were verified locally.
- Ten published-component tests and three focused RAM packaging tests pass.
- Actual image component hashes, CPIO contents, init, standard USB helper,
  Dropbear and SSH permissions pass inspection. No private key, firmware,
  optional modules or cache metadata is included.
- Final complete Orchard unit suite: **510 tests pass, no skips** (task umask022).
- Hardware qualification: pending a new owner-authorized DFU.

Only source and public recipe metadata are included. Apple firmware,
calibration, credentials, raw device logs and binary boot images stay local.
Kernel topics will be exported through Orchard's prescribed workflow only
after their hardware gates pass; these files are CLI/recipe source patches.
