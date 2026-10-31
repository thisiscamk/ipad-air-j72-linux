# iPad Air 1 Cellular (J72) Linux bring-up

An experimental, tethered **RAM-only** Linux and Omarchy A desktop project for the iPad Air 1 Cellular (`iPad4,2` / `J72AP`). The iPad's iOS installation and internal storage remain intact.

Read the [progress report](J72-PROGRESS.md) for measured results and current limits, the [process guide](PROCESS.md) for the checks and RAM boot sequence, the [roadmap](ROADMAP.md) for milestones, the [DFU session plan](DFU-PLAN.md) for proposed test batches, and the [internal-storage plan](INTERNAL-STORAGE-PLAN.md) for the later installation gates.

The present desktop uses software rendering and a read-only Arch Linux ARM filesystem served by a Raspberry Pi over USB. Native finger reports now respond to physical touch; Linux input integration is next. This repository is a place to share reviewed notes while J72 support is developed; a focused hardware implementation may later be proposed to [OrchardLinux/orchard](https://github.com/OrchardLinux/orchard).

**Touch milestone:** correcting an omitted shared analog-power enable changed the result from zero-contact reports to real native touch: 542 one-finger and 50 two-finger reports during the owner's gestures, with nine matched press/release lifecycles and no contacts left down. The capture passed firmware health and hardware restoration checks. Evdev, coordinate orientation and desktop interaction are the next checks.

Private firmware, device calibration, identifying logs, and local disk images are intentionally excluded.
