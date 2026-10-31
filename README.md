# iPad Air 1 Cellular (J72) Linux bring-up

An experimental, tethered **RAM-only** Linux and Omarchy A desktop project for the iPad Air 1 Cellular (`iPad4,2` / `J72AP`). The iPad's iOS installation and internal storage remain intact.

Read the [progress report](J72-PROGRESS.md) for measured results and current limits, the [process guide](PROCESS.md) for the checks and RAM boot sequence, the [roadmap](ROADMAP.md) for milestones, the [DFU session plan](DFU-PLAN.md) for proposed test batches, and the [internal-storage plan](INTERNAL-STORAGE-PLAN.md) for the later installation gates.

The present desktop uses software rendering and a read-only Arch Linux ARM filesystem served by a Raspberry Pi over USB. Native multitouch now reaches Linux input, and the owner has confirmed full-screen touch mapping with a visual target test. This repository is a place to share reviewed notes while J72 support is developed; a focused hardware implementation may later be proposed to [OrchardLinux/orchard](https://github.com/OrchardLinux/orchard).

**Touch milestone:** correcting an omitted shared analog-power enable changed the result from zero-contact reports to real native touch: 542 one-finger and 50 two-finger reports during the owner's gestures, with nine matched press/release lifecycles and no contacts left down. The capture passed firmware health and hardware restoration checks. A Linux multitouch device now drives a visual target/trace test; the owner confirmed accurate mapping across the screen. The owner has also opened desktop menus and launched Foot by touch. On-screen keyboard typing and its bar toggle also work. The latest cold RAM boot automatically started touch and the desktop; window dragging and tap-to-keyboard behavior now work in the live session.

Private firmware, device calibration, identifying logs, and local disk images are intentionally excluded.

**Latest session:** UART5 now communicates with the battery gauge. Three voltage reads returned 3.824 V; the gauge identified as BQ27545 and returned charge level, temperature, current and cycle data. Charging remains untested. A touch status-query failure was diagnosed and a revised worker restored input without DFU; it then emitted 11,708 frames and passed final health/cleanup. The owner confirmed repeated keyboard hide/tap/type with a small Foot patch. The desktop and read-only root were shut down cleanly.

**Next build in progress:** integrate the gauge with Linux's battery interface and combine the Foot patch with bounded touch status-read retries. These changes still need independent cold qualification. The iPad has been asked to reboot to iOS for charging; no next DFU has been requested.
