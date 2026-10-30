# iPad Air 1 Cellular (J72) Linux bring-up

An experimental, tethered **RAM-only** Linux and Omarchy A desktop project for the iPad Air 1 Cellular (`iPad4,2` / `J72AP`). The iPad's iOS installation and internal storage remain intact.

Read the [progress report](J72-PROGRESS.md) for measured results and current limits, the [process guide](PROCESS.md) for the checks and RAM boot sequence, the [roadmap](ROADMAP.md) for milestones, the [DFU session plan](DFU-PLAN.md) for proposed test batches, and the [internal-storage plan](INTERNAL-STORAGE-PLAN.md) for the later installation gates.

The present desktop uses software rendering and a read-only Arch Linux ARM filesystem served by a Raspberry Pi over USB. Native touch is still being ported. This repository is a place to share reviewed notes while J72 support is developed; a focused hardware implementation may later be proposed to [OrchardLinux/hardware](https://github.com/OrchardLinux/hardware).

**Touch milestone:** firmware startup, calibration retention and raw reporting pass. The active native-report mask was found to be separate from the BF setting. Enabling contact and periodic reporting through C8 produced 228 checksum-valid native `0x44` frames in an eight-second idle test. Their zero-finger contents were expected at idle; actual contact coordinates still need qualification. Firmware health and hardware restoration passed. A gesture capture with the corrected mask is next in the same RAM boot.

Private firmware, device calibration, identifying logs, and local disk images are intentionally excluded.
