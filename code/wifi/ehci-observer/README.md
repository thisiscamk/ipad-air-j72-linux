# Halted J72 EHCI observation

Developer diagnostic for the exact J72 development kernel #33. It repeats the
qualified radio reset/HOST_READY handshake while **only reading** EHCI registers.
It releases its GPIO and power-domain owners before returning; the module remains
resident because this kernel disables module unloading.

All four snapshots were identical: command `0x80b00`, halted status `0x1000`,
interrupts and both schedule pointers zero, configuration flag zero, and port3
`0x2000` (companion ownership, no port power). DEVICE_READY again rose after
HOST_READY. This did not start the host or enumerate a USB device.

[Sanitized result](VALIDATION.json). Run the host-only fault test with
`python3 test-observer.py`; its 44 cases use synthetic APIs, not a hardware model.
Build against the exact configured kernel tree with
`make -C /path/to/kernel/out M="$PWD" modules`. Other devices/builds are refused.
No firmware, calibration, device identifiers or raw Apple inputs are included.

## Subsequent enumeration attempt

A separate experimental standard-EHCI probe stopped responding before any result
or cleanup record was retrieved. Both Linux shell paths stopped answering while
the external USB gadget remained enumerated. USB descriptors and ROM identity
are **not qualified**. Source review found that an unbound HCD controller is
invalid here: Linux USB hub code falls back to `sysdev->driver->name` when the
controller has no driver. The next candidate must bind a real platform driver
and retain it through HCD removal. The subsequent screen photo shows EHCI startup and a three-port USB root hub,
with no WLAN descriptor or oops/backtrace visible. Both shell checks still fail;
the actual stall cause remains unconfirmed. Synthetic API fault tests did not cover that real
USB-core lifecycle requirement. Do not repeat the original enumeration probe.
