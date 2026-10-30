# iPad Air 1 Cellular (J72) Linux bring-up

An experimental, tethered **RAM-only** Linux and Omarchy A desktop project for the iPad Air 1 Cellular (`iPad4,2` / `J72AP`). The iPad's iOS installation and internal storage remain intact.

Read the [progress report](J72-PROGRESS.md) for measured results and current limits, the [process guide](PROCESS.md) for the checks and RAM boot sequence, the [roadmap](ROADMAP.md) for the remaining work, and the [deferred internal-storage plan](INTERNAL-STORAGE-PLAN.md) for the later installation gates.

The present desktop uses software rendering and a read-only Arch Linux ARM filesystem served by a Raspberry Pi over USB. Native touch is still being ported. This repository is a place to share reviewed notes while J72 support is developed; a focused hardware implementation may later be proposed to [OrchardLinux/hardware](https://github.com/OrchardLinux/hardware).

**Touch milestone:** the controller now accepts its firmware (`0x4bc1`) through GPIO SPI, direct hardware PIO, and the corrected normal Linux SPI driver. Guarded execute tests produced a response and attention change. The next work is firmware device information, private calibration and touch reports; native touch input is not working yet.

Private firmware, device calibration, identifying logs, and local disk images are intentionally excluded.
