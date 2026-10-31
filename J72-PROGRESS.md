# Linux and Omarchy A on an iPad Air 1 Cellular (J72)

Progress report as of 31 October 2026. This is a hardware bring-up report for one iPad, not a general installation guide or an Orchard hardware profile.

**Latest:** the corrected D2089 analog enable (`0x84: 0x00 → 0x07`, preserving voltage setting `0x398 = 0x14`) produced real native finger reports during owner gestures. Of 1,801 checksum-valid native `0x44` frames, 542 contained one finger and 50 contained two. The decoded stream has nine matched press/release lifecycles, coordinates covering most of the panel, and no contacts remaining at the end. No malformed layouts, SPI errors or dropped records occurred; final firmware health, zero global status flags and full hardware restoration passed. Linux evdev and visual orientation have since passed an owner target/trace test, including multiple fingers and 21 matched presses/releases. The owner subsequently opened desktop menus and launched Foot by touch. The owner has now confirmed on-screen keyboard typing and the bar toggle too. Automatic touch and desktop startup have now passed a fresh RAM boot. The owner confirms window dragging and keyboard reopening in both Foot windows after live keyboard changes; the revised keyboard startup package still needs a cold confirmation.

## Device and approach

The test device is an iPad Air 1 Cellular (`iPad4,2`, `J72AP`) with an Apple A7 (`CPID 0x8960`, `BDID 0x12`) and iOS 12.5.7. The host is a Raspberry Pi 4 running Debian 13 on aarch64. The experiment uses a **RAM-only, tethered boot**: checkm8/PongoOS → m1n1 → a 4 KiB-page AArch64 Linux kernel and initramfs. The iPad's internal storage and iOS installation have not been changed. The Pi's existing kernel has also been left alone.

