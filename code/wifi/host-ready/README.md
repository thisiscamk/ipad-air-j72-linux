# J72 radio reset and HOST_READY diagnostic

**The radio responds to HOST_READY.** In one bounded RAM test, DEVICE_READY
was high in **0 / 45 / 50** of the 50 samples in HOST_READY **low / high / low**
windows. It returned low after radio reset was asserted. This does not prove
USB enumeration, firmware upload, scanning or association. [Measured result](VALIDATION.json).

The source uses the existing Linux genpd owner, the qualified native PHY
sequence, and exact GPIO3 reset bytes `09 → 0b → 09`. HOST_READY GPIO163 is
claimed through the standard `gpiod_get()` consumer API using the existing
controller, retained direction/mux (`GPIOD_ASIS`), then driven high/low. A busy
line is refused. DEVICE_READY GPIO164 is read passively; no input direction,
IRQ or pin configuration is changed. Radio reset is restored before PHY
control and power-domain cleanup. GPIO descriptors, lookup and device
references are released on success; uncertain ownership/restoration remains
held for investigation. No USB host, DMA or firmware upload is started.

This is an **exact #33 development diagnostic**, not a persistent Wi-Fi driver
or an installer. It requires the measured J72 baselines and prior clean
workload/charge teardown; other devices/builds are refused. Do not use it as
a generic Apple GPIO recipe. No private firmware/calibration or raw logs are
included.

The original hardware record had two `host_after` labels, and the host harness
failed its final field assertion after all hardware cleanup succeeded. Ordered
record analysis and independent after-snapshots verified both values. This
public source changes only the GPIO label to `host_gpio_after`; that reporting
change has not been reloaded on hardware. Both source hashes are recorded.

Run `python3 test-host-ready.py` for 40 actual-source fault paths with synthetic
kernel APIs and UBSan, including ambiguous writes, failed reset/PHY rollback,
GPIO busy/direction/mux changes, lookup/ref cleanup and unique field names.
This host simulation does not emulate the radio.
