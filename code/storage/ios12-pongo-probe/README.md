# Read-only J72 Pongo recovery-handoff probe

**Built and checked offline; not yet run on the iPad.** The checkra1n → Pongo
boot path is already proven by our Linux sessions. This new observer is a
separate device test. It does not boot the prepared iOS recovery image.

## Why change the route?

The gaster attempt reached its A7 PATCH/reconnect prompt, but two cable cycles
did not restore Apple USB. Its saved attempt was not resumed. No bootloader,
RAM image or storage inspector was uploaded. A comparison against
[Legacy iOS Kit's gaster fork](https://github.com/LukeZGD/gaster/tree/f91d322e0feaf3ceb4f800b5ece8f0423d3f57dd)
found the same A7 payload and reconnect logic, so that swap is not a changed
test. The owner has returned the device to normal iOS.

[Pongo's XNU driver](https://github.com/checkra1n/pongoOS/blob/e98323f8a09abd80fc4cbcd74dee023b91a1ec22/src/drivers/xnu/xnu.c)
contains RAM-disk loading and XNU boot commands. Its
[boot dispatcher](https://github.com/checkra1n/pongoOS/blob/e98323f8a09abd80fc4cbcd74dee023b91a1ec22/src/kernel/entry.c)
provides a starting point for a RAM recovery handoff. We first need to measure
the actual kernel and memory-map state. Those source interfaces do not establish
that our recovery image or augmented trust cache will work through Pongo.

## What the observer does

`j72-pongo-recovery-probe.c` registers only `j72rescueprobe`.

- Requires A7 and the exact `iPad4,2` DeviceTree model. The host separately
  requires one Pongo USB device with CPID `8960` and BDID `12`.
- Validates RAM bounds and the DeviceTree's existing physical/cacheable view.
- Records boot-argument metadata and bounded memory-map entries, including
  unused reserved slots. It does not change boot arguments or the DeviceTree.
- Searches at most 8 MiB backwards from the existing kernel entry, at 4 KiB
  intervals, for a structurally valid ARM64 executable header and UUID.
  It never follows Mach-O pointers. The canonical Apple kernel's entry is
  inside this search bound; the host must match its UUID before accepting
  the runtime result.
- Leaves Pongo running for compatible follow-up work.

The module has ten imports, all exported by the pinned Pongo binary: console,
command registration, DeviceTree readers and boot-state globals. There is no
boot command, kernel patch, raw MMIO, storage, snapshot or installer interface.
Loading the module uses ordinary Pongo RAM allocation and command registration.
The host capture process is scoped, parent-bound and reaped on exit.

## Build and capture recipes

The five source files here are the actual lab sources. They expect the lab
layout, with scripts in `tools/` and private inputs/artifacts under
`private/j72-platform/power-storage-20261102/recovery-prep/pongo-route/`.
They are not a standalone firmware distribution. Apple images, raw logs,
kernel UUID/profile data and compiled outputs remain private.

`prepare-j72-pongo-recovery-probe.py` checks the exact Apple BuildManifest,
decompresses the original kernel locally, compiles the module and writes
private pins. It uses Clang and the previously cached **native ARM64** Apple
`ld64`, with command-local private runtime libraries. No host kernel or global
linker/library replacement is involved. LLVM 19's `-kext` flag is unimplemented;
its output was not accepted as a Pongo module.

```sh
python3 tools/prepare-j72-pongo-recovery-probe.py
python3 tools/test-j72-pongo-recovery-probe.py
python3 tools/run-j72-pongo-recovery-probe.py
```

All three commands above are offline. The third defaults to preflight only.
After a fresh DFU, the existing lab launcher starts the proven Pongo image:

```sh
sudo -n python3 tools/j72-pongo-boot.py --require-direct-pi --confirm-pongo
sudo -n python3 tools/run-j72-pongo-recovery-probe.py --capture
```

Run those hardware steps sequentially. The capture takes the shared USB lock,
uploads this module, invokes only the read-only probe, validates the framed
response and saves it privately. It does not automatically boot, reset or
continue into a different test after a refusal. Source pins, UUID and source
hashes must match the prepared private manifest.

## Offline evidence

[RESULT.json](RESULT.json) records eight actual-source RAM-span cases,
143 Mach-O cases including the canonical original kernel, eight malformed
response refusals and a deliberately fragmented CR/LF transport test.
The native module's kext type, segments, symbol table and ten external
relocations/imports are checked against the pinned Pongo exports.

All authored files are MIT. ABI declarations follow the pinned Pongo source;
no Apple SDK headers, firmware or private capture contents are redistributed.
[PROVENANCE.json](PROVENANCE.json) records the source hashes and upstream pins.
