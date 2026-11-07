# Contributing

Use [current source](code/current/README.md) and [current status](J72-PROGRESS.md)
as the entry points. Keep dated investigations labelled historical.

- Preserve exact target, source/base revisions, kernel ABI and component receipts.
- Distinguish synthetic/host checks, measured device behaviour and owner observations.
- Reuse unchanged Orchard/Omarchy-A. Explain the J72 hardware reason for each change.
- Never commit Apple firmware, unit calibration, raw device dumps/logs, serials/ECIDs,
  credentials, network profiles or generated firmware-bearing images/modules.
- Source snapshots retain original license/copyright notices. Treat compiler output
  and generated private inputs as local. See `code/LICENSES/` for existing notices.
- Charging qualification belongs to a specific installation/source. Tests or hashes
  are not proof of performed hardware measurements. Never fabricate passing evidence.
- Do not turn experimental disk writes or charge commands into default/autostart
  behaviour without a reviewed implementation and physical tests.
- Publishing here does not authorize an upstream PR. Discuss the exact proposed
  changes with the owner before submitting/updating upstream or changing review state.

Before publishing documentation/source changes:

```sh
python3 tools/check-docs.py
python3 tools/check-current-source.py
python3 code/current/charging/tools/test-j72-charge-profile.py
python3 code/current/charging/tools/test-j72-charge-auto.py
python3 code/current/charging/tools/test-j72-charge-supervisor.py
```

These checks are offline. No device should be connected merely to edit this repo.
