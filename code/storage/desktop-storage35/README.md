# Combined #35 desktop/storage candidate — device untested

This prepares the next changed DFU. The existing proven #35 storage kernel,
loader and DTB are retained; the initramfs now has freshly matched touch,
WLAN/provider, brcmfmac, recovery and SquashFS modules. Module imports resolve
against the actual kernel and selected module providers. Builds, payload audit,
hash preflights and an actual wrong-kernel refusal pass. **This combined image
has not booted on the iPad yet.** [Sanitized results](RESULT.json).

## Proposed filesystem format: host rehearsal passes

A **1536 MiB (1,610,612,736-byte) ext4 host file** contains a
**572,002,304-byte SquashFS base**, a format contract and empty state directory.
Read-only fsck, read-only loop mount with journal replay disabled, base/contract
readback and normal unmount/loop detach pass. Free space after the first base is
958,230,528 bytes. An equal second base would leave 386,228,224 bytes.
This is host capacity evidence; no partition was created on the iPad.

Next, export this file read-only over USB. The #35 candidate mounts ext4
`ro,noload,nodev,nosuid,noexec`, attaches the inner base to a read-only loop,
mounts SquashFS read-only and keeps writable runtime in RAM. Built-in #35
EXT4/LOOP support is reused. Persistent overlay remains disabled.

## Next device sequence

1. Direct-Pi DFU using the proven Pongo launcher, then the new explicit
   `j72-pongo-pmic-boot.py --desktop-storage35` selector.
2. Establish both recovery shells. Run
   `run-j72-storage-observer.py inventory --desktop-storage35`; verify the actual
   live firmware, reserved DRAM, board and exact boot identity before ASP loading.
3. `run-j72-native35-readcheck.py probe --receipt PRIVATE_INVENTORY`, then
   `check --receipt PRIVATE_COMPLETED_PROBE`: read-only namespace, six bounded
   aligned reads, repeated hashes and both GPT signatures. No internal mount.
4. Stage networking, start the matched radio and connect with the private owner
   profile using the explicit `--storage35` selectors; verify HTTPS and Wi-Fi SSH.
5. Run `run-j72-compressed-desktop.py --container35 --run`. Check native reads
   again while the desktop is active, and ask the owner to verify input/UI.
6. Keep USB connected until `--container35 --stop` has normally unmounted the
   desktop, detached its owned loop, unmounted ext4 and detached NBD; only then
   terminate the owned host export. Never lazy-unmount or pull the cable.

ASP, radio, touch and charging start opt-in. A failed ASP probe retains its DMA;
do not unload or repeat it. Preserve recovery and diagnose the failure. The new
#35 charging module is untested and has no qualified host controller adapter.
Do not use a #34 module on #35 or weaken workload/source guards.

## What this does not qualify

This is a read-only format and coexistence rehearsal over USB. Local root still
needs a bounded native partition/offset mapping, an exact reviewed iOS resize/
GPT/write procedure, separate installation authorization, image verification and
an actual local-root boot. The current BusyBox loop tool lacks a size-limit
option; an offset alone would not fence a mapping to the intended partition.
Durable writes, flush/error behavior and persistent state remain later gates.

The Python files here are authored lab references with their original `tools/`
locations recorded in [provenance](PROVENANCE.json). They require preceding lab
helpers, private pinned manifests and lawful local firmware inputs. Copying this
folder alone does not produce a working installer. Builds use Orchard's frontend;
no Apple firmware, firmware includes, modules, disk images, keys or raw receipts
are distributed.