The work builds on [Hoolock Linux's A7 documentation](https://github.com/HoolockLinux/docs/blob/master/features/A7.md), its [PongoOS boot method](https://github.com/HoolockLinux/docs/blob/master/tutorials/SETUP_pongoOS.md), and the [Pomme build pipeline](https://github.com/xenoaitham/pomme). [Another J72 Omarchy A experiment](https://github.com/Phoenix2479/ipad-air-linux) provided useful precedent; the results below are measurements from this device.

## Confirmed on the device

| Area | Result |
| --- | --- |
| Boot | PongoOS and m1n1 have booted Linux into RAM on the iPad through the Pi. The USB handoff has occasionally failed on one Pi port, so boot transport still needs hardening. |
| Linux identity | The running system reports `Apple iPad Air (Cellular)`, AArch64, and 4 KiB kernel pages. A rebuilt J72 development kernel reports `7.0.12-j72spi2`. |
| Display | SimpleDRM exposes the panel at 1536 × 2048, 60 Hz. Labwc runs with software rendering. |
| USB access | The Linux USB gadget provides CDC NCM networking and an ACM serial shell. The USB-only network link supports a RAM shell and a host-backed filesystem. |
| Arch and Omarchy A | An Arch Linux ARM root filesystem was served **read-only** over USB NBD. Labwc and Omarchy A's Quickshell ran as an unprivileged tablet user. With the corrected J72 initramfs, the owner again saw the rocket wallpaper, top bar, menu icon, clock, and pointer. The rebuilt kernel reported 1536 × 2048 at 60 Hz. |
| Home button | The kernel reports Home presses as `KEY_HOMEPAGE`. Native compositor/libinput handling now opens and closes the menu on successive presses, confirmed by the owner. The earlier temporary bridge is no longer needed. |
| SPI2 foundation | A J72 SPI2 controller-only kernel build and device tree booted with **no touch child**. The measured controller input clock is 60 MHz. A guarded RAM diagnostic brought its Linux power domain from `0x200` to `0x2ff`, read configuration registers, restored automatic power control, and returned it to `0x200`. It sent no SPI transfer. |
| Touch power baseline | A one-shot, read-only RAM Linux module read PMU enable registers `0x84 = 0x00`, `0x85 = 0x11` and analog rail setting register `0x398 = 0x14` through the existing I²C regmap. The touch rail enable bits were clear. The setting corresponds to a nominal 6,000 mV code in the matching driver table; the rail was off, so no voltage was measured. No PMU write or touch transfer was made. |
| Touch clock baseline | A guarded RAM module powered the J72 PWM0 domain, read the channel 2 control and capture words at `0x10`, `0x14`, `0x20`, `0x34`, and `0x38`, and let Linux power the domain off again. All five words were zero in this idle state; PMGR actual state returned from `0x2ff` to `0x200`. This did not generate or measure a clock. |
| Touch clock programming | A separate one-shot RAM module checked that reset was low, the candidate touch rails were off, and PWM channel 2 was idle. It programmed two count words to 366 and control to `0x4003` for 250 ms. Readback showed counts of 366 and control `0x4001`; it then restored all three words to zero and PWM0 returned to off. This validates a bounded write and restore path, but the physical output rate was not measured. |
| Touch power sequencing | With reset held low and no SPI traffic, a guarded RAM test enabled the candidate analog rail and then LDO rail for 100 ms, following the order in the matching iOS driver. Their enable bits read back as set, then returned to their original clear values in reverse order. PWM registers and its power domain also returned to idle. Voltage at the touch panel and controller readiness were not measured. |
| SPI transport baseline | With the same short power sequence and reset still low, Linux completed one 16-byte, full-duplex SPI2 transfer at a conservative requested 1 MHz. The first four reply bytes were zero in this reset state. The temporary SPI device, rails, PWM registers, and SPI2/PWM0 domains were cleaned up. This establishes a bounded controller transfer, not a touch-chip response. |
| Touch boot-ROM communication | The first two bounded identification tests returned zero reply words. In the third, GPIO79 was routed from GPIO output mode to the SPI chip-select function during the transfer. The same mode 0, least significant bit first HBPP frame then returned `0x1f01, 0x1f01`, both accepted boot-ROM status words. The probe restored GPIO79, reset, rail and PWM registers, and power domains before the iPad returned to iOS. Firmware loading and touch reports remain untested. |
| Longer SPI transfer | After another accepted boot-ROM reply, a guarded one-shot test sent a 256-byte transmit-only protocol filler frame. Linux reported all 256 bytes transferred in about 3.3 ms; a short status query returned the known idle word `0x1f01`. No SPI timeout or incomplete-transfer error appeared. The pin, reset, rails, PWM and domains restored, and iOS returned. This verifies the small FIFO refill path on J72, but does not prove a full firmware transfer. |
| Firmware acknowledgment attempt | After a fresh accepted ID, one private, validated 57,016-byte touch firmware packet was transmitted in a single bounded transfer. Linux reported all bytes sent in about 741 ms with no SPI error. The controller replied `0x4cb1`, while Apple's loader requires `0x4bc1`; acceptance was therefore **not confirmed**. The test did not retry, send calibration, or issue an execute command. It restored all temporary hardware state and returned to iOS. |
| Smaller data packet | A distinct one-shot test sent a valid 80-byte packet after an accepted boot-ROM reply. Linux reported the full transfer in about 0.9 ms, and the controller returned idle `0x1f01`, not the required data acknowledgment `0x4bc1`. The prior full packet returned `0x4cb1`. The shorter packet also has different payload and checksums, so the comparison does not isolate packet length as the cause. All temporary hardware state restored and iOS returned. |
| Intermediate data packet | A valid 16,400-byte packet transferred once in about 213 ms after an accepted boot-ROM reply. The controller returned `0x4969`, matching the intermediate status found in a related A7 iPad experiment. J72 has now returned `0x1f01` for 80 bytes, `0x4969` for 16,400 bytes, and `0x4cb1` for the full packet. None is the required `0x4bc1` data acknowledgment. The module restored the temporary hardware state and the iPad returned to iOS. |
| N1 startup wake | A separate one-shot test added the matching iOS driver's two-byte `19 c1` wake while reset was held. The transfer completed, the boot-ROM ID remained accepted, and the full private firmware packet transferred once. Its status was still `0x4cb1`, not the required `0x4bc1`. Reset, chip select, rails, PWM and power domains restored; iOS returned. The omitted wake alone does not explain the missing acknowledgment. |
| SPI final drain and status comparison | An isolated RAM kernel added a bounded check that the transmit FIFO emptied after each transfer. It did. Its final status was `0x32` after the 256-byte filler, the 16,400-byte DATA packet, and the full packet, so those flags are not specific to the missing acknowledgment. Replies remained `0x1f01`, `0x4969`, and `0x4cb1` respectively. The short and medium comparisons ran in one RAM boot with complete cleanup between them; iOS returned. FIFO drain does not prove byte integrity on the physical wire. |
| S5L receive drain experiment | An isolated kernel was changed to count and discard received words during transmit-only SPI, matching a behavior identified in the exact-board iOS controller driver. Wake and boot-ROM identification still succeeded. During the 57,016-byte firmware transfer, Linux queued all TX words but timed out with **16 RX words outstanding** and status `0x32`; it did not reach the ACK query. The one-shot probe restored reset, chip select, rails and clocks. |
| Strict receive-window experiment | A distinct kernel capped outstanding TX-only words at the 16-word receive FIFO depth. Wake and boot-ROM identification succeeded, but the firmware transfer stalled after only 16 TX words had been queued, with no RX words received, then timed out. No ACK was queried. The probe restored its temporary settings, and normal iOS USB returned. |
| Half-prefill receive-window experiment | The kernel queued 8 firmware TX words before starting the SPI controller and used a 16-word receive window. The rest of the 57,016-byte packet was queued, but the transfer timed out with **8 RX words outstanding**. With a prior 16-word prefill, exactly 16 RX words had been missing. Wake and boot-ROM identification succeeded; no ACK query ran. The probe cleaned up, and the Pi confirmed normal iOS USB afterward. |
| Zero-prefill receive-window experiment | A separate kernel queued the long packet only after starting SPI and drained received words within a 16-word window. Wake and boot-ROM identification succeeded; all 57,016 packet bytes transferred in about 745 ms. The reply was idle `0x1f01`, not the required `0x4bc1`. This removes the prior RX timeout but does not establish that the controller saw an intact packet. The probe restored temporary hardware state and the Pi confirmed normal iOS USB (`iPad4,2`) after reboot. |
| One-word prefill receive-window experiment | With one firmware TX word queued before starting SPI and receive accounting adjusted for that word, the same full packet transferred in about 745 ms without an RX timeout. The controller replied `0x4cb1`, matching the earlier full-prefill result but still not the required `0x4bc1`. The probe restored its temporary state, and normal iOS USB (`iPad4,2`) returned. |
| Header checksum sensitivity test | A distinct one-shot test sent the same 57,016-byte packet with just one header checksum byte altered. Transfer time and length matched the valid-packet test; the reply was again `0x4cb1`. This did not demonstrate content sensitivity and does not prove the physical wire stream or the ROM's meaning for `0x4cb1`. The probe restored temporary hardware state and the Pi confirmed normal iOS USB afterward. |
| SPI transmit completion counter | A one-shot RAM test sent the valid full packet with one word queued before starting the controller. Linux queued all 57,016 bytes and the TX FIFO emptied, but the hardware TX count remained **1** and its transmit-complete bit stayed clear through a bounded 20 ms wait. The touch reply was still `0x4cb1`. All temporary hardware state was restored and the Pi confirmed normal iOS USB after reboot. This exposes a concrete controller accounting gap; it does not establish which bytes reached the touch chip. |
| Residual transmit byte | A second one-shot RAM test clocked a copy of the packet's final byte only after that same residual TX count of 1 recurred. The hardware count fell to 0 and the transmit-complete bit set, but the touch reply remained `0x4cb1`. The probe cleaned up, and iOS returned. The matching J72 iOS PIO code uses `0xff` filler when it has no transmit data left; that was examined in the subsequent test. |
| `0xff` filler after receive completion | A third one-shot RAM test used `0xff` for the residual hardware TX count. The count again fell to 0 and the completion bit set, but the touch reply remained `0x4cb1`. The probe restored all temporary state and the Pi verified normal iOS USB. This test sent filler after Linux had already consumed its reduced receive count. The subsequent test kept the full receive count and supplied filler inside the active receive window. |
| Full receive count and in-window filler | A fourth one-shot RAM test kept the receive count equal to all 57,016 firmware bytes. With one receive byte still due, it sent the `0xff` filler inside the active receive window. Both hardware counters reached zero and transmit-complete was set. The touch reply nevertheless remained `0x4cb1`. The probe restored its temporary state and the Pi verified normal iOS USB. |
| SPI mode-bit comparison | A fifth one-shot RAM test set SPI configuration mode bits to `0x40` for the long transfer. The configured value changed from `0x44038` to `0x44058`. The firmware transfer completed with both hardware counts at zero and transmit-complete set; its final status flags changed, but the touch reply remained `0x4cb1`. The mode and temporary hardware state were restored, and the Pi verified normal iOS USB. A later disassembly audit identified the `0x40` write as part of iOS's memory-descriptor path; its FIFO PIO path uses `0x20`. This corrects our earlier attribution of the tested bit to PIO. |
| Recovery | Earlier RAM tests returned to normal iOS USB (`iPad4,2`) after teardown and reboot. After the 30 October receive-drain test, Linux disconnected on reboot; the owner later confirmed the iOS screen, and the Pi again detected normal iOS USB (`05ac:12ab`, `iPad4,2`). |
| Software observation of SPI pads | GPIO input sampling captured a roughly 29 kHz clock on GPIO76 and the known data pattern on GPIO77. Separate bit-13 cases established the physical bit-order polarity. AUTO_TX cases clocked while the data pad stayed constant. Touch reset stayed low and its rails stayed off for these observations. |
| Accepted firmware through GPIO SPI | A guarded GPIO SPI implementation using measured SCLK/MOSI and input-only MISO received readiness `0x1f01, 0x4879`, then transferred the same 57,016-byte packet in about 5.54 seconds and received ACK `0x4bc1`. It restored all pads, rails, reset and clocks. |
| Four-byte C4 command after valid ACK | A distinct one-shot probe repeated `0x4bc1`, issued the matching four-byte execute command, received `0x4879, 0x4f81`, and observed attention change. It restored temporary state; no calibration or touch reports were attempted. A later device-info query showed that this reply did not prove application startup. |
| Accepted firmware through hardware SPI | A direct-register S5L probe disabled AUTO_TX for explicit payloads, started before queuing bytes, drained receive data and capped the FIFO window. Readiness advanced to `0x4879`; all 57,016 bytes transferred in about 745 ms and ACK was `0x4bc1`. This validates the hardware-controller transfer method before normal Linux SPI API integration. |
| Normal Linux SPI API integration | The corrected driver completed the same 57,016-byte upload in about 745 ms, received `0x4bc1`, and sent the four-byte C4 command with response `0x4879, 0x4f81` and an attention edge. Both power domains and temporary settings restored. No calibration or input reports were attempted in this test. Later application checks established that C4 was not the required Z2 execute path. |
| Correct N1 startup and firmware readiness | The read-only ROM query identified C1F15, and private proximity/panel calibration packets received `0x4bc1`. Five N1 setup writes each received `0x4ad1`. After calibration and the address-bearing Z2 execute command, the device-info reply passed its checksum with interface version 1 and maximum packet size 2,454, matching iOS. This repeated in later probes in the same RAM boot. |
| Screen metrics and operating mode | The 16-byte D9 screen descriptor was read with a valid checksum and matched the private iOS snapshot exactly. AF operating mode read as normal (0), and its readback remained valid after a normal-mode request. |
| Application frame observation | A bounded reader received an application result frame with valid five-byte header checksum and payload checksum. It was an initial status result, not evidence of finger input. Continuous reading exposed pipeline/counter differences that are being resolved before a live swipe capture. |

## Current limits and next test

Native touch input is not yet running. Firmware and calibration upload now pass, and the firmware application responds correctly after the exact N1 setup. A read-only ROM query identifies the controller as C1F15; the live iOS properties and matching driver select the N1 calibration override. After the address-bearing Z2 execute command, device information reports interface version 1 and maximum packet size 2,454 with a valid checksum. Screen metrics match iOS exactly. These establish application startup; they do not yet establish usable touch input.

The decisive measurements came from reading GPIO input buffers while SPI emitted a slow known pattern. GPIO76 followed the clock and GPIO77 carried the transmitted data. With AUTO_TX enabled, MOSI stayed constant rather than following queued payload bytes. With AUTO_TX disabled, the supplied pattern appeared. Configuration bit 13 clear produced MSB-first output; setting it produced LSB-first output. The old S5L driver's Linux flag mapping was reversed. Earlier labels of “LSB-first” in the historical tests described the requested flag; the measured physical wire order was MSB-first. Testing physical LSB-first returned bit-reversed readiness `0xf880`, and its guard stopped before firmware.

The prior readiness check had accepted idle `0x1f01` without proving that the short initialization command was transmitted. The GPIO path progressed from `0x1f01` to `0x4879` before sending the firmware. A hardware-register probe then did the same and received `0x4bc1` after the identical 57,016-byte packet. Its explicit transfers disabled AUTO_TX, queued every byte after RUN, counted and drained the receive side, and bounded outstanding data to the FIFO depth. Applying the same rules through the normal Linux SPI API also received `0x4bc1`, resolving the acknowledgment blocker in the integrated driver.

The tested RAM kernel applies the SPI corrections to short commands as well as long uploads. It polls FIFO levels, requires readiness `0x4879` before upload and ACK `0x4bc1` after each data packet, and restores temporary hardware state after each probe. Multiple distinct modules have run in the same RAM session, avoiding further DFU button sequences.

The earlier four-byte C4 command returned `0x4879, 0x4f81` but did not produce valid application information. The correct J72 path uses the N1 calibration routine and the address-bearing 12-byte Z2 execute frame. Live iOS properties also enable the controller's internal 32 kHz clock; a static default alone missed that setting. Private calibration and firmware are accepted before startup. The application now responds to device-info, report-info, screen-metric and operating-mode queries with valid checksums.

The owner completed the first tap-and-swipe capture. The 120-second recorder received one valid startup status packet and no finger packets. Its attention-low gate was inferred from startup behavior; the polarity for actual finger reporting is not established. A separate 120-second comparison polled both attention levels with alternating read counters and again received only the startup packet. Owner participation in that second window has not been confirmed. Neither result establishes native touch input.

The matching iOS driver enables display sync on GPIO119 before releasing touch reset, a step the earlier probes omitted. A guarded idle test validated the exact mux setting and full restoration. A separate GPIO-only observation sampled 20,000 times over about 116 ms: the disabled pin stayed low, while the display-sync mux produced 7 transitions and both high and low samples. This establishes an active digital signal at the pad, not the panel refresh rate. The owner then completed a new gesture test in a 180-second capture with sync enabled: **zero packets** arrived. Display sync alone has not solved reporting.

Follow-up diagnostics ran in the same RAM boot. Six known device-info, mode and format checks passed over ten seconds, so the application stays responsive under those queries. A broader metadata inventory stopped at its three-invalid-reply limit and restored the controller; it is not evidence that arbitrary report IDs are safe to query. Subsequent work uses known commands.

The candidate stream-setting comparison now has stronger validation. The E1 command-status reply carries the write command, report ID and status at bytes 6, 7 and 8. After writing report BF with `95 81 09 00`, three independent delayed wake/info/readback cycles returned that exact value. A normal-mode write also passed status and readback checks. This resolves the earlier uncertain readback for this candidate configuration; it does **not** establish that the setting enables touch scanning. A two-second idle recorder with the new configuration received no packets or malformed frames, validated application information again at the end, and restored reset, sync pad, chip select, rails, PWM and power domains. The owner then completed gestures during a 180-second capture with this verified configuration: **zero packets**, no malformed frames, and a checksum-valid device-info reply at the end. The firmware still responded after the observation window; this setting has not solved reporting. The current Linux `apple_z2` finger layout remains unqualified until real finger packets are captured.

Two further diagnostics narrowed the startup fault without another DFU. All 288 calibration words (1,024 panel bytes plus 128 proximity bytes) matched the expected private payload both before and after firmware upload, with valid read checksums. Each of the five N1 setup registers also read back its intended value immediately after writing and again after the calibration wait. These results establish data retention and register programming; they do not prove that the application started scanning. The PWM mode also matches the iOS clock-enable call path, although the physical clock output remains unmeasured. The 31 October comparisons below examine chip-select timing and report transactions.

Wi-Fi, Bluetooth, audio, brightness control, suspend, charging and battery reporting have not been qualified under Linux. GPU acceleration, cameras and cellular are also unqualified. The Pi USB connection may not charge the iPad reliably. The physical 32.768 kHz output has not been independently calibrated. The panel's calibration, Apple firmware, raw captures and identifying logs remain private. Normal iOS USB recovery was verified after the preceding SPI integration round. All completed application/report probes restored touch reset, pins, rails, PWM and power domains. The preceding batch returned to iOS for charging; a new RAM session is now active for the 31 October reader comparisons.

## Next development steps

### 31 October: reader comparisons in one RAM boot

Eight distinct short diagnostics completed with final checksum-valid firmware information and full restoration of reset, pins, rails, PWM and power domains:

- CS setup/hold delays of 0, 10 and 1,000 microseconds each recovered the same valid startup status frame. None established finger reporting.
- Success-only read-tag advancement yielded roughly 50% valid empty replies, compared with roughly 25% when advancing after every attempt. This improves the reader but has not resolved touch.
- Idle tests with display sync enabled, using either the default BF value or the verified candidate value, returned valid empty replies and no data frames. Idle results do not qualify gesture behavior.
- An additional query-priming policy did not improve results and produced one invalid checksum in the no-sync comparison. Final firmware health and cleanup still passed.

A first 180-second owner window ended before the delayed reply, so gesture overlap is unconfirmed and it is excluded from qualified negative tests. A fresh recorder then ran throughout a confirmed owner tap-and-swipe test: approximately 59 seconds, 1,913 polls, one checksum-valid startup status frame and no finger packets. There were no malformed frames or transfer errors; final firmware health and cleanup passed. This test used the success-only counter, 10-microsecond CS timing, default BF setting and display sync disabled. The same corrected reader then ran with display sync enabled throughout a second confirmed gesture test. It recorded 9,823 polls, 4,911 valid empty replies and zero positive lengths or frames. No malformed replies or transfer errors occurred; final firmware information was valid and full cleanup passed, including sync restoration. Display sync alone has not solved reporting.

Two targeted one-byte status reads stayed unchanged with sync off and on. A separate read of report `0x7f` showed status `0x00040000` without sync and zero with sync, before and after each eight-second test. This establishes an internal status difference; the flag's complete meaning is still under investigation. All four targeted diagnostics passed firmware health and full restoration.

A separate, audited RAM report selector exposed a useful second path: changing report AC from its default value 2 to value 1 produced **106 full, checksum-valid `0x43` raw result frames in eight seconds**. The test retained all packets locally. Eight other data-stage replies were rejected because they contained command-status responses rather than valid data frames; they are excluded from the 106. There were no transfer errors, final firmware information was valid, status flags remained zero, and hardware restoration passed. This establishes continuous raw reporting under this configuration. It does not yet establish touch-sensitive sensor content, finger coordinates or desktop input. The next owner comparison will check raw contents during deliberate touches in the same RAM boot.

The first longer raw capture counted 5,247 valid frames with no transfer errors, zero final status flags, valid firmware information and full restoration. Its rolling buffer retained 870 valid frames from the final 72 seconds. The owner reported a pause of more than a minute after the gestures, so overlap with the planned gesture sequence is unconfirmed. Small moving variations in that retained window are not counted as confirmed touch response. A replacement recorder is prepared to retain the full ten-minute window instead of overwriting earlier data; it stops and flags a result if its storage bound is reached.

The replacement full-window capture completed after about 68 seconds, retaining all 833 checksum-valid raw frames with no overwritten records. It rejected 136 command-status replies at the data stage; there were no transfer errors, final status flags were zero, firmware information was valid, and cleanup passed. A raw descriptor and payload length are consistent with 1,200 signed 16-bit samples in a 40-by-30 grid. Small localized changes appeared during the final gestures, but reliable contacts and coordinates remain unproven. The owner clarified that this sequence used taps rather than steady holds; a separate hold test is next. No stationary-contact conclusion is drawn from the tap capture.

The owner then performed steady holds in a separate 88-second full-window capture: 1,089 valid raw frames, 156 command-status replies rejected at the data stage, zero transfer errors and no overwritten records. Final status flags were zero, firmware information was valid and restoration passed. The data still does not establish reliable stationary contact coordinates. A subsequent eight-second automated comparison used raw mode for two seconds, native mode for four, then raw mode for two. It retained 54 valid raw frames around the native interval, with no native finger frames during that interval. Both mode changes passed acknowledgment, readback and status checks; final health and restoration passed. Raw warm-up alone has not activated native reporting.

A targeted read-only processing-counter report now narrows the missing-output problem. During an eight-second native-mode test, a counter updated by the capture path advanced from 15 to 306, while the counter updated after native report submission remained zero. The USB reader received no native frames. In raw mode, the capture counter advanced from 18 to 309 and 103 valid raw frames were received. Both probes ended with zero status flags, valid firmware information and full restoration. This supports continued sensor capture in native mode; it does not identify a threshold, calibration or filtering fault by itself.

The previously readback-verified candidate BF setting has now also been tested during confirmed owner gestures with success-only read-tag handling. This distinct 68-second comparison produced 2,208 polls: 1,104 silent responses, 1,104 checksum-valid empty lengths and no frames. There were no malformed replies, transfer errors or overwritten records. The capture-path counter advanced from 32 to 2,122 while the native-submission counter remained zero. Status flags stayed clear, final firmware information was valid and full restoration passed. Combining the candidate setting with the corrected reader has not solved native reporting. Targeted processing-state diagnostics continue in the same RAM session.

A targeted RAM-state snapshot exposed an important distinction: the active native-report gate was `0x08`, while BF referred to a separate parameter block. The diagnostic stopped when one late read could not be validated; final firmware information and full restoration still passed. A separately audited C8 getter independently confirmed the gate value. Its one-byte setter changes only the active RAM mask. The firmware's gate tests contact (`0x01`), periodic/empty-frame (`0x10`) and status-change (`0x08`) flags. The diagnostic preserved the existing status bit and enabled the other two by writing C8 = `0x19`, then checked acknowledgment and readback.

That new idle comparison produced **228 checksum-valid native `0x44` frames in eight seconds**, each with a 24-byte header, zero fingers and a 30-byte contact stride. The native-submission counter advanced alongside the capture counter, from 18 to 308. There were 32 rejected command-status replies at the data stage and no transfer errors. C8 remained `0x19`; final status flags were zero, firmware information was valid and restoration passed. This validates native packet generation and the empty-frame positive control. The following owner test is recorded below. Firmware disassembly and RAM snapshots remain private.

The owner then completed holds, swipes and two-finger gestures during a roughly 190-second recording with C8 enabled. All **5,297 valid native `0x44` frames reported zero fingers**, with the same 24-byte header and 30-byte contact stride. Every retained frame passed independent header and payload checksum validation. The reader rejected 884 other data-stage replies: 822 command-status responses and 62 zero responses. There were zero SPI transfer errors and no overwritten records. The native-submission counter advanced to 5,876 alongside the capture counter. C8 stayed `0x19`; final status flags were zero, firmware information was valid, and reset, pins, rails, PWM and power domains restored. This is a qualified negative contact test with a working native-output positive control. Investigation now moves to acquisition and processing configuration, rather than repeating the same gestures.

Full returned packets are retained privately. Compressed snapshot export removes a transfer bottleneck. Thirteen synthetic parser and shell-transfer checks pass, including the larger full-session snapshot and version/size rejection. The runner verifies the exact J72 model, kernel, module ABI and artifact hashes, and stops on failed firmware health or restoration. The gesture recorder now has a ten-minute maximum and an explicit stop control so an owner response can finish it while it is still active. Firmware, calibration, binaries and raw captures remain local.

The [expanded session plan](DFU-PLAN.md) now covers input integration, battery/brightness, J72 HSIC Wi-Fi, Bluetooth, charging, the remaining tablet services, integrated qualification and the separately gated internal installation.

### Development queue

1. Make the validated RAM boot and graphical startup easier to repeat, including a scripted read-only NBD mount and clean teardown.
2. Finish the continuous report reader and qualify actual finger data; verify native input before enabling it in the desktop.
3. Add an **experimental J72** profile to [OrchardLinux/hardware](https://github.com/OrchardLinux/hardware), with exact board matching, a 4 KiB kernel and matching modules, a RAM boot path, and explicit support limits. The public `devices/` directory has no J72 profile. Its [J72b profile](https://github.com/OrchardLinux/hardware/blob/main/devices/j72b/device.toml) is for the iPad 6 Cellular (`iPad7,6`, A10), a different board. The local J72 worktree is not an upstream port. See the [full roadmap](ROADMAP.md) for milestones and pass conditions.

## Sharing and attribution

This report is suitable for a public repository. The project workspace also contains private Apple firmware, owner-specific calibration, raw USB/device logs, and local images. Those files are intentionally omitted here. A public PR should contain only original source, build instructions, permitted patches, and evidence that has been reviewed for private data.

Relevant upstream projects: [Hoolock Linux](https://github.com/HoolockLinux/docs), [Pomme](https://github.com/xenoaitham/pomme), [Orchard hardware](https://github.com/OrchardLinux/hardware), and the [J72 Omarchy A precedent](https://github.com/Phoenix2479/ipad-air-linux).


## Latest upstream touch review — 31 October

GitHub now redirects `OrchardLinux/hardware` to `OrchardLinux/orchard`. The review checked the current API list, relevant diffs, and review discussions, including the recent merged work rather than only open PRs.

| Contribution | Reusable result | J72 limit / action |
| --- | --- | --- |
| [#28: iPad 5 N1 touch](https://github.com/OrchardLinux/orchard/pull/28) | Same five N1 setup-register values, execute argument, 40×30 sensor geometry and 14745×19657 surface as the verified J72 setup. Classic reports specify header length, image bytes before contacts and contact stride. Control reads retain the phase-zero checksum in phase one. Follow-up patches add bounded retries, falling-edge/attention handling and contact release on errors. | Strongest protocol comparison. Reuse the bounded layout rules and test the control framing separately. A9 SPI, clocks, power wiring and firmware are not J72 resources. The API's merged head is `25bfbd4d53a6d5acb680711bd0219d1510839637`. |
| [#29: iPhone 6 Gen1 touch](https://github.com/OrchardLinux/orchard/pull/29) | Verified physical contacts and releases, private per-unit calibration, data-phase checksum in the final two transfer bytes, coordinate scaling and bounded packet handling. | Our EB data checksum already uses the transfer tail. N61's `9d` initialization write is unsupported on this J72 and must not be copied. T7000 regulator/clock settings do not apply to A7. Reviewed head `c1e0550199394efc2fbc6fbcf20295261533fa5e`. |
| [#32: Linux touchscreen test fixture](https://github.com/OrchardLinux/orchard/pull/32) | Fixes recursive errno includes in host-side packet tests. | Useful when importing the upstream harness; it changes no controller behavior. |
| [#39: iPhone X](https://github.com/OrchardLinux/orchard/pull/39) | New A11 RAM-boot record and Wi-Fi recipe. | Touch remains unimplemented and uses a different HID transport; no Z2 contact-detection fix. |
| [#38: speakers](https://github.com/OrchardLinux/orchard/pull/38), [#36: rotation](https://github.com/OrchardLinux/orchard/pull/36) | Useful references for later platform qualification. | These are J71b contributions, not fixes for J72's current zero-contact result. |

No reviewed PR supplies a verified A7/J72 fix for contact detection or our C8-mask finding. The classic-layout analyzer now uses the reported image offset and stride, rejects truncated or duplicate-ID records, and treats X/Y as signed values. Eighteen offline wire/parser/transfer checks pass. Re-analysis of the latest J72 recording still finds 5,297 valid empty native frames and no malformed classic layouts; parser changes do not create contacts. The N1 control-read comparison then completed in the same RAM boot: 262 polls and 236 checksum-valid native frames in eight seconds, all zero fingers at idle. Twenty-six other data replies were rejected; there were no SPI transfer errors or overwritten records. C8 remained `0x19`, status flags stayed zero, final firmware information was valid and full hardware restoration passed. This qualifies the corrected E6/E7 control framing on J72, without establishing contact detection.

## Charging-break preparation — 31 October

A normal reboot was requested for the owner's charging break after all captures had been saved and touch restoration verified. No probe is active. Further hardware tests wait for a charged device and a fresh owner-confirmed DFU.

Offline tracing now establishes that the previously captured `0x43` images are emitted after several firmware processing stages. They must not be treated as untouched acquisition samples. An audited one-byte RAM report-format setting selects an earlier path, with the same 1,200-sample image layout. That path still copies or combines sample planes, so even its output is not claimed to be pristine ADC data. Two private diagnostics are built but **not run**: an eight-second idle qualification and a full-window owner capture. They check the format before writing, acknowledgment, readback, returned report type/format/image length, final firmware health and complete restoration. The earlier stream will test whether a clear spatial contact response exists before the later processing stages.

A separate pair of diagnostics is built but **not run** for C8 = `0x09`: contact/status reporting without the continuous empty-frame bit used by `0x19`. Static inspection shows that the gate combines previous and current frame flags, allowing a final empty frame after contacts disappear; actual contact/release behavior still needs hardware qualification. These probes leave startup, calibration, SPI timing and read-tag policy unchanged.

Per-frame status `0x1000` occurs in 5,187 of the 5,297 native frames and 1,037 of the 1,089 raw hold frames. One producer derives those high status bits from a difference between frame and selected-channel masks. This does not establish a fatal error or a defective sensor. The separately queried global status flags were zero. Full interpretation remains open.

All four prepared modules pass local source/hash/ARM64/ABI preflight. Twenty offline wire, parser, transfer and sample-stage checks pass; a later-stage image cannot silently pass the earlier-stage trial. The next boot can qualify the short probes first, then select the justified owner test without another DFU between modules. Firmware, disassembly, calibration and captures remain private. The reusable diagnostic redesign remains planned; these prepared probes use the existing one-shot guards.

## Controller identity and reusable research — 31 October

### Identity and related Apple devices

The [iFixit iPad Air LTE teardown, step 18](https://www.ifixit.com/Teardown/iPad+Air+LTE+Teardown/18907) identifies **two Broadcom BCM5976C1KUB6G** touchscreen controllers. That is physical evidence for the model, not an inspection of this owner's unopened board. On this J72, the measured ROM identity is `0x434d15c1`, while the working iOS driver identifies the N1 path and personality `C1F15,1`. These software identifiers are not interchangeable with a package part number, nor do they identify the role of both physical chips.

| Device | Evidence of relationship | Porting relevance |
| --- | --- | --- |
| iPad Air 1 LTE | Two BCM5976C1KUB6G parts in the teardown above; exact J72 software measurements recorded here. | Target board. |
| [iPad Air 2](https://www.ifixit.com/Teardown/iPad+Air+2+Teardown/30592) | BCM5976 digitizer controller identified; also a TI part. | Related silicon, different A8X SPI/power/board wiring. |
| [iPad 5, 2017](https://www.ifixit.com/Teardown/iPad+5+Teardown/85098) | Two BCM5976 controllers identified. | Its working Orchard N1 port is already a close protocol reference. |
| [iPad mini 4](https://www.ifixit.com/Teardown/iPad+Mini+4+Teardown/48891) | BCM5976 digitizer controller identified. | Related hardware; no interchangeable firmware/profile assumption. |
| iPhone 5/5c/5s/6/6 Plus/first SE | The iPad 5 teardown explicitly identifies the family across these models; [first-generation SE teardown](https://www.ifixit.com/Teardown/iPhone+SE+Teardown/60902) also lists BCM5976. | Useful older Z2/N1 comparisons; screen geometry, silicon revisions and power controls vary. |
| A7 iPad mini 2 J86 | [Native driver and board notes](https://github.com/perryraskin/ipad-mini2-linux/blob/e23198d54211ac46a7a9dc14d11100a308555543/HARDWARE.md) report a working N1 implementation. Its source expects ROM `0x434d15c0` and firmware personality `C1F14,3`. | Closest new software reference, with a different ROM revision, firmware and GPIO/SPI mapping. Exact BCM package marking is not established by this software source. |
| MacBook trackpads / Touch Bars | The Air teardown identifies a related BCM5976 MacBook part; Linux also has `bcm5974`, `applespi` and `apple_z2` input drivers. | Report/slot/coordinate ideas only; related silicon or formats do not imply the same transport, startup or record stride. |

### GitHub references ranked for this problem

| Project | What is useful now | Qualification limit |
| --- | --- | --- |
| [perryraskin/ipad-mini2-linux](https://github.com/perryraskin/ipad-mini2-linux/tree/e23198d54211ac46a7a9dc14d11100a308555543) | Same A7 generation, N1 startup, resident stop/restart design, and a concrete D2089 analog-control difference. The README reports owner-confirmed aligned app taps. | Different exact board/ROM/firmware. Inspect source and independently verify J72 values. |
| [jacopone/ipad-nixos BCM5976 research](https://github.com/jacopone/ipad-nixos/blob/a5a92b3921e01b0a6a22991829531cd8e13aa7e9/research/touch-deep-dive.md) and [mattonik's developed work](https://github.com/mattonik/ipad-nixos/blob/b94d42f78e04c5465e290340a5b6879bbc5956b6/research/touch-deep-dive.md) | Useful Air 2 research index, SPI/FIFO investigations, firmware framing and board-evidence workflow; the developed tree has already informed this project. | The mattonik copy explicitly corrects early drop-in-driver claims. Neither the research title nor selecting `CONFIG_TOUCHSCREEN_APPLE_Z2` proves working J81 touch. Our observed 30-byte contact stride also prevents blindly copying a 32-byte structure. |
| [Orchard J71t/N61 work](https://github.com/OrchardLinux/orchard/pull/28) | Physically tested N1 control framing, bounded classic reports and input handling; see the PR review above. | Device power, firmware and calibration stay model-specific. |
| [Project Cascadia P105 N1 analysis](https://github.com/rzxvx/Project-Cascadia/blob/9e299e4af773cdb43a1206c5051f5d3964769acc/docs/research/p105-z2-boot.md) | Exact-stock N1 defaults, live calibration, and the distinction between responding firmware and active scanning. | A5/P105, not A7/J72. |
| [Corellium hx-touchd](https://github.com/corellium/projectsandcastle/blob/03db9c6ae04141eb940f3b9f56d446f50d57fadf/hx-touchd/mtfw/mtfw.c) | Historical Z2/HBPP framing, checksums and firmware conversion; already used as a reference. | Generic loader behavior does not replace the exact N1 personality/defaults. |
| [lemonjesus/ipad-touch-screen](https://github.com/lemonjesus/ipad-touch-screen/tree/1f8a12e562c358356dfa171e3989f7bc53e37ace) | Demonstrated iPad 3 initialization capture/replay and USB multitouch conversion; useful methodology and report handling. | Its physical Pico/soldering path is outside this owner's software-only scope, and its README explicitly excludes direct Air/Mini compatibility. |
| [modpunk's iPhone 6s touch research](https://github.com/modpunk/Omarchy-iPhone6s/blob/ed2a4584caa8bcf908d1958d791242932da8e26c/docs/drivers/touch.md) | Documents a real coarse-report failure despite working firmware/IRQ/SPI, reinforcing the need to inspect actual packet content. | That revision explicitly parks full-resolution touch; it is not a working replacement driver. |

Mainline [apple_z2](https://github.com/torvalds/linux/blob/master/drivers/input/touchscreen/apple_z2.c), [bcm5974](https://github.com/torvalds/linux/blob/master/drivers/input/mouse/bcm5974.c), [openiBoot](https://github.com/iDroid-Project/openiBoot) and [Asahi's firmware extraction](https://github.com/AsahiLinux/asahi-installer/blob/main/asahi_firmware/multitouch.py) remain supporting references. Their packet and transport assumptions must be checked individually.

### Concrete finding: an omitted analog dependency

The [J86 driver](https://github.com/perryraskin/ipad-mini2-linux/blob/e23198d54211ac46a7a9dc14d11100a308555543/touch/native/j86_touch.c) enabled bits `0..2` of D2089 register `0x84`; our J72 probes enabled only bit 2. Re-reading the **exact J72 iOS 12.5.7 driver** independently confirms the missing dependency: after applying the table's rail bit, its special handling also sets the two shared control bits. For our guarded idle baseline, the intended transition is therefore `0x00 → 0x07`, not `0x00 → 0x04`.

This is a demonstrated mismatch to the stock software sequence, **not yet proof of the entire touch failure's cause**. Firmware communication can be healthy while an analog prerequisite is missing. The programmed voltage code is retained; no new voltage is selected. The new probes require the exact initial register values, verify the corrected enabled values, and restore all three owned bits along with the existing LDO/pin/clock state.

The next priority is now the corrected-analog native idle probe, followed by a confirmed owner contact/release capture if health and restoration pass. Corrected-analog earlier-image idle/live probes are also built as a fallback in the same RAM boot. All four pass offline hash/ARM64/ABI preflight; the existing 20 offline checks pass. **None of the corrected-power probes has run.** The earlier contact-mask/sample-stage probes remain controls, but their old analog setup must not be mistaken for the corrected baseline. The iPad remains on its charging break; no new DFU has been requested.


## 31 October: corrected analog power produces native contacts

A working related A7 iPad mini 2 implementation supplied a lead: its D2089 analog enable uses all three low bits. We checked the exact J72 stock driver's dependency handling independently. Our earlier probes set only `0x04`; the matching driver also enables shared `0x03` when the relevant analog rail is enabled. The next test changed that enable to `0x07` while preserving firmware, calibration, SPI timing, native report mask and the voltage setting.

The short idle control produced 237 valid empty native frames and passed health/cleanup. The subsequent owner gesture capture produced 1,801 valid native frames: 1,209 empty, 542 one-finger and 50 two-finger. Active native coordinates ranged x=447–13,858 and y=672–18,924. There were nine down transitions and nine matching up transitions, ending empty. The 150 rejected data transactions were not passed to the contact decoder; no SPI transfer errors or capture loss occurred.

This qualifies actual contact detection in the diagnostic path. It does not yet qualify a Linux touchscreen, visual coordinate orientation, a persistent driver or a cold integrated boot. Those are the immediate next steps, using this same RAM session where possible. All firmware, calibration, raw captures and identifying logs remain local.


### Linux input and visual mapping confirmed

A guarded RAM module now registers a direct Linux multitouch device with ten slots. Its decoder checks the complete native layout before emitting events, handles the observed 30-byte stride, inverts native Y using the validated J72 surface bounds, and releases absent contacts. A frame timeout releases outstanding slots. The same C decoder accepted all 1,801 captured reports and rejected malformed-layout test cases with undefined-behavior/bounds instrumentation enabled.

The first integration trial stopped on its diagnostic three-invalid-reply guard; firmware health and full hardware cleanup passed. A distinct bounded recovery trial releases contacts and checks firmware health, zero global flags and the active report gate before continuing, with a strict recovery limit. The visual test then recorded 21 presses and 21 releases, including simultaneous contacts. The owner confirmed that all targets and traces worked at the correct on-screen positions. This qualifies Linux input and screen mapping in the live RAM session. Compositor interaction, keyboard entry and integrated cold boot remain separate checks.


### Desktop menus and application launch confirmed

The owner opened Omarchy A menus and launched Foot using the touchscreen. The compositor now explicitly enables both DRM and libinput backends (`WLR_BACKENDS=drm,libinput`); the previous display-only setting excluded input. Labwc logs confirm the touchscreen and GPIO keys were added, and its file descriptors show both evdev devices open. This also explains the earlier need for a Home userspace bridge, although the new native Home binding still needs a physical check.

A source-built, pinned wvkbd v0.20 keyboard with the existing Omarchy patch is now staged in RAM with a top-bar toggle. Its visible state and startup have been checked; owner text entry is the next test. A small Bash session controller is used because the minimal read-only desktop image lacks Python. The desktop remains a read-only USB-backed root with RAM state, rather than an installed system.


### On-screen typing confirmed

The owner confirmed that the on-screen keyboard works in Foot and its top-bar toggle works. Touch, desktop menu selection, application launch and text entry have now been exercised in one RAM boot. The keyboard binary and controller remain in temporary RAM storage; integrating reproducible startup and independently verifying it after a fresh boot are the next touch milestones. Native Home handling still needs an explicit physical confirmation. The owner is taking a charging break; no internal-storage work is authorized.


## Charging-break preparation after the touch milestone

The owner confirms the iPad is charging in iOS. A private 11.7 MB RAM bundle is built for the next owner-confirmed DFU. It adds an initramfs overlay while preserving the exact successful kernel, original boot image and original read-only desktop image. The overlay includes automatic touch start/stop/restart checks, a reusable worker, separate bounded anomaly buffers, corrected DRM/libinput startup, keyboard packaging, native Home binding and orderly teardown scripts.

The matching module builds without warnings under the additional kernel warning checks. The contact decoder accepts all 1,801 earlier native reports and passes malformed-input checks; six anomaly-ring tests and twenty existing audit tests pass. No device was contacted during preparation. These are offline results: the new worker, external-initramfs handoff and automatic desktop startup still need the next hardware test.

A read-only platform inventory and a guarded three-second backlight dim/restore tool are staged for later use in the same boot. They do not enable or qualify the J72 HDQ battery gauge, Linux charging or HSIC Wi-Fi. The next hardware gates and remaining storage prerequisites are in [the DFU plan](DFU-PLAN.md). No internal-storage installation is authorized.


## Integrated cold start and same-boot touch reuse

The private overlay booted with the exact previously successful kernel. Its automatic five-second touch self-check produced 151 valid native frames with no layout rejects, SPI errors, timeouts or recoveries. It stopped with firmware health and complete hardware restoration confirmed, then restarted touch and automatically launched the unprivileged desktop from the original read-only host image. The owner confirmed the wallpaper, menu, clock, pointer, working menus and draggable Foot window.

A subsequent longer cycle produced 29,540 valid wire frames and emitted 29,532 layouts. All eight rejected layouts were retained separately and contained contact state `1`, which the current decoder refuses; its meaning remains unassigned. There were three bounded recoveries, zero SPI errors and zero timeouts. Final firmware health, global status and full cleanup passed. Restarting the same loaded worker succeeded in this boot, and Labwc accepted the replacement input device automatically. Common rejected wire replies remain separate from these layout anomalies.

The keyboard initially required live corrections. Automatic input-method focus mode is now enabled. The owner confirms keyboard reopening and typing in both the new test terminal and the original Foot, and the top-bar icon closes it. A small experimental Foot tap patch was also tried, but its separate contribution has not been isolated because the stock terminal now works too. It remains optional. The revised automatic keyboard startup is packaged and checked offline; its next independent cold boot is still pending.

The owner confirmed native Home menu open/close and the guarded three-second brightness dim/restore. Brightness readback returned to the original 1604. The read-only inventory exposes the PMIC backlight but no battery or thermal telemetry. No charging or Wi-Fi success is claimed, and no internal storage has been written.


### End-of-session cleanup and battery preparation

The final reusable-worker cycle emitted 38,237 frames with no layout rejects, timeouts, recoveries or SPI errors. Rejected wire replies were filtered separately. Final firmware health and hardware restoration passed. Desktop shutdown revealed that Arch's udev daemon resolves to a different executable path; resolving the expected symlink fixed the PID check. The revised teardown then unmounted the original read-only root, detached NBD and stopped the owned host export successfully. A normal reboot to iOS was requested.

A passive J72 check found the inherited UART5 pad on peripheral function 1 and its power domain off; it sent no battery traffic. Saved J72 configuration distinguishes AP GPIO44 for UART5 from a separate PMU GPIO control, unlike the Air 2 reference wiring. An exact-board DT variant and bounded voltage-only reader are prepared for the next boot, preserving the kernel. The reader passed encoding, malformed-response and timeout tests using pseudo-terminals, plus a loader test and wrong-controller refusal in the live Arch environment. Actual gauge communication, exact identity, telemetry and charging remain unqualified. See the [next DFU checklist](DFU-PLAN.md).


## Battery transport identified; touch and keyboard recovered in one boot

The UART5 device-tree variant booted with the existing kernel. UART5 registered on the exact J72 controller and provided a tty while external USB debugging stayed available. A guarded 57,600-baud 8N2 diagnostic read the voltage registers three times: all returned 3,824 mV. Subsequent standard reads returned 41% charge, about 38.8°C and cycle count 419; a later sample returned 31% and 3,787 mV. Each diagnostic restored its UART settings. The volatile `DEVICE_TYPE` query returned `0x0545`, which [TI documents as BQ27545](https://www.ti.com/lit/ds/symlink/bq27545-g1.pdf). No gauge reset, unseal, authentication, firmware or NVM operation was used. The J72 PMU GPIO control stayed untouched.

Capacity and current interpretation still needs comparison with iOS. The gauge returned raw full capacity 1,362 and design capacity 8,557; this report does not infer physical battery health from that discrepancy. Linux power-supply integration and measured charging are separate remaining steps.

During the same boot, the original touch worker stopped after a stale reply to its read-only C8 status query. Firmware health, zero global status and hardware restoration subsequently passed. The stop predated the new Foot test window, so the initial keyboard result was confounded by missing input. A separately named revised worker retained all hardware and health guards, added at most three attempts for malformed read-only short replies, and restored input without reboot. Transport errors still stop immediately. Tests exercised the actual C read function under bounds instrumentation. The owner then confirmed repeat hide/tap/type; two Foot tap log entries and matching input-method callbacks independently recorded the path.

The revised worker emitted 11,708 frames with zero layout rejects, SPI errors, timeouts or recoveries, and passed final firmware health and full hardware restoration. The desktop/root unmounted, NBD detached and host export stopped before a normal reboot request. Automatic battery-interface integration and a cold test of the combined touch/Foot changes are being prepared while the device charges.

### Charging break: combined battery-kernel image prepared

The owner confirms iOS is visible and wall charging. A separate target-kernel build now contains the two-stop-bit serdev API and an HDQ/UART frontend derived from [the Air 2 work](https://github.com/mattonik/ipad-nixos/tree/b94d42f78e04c5465e290340a5b6879bbc5956b6). The J72 adaptation requires the exact board and previously measured BQ27545 identity. It permits only the volatile chip-identification write pair; no gauge reset, unseal, firmware, NVM or charger-control operation is enabled. It retains the reference's UART decoding and corrects command-echo matching to require a contiguous sequence.

The driver/API compiled, and extracted driver functions passed 512 encode/decode cases, 71 receive/chunk/noise cases and exhaustive checks of all 65,536 write pairs. The rebuilt touch module's imported symbols are present in the new kernel. The private combined image retains 4 KiB pages, packages the tested Foot/touch fixes and passes pinned-artifact preflight against the unchanged read-only desktop. It has a distinct kernel build identity; **none of these offline checks establishes that the new battery interface works on the iPad yet**.

The next charged RAM session will check Linux power-supply registration and plausible voltage, temperature, state of charge and current alongside automatic touch/keyboard startup. Signed desktop battery-service packages are also staged for a later same-boot userspace trial. A battery indicator, current/capacity interpretation and measured charging remain unqualified. No internal-storage write has been authorized.

## Linux battery interface and cold keyboard passed; charger return unresolved

The combined image booted and registered `j72-bq27545-battery`. Three initial samples reported 78%, 4.087–4.088 V, 34.6°C and approximately 0.74 A discharge on the Pi connection. Both USB network and serial shells responded. The owner confirmed repeated keyboard hide/tap/type after automatic startup, without live repairs.

A fixed read-only audit through the bound kernel transport explained the capacity discrepancy: compensated remaining/full values were approximately 1,111/1,487, agreeing with 75% state of charge. Linux's `charge_now` instead used the uncompensated value 5,801 while `charge_full` used the compensated full value. [TI documents these distinct capacity definitions](https://www.ti.com/lit/ds/symlink/bq27545-g1.pdf). A correction to that exported pairing is needed; these values do not establish physical battery health.

Final touch cleanup passed after 12,404 emitted frames, with zero SPI errors, timeouts or recoveries. One checksum-valid contact-state-1 layout was refused and retained for review; its meaning remains unassigned. The desktop/root unmounted, NBD detached and host export stopped normally before cable changes.

A recorder then ran entirely from RAM to observe the wall charger. USB descriptor requests failed when the device returned to the Pi. The owner subsequently reported a Pi hang during the cable/port change and restarted the host. The wall-charger log was not retrieved, and the preceding host crash journal is unavailable. **This does not establish Linux charging or its failure; charging and USB reconnection remain unresolved.** The next test needs visible readings and local recovery in addition to RAM logging. No charger-control, battery-NVM or internal-storage write was made.

### Revised diagnostic image prepared

A new target-kernel image now selects compensated remaining capacity for this exact J72/BQ27545, pairing it with compensated full capacity. Six tests of the actual C selection branch cover J72 and preserved behavior on other chips/boards. The RAM kernel log grows from 128 KiB to 8 MiB to retain startup evidence; the working SPI code and register accesses are unchanged.

Manual diagnostic tools now display battery readings and current-sign colours on the active text console, retain the RAM log and offer at most three separately requested Home-button USB rebinds after full desktop/NBD/input teardown. Eleven tests cover the actual Home-event decoder, and the static helper refuses the non-J72 host. The kernel/module build, shell checks and full artifact preflight passed. **The visible console and recovery action are not yet device tested.** The recovery candidate is not evidence that the USB or Pi-hang problem is fixed.

The next wall-charger observation will use screen readings/photos and return to iOS while still on the charger before another Pi connection. Live Linux USB return, charger policy/limits and the cause of the host hang still need qualification. The Pi kernel and original desktop image remain unchanged.

### Revised image tested: capacity pairing and visible recorder passed

The revised kernel booted with the expected build identity, registered the guarded battery driver and retained its startup identity log. At startup, compensated remaining and full capacity both read 1,520,000 µAh, agreeing with 100% state of charge. Later readings of 1,359,000 / 1,520,000 µAh agreed with 90%. This validates the corrected pairing in this run; it does not establish physical battery health. The gauge initially reported `Full` while measured current was negative, so that status alone must not be interpreted as active charging.

Automatic touch self-check, full cleanup, restart and desktop startup passed. The second touch session emitted 2,619 frames with zero layout rejects, SPI errors, timeouts or recoveries. Final firmware health and complete hardware restoration passed. The desktop/root unmounted, NBD detached and the host export stopped before USB tests.

The owner confirmed the red live readings screen and an advancing uptime counter. The first physical Home request rebound the USB gadget and restored network collection without new host USB descriptor errors. A serial-shell check then failed, and subsequent network traffic also stopped responding. This sequence does not establish the cause. The second Home request restored network access; four successive network queries over 30 seconds passed without opening serial. Thus local USB recovery is **partial**, not a demonstrated fix for both debugging paths or the earlier host hang.

A fresh RAM recorder now reports voltage, current, temperature and percentage on screen. Its Pi baseline was 90%, 4.053 V, approximately −744 mA and 34.9°C. The Home recovery watcher was stopped so it cannot change USB state during the wall measurement. The owner has been asked for screen readings/photos after about one and five minutes on the usual wall charger, leaving Linux running and the iPad on that charger. Results are pending; **no Linux wall-charging success is claimed**. Return to iOS on the charger is required before another Pi connection in this trial. No charger-control, battery-NVM or internal-storage write was made.

### Wall-charger photos: net discharge observed

The owner supplied two screen photos and explicitly confirmed both were taken while connected to the wall charger, after disconnecting from the Pi. Ordered by displayed uptime, the readings are:

| Uptime | Battery | Voltage | Current | Temperature | Status |
| --- | --- | --- | --- | --- | --- |
| 1,017.95 s | 88% | 4,046 mV | −743 mA | 34.0°C | Discharging |
| 1,179.34 s | 86% | 4,037 mV | −746 mA | 34.5°C | Discharging |

The 161.39-second interval shows **net battery discharge on the wall charger in this Linux session**. It does not identify the missing charger/source-control behavior or establish a full charger policy. The screen continued to say USB `configured` after the physical change; that value does not prove current source detection. The complete wall RAM log has not been retrieved. No charger control was changed. The owner returned to iOS while the iPad stayed on the wall charger and confirmed that iOS is visible and charging. The photos and identifying raw evidence remain private.

### Next read-only charger capture prepared

Static analysis of the exact J72 driver confirms separate paths for USB input suspend, USB input-current ceiling and battery charge current. The J72 configured battery-current ceiling getter also reads a different register from the Air 2 reference, so that related model's register list cannot be copied unchanged. These findings identify what to measure; they do not establish the inherited hardware state or the cause of the discharge.

A module now built against the existing target kernel exposes a root-only snapshot of 18 fixed PMIC registers through the already-bound regmap, bypassing cached values. It has no charger writes, raw I²C calls, timers or background worker. A manually staged RAM recorder adds these raw fields to the visible battery screen and recording. Native module compilation, imported-symbol checks, shell syntax and pinned-artifact preflight passed. **This observer has not been device tested.** The next charged DFU can reuse the current kernel and original read-only desktop, then load the observer after full desktop/NBD/input teardown. Serial access and Home USB recovery are excluded from that measurement; return to iOS on the wall charger before any Pi attachment remains the procedure.

### Read-only observer device test passed; wall comparison pending

A fresh RAM boot reused the current kernel and passed automatic input/desktop startup. Final touch shutdown passed with 1,778 emitted frames, zero layout rejects, SPI errors, timeouts or recoveries, and complete hardware restoration. The desktop/root, NBD and owned host export were detached before loading the observer.

The exact-board observer loaded and read all 18 permitted registers. The initial Pi snapshot reports input-suspend bit 2 clear at `0x0010`, input-limit code `0x02` at `0x04c0` (about 100 mA nominal), and `0x3f` at active battery-current register `0x04c6` and both ceiling registers `0x04c7`/`0x04ce`. The latter codes correspond to 3,150 mA settings, **not measured charging current**. The RAM-only baseline remained about −741 mA, 4.07 V, 91% and 34.6°C.

The visible recorder now includes raw PMIC fields. The owner has been asked to check that block is readable, then photograph it after about one and five minutes on the usual wall charger. That comparison is pending; the low Pi input setting alone does not establish the cause of the earlier wall discharge or the wall source's capability. No charger settings, ADC controls, charge timers or GPIOs were changed, and no serial connection or Home recovery is part of this trial. Return to iOS on the charger before any Pi attachment remains required.

### Wall comparison received: 100 mA input-limit setting persists

The owner supplied the PMIC-screen photos and explicitly confirmed both were on the wall charger. The displayed sample times are 277.17 and 381.51 seconds, an interval of 104.34 seconds; these are two observations, not a verified five-minute interval. The corresponding PMIC timestamps advance as well.

| Observation | Battery | Voltage | Current | Temperature |
| --- | --- | --- | --- | --- |
| First wall photo | 89% | 4,056 mV | −742 mA | 34.5°C |
| Second wall photo | 87% | 4,050 mV | −743 mA | 34.6°C |

All 18 observed PMIC values match the Pi baseline, including `0x0010 = 0x00`, `0x04c0 = 0x02`, and `0x04c6`/`0x04c7`/`0x04ce = 0x3f`. Thus the nominal 100 mA input ceiling persisted on the wall charger while input suspend was clear and the battery-current setting remained nonzero. The latter is a setting, not measured battery charge current. The screen's USB `configured` value is not source-capability evidence.

This makes input-current policy/source detection the concrete next investigation. It does not yet establish that changing the ceiling will restore net charging, and actual USB input power has not been measured. No register setting was changed. The owner has been asked for the charger's output rating and to return to iOS while staying on the wall charger; those replies are pending. The next control experiment must use a bounded limit, telemetry checks and verified restoration, selected for the known source.

### Bounded input-limit comparison prepared

The owner confirms the iPad has returned to iOS and is charging. The charger is a USB socket built into a powerboard; its label is too unclear to establish its output rating. The next experiment therefore contains only one fixed 425 mA attempt, with no higher-current step.

An external module for the unchanged target kernel now restricts writes to the exact J72 USB input-limit register, using only the original 100 mA code and the 425 mA trial code. Loading and arming write no PMIC register. After the desktop/input/export are detached and the owner confirms wall attachment, one physical Home press can start the trial. Battery voltage, temperature, presence, percentage and current are checked. A separate kernel queue schedules restoration after 30 seconds and verifies readback; failed or ambiguous writes also trigger restoration. A sticky failure blocks further trials. Software restoration cannot guarantee recovery from a stalled kernel or PMIC bus.

Native compilation with additional warnings passed, and all 46 imported symbols exist in the exact target kernel. Tests exercise the actual shared policy core: 15 normal/failure scenarios and 10 battery-guard cases passed with undefined-behavior checks. Recorder syntax and pinned-artifact preflight also passed. **These are offline results; the control module and restoration have not been device tested.** The RAM screen retains trial samples and restoration status for photographs. No higher-current step, battery-current control, charge-timer reset, ADC start, GPIO change, battery NVM operation or internal-storage write is included.

Success in this comparison means acknowledged setting change, a measured battery-current response and verified restoration, assessed separately. It may reduce net discharge without producing net charging. Sustained charging, source detection/protection and the later desktop regression remain required before B04C can pass.

### Current boot: module loading and visible unarmed screen passed

The existing DFU connection was verified as J72 and reused without another button sequence. The unchanged RAM image passed automatic desktop startup. Battery telemetry initially reported 100%, about 4.06–4.08 V, 34.5°C and negative battery current. Desktop/root, input and NBD export stopped cleanly: 2,362 emitted frames, zero layout rejects, SPI errors, timeouts or recoveries, and successful firmware health/hardware restoration.

Both diagnostic modules loaded successfully. The new module reported ready, unarmed and unused, and readback retained the original nominal 100 mA input setting. The owner confirms those values are visible on the comparison screen. No charger control has been written. The same RAM boot is waiting for the battery to enter the test's maximum 95% guard before arming; the current-change and restoration sequence remains untested. One transient descriptor error at USB attachment recovered without a reset. Serial access and live Linux charger-to-Pi return are still excluded.

### Wall control test: 425 mA acknowledged, discharge reduced, restoration verified

After the pause, the same RAM boot remained healthy at 83% and 35.7°C. The stopped recorder's files were preserved, its pinned RAM script restarted, and arming passed without changing the original input setting. The owner moved to wall power and confirmed the screen's uptime continued advancing. One physical Home press triggered the single trial. Active-phase photographs show the 425 mA input-limit code and an active trial; the kernel message also reports successful setting verification.

The final photograph retains the comparison:

| Phase | Nominal USB input-limit setting | Battery current |
| --- | --- | --- |
| Before trial | 100 mA | −764 mA |
| During trial | 425 mA | −423 to −400 mA across 12 retained samples |
| After automatic restoration | 100 mA | −767 mA |

The final screen reports `used=1`, `active=0`, `restored=1`, `restore_failed=0`, `error=0`, with actual input-register readback back at the original code. It also shows 78%, 3.955 V and 35.3°C. The exact restoration instant was not photographed; the module's completion state and the independent register snapshot verify the restored result. The complete wall RAM log was not retrieved.

This reversible response supports a substantial input-limit contribution to the discharge: its magnitude fell by approximately 45–48% during the trial. It does not measure actual USB input current. **Net battery current remained negative throughout the retained samples, so Linux charging has not passed.** No higher-current step, charge-timer reset, GPIO/ADC change, battery NVM operation or internal-storage write was performed.

The owner returned to iOS while keeping the iPad on the charger and confirmed iOS is visible and charging. The next experiment requires a USB source with a readable output rating before selecting a higher bounded setting. The powerboard's blurred label remains unconfirmed. Charging policy/source detection, sustained net charging and the later desktop regression remain open.

### Next test prepared: 850 mA with the separate 5 V / 1 A charger

The owner supplied a separate USB charger photograph and explicitly confirmed its 5 V / 1 A label rating. This establishes the stated rating for the planned test; actual source capacity has not been independently measured. The next comparison will use this specific charger for the baseline, trial and restored readings. The earlier powerboard's rating remains unconfirmed.

An isolated variant preserves the successful 425 mA artifacts and changes the fixed trial target to nominal 850 mA, 150 mA below the source's stated maximum. The one-attempt policy, 30-second timer, independent rollback queue and battery guards remain the same. Source-specific arming is required, and physical Home triggering happens only after the owner confirms the wall connection. Loading and arming perform no PMIC writes. The existing target image, read-only desktop and Pi kernel are unchanged.

Native compilation with additional warnings passed, with the same 46 exact-kernel imports as the measured variant. The actual policy core passed 15 normal/failure cases, 10 battery-guard cases and four fixed encoding/timer assertions. Two incorrect source-flag invocations were rejected before device contact. Shell/Python syntax and pinned-artifact preflight passed; the original 425 mA artifact preflight also remains intact. **The 850 mA experiment has not been device tested.**

One new DFU will cover baseline, the single 850 mA trial, restored-state photographs and return to iOS on the charger. A positive reading would demonstrate short observed net charging; sustained charging, source policy/protections and the later desktop regression remain separate qualification gates.

### Interim upstream report opened

[Draft Orchard PR #43](https://github.com/OrchardLinux/orchard/pull/43) adds the J72 field report and a README link, following the current CONTRIBUTING.md guidance for bring-up material. It records verified display, touch, Home, brightness, keyboard, battery and the reversible charging result, with kernel provenance and physical-test limits. The two-file contribution contains no runtime/device-profile changes or private inputs. Production driver/DT/firmware-recipe integration remains future work.

The submitted commit is `c6c08694862b5a18bba71535c6b5f3895fe8434a`. All 362 Orchard tests passed in an isolated editable installation with normal file permissions; local link, whitespace, evidence and publication-scope checks passed. The report describes the identified lab image’s earlier physical tests; this documentation revision was not newly booted on the device. The ready 850 mA test remains unrun while work shifted to this interim contribution.

### Working implementation sources published for reuse

The [code directory](code/README.md) now contains the measured S5L SPI source and exact baseline delta, full touch worker and decoder, HDQ/UART battery frontend and serdev/build/capacity patches, the read-only PMIC observer and 425 mA worker, and desktop keyboard/Foot changes. Original source notices, provenance and component licenses are preserved. Firmware/calibration includes, raw captures, images and prebuilt modules are excluded. An owner-local renderer accepts already-framed private packets; it does not claim firmware extraction or recipe completeness.

The public test runner exercises actual HDQ functions with 512 encode/decode cases, 71 echo/chunk/noise cases and all 65,536 write pairs, alongside touch bounds, 15 rollback cases, 10 battery guards and four private-input helper tests. All pass. Five kernel components also pass ARM64 W=1 compilation against the measured kernel, using its real exported-symbol records. SPI/keyboard patch round trips and battery/Foot reverse checks pass. No newly built module was loaded and no hardware was contacted during publication checks.

At the owner's request, PR #43 is back in draft with review on hold. The [implementation plan](code/UPSTREAM-PLAN.md) identifies the native Orchard work before resubmission. Its newer kernel, match-data/binding requirements, normal resource ownership and private-input recipes still need integration and exact-revision testing. The code release makes the working development sources available now without representing that integration as complete.

## Working hardware code added to draft Orchard PR #43

At the owner's request, [PR #43](https://github.com/OrchardLinux/orchard/pull/43/files) now includes the actual hardware development implementation at commit `fb22beb94995e216b7b14c6a535dd41e6817bed5`: full SPI correction/baseline, touch worker/decoder, battery frontend/support patches, read-only observer, tested 425 mA worker, synthetic tests and provenance/licenses. The source is under `experiments/j72/` and is inactive in Orchard's builds. Desktop code remains here for a separate omarchy-a change.

The PR remains draft. All 362 Orchard unit tests and the copied source's offline checks passed. Firmware/calibration/generated includes/binaries/raw captures stay private. Normal driver/DT/recipe/host integration and device testing of that integrated revision remain required; this code snapshot does not make J72 a supported Orchard device. The prepared 850 mA comparison remains untested at this publication point.

## 850 mA wall comparison: brief net charging observed

One 30-second, single-attempt test on the separate owner-rated 5 V / 1 A
charger changed the nominal input limit from 100 mA (`0x04c0 = 0x02`) to
850 mA (`0x3e`). The USB-backed desktop/root and touch worker were stopped
before the cable move. The owner confirmed advancing uptime on that charger
and pressed Home once after the baseline interval.

| Phase | Battery current |
| --- | --- |
| Same-source baseline | -766 mA |
| Trial, 12 retained samples | **+20 to +51 mA** |
| After automatic restoration | -765 mA |

The active photo shows the green screen, `Charging` and `0x04c0 = 0x3e`.
The final photo shows `used=1`, `active=0`, `armed=0`, `restored=1`,
`restore_failed=0`, `error=0`, and `0x04c0 = 0x02`. Temperature in the two
photos is 34.9 and 35.1 degrees C; reported charge stays at 91%. The owner
then confirmed iOS is visible and charging on the same wall source.

This demonstrates brief positive **net battery current**, with verified
restoration. It does not qualify sustained charging, a charge-level trend,
source detection, protections or desktop charging. Actual USB input current
and supply capacity were not measured; the exact restoration instant was
not photographed, and the full wall RAM log was not retrieved. Raw photos
remain private. The source snapshot still contains the tested 425 mA worker;
the 850 mA variant used for this result is not bundled in that snapshot.

Next: implement source-aware bounded charging, qualify a longer guarded
measurement and recovery, then proceed to Wi-Fi. No internal-storage writes
or host-kernel changes were performed.

## Powered hub identified and iOS charging/data verified

The owner-confirmed JCH377 with a 5 V / 4 A adapter enumerates as self-powered.
The iPad is reachable through its marked charging port at 480 Mbit/s; pairing
and three diagnostic reads pass while iOS reports charging and a 5 V / 1.5 A
adapter allowance. Actual USB current and the precise detection protocol were
not independently measured. The owner reports a Pi hang during changes to
only hub/iPad cables; the SSD stayed connected. The cause is unresolved
because the previous boot's journal was not retained.

A separate hub-source 850 mA / 30-second worker and source-gated host helper
are prepared; native build and policy/topology/refusal tests pass. No Linux
hub current trial has run yet, no charger setting was changed during this
preparation, and the next test keeps all cables fixed. See
[the Pi charging plan](PI-CHARGING-PLAN.md).

## First powered-hub boot attempt: download handoff did not return

The exact J72 DFU identity and pinned assets passed. One isolated checkra1n
attempt reported successful exploit setup and Checkmate, but no download-mode
USB device reappeared within the loader's 20-second wait. The launcher stopped
and reaped its whole process group. Pongo and Linux did not start; the hub
charging worker never loaded and no charging control was written.

Normal iOS recovery has been requested on the same hub connection. The
prepared next control uses the existing launcher's narrow, dynamically
discovered iPad-port reconnect after Checkmate, matching the loader's stated
replug workaround. Only the target port would be cycled, before Linux starts.
This control has not run on this Pi/hub setup, and an unchanged DFU retry is
not planned. The hub's iOS charging/data result remains separate from Linux
boot and charging qualification.

## Second hub boot control stopped before Pongo

The exact-iPad-port reconnect completed off/on and restored power, but the
loader again timed out waiting for download mode after Checkmate. Its full
process group was reaped; no Pongo, Linux or charging worker ran. The owner
confirmed recovery to iOS on the hub.

A direct-Pi boot followed by a one-shot RAM USB handoff is prepared. It
requires clean desktop/root/NBD/input teardown before unbinding, then an
owner move to the powered hub and one Home-triggered rebind. Charging is
gated on live data and completed handoff; no current write occurs during
the transfer. See [the revised plan](PI-CHARGING-PLAN.md).

## Direct RAM boot and powered-hub data handoff passed

The final direct-connected DFU boot reached Pongo and the unchanged #33
Linux image. Automatic desktop/touch startup passed. Healthy teardown
retained 2,807 native frames, zero layout rejects/SPI errors/timeouts/
recoveries, and successful firmware health and restoration. Root/NBD/export
were detached before the cable move.

The owner moved to the powered JCH377 marked port and pressed Home once.
The one-shot gadget rebind completed; the native NCM shell now responds
through the hub with the exact model/kernel, `REBOUND` status and the
transfer process exited. The separately guarded 850 mA worker is staged
unarmed at the original 100 mA input setting. The current comparison has
not yet run.

Current Orchard main was reviewed for reuse; see
[the integration notes](ORCHARD-POWER-PLAN.md). No driver/mux/source-detection
change was made to the running kernel.
