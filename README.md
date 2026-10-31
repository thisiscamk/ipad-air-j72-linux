# iPad Air 1 Cellular (J72) Linux bring-up

An experimental, tethered **RAM-only** Linux and Omarchy A desktop project for the iPad Air 1 Cellular (`iPad4,2` / `J72AP`). The iPad's iOS installation and internal storage remain intact.

Read the [progress report](J72-PROGRESS.md) for measured results and current limits, the [process guide](PROCESS.md) for the checks and RAM boot sequence, the [roadmap](ROADMAP.md) for milestones, the [DFU session plan](DFU-PLAN.md) for proposed test batches, and the [internal-storage plan](INTERNAL-STORAGE-PLAN.md) for the later installation gates.

The present desktop uses software rendering and a read-only Arch Linux ARM filesystem served by a Raspberry Pi over USB. Native multitouch now reaches Linux input, and the owner has confirmed full-screen touch mapping with a visual target test. This repository is a place to share reviewed notes while J72 support is developed; a focused hardware implementation may later be proposed to [OrchardLinux/orchard](https://github.com/OrchardLinux/orchard).

**Touch milestone:** correcting an omitted shared analog-power enable changed the result from zero-contact reports to real native touch: 542 one-finger and 50 two-finger reports during the owner's gestures, with nine matched press/release lifecycles and no contacts left down. The capture passed firmware health and hardware restoration checks. A Linux multitouch device now drives a visual target/trace test; the owner confirmed accurate mapping across the screen. The owner has also opened desktop menus and launched Foot by touch. On-screen keyboard typing and its bar toggle also work. The latest cold RAM boot automatically started touch and the desktop; window dragging and tap-to-keyboard behavior now work in the live session.

Private firmware, device calibration, identifying logs, and local disk images are intentionally excluded.

**Current session:** automatic touch self-check, full cleanup, restart and read-only desktop startup passed on the device. A longer touch cycle also stopped cleanly, and the same worker restarted without DFU. The keyboard now uses automatic text focus; its revised startup package still needs an independent cold confirmation. Native Home opens/closes the menu, and the owner confirmed a three-second brightness dim followed by restoration. Battery telemetry, charging and Wi-Fi remain unqualified.


**Next DFU prepared:** cold confirmation of automatic keyboard behavior, then UART5 registration and one bounded battery-voltage read trial. The exact-board device-tree change preserves the kernel; no battery commands run automatically. The reader has passed offline protocol and timeout checks. Actual battery communication is still untested.
