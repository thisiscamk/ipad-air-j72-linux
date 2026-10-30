# iPad Air 1 Cellular (J72) Linux bring-up

An experimental, tethered **RAM-only** Linux and Omarchy A desktop project for the iPad Air 1 Cellular (`iPad4,2` / `J72AP`). The iPad's iOS installation and internal storage remain intact.

Read the [progress report](J72-PROGRESS.md) for measured results and current limits, the [process guide](PROCESS.md) for the checks and RAM boot sequence, the [roadmap](ROADMAP.md) for milestones, the [DFU session plan](DFU-PLAN.md) for proposed test batches, and the [internal-storage plan](INTERNAL-STORAGE-PLAN.md) for the later installation gates.

The present desktop uses software rendering and a read-only Arch Linux ARM filesystem served by a Raspberry Pi over USB. Native touch is still being ported. This repository is a place to share reviewed notes while J72 support is developed; a focused hardware implementation may later be proposed to [OrchardLinux/hardware](https://github.com/OrchardLinux/hardware).

**Touch milestone:** SPI upload, N1 firmware startup, calibration retention and setup-register readbacks pass. Selecting the controller's raw-report path produces continuous checksum-valid sensor frames. Complete tap/swipe and steady-hold captures retained 833 and 1,089 valid frames respectively, with no overwritten data, healthy firmware and full hardware restoration. Reliable contact coordinates remain unproven. Switching back to native finger reporting still produces no finger frames; the current investigation follows the processing and report-selection paths. Native desktop touch is not enabled.

Private firmware, device calibration, identifying logs, and local disk images are intentionally excluded.
