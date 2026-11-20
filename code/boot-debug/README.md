# J72 early-boot diagnostics

This directory contains the reusable, source-only diagnostics developed during
the 17–20 November 2026 A7 early-kernel investigation.

- `flightrec.h` and `flightrec.py` define and decode the RAM flight-recorder
  format.
- `observe.py` and `replay.py` support offline observation and replay.
- `early_*_shim.S` are progressively corrected watchdog observers. The latest
  `early_watchdog_shim_readback.S` completes only the watchdog MMIO write with
  a same-register readback; it does not insert a global barrier into the
  translation-maintenance sequence being observed.
- `compare-j72-entry-state.py` compares normalized JSON system-register
  captures from two entry paths.

Generated kernels, Apple firmware, device inputs and live logs are deliberately
excluded. The dated design and evidence notes are in
`history/bringup-20261117-20/`.

These are experimental bring-up tools, not a supported boot path. Several
earlier watchdog conclusions were retired after discovering that the observer
itself contained `dsb sy`; read the dated audit before interpreting results.
