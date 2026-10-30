# iPad Air 1 Cellular (J72) Linux bring-up

An experimental, tethered **RAM-only** Linux and Omarchy A desktop project for the iPad Air 1 Cellular (`iPad4,2` / `J72AP`). The iPad's iOS installation and internal storage remain intact.

Read the [progress report](J72-PROGRESS.md) for measured results and current limits, the [process guide](PROCESS.md) for the checks and RAM boot sequence, the [roadmap](ROADMAP.md) for the remaining work, and the [deferred internal-storage plan](INTERNAL-STORAGE-PLAN.md) for the later installation gates.

The present desktop uses software rendering and a read-only Arch Linux ARM filesystem served by a Raspberry Pi over USB. Native touch is still being ported. This repository is a place to share reviewed notes while J72 support is developed; a focused hardware implementation may later be proposed to [OrchardLinux/hardware](https://github.com/OrchardLinux/hardware).

**Touch milestone:** the corrected SPI driver accepts firmware and panel calibration. The firmware now starts through the exact N1 sequence and answers checksum-validated device-info and screen-metric queries matching iOS. An attention-gated recorder passed its idle check; real finger capture is next, and touchscreen input is not enabled in the desktop yet.

Private firmware, device calibration, identifying logs, and local disk images are intentionally excluded.
