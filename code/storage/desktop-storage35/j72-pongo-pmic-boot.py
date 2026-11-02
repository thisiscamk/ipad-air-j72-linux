#!/usr/bin/env python3
"""Boot a hash-pinned, RAM-only J72 diagnostic image from exact Pongo USB."""
import fcntl
import argparse
import hashlib
import os
import pty
import select
import signal
import subprocess
import time
import tty
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "private/j72-touch/m1n1-j72-pmic-readonly.bin"
SHA256 = "06ee2329d11b7e9c5b5d6d9c79131358c05fa5a30f0cc8d5b7baedf47eb09cff"
LOG = ROOT / "private/j72-touch/j72-pmic-readonly-pongoterm.log"
VOLTAGE_PAYLOAD = ROOT / "private/j72-touch/m1n1-j72-pmic-voltage-readonly.bin"
VOLTAGE_SHA256 = "03b1159e678d9b93ddf3c340fc10a3076f1bfdfc4b290c846ae4e659d6a8b002"
VOLTAGE_LOG = ROOT / "private/j72-touch/j72-pmic-voltage-readonly-pongoterm.log"
PWM_PAYLOAD = ROOT / "private/j72-touch/m1n1-j72-pwm0-observer.bin"
PWM_SHA256 = "8985a27208587547802e8c3a62b8a76ecc8f37a1dde9803825bef42c2ba945b3"
PWM_LOG = ROOT / "private/j72-touch/j72-pwm0-observer-pongoterm.log"
DRAIN_PAYLOAD = ROOT / "private/j72-touch/m1n1-j72-spi-drain-observer.bin"
DRAIN_SHA256 = "47388a15d831bb47832a1e4a9b8cb0e672c3dba52c5e4e011e804ee1d5123bec"
DRAIN_LOG = ROOT / "private/j72-touch/j72-spi-drain-observer-pongoterm.log"
MATRIX_PAYLOAD = ROOT / "private/j72-touch/m1n1-j72-spi-status-matrix.bin"
MATRIX_SHA256 = "ca9593e0871b661e593a9b35fe743dc5b8773cdb6b8b8b996f9eb12b1424bdd2"
MATRIX_LOG = ROOT / "private/j72-touch/j72-spi-status-matrix-pongoterm.log"
RX_DRAIN_PAYLOAD = ROOT / "private/j72-touch/m1n1-j72-spi-rx-drain.bin"
RX_DRAIN_SHA256 = "83e8d111e63a9ce4ae6ea463147f74c90b8469629549e9013075f2d3bc9f7bf3"
RX_DRAIN_LOG = ROOT / "private/j72-touch/j72-spi-rx-drain-pongoterm.log"
RX_WINDOW_PAYLOAD = ROOT / "private/j72-touch/m1n1-j72-spi-rx-window.bin"
RX_WINDOW_SHA256 = "d2472035d461ea6b33e78fa2c4d50ff27c0e066b021be9182d126a52b1716418"
RX_WINDOW_LOG = ROOT / "private/j72-touch/j72-spi-rx-window-pongoterm.log"
HALF_PRIME_PAYLOAD = ROOT / "private/j72-touch/m1n1-j72-spi-rx-half-prime.bin"
HALF_PRIME_SHA256 = "f0273ebf91996e4921c6737c167de52686c26f50aa5ed12064a1586c39726755"
HALF_PRIME_LOG = ROOT / "private/j72-touch/j72-spi-rx-half-prime-pongoterm.log"
ZERO_PRIME_PAYLOAD = ROOT / "private/j72-touch/m1n1-j72-spi-rx-zero-prime.bin"
ZERO_PRIME_SHA256 = "8968cb42946b427db87827f13ac3fffedd22118b0a0ff1128a41fa5d2d065847"
ZERO_PRIME_LOG = ROOT / "private/j72-touch/j72-spi-rx-zero-prime-pongoterm.log"
ONE_PRIME_PAYLOAD = ROOT / "private/j72-touch/m1n1-j72-spi-rx-one-prime.bin"
ONE_PRIME_SHA256 = "98588e3bf62695bcb25df5940fd3e50a29ff9a05f23c85dc2a59c5b077de7d26"
ONE_PRIME_LOG = ROOT / "private/j72-touch/j72-spi-rx-one-prime-pongoterm.log"
TXCNT_OBSERVE_PAYLOAD = ROOT / "private/j72-touch/m1n1-j72-spi-txcnt-observe.bin"
TXCNT_OBSERVE_SHA256 = "3dc3200a92ce314119c77d0053409fc3f93f8da4e393904918b9e64192cf7c8d"
TXCNT_OBSERVE_LOG = ROOT / "private/j72-touch/j72-spi-txcnt-observe-pongoterm.log"
FINAL_BYTE_PAYLOAD = ROOT / "private/j72-touch/m1n1-j72-spi-final-byte-clock.bin"
FINAL_BYTE_SHA256 = "4924d18b6b20c367c56f09926be9f7e7a474e3d45717d221270ff503974bb3a8"
FINAL_BYTE_LOG = ROOT / "private/j72-touch/j72-spi-final-byte-clock-pongoterm.log"
FF_FILLER_PAYLOAD = ROOT / "private/j72-touch/m1n1-j72-spi-ff-filler.bin"
FF_FILLER_SHA256 = "122a5c18f1cb247a88323fa8640d21e47ddc92c50f7a2cc1296d7d3ef88af968"
FF_FILLER_LOG = ROOT / "private/j72-touch/j72-spi-ff-filler-pongoterm.log"
IN_WINDOW_FF_PAYLOAD = ROOT / "private/j72-touch/m1n1-j72-spi-in-window-ff.bin"
IN_WINDOW_FF_SHA256 = "4bb3fe4ea906e39350ca3a69899a3348015b851b11bca986dac8716a44165ed7"
IN_WINDOW_FF_LOG = ROOT / "private/j72-touch/j72-spi-in-window-ff-pongoterm.log"
IOS_PIO_MODE_PAYLOAD = ROOT / "private/j72-touch/m1n1-j72-spi-ios-pio-mode.bin"
IOS_PIO_MODE_SHA256 = "c6e2f27927d1cb65b6dbefcd7db96e3abeaebe8f65c06f69e25a27112b0da4f2"
IOS_PIO_MODE_LOG = ROOT / "private/j72-touch/j72-spi-ios-pio-mode-pongoterm.log"
ATOMIC_RUN_PAYLOAD = ROOT / "private/j72-touch/m1n1-j72-spi-atomic-run.bin"
ATOMIC_RUN_SHA256 = "8ae7edbf370cdb78ae56a3213ddbcd7555eb696d58c6daa89f81458eb6e329f9"
ATOMIC_RUN_LOG = ROOT / "private/j72-touch/j72-spi-atomic-run-pongoterm.log"
PRIME_RETENTION_PAYLOAD = ROOT / "private/j72-touch/m1n1-j72-spi-prime-retention.bin"
PRIME_RETENTION_SHA256 = "442ef784c9aabaf2ad0ac724dcd3e078fb31b5dbf3eecda901118ddbc51ad987"
PRIME_RETENTION_LOG = ROOT / "private/j72-touch/j72-spi-prime-retention-pongoterm.log"
PRIME_REPLAY_PAYLOAD = ROOT / "private/j72-touch/m1n1-j72-spi-prime-replay.bin"
PRIME_REPLAY_SHA256 = "e4ddb40d6b3e8c0085cb82b92c1478934e738415245fbbe651196dfcb69496f0"
PRIME_REPLAY_LOG = ROOT / "private/j72-touch/j72-spi-prime-replay-pongoterm.log"
LONG_RX_PAYLOAD = ROOT / "private/j72-touch/m1n1-j72-spi-long-rx-capture.bin"
LONG_RX_SHA256 = "ab3ee2db099b43b6b9513fa46f29b32e87c03c3527099a0d82a21b8a438978d7"
LONG_RX_LOG = ROOT / "private/j72-touch/j72-spi-long-rx-capture-pongoterm.log"
LONG_AUTO_RX_PAYLOAD = ROOT / "private/j72-touch/m1n1-j72-spi-long-auto-rx.bin"
LONG_AUTO_RX_SHA256 = "2aa079fd218e849c9659e80dc586ec4548c0522b6fafb06684b27f158ded5cd6"
LONG_AUTO_RX_LOG = ROOT / "private/j72-touch/j72-spi-long-auto-rx-pongoterm.log"
TOUCH_SESSION_PAYLOAD = ROOT / "private/j72-touch/m1n1-j72-touch-session.bin"
TOUCH_SESSION_SHA256 = "20cc7ab3529d5cdfbeba27e524d78e51a7b17ede711e536dd0466ae8f9579b28"
TOUCH_SESSION_LOG = ROOT / "private/j72-touch/j72-touch-session-pongoterm.log"
BATTERY_UART_PAYLOAD = ROOT / "private/j72-platform/battery-uart/m1n1-j72-battery-uart.bin"
BATTERY_UART_SHA256 = "bffa4a62c6d46dd1e497381336c0850d013f9dc1e289710cfee3933dc7aa7d0c"
BATTERY_UART_LOG = ROOT / "private/j72-touch/j72-battery-uart-pongoterm.log"
BATTERY_GAUGE_PAYLOAD = ROOT / "private/j72-platform/kernel-battery/m1n1-j72-battery-gauge.bin"
BATTERY_GAUGE_SHA256 = "9b46395e9d175dbac00f244465886a6eedd96503864117cfbe71a56532803ea4"
BATTERY_GAUGE_LOG = ROOT / "private/j72-touch/j72-battery-gauge-pongoterm.log"
CONTINUOUS_TOUCH_PAYLOAD = ROOT / "private/j72-platform/continuous-desktop/m1n1-j72-continuous-desktop.bin"
CONTINUOUS_TOUCH_SHA256 = "25474ed8211e17b705fc181b977320b7e6994b03a4ef4153cdd4c0f44fa9b3ce"
CONTINUOUS_TOUCH_LOG = ROOT / "private/j72-touch/j72-continuous-desktop-pongoterm.log"
WIFI_DESKTOP_PAYLOAD = ROOT / "private/j72-platform/wifi-desktop/m1n1-j72-wifi-desktop.bin"
WIFI_DESKTOP_SHA256 = "e65d20bd457746ece3b00f83cc74f7b5a8fa03333ff6b3f13dd91f43a0c1ca54"
WIFI_DESKTOP_LOG = ROOT / "private/j72-touch/j72-wifi-desktop-pongoterm.log"
WIFI_V3_PAYLOAD = ROOT / "private/j72-platform/wifi-desktop-v3/m1n1-j72-wifi-v3.bin"
WIFI_V3_SHA256 = "fb7c240e97e0b08ebfe775e5d9b54e430cea46ae3908f0bc92a7778a815a5030"
WIFI_V3_LOG = ROOT / "private/j72-touch/j72-wifi-v3-pongoterm.log"
WIFI_RAM_PAYLOAD = ROOT / "private/j72-platform/wifi-ram-desktop/m1n1-j72-wifi-ram.bin"
WIFI_RAM_SHA256 = "fc7aa12caa84166649ce552248a8f9bd5d10dbf06eca9b598df7421ef9d013ea"
WIFI_RAM_LOG = ROOT / "private/j72-touch/j72-wifi-ram-pongoterm.log"
STORAGE35_PAYLOAD = ROOT / "private/j72-platform/power-storage-20261102/storage-observer35/payload/out/apple-4k/linux.bin"
STORAGE35_SHA256 = "a132327742bf7942c1bbccdc8a38e0039921209edbbc31dada860d41e1dd5661"
STORAGE35_LOG = ROOT / "private/j72-touch/j72-storage-observer35-pongoterm.log"
DESKTOP_STORAGE35_PAYLOAD = ROOT / "private/j72-platform/power-storage-20261102/desktop-storage35/payload/out/apple-4k/linux.bin"
DESKTOP_STORAGE35_SHA256 = "4d4395c8baf965bbb7938bea5b8db49cae98802d0cd4841e5c92587fac8cdd11"
DESKTOP_STORAGE35_LOG = ROOT / "private/j72-touch/j72-desktop-storage35-pongoterm.log"
EXPLICIT_ALL_PAYLOAD = ROOT / "private/j72-touch/m1n1-j72-spi-explicit-poll-all.bin"
EXPLICIT_ALL_SHA256 = "5885425d85411f27ba1f2bee83a709c7831be94e09f0294d883d497200a29b69"
EXPLICIT_ALL_LOG = ROOT / "private/j72-touch/j72-spi-explicit-all-pongoterm.log"
PONGOTERM = ROOT / "tools/host/aarch64/bin/pongoterm"


