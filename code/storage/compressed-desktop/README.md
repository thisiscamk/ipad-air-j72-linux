# Compressed J72 desktop — first device startup passes

**The owner confirmed the compressed desktop UI. Normal cleanup and a same-boot
restart with Wi-Fi also pass. HTTPS and pinned-key Wi-Fi SSH work; the bar status
says connected. The owner confirms Wi-Fi/menu/keyboard work after restart.
No internal storage has been changed.** This follows the [passing RAM recovery inspection](../ios12-pongo-handoff/).

## Why test this

The unmounted APFS query permits only 1,642,352,640 bytes of shrink, while the
existing ext4 desktop does not fit unchanged. A private gzip SquashFS built
from that desktop is **572,002,304 bytes** (about 546 MiB). Five selected files,
including desktop executables, were decompressed and matched byte-for-byte.
The source ext4 was hash-checked, mounted read-only with journal replay disabled
and unmounted normally afterward. No runtime settings or private firmware were
published. [Measured result](RESULT.json).

A conditional 1536 MiB Linux partition could hold this base with space left for
filesystem metadata and a future overlay. An actual shrink remains unqualified
and requires separate approval. [Capacity/layout review](../../../history/plans-and-reports/SPACE-CREATION-REVIEW.md).

## Device test: desktop-format qualification only

Use the proven **#34** Wi-Fi/RAM boot. The new filesystem module was built
against that exact kernel configuration/headers; all 106 strong imports resolve
to vmlinux with no additional module dependency. Kernel image, configuration,
release and export hashes remained unchanged. A separate #35 module is also
built for later native-storage integration; the two are not mixed.

The test host serves only the pinned compressed regular file over read-only
NBD on the dedicated USB interface/port 10831. The target requires the exact
board/#34 build, an unattached `/dev/nbd2`, the expected sector count and read-only
block state. Its controller mounts **SquashFS read-only**, reusing the existing
desktop lifecycle with RAM `/home`, `/run` and `/tmp`. Locale is explicit C.utf8,
portrait transform is explicit, and Foot starts Bash directly.

This test accesses no internal disk and starts no charging controller.
Its initial format-only start does not initialize Wi-Fi. In the actual device
test, normal desktop cleanup was followed by the proven #34 RAM networking
stage/provider/association workflow, then `--resume` in the same Linux boot. It
**requires the USB cable until cleanup** because the base is still hosted on
the Pi. It is neither a local installation nor persistent user storage.
The fixed controller and autostart examples are authored shell code; firmware,
filesystem images, modules, credentials and raw logs stay private.

```sh
# After a fresh direct-Pi DFU:
sudo -n python3 tools/j72-pongo-boot.py --require-direct-pi --confirm-pongo
# Wait for success and full loader cleanup:
sudo -n python3 tools/j72-pongo-pmic-boot.py --wifi-ram-desktop
# After RAM Linux USB is ready:
sudo -n python3 tools/run-j72-compressed-desktop.py --run
# Owner checks menu, dragging and hide -> tap -> typing; keep USB connected.
# Before moving the cable or shutting down:
sudo -n python3 tools/run-j72-compressed-desktop.py --stop
# Optional: after Wi-Fi setup, restart already-staged files in this RAM boot:
sudo -n python3 tools/run-j72-compressed-desktop.py --resume
# Keep USB attached again until --stop.
```

A failed startup keeps the current boot/export available for inspection. Do not
request another unchanged DFU. Stop checks normal unmount, NBD detach and touch
cleanup before terminating the owned host export. PID/group/start-time/source
checks prevent signalling an unrelated process. Resume requires an unmounted,
detached desktop and stopped healthy touch worker; it verifies the loaded
SquashFS GNU build ID and all staged module/controller/autostart file hashes.
The initial source-version check refused safely because this module has no
`srcversion`; GNU build ID is present and passed the replacement identity guard.

The same healthy Linux boot can then resume the existing RAM desktop and Wi-Fi
workflow for later power checks, after the compressed export is detached. A
hub move or screen check is a physical gate; it does not inherently need a DFU.

## Offline preparation recipes

These scripts expect the existing private lab layout and preceding #34 recovery,
input, USB-shell and desktop helpers. They are not a standalone distribution.
The native Debian squashfs-tools package was downloaded/extracted locally;
no host kernel or installed package was changed. The capacity builder pins the
actual native binaries and uses two workers with 256 MiB cache.

```sh
# Fresh private capacity output only:
sudo -n python3 tools/prepare-j72-compressed-root.py
# Build SquashFS in an isolated source copy against the exact #34 output:
# make -C MATCHED_KERNEL_SOURCE O=MATCHED_KERNEL_OUTPUT ARCH=arm64 M=PRIVATE_COPY -j2 modules
# Audit module imports/providers and unchanged kernel/config/export pins first.
sudo -n python3 tools/prepare-j72-compressed-desktop.py
sudo -n python3 tools/run-j72-compressed-desktop.py
```

Current cold-image validation and shell-syntax checks pass. An actual read-only
loopback export also passed process-identity, virtual-size and cleanup checks.
The first device startup passes module load, exact read-only NBD size and
SquashFS mount checks. Available memory was 535,568 KiB in a post-start sample
with no swap. The owner confirmed
the initial rendering/menu/Foot/keyboard check. Normal unmount, NBD/export
cleanup and firmware-health checks passed. The same-boot restart after Wi-Fi
activation has 474,240 KiB available; association, HTTPS 200 and pinned-key SSH
pass. The owner confirms restored Wi-Fi/menu/keyboard. A second normal
unmount/NBD/export/touch cleanup passed, and the proven RAM desktop was restored
for separate power testing; no compressed export remains.
[Sanitized device result](DEVICE-RESULT.json). Native storage reads/root,
approved space creation, write/flush durability,
persistent overlays and sustained unattended charging remain later gates.

Authored host/shell code is MIT. The private filesystem module is built from
Linux's GPL-2.0 source and is not redistributed here.

## New explicit #35 selectors

The current host runner additionally has `--storage35` and `--container35` modes
for the [combined candidate](../desktop-storage35/). Those modes are device
untested. The exact runner from the measured #34 Wi-Fi resume/cleanup checkpoint
is preserved as [tested34-runner.py](tested34-runner.py); the shared runner's
new selectors do not imply a completed #35 hardware test.
