# RAM profile using the optional Foot component

Apply the four [RAM producer patches](../omarchy-a-ram-desktop), then the
[optional Foot component patch](../omarchy-a-foot-touch-ime), then this patch.
A replay of these published patches matches combined source
`ca09d407e7615b6a232cbe24f457cb16ae4e1a62` exactly.

The additional `--foot-tools DIRECTORY` input uses the normal component
verifier and records the override, original stock binary hash and provenance.
Omitting it keeps the signed Arch Foot. It does not mutate the staged base.
The dependency closure includes the selected Foot's libraries from that same
normal base root. Cursor and Labwc inputs remain unchanged.

All 133 combined host tests pass, including 16 RAM fixtures. The actual
normal-root plan passes with 295,290,967 expanded bytes and 3,765 selected files.
The actual gzip SquashFS build passes at 110,972,928 bytes (105.83 MiB),
within the unchanged 128 MiB cap. Independent extraction checks match the
selected binaries, libraries, configuration and ownership. All 52 required QML
imports remain covered. Native GUI, repeated taps and cleanup have not been
tested on the device. Apple firmware and calibration remain private.
