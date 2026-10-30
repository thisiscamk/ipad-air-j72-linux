# iPad Air 1 Cellular (J72) Linux bring-up

An experimental, tethered **RAM-only** Linux and Omarchy A desktop project for the iPad Air 1 Cellular (`iPad4,2` / `J72AP`). The iPad's iOS installation and internal storage remain intact.

Read the [progress report](J72-PROGRESS.md) for measured results and current limits, the [process guide](PROCESS.md) for the checks and RAM boot sequence, the [roadmap](ROADMAP.md) for milestones, the [DFU session plan](DFU-PLAN.md) for proposed test batches, and the [internal-storage plan](INTERNAL-STORAGE-PLAN.md) for the later installation gates.

The present desktop uses software rendering and a read-only Arch Linux ARM filesystem served by a Raspberry Pi over USB. Native touch is still being ported. This repository is a place to share reviewed notes while J72 support is developed; a focused hardware implementation may later be proposed to [OrchardLinux/orchard](https://github.com/OrchardLinux/orchard).

**Touch milestone:** the corrected SPI path, N1 startup and calibration retention pass. Enabling the separate C8 native-report gate produced 228 valid empty native frames at idle. The subsequent owner gesture capture retained all 5,297 checksum-valid native frames, but every frame still reported zero fingers. Firmware health and hardware restoration passed. Native packet output now works; contact detection and desktop input remain unresolved.

Private firmware, device calibration, identifying logs, and local disk images are intentionally excluded.
