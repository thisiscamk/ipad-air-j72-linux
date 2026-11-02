# Combined #35 storage, Wi-Fi and container desktop start on device

The cold boot and both USB recovery shells pass. The live firmware/reserved-memory
inventory passes before loading ASP. The internal namespace is read-only; six
bounded aligned reads match before and during desktop/Wi-Fi activity, including
both GPT signatures. Wi-Fi association, HTTPS and pinned-key SSH pass.

The proposed filesystem format now reports desktop ready: ext4 mounted
`ro,norecovery,nosuid,nodev,noexec`, read-only loop/SquashFS base, RAM runtime.
Brightness is 1604/2047 with 475,880 KiB available after startup. **The owner confirms all desktop functions. Normal nested loop/ext4/NBD cleanup
and owned host export termination also pass.** This was a Pi-hosted format rehearsal, not an internal installation. The known
RAM desktop is now restored and the USB filesystem export is detached.
[Measured status](RESULT.json).

## Two RAM-only compatibility fixes

The recovery BusyBox HTTP applet crashed, and it lacks `nbd-client`. Both USB
shells remained healthy. [stage-j72-network35.py](stage-j72-network35.py) stages
the separately hash-pinned static bootstrap BusyBox under a directory retaining
its required basename `busybox`. It uses this helper only for HTTP while
preserving the networking bundle's archive hashes and RAM staging checks.
The regular bundled BusyBox is dynamic and cannot bootstrap an empty recovery
root; arbitrary renaming of the static multicall binary also changes dispatch.

After the first desktop attempt stopped and its bounded child exited, normal
touch/NBD/export cleanup passed. [repair-j72-container35-nbd.py](repair-j72-container35-nbd.py)
checked exact #35, healthy stopped input, zero NBD size, no mounted roots/export,
old controller hash and static helper hash. It archived the old controller and
manifest, changed only NBD calls to a hash-checked helper, updated source pins
and uploaded the authored RAM controller. `--container35 --resume` then passed.
[Actual controller](controller-example.sh), [autostart](autostart-example.sh).
The original kernel, firmware, payload and filesystem image were unchanged;
`/bin/busybox` was retained. A future fresh start in this workspace must stage
the helper first and use the corrected pinned controller already prepared here.
The original offline container preparation recipe predates this compatibility
fix; its output needs the same controller adaptation before target startup.

The payload audit currently also refreshes the builder manifest. Running it
after source sealing invalidates the container's manifest pin; the startup
preflight refused safely. Re-sealing verified unchanged kernel/artifacts before
updating authored source pins. Do not omit preflight to bypass that refusal.

## Earlier preparation and format details

# Earlier offline preparation of the combined #35 candidate

This prepares the next changed DFU. The existing proven #35 storage kernel,
loader and DTB are retained; the initramfs now has freshly matched touch,
WLAN/provider, brcmfmac, recovery and SquashFS modules. Module imports resolve
against the actual kernel and selected module providers. Builds, payload audit,
hash preflights and an actual wrong-kernel refusal pass. **At that preparation checkpoint this combined image was device untested;
the later device results are recorded above.** [Sanitized results](RESULT.json).

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
4. Stage networking with `stage-j72-network35.py`, start the matched radio and connect with the private owner
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