def read_until(master, logfd, marker, seconds):
    deadline = time.monotonic() + seconds
    seen = bytearray()
    while marker not in seen:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(f"Pongo response timed out waiting for {marker!r}")
        if not select.select([master], [], [], remaining)[0]:
            raise TimeoutError(f"Pongo response timed out waiting for {marker!r}")
        block = os.read(master, 4096)
        if not block:
            raise RuntimeError("Pongo console closed")
        os.write(logfd, block)
        seen.extend(block)
        if len(seen) > 32768:
            raise RuntimeError("Pongo response too long")
    return bytes(seen)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--voltage-readonly", action="store_true",
                        help="boot the second, 0x398 read-only PMU image")
    parser.add_argument("--pwm0-observer", action="store_true",
                        help="boot the J72 PWM0 power-domain observer image")
    parser.add_argument("--spi-drain-observer", action="store_true",
                        help="boot the J72 SPI final-drain diagnostic image")
    parser.add_argument("--spi-status-matrix", action="store_true",
                        help="boot the J72 short/medium SPI status comparison image")
    parser.add_argument("--spi-rx-drain", action="store_true",
                        help="boot the isolated J72 S5L RX FIFO drain image")
    parser.add_argument("--spi-rx-window", action="store_true",
                        help="boot the isolated J72 S5L bounded RX window image")
    parser.add_argument("--spi-rx-half-prime", action="store_true",
                        help="boot the isolated J72 S5L half-prefill RX window image")
    parser.add_argument("--spi-rx-zero-prime", action="store_true",
                        help="boot the isolated J72 S5L zero-prefill RX window image")
    parser.add_argument("--spi-rx-one-prime", action="store_true",
                        help="boot the isolated J72 S5L one-word prefill RX window image")
    parser.add_argument("--spi-txcnt-observe", action="store_true",
                        help="boot the isolated J72 S5L TX completion counter observer")
    parser.add_argument("--spi-final-byte-clock", action="store_true",
                        help="boot the isolated J72 S5L residual TX byte correction")
    parser.add_argument("--spi-ff-filler", action="store_true",
                        help="boot the isolated J72 S5L iOS-style 0xff filler test")
    parser.add_argument("--spi-in-window-ff", action="store_true",
                        help="boot the isolated J72 S5L full-RXCNT in-window filler test")
    parser.add_argument("--spi-ios-pio-mode", action="store_true",
                        help="boot the isolated J72 S5L iOS PIO mode-bit diagnostic")
    parser.add_argument("--spi-atomic-run", action="store_true",
                        help="boot the isolated J72 S5L combined reset/RUN diagnostic")
    parser.add_argument("--spi-prime-retention", action="store_true",
                        help="boot the isolated J72 S5L reset-release FIFO retention diagnostic")
    parser.add_argument("--spi-prime-replay", action="store_true",
                        help="boot the isolated J72 S5L uncounted-prime packet replay diagnostic")
    parser.add_argument("--spi-long-rx-capture", action="store_true",
                        help="boot the isolated J72 S5L bounded long full-duplex capture test")
    parser.add_argument("--spi-long-auto-rx", action="store_true",
                        help="boot the bounded long full-duplex capture with AUTO_TX enabled")
    parser.add_argument("--spi-pad-sample", action="store_true",
                        help="boot the validated RAM image for manual reset-held GPIO pad sampling")
    parser.add_argument("--touch-session", action="store_true",
                        help="boot reusable J72 touch and automatic read-only desktop overlay")
    parser.add_argument("--battery-uart", action="store_true",
                        help="boot J72 UART5 descriptor with integrated touch/desktop; no battery traffic")
    parser.add_argument("--battery-gauge", action="store_true",
                        help="boot new J72 battery-gauge kernel with integrated touch and desktop")
    parser.add_argument("--continuous-touch", action="store_true",
                        help="boot #33 continuous touch, battery widget and reduced initial brightness")
    parser.add_argument("--wifi-desktop-v3", action="store_true",
                        help="boot recovery-complete #34 with opt-in J72 HSIC firmware transport and brighter display")
    parser.add_argument("--wifi-ram-desktop", action="store_true",
                        help="boot #34 repeat candidate with serial respawn and deferred RAM desktop staging")
    parser.add_argument("--desktop-storage35", action="store_true",
                        help="boot the combined #35 opt-in desktop/Wi-Fi/read-only storage candidate")
    parser.add_argument("--storage-observer35", action="store_true",
                        help="boot #35 recovery-only observer; storage remains unloaded pending live firmware review")
    parser.add_argument("--wifi-desktop", action="store_true",
                        help="boot matched #34 wireless kernel/touch with opt-in bound-controller probe")
    parser.add_argument("--spi-explicit-all", action="store_true",
                        help="boot corrected explicit S5L TX startup, AUTO_TX and bit-order handling")
    parser.add_argument("--log-path", type=Path,
                        help="new private, exclusive Pongo log path")
    args = parser.parse_args()
    if sum((args.voltage_readonly, args.pwm0_observer,
            args.spi_drain_observer, args.spi_status_matrix,
            args.spi_rx_drain, args.spi_rx_window, args.spi_rx_half_prime,
            args.spi_rx_zero_prime, args.spi_rx_one_prime,
            args.spi_txcnt_observe, args.spi_final_byte_clock,
            args.spi_ff_filler, args.spi_in_window_ff,
            args.spi_ios_pio_mode, args.spi_atomic_run,
            args.spi_prime_retention, args.spi_prime_replay,
            args.spi_long_rx_capture, args.spi_long_auto_rx,
            args.spi_pad_sample, args.spi_explicit_all, args.touch_session, args.battery_uart, args.battery_gauge, args.continuous_touch, args.wifi_desktop, args.wifi_desktop_v3, args.wifi_ram_desktop, args.storage_observer35, args.desktop_storage35)) > 1:
        parser.error("select only one RAM image")
    if args.desktop_storage35:
        payload_path, expected_sha, log_path = DESKTOP_STORAGE35_PAYLOAD, DESKTOP_STORAGE35_SHA256, DESKTOP_STORAGE35_LOG
    elif args.storage_observer35:
        payload_path, expected_sha, log_path = STORAGE35_PAYLOAD, STORAGE35_SHA256, STORAGE35_LOG
    elif args.wifi_ram_desktop:
        payload_path, expected_sha, log_path = WIFI_RAM_PAYLOAD, WIFI_RAM_SHA256, WIFI_RAM_LOG
    elif args.wifi_desktop_v3:
        payload_path, expected_sha, log_path = WIFI_V3_PAYLOAD, WIFI_V3_SHA256, WIFI_V3_LOG
    elif args.wifi_desktop:
        payload_path, expected_sha, log_path = WIFI_DESKTOP_PAYLOAD, WIFI_DESKTOP_SHA256, WIFI_DESKTOP_LOG
    elif args.continuous_touch:
        payload_path, expected_sha, log_path = CONTINUOUS_TOUCH_PAYLOAD, CONTINUOUS_TOUCH_SHA256, CONTINUOUS_TOUCH_LOG
    elif args.battery_gauge:
        payload_path, expected_sha, log_path = BATTERY_GAUGE_PAYLOAD, BATTERY_GAUGE_SHA256, BATTERY_GAUGE_LOG
    elif args.battery_uart:
        payload_path, expected_sha, log_path = BATTERY_UART_PAYLOAD, BATTERY_UART_SHA256, BATTERY_UART_LOG
    elif args.touch_session:
        payload_path, expected_sha, log_path = TOUCH_SESSION_PAYLOAD, TOUCH_SESSION_SHA256, TOUCH_SESSION_LOG
    elif args.spi_explicit_all:
        payload_path, expected_sha, log_path = EXPLICIT_ALL_PAYLOAD, EXPLICIT_ALL_SHA256, EXPLICIT_ALL_LOG
    elif args.spi_pad_sample:
        payload_path, expected_sha, log_path = LONG_RX_PAYLOAD, LONG_RX_SHA256, ROOT / "private/j72-touch/j72-spi-pad-sample-pongoterm.log"
    elif args.spi_long_auto_rx:
        payload_path, expected_sha, log_path = LONG_AUTO_RX_PAYLOAD, LONG_AUTO_RX_SHA256, LONG_AUTO_RX_LOG
    elif args.spi_long_rx_capture:
        payload_path, expected_sha, log_path = LONG_RX_PAYLOAD, LONG_RX_SHA256, LONG_RX_LOG
    elif args.spi_prime_replay:
        payload_path, expected_sha, log_path = PRIME_REPLAY_PAYLOAD, PRIME_REPLAY_SHA256, PRIME_REPLAY_LOG
    elif args.spi_prime_retention:
        payload_path, expected_sha, log_path = PRIME_RETENTION_PAYLOAD, PRIME_RETENTION_SHA256, PRIME_RETENTION_LOG
    elif args.spi_atomic_run:
        payload_path, expected_sha, log_path = ATOMIC_RUN_PAYLOAD, ATOMIC_RUN_SHA256, ATOMIC_RUN_LOG
    elif args.spi_ios_pio_mode:
        payload_path, expected_sha, log_path = IOS_PIO_MODE_PAYLOAD, IOS_PIO_MODE_SHA256, IOS_PIO_MODE_LOG
    elif args.spi_in_window_ff:
        payload_path, expected_sha, log_path = IN_WINDOW_FF_PAYLOAD, IN_WINDOW_FF_SHA256, IN_WINDOW_FF_LOG
    elif args.spi_ff_filler:
        payload_path, expected_sha, log_path = FF_FILLER_PAYLOAD, FF_FILLER_SHA256, FF_FILLER_LOG
    elif args.spi_final_byte_clock:
        payload_path, expected_sha, log_path = FINAL_BYTE_PAYLOAD, FINAL_BYTE_SHA256, FINAL_BYTE_LOG
    elif args.spi_txcnt_observe:
        payload_path, expected_sha, log_path = TXCNT_OBSERVE_PAYLOAD, TXCNT_OBSERVE_SHA256, TXCNT_OBSERVE_LOG
    elif args.spi_rx_one_prime:
        payload_path, expected_sha, log_path = ONE_PRIME_PAYLOAD, ONE_PRIME_SHA256, ONE_PRIME_LOG
    elif args.spi_rx_zero_prime:
        payload_path, expected_sha, log_path = ZERO_PRIME_PAYLOAD, ZERO_PRIME_SHA256, ZERO_PRIME_LOG
    elif args.spi_rx_half_prime:
        payload_path, expected_sha, log_path = HALF_PRIME_PAYLOAD, HALF_PRIME_SHA256, HALF_PRIME_LOG
    elif args.spi_rx_window:
        payload_path, expected_sha, log_path = RX_WINDOW_PAYLOAD, RX_WINDOW_SHA256, RX_WINDOW_LOG
    elif args.spi_rx_drain:
        payload_path, expected_sha, log_path = RX_DRAIN_PAYLOAD, RX_DRAIN_SHA256, RX_DRAIN_LOG
    elif args.spi_status_matrix:
        payload_path, expected_sha, log_path = MATRIX_PAYLOAD, MATRIX_SHA256, MATRIX_LOG
    elif args.spi_drain_observer:
        payload_path, expected_sha, log_path = DRAIN_PAYLOAD, DRAIN_SHA256, DRAIN_LOG
    elif args.pwm0_observer:
        payload_path, expected_sha, log_path = PWM_PAYLOAD, PWM_SHA256, PWM_LOG
    elif args.voltage_readonly:
        payload_path, expected_sha, log_path = VOLTAGE_PAYLOAD, VOLTAGE_SHA256, VOLTAGE_LOG
    else:
        payload_path, expected_sha, log_path = PAYLOAD, SHA256, LOG
    if args.log_path is not None:
        log_path = args.log_path.resolve()
        if log_path.parent != (ROOT / "private/j72-touch").resolve():
            parser.error("--log-path must be directly under private/j72-touch")
    if os.geteuid():
        raise RuntimeError("Root required for USB access")
    with (ROOT / "private/j72-usb.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        found = []
        for path in Path("/sys/bus/usb/devices").iterdir():
            try:
                if (path / "idVendor").read_text().strip() == "05ac" and (path / "idProduct").read_text().strip() == "4141":
                    found.append((path / "serial").read_text().strip())
            except (FileNotFoundError, PermissionError):
                pass
        if len(found) != 1 or "CPID:8960 BDID:12" not in found[0]:
            raise RuntimeError("Expected exactly one J72 PongoOS USB device")
        payload = payload_path.read_bytes()
        if hashlib.sha256(payload).hexdigest() != expected_sha:
            raise RuntimeError("RAM payload hash mismatch")
        master, slave = pty.openpty()
        tty.setraw(slave)
        logfd = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        process = None
        try:
            process = subprocess.Popen([str(PONGOTERM)], stdin=slave, stdout=slave, stderr=slave, start_new_session=True)
            os.close(slave)
            slave = -1
            os.write(master, b"\n")
            greeting = read_until(master, logfd, b"pongoOS> ", 12)
            if b"Apple A7 (S5L8960)" not in greeting:
                raise RuntimeError("Pongo did not identify Apple A7")
            os.write(master, f"/send {payload_path}\n".encode())
            read_until(master, logfd, f"Uploaded {len(payload)} bytes".encode(), 30)
            print(f"Uploaded verified {len(payload)}-byte RAM image", flush=True)
            os.write(master, b"bootm\n")
            time.sleep(2)
            print("Issued bootm; Pongo log saved privately", flush=True)
        finally:
            if process is not None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
            if slave >= 0:
                os.close(slave)
            os.close(master)
            os.close(logfd)


if __name__ == "__main__":
    main()
