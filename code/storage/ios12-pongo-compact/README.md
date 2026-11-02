# Compact read-only Pongo inventory — v2 candidate

**Built and tested offline. Not yet run on the iPad.** This replaces the next
verbose observer test; it does not boot the RAM recovery image or install Linux.

## Measured reason for the change

The second direct-Pi DFU reached Pongo. The revised v1 module loaded, although
its load message was only retrieved after reconnecting the host client. Calling
the already-loaded probe passed model/RAM/DT guards, read allocator/argument
metadata and got past the 4-byte handle. USB failed partway through its verbose
memory-map output. A later direct libusb status read timed out; the owner saw
Apple logo/iOS, and normal iPad4,2 / iOS12.5.7 USB was then verified. No RAM
recovery image booted and no disk, partition or snapshot was changed.

These observations do not identify a proven cause. Console production/read
interaction is a hypothesis to test, not an established fix. The preceding
built-in boot-argument pointer concern also remains unproved.

## What changes in this candidate

- Collect DT metadata without printing inside its traversal callback.
- Emit a fixed compact summary, not every map row. The synthetic successful
  response is 562 bytes; accepted frames must stay below 2 KiB.
- Use the validated `Kernel-__TEXT` DT range to read its bounded Mach-O header
  and UUID directly, replacing the backward page search. The original kernel
  UUID must still match the privately pinned Apple image.
- Keep exact J72/SOC/DT/RAM guards, require empty reserved slots, bound metadata
  count and check trust-cache/text ranges. Read allocator top directly.
- Use a small native-libusb client. Device stdout is non-blocking; the client
  waits for command completion before fetching it. No concurrent producer/read
  loop is used. Commands are restricted to help, module load and this observer.
- Fetch the supported **4096-byte** stdout response. Pongo empties its ring per
  request and discards leading bytes when the requested length is smaller;
  a sequence of 512-byte requests would not preserve a long response.
- Upload once per discovered USB session; refuse replacement/repeated uploads.
  Always release the claimed interface and native libusb context on exit.

This is a read-only observer. Ordinary module allocation/registration occurs in
RAM. It has no boot, kernel patch, boot-argument edit, storage or snapshot command.
Native libusb is already installed on the Pi; no host kernel change, system
package installation or global library replacement is needed.

## Offline checks and use

[RESULT.json](RESULT.json): 11 cases using the actual C inventory callback,
eight frame refusals, a fake-device check that refuses stdout reads while a
command is active, four transport refusals, and the existing shared 8 span /
143 Mach-O cases. The fake device models Pongo's drain-and-truncate ring behavior,
not a byte stream. Native kext relocations and actual Pongo export pointer pairs
are checked, alongside source/tool/firmware pins. This is not hardware validation.

These are actual lab sources, expecting scripts in `tools/` and the private
lab layout. They also use `run-j72-pongo-recovery-probe.py` from the
[v1 source set](../ios12-pongo-probe/) for Mach-O/pin helpers. Apple firmware,
compiled images, kernel UUIDs, device identities, keys and raw logs remain private.

```sh
python3 tools/prepare-j72-pongo-recovery-compact.py
python3 tools/test-j72-pongo-recovery-compact.py
python3 tools/run-j72-pongo-recovery-compact.py
```

The commands above are offline. After a fresh direct-Pi DFU:

```sh
sudo -n python3 tools/j72-pongo-boot.py --require-direct-pi --confirm-pongo
# Wait for success and full loader cleanup before continuing:
sudo -n python3 tools/run-j72-pongo-recovery-compact.py --capture
```

Do not run the old verbose capture or built-in `bootargs`/`xargs` commands.
A passing compact inventory would let us prepare the RAM-disk/trust-cache
handoff using verified kernel state. It would not qualify recovery or storage
writes. Keep a healthy Pongo session open for compatible follow-up work.

## Source references

- [Pongo USB console semantics](https://github.com/checkra1n/pongoOS/blob/e98323f8a09abd80fc4cbcd74dee023b91a1ec22/src/shell/usbloader.c)
- [Pongo console ring and blocking](https://github.com/checkra1n/pongoOS/blob/e98323f8a09abd80fc4cbcd74dee023b91a1ec22/src/kernel/support/io.c)
- [Existing pongoterm polling loop](https://github.com/checkra1n/pongoOS/blob/e98323f8a09abd80fc4cbcd74dee023b91a1ec22/scripts/pongoterm.c)

All authored code is MIT; [PROVENANCE.json](PROVENANCE.json) records its hashes.
