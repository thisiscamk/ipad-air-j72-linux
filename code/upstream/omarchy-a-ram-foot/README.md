# RAM profile using the optional Foot component

Apply the four [RAM producer patches](../omarchy-a-ram-desktop), then the
[optional Foot component patch](../omarchy-a-foot-touch-ime), then these three patches in order.
A replay of these published patches matches combined source
`93777b0` exactly (including its Git tree).

The additional `--foot-tools DIRECTORY` input uses the normal component
verifier and records the override, original stock binary hash and provenance.
Omitting it keeps the signed Arch Foot. It does not mutate the staged base.
The dependency closure includes the selected Foot's libraries from that same
normal base root. Cursor and Labwc inputs remain unchanged.

The original combined source passed 133 host tests, including 16 RAM fixtures. The actual
normal-root plan passes with 295,290,967 expanded bytes and 3,765 selected files.
The actual gzip SquashFS build passes at 110,972,928 bytes (105.83 MiB),
within the unchanged 128 MiB cap. Independent extraction checks match the
selected binaries, libraries, configuration and ownership. All 52 required QML
imports remain covered. Those were host-only results at the time of that build. Apple firmware and calibration remain private.


## 4 November device result and follow-up fixes

The owner verified menu, terminal, keyboard and automatic keyboard reopening
on the native kernel after RAM-only userspace fixes. Patches 2 and 3 include
those startup/closure fixes and detached-process cleanup by chroot root, PID
and start time, with ordinary TERM only. The latest source passes 136 combined
host tests, including 19 RAM fixtures. Patch replay independently matches the
source tree. [Measured device result](../../../history/plans-and-reports/NATIVE-TOUCH-BOOT-2026-11-04.md).

The actual tested SquashFS and payload remain the original image with runtime
repairs. A new clean build containing both follow-up patches still needs device
qualification. The original image measurements do not describe the rebuilt
candidate. The opt-in Foot interface and signed-Arch default are unchanged.
