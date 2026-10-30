# Roadmap to a usable J72 Omarchy A tablet

This is a staged research plan, not an installation procedure. The current boot runs from RAM with a read-only root filesystem served by a Raspberry Pi. iOS and the iPad's internal storage remain intact. Each stage needs real-device evidence before it can be called working.

## 1. Finish native touch

- Continue from the accepted J72 boot-ROM reply and successful bounded SPI transfers. Valid 80-byte, 16,400-byte, and full firmware packets returned `0x1f01`, `0x4969`, and `0x4cb1`, respectively; none received the required `0x4bc1` acknowledgment. Adding the matching iOS pre-reset N1 wake still gave `0x4cb1` for the full packet. A receive-drain kernel timed out with 16 RX words outstanding; a half-prefill variation timed out with 8 outstanding. Zero prefill completed the full transfer but returned idle `0x1f01`. One-word prefill with corrected RX accounting completed the transfer and restored the `0x4cb1` reply. Altering one header checksum byte did not change that reply. A bounded counter test then showed one hardware TX byte outstanding after the full one-word-prefill packet, despite an empty FIFO and a 20 ms wait; the transmit-complete bit stayed clear. Clocking an extra byte cleared that count and set completion, but the touch reply remained `0x4cb1` both when copying the last packet byte and when using the `0xff` filler found in iOS. Keeping the full receive count and supplying filler while the receive window was active completed both hardware counters, yet the reply stayed `0x4cb1`. Setting SPI mode bits to `0x40` changed transfer status flags but not the reply; further audit showed the iOS `0x40` write belongs to its memory-descriptor path, while FIFO PIO uses `0x20`. Further touch DFUs require stronger evidence about the physical wire stream or another specific controller difference. Qualify transport before calibration or execution. Physical clock rate, reset timing and attention behavior still need qualification.
- The combined reset/RUN (`0x0d`) test completed TX/RX counts but returned idle `0x1f01`, as did zero prefill with RUN `0x01`. Next staged touch DFU: explicitly release FIFO reset with control `0x00`, queue one byte, verify that the FIFO retains it before RUN, then measure full-count completion or timeout without filler.
- Implement board-specific power, clock, reset and SPI handling with reliable cleanup.
- Load the correct touch firmware format and this panel's calibration through a private, owner-controlled path. Verify firmware acknowledgment, touch events, multiple contacts, orientation and edge accuracy in Linux and the desktop.

**Pass:** repeated cold RAM boots give usable touch in an unprivileged Omarchy A session, with clean return to iOS.

## 2. Make the tethered desktop dependable

- Script the Pi-to-iPad RAM boot, read-only root handoff, graphical startup and teardown with exact board and artifact checks.
- Integrate Home button handling into the input stack, then test menu behavior without the temporary bridge.
- Measure memory, frame rate and responsiveness on the A7 software-rendered desktop; trim the session where needed.

**Pass:** repeatable desktop sessions with touch, Home and USB recovery.

## 3. Bring up platform services individually

- Establish battery reporting and safe charging under Linux. The Pi USB port has not provided reliable charging in these experiments.
- Bring up Wi-Fi and Bluetooth using the J72 buses, power controls and required firmware. Keep USB networking available for recovery.
- Qualify audio, brightness, cameras, cellular, GPU acceleration and suspend separately. There is no evidence yet that all will be available.

**Pass:** each service works in use and survives repeated boot and shutdown cycles.

## 4. Integrate and share the port

- Turn the local experimental J72 worktree into a reproducible build with a 4 KiB-page kernel, matching modules, exact `iPad4,2`/`J72AP` identification and a documented RAM boot path.
- Propose an experimental J72 profile to [OrchardLinux/hardware](https://github.com/OrchardLinux/hardware) once core desktop and touch are reproducible. State support limits clearly; J72 differs from existing Orchard profiles.
- Publish original code and sanitized evidence. Keep Apple firmware, calibration and raw device logs local.

**Pass:** another owner can build and test the RAM-only path on the exact model, with recovery instructions.

## 5. Consider independent operation later

A persistent root filesystem on an external host can come before internal-storage work. A host-launched internal install would need J72 ANS1 write support, an iOS 12-compatible layout procedure, backup and recovery evidence, and explicit owner authorization. The current Orchard installer and APFS resizer do not support this J72/iOS 12 combination. See the [deferred internal-storage plan](INTERNAL-STORAGE-PLAN.md). Internal storage would not by itself eliminate the host needed for DFU/Pongo after a cold restart. That work is outside the current RAM-only scope.

Native touch is the main uncertainty. No reliable completion date is possible until the controller responds and its firmware protocol works on J72.
