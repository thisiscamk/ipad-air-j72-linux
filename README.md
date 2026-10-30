# iPad Air 1 Cellular (J72) Linux bring-up

An experimental, tethered **RAM-only** Linux and Omarchy A desktop project for the iPad Air 1 Cellular (`iPad4,2` / `J72AP`). The iPad's iOS installation and internal storage remain intact.

Read the [progress report](J72-PROGRESS.md) for measured results and current limits, the [process guide](PROCESS.md) for the checks and RAM boot sequence, the [roadmap](ROADMAP.md) for milestones, the [DFU session plan](DFU-PLAN.md) for proposed test batches, and the [internal-storage plan](INTERNAL-STORAGE-PLAN.md) for the later installation gates.

The present desktop uses software rendering and a read-only Arch Linux ARM filesystem served by a Raspberry Pi over USB. Native touch is still being ported. This repository is a place to share reviewed notes while J72 support is developed; a focused hardware implementation may later be proposed to [OrchardLinux/hardware](https://github.com/OrchardLinux/hardware).

**Touch milestone:** firmware upload, N1 startup, device information, screen metrics, all 1,152 calibration bytes and five setup-register readbacks pass. On 31 October, eight short reader comparisons completed in one RAM boot with final firmware health and hardware restoration verified. Advancing the read tag only after success improves valid empty replies, but a confirmed owner gesture capture still returned only the startup status frame. A confirmed gesture test with display sync enabled also returned no packets; firmware health and cleanup passed in both cases. A subsequent temporary raw-report selection produced 106 checksum-valid raw result frames in eight seconds. A longer capture counted 5,247 valid frames, but gesture overlap with its retained window was unconfirmed. The replacement recorder retained all 833 valid frames from a 68-second tap-and-swipe test; steady-hold validation is next. Native desktop touch remains unavailable.

Private firmware, device calibration, identifying logs, and local disk images are intentionally excluded.
