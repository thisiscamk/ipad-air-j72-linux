# J72 speaker audio: measured experimental source

The CS42L81 codec is reused unchanged. J72 needs an A7 SmartIO layout/protocol
variant and MCA-v1 playback support. The included C sources and `audio.dts`
are the implementation used for the speaker tests. `apple-sio-dma.c`,
`virt-dma.c` and the DMA headers retain their upstream implementations.

## Proven on the device

- Codec ID reads; six-command A7 SmartIO setup and two DMA channels.
- 48 kHz, stereo, signed 16-bit playback, including drained muted PCM.
- Owner heard both individual channel tones; physical side separation seemed
  correct but was hard to distinguish on the small device.
- Unchanged PipeWire/WirePlumber discovered a stereo output. A normal
  `pw-play` transfer completed. The PCM closed and MCA suspended after idle.

The on-device audio service was enabled, but a fresh boot has **not** verified
it. No headphone, microphone, Bluetooth audio or browser playback qualification
is claimed. A dynamic-overlay teardown reference warning remains unresolved.
Do not repeatedly insert/remove the overlay as if cleanup were leak-free.

## Build only

Use the exact prepared kernel source/output tree from the current snapshot:

```sh
python3 code/current/audio/make-overlay-header.py
make -C "$J72_KERNEL_SRC" O="$J72_KERNEL_OUT" ARCH=arm64 LLVM=1 \
  M="$PWD/code/current/audio" modules
```

`dtc` and `fdtput` come from the device-tree compiler package. These commands
generate a hardware-description header and modules; they load nothing.
Check `vermagic` against the running kernel before any device experiment.
No force-loading or host-kernel replacement is part of this procedure.

## Private firmware is still required

The firmware request is `apple/s5l8960x-smartio.bin`. Obtain the matching
SmartIO firmware from your own iOS 12.5.7 inputs. The measured payload was
464,208 bytes, SHA-256
`af3d61851d4a2dd53d7301d945d7ff3f0d94eef2e15947f1de2c9a8982708e33`.
This is an identity check, not a firmware download. The A7 extraction path
and persistent deployment are not yet packaged as a public installer.
No firmware or generated firmware-bearing module is in this repository.

## Stage the actual development startup service

`runtime/` contains the actual loader, mute helper and systemd unit used on
the development installation. They pin J72, this kernel ABI and the local file
manifest. The service registers the card before `user@1000.service`, initializes
a conservative volume/mute, and leaves normal PipeWire/WirePlumber in control.
There is no startup tone. The test card is named `J72 Audio Test`.

After building modules and obtaining your own verified private firmware:

```sh
python3 code/current/audio/stage-runtime.py \
  --modules-dir code/current/audio \
  --firmware /your/private/s5l8960x-smartio.bin \
  --output /your/private/j72-audio-root
```

This prepares a private root overlay, checks firmware identity and module ABI,
and loads/enables nothing. Include that overlay in your reviewed installed
system deployment; its output contains firmware and must not be published.
The runtime relies on the matching native codec/simple-card modules already
being installed. It uses UID 1000, as on the measured Omarchy-A installation.
Review/change service ordering if your user differs, then requalify.

On the matching installed J72 only, after reviewing deployment:

```sh
sudo systemctl daemon-reload
sudo systemctl enable orchard-j72-audio.service
```

The live start already passed on the development iPad. **Do not advertise
automatic startup until a fresh boot passes.** Stop mutes; it intentionally
does not remove the known-leaking hot overlay. Disabling the service and
rebooting clears the runtime hardware without repeated overlay teardown.
