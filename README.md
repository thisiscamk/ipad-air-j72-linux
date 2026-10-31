# iPad Air 1 Cellular (J72) Linux bring-up

An experimental, tethered **RAM-only** Linux and Omarchy A desktop project for the iPad Air 1 Cellular (`iPad4,2` / `J72AP`). The iPad's iOS installation and internal storage remain intact.

Read the [progress report](J72-PROGRESS.md) for measured results and current limits, the [process guide](PROCESS.md) for the checks and RAM boot sequence, the [roadmap](ROADMAP.md) for milestones, the [DFU session plan](DFU-PLAN.md) for proposed test batches, and the [internal-storage plan](INTERNAL-STORAGE-PLAN.md) for the later installation gates.

The present desktop uses software rendering and a read-only Arch Linux ARM filesystem served by a Raspberry Pi over USB. Native multitouch now reaches Linux input, and the owner has confirmed full-screen touch mapping with a visual target test. This repository is a place to share reviewed notes while J72 support is developed; a focused hardware implementation may later be proposed to [OrchardLinux/orchard](https://github.com/OrchardLinux/orchard).

**Touch milestone:** correcting an omitted shared analog-power enable changed the result from zero-contact reports to real native touch: 542 one-finger and 50 two-finger reports during the owner's gestures, with nine matched press/release lifecycles and no contacts left down. The capture passed firmware health and hardware restoration checks. A Linux multitouch device now drives a visual target/trace test; the owner confirmed accurate mapping across the screen. The owner has also opened desktop menus and launched Foot by touch. On-screen keyboard typing and its bar toggle also work. The latest cold RAM boot automatically started touch and the desktop; window dragging and tap-to-keyboard behavior now work in the live session.

Private firmware, device calibration, identifying logs, and local disk images are intentionally excluded.

**Latest session:** the new kernel registered the BQ27545 as a Linux power supply. Three initial samples reported 78%, about 4.09 V, 34.6°C and discharge current on the Pi. The owner confirmed automatic touch and repeated keyboard hide/tap/type from a fresh boot. Touch then stopped with firmware health and hardware cleanup passed; one rejected contact-state packet was retained for review.

**Charging test unresolved:** after detaching the desktop and host export, a recorder ran entirely from RAM for a wall-charger observation. USB failed to enumerate on return to the Pi. The owner then reported a Pi hang during the cable/port change and restarted the Pi. The wall-charger recording was not retrieved, so **Linux charging is not yet established**. The iPad is back on its wall charger. The Pi kernel and original desktop image are unchanged. A separate capacity audit also found that Linux exports unmatched capacity definitions; battery-health estimates are not qualified.

**Next priority after battery reporting:** bring up and measure Linux charging before Wi-Fi work. The [B04C charging plan](DFU-PLAN.md#immediately-after-battery-reporting-b04c-charging-bring-up) uses a RAM-only recorder for wall-charger tests; the USB-backed desktop will be detached before cable changes. Linux charging remains unproven.

**Revised test ready:** a new private image corrects the capacity pairing, retains more kernel diagnostics and adds visible battery readings plus a bounded Home-button USB-recovery candidate. Offline checks passed; these changes still need device qualification. The next charger observation will use screen readings/photos and return to iOS on the wall charger before any Pi reconnection.
