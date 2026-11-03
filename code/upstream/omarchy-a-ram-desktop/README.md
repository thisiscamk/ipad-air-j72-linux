# Omarchy A bounded RAM desktop candidate

Source-only topic for `OrchardLinux/omarchy-a`, based on
`fa25972a83a279bdd7e5edc9ff6013cd211562fb`. Apply patches in numbered order.
That base includes the separately prepared optional automatic-keyboard setting;
its normal default remains disabled.

The producer accepts a normal staged Arch root and verified desktop, cursor
and Labwc component directories. It computes the runtime closure and produces
a compact gzip SquashFS plus a normal Orchard RAM project. It does not borrow
the earlier laboratory desktop. The generic helper is invoked as a command;
no Orchard Python internals are imported into Omarchy.

The normal distribution and installed desktop are unchanged. This explicit
RAM profile offers the shell, Foot and software keyboard, bounded writable
RAM, and manual desktop start. Its rescue PID 1 and standard USB serial/SSH
remain outside the desktop chroot. Optional hardware drivers are not loaded
automatically; internal storage is not mounted. See the included
`docs/ram-desktop.md` patch for exact inputs and commands.

## Measured host results

- All 128 host tests pass, including 15 RAM fixtures.
- The corrected actual image is 109,719,552 bytes (104.64 MiB), under 128 MiB.
- Selected expanded regular files total 293,944,222 bytes, under 384 MiB.
- Independent extraction checks match critical binaries, configuration,
  ownership and QML metadata. All 52 required imports are in 77 selected modules.
- Initial writable limits: upper 64 MiB, runtime 32 MiB, shared memory 16 MiB.

These results qualify source selection and image construction. The generated
init, mounts, chroot and desktop session have **not run on the device**. Their
lifecycle, memory headroom, input and USB survival still need qualification.
The signed base Foot also lacks the separately prepared experimental repeated
touch/IME client change; automatic-keyboard opt-in alone is not proof of
repeated tap activation.

The image and package archives remain local. This directory contains only
source patches and a sanitized validation receipt: no Apple bytes, unit
calibration, credentials, raw device trees or private logs. No upstream kernel
patch export, support declaration or internal-storage installation is included.
