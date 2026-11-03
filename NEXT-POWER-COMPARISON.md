# Next prepared Linux charging comparison

Prepared 3 November 2026. The previous run is complete: touch/cleanup pass,
net charge fails. [Measured diagnosis](SESSION-2026-11-03.md).
**First confirm iOS is visible and charging on the powered hub.** USB has not
returned; neither a requested reboot nor a connected charger proves charging.
No new DFU has been requested yet.

## Concrete change and scope

Use the same #35 cold payload and successful recovery-window touch worker.
The only deliberate power-policy change is the separate
[voltage-hold restart candidate](code/charging/voltage-resume35/): voltage/SOC
holds may resume at 36.6–38°C. Initial starts, actual thermal recovery,
stop/rearm and expired-window starts retain 36.5°C. An actual >38°C reading
latches thermal history until a cool restart. Active hard limits, 1050 mA
nominal setting, source lease and independent restoration remain intact.
Host tests/build pass; device behaviour and net gain are unproved.

## One prepared session

1. Verify current iOS/source state, host boot, same powered hub/marked port and
   no boot/test owner. Refresh source qualification if its identity changed.
2. Use the proven direct-Pi DFU path and a new log filename. Boot the unchanged
   #35 payload; stage the successful separate touch worker before radio/desktop.
   Reap one boot owner before starting another. The failed unchanged hub boot
   handoff is not part of this trial.
3. Start existing Wi-Fi/HTTPS/pinned SSH and the RAM-only desktop. At brightness
   1604, check menu, typing and keyboard reopening. Do not load charging yet.
4. Collect a fresh native inventory, probe the existing read-only ASP driver
   and complete six bounded matching reads. No internal mounts or writes.
   Keep ASP active; do not unload/reprobe a failed controller.
5. Move only the iPad cable to the qualified hub. Verify source and USB/Wi-Fi
   communication. The new session driver sets the fixed 802 brightness for the
   idle measurement, stages the **candidate** disabled, waits up to 90 minutes
   for the unchanged initial entry gate, then observes up to 90 minutes.
6. Include every hold in current integration. Record warm voltage-only resumes,
   actual thermal history, input progress and faults. Independent final `02`,
   normal cleanup and an iOS reboot request end the run. Failure stops progression.
7. Confirm actual iOS charging before leaving the device on the hub. The optional
   post-test helper uses the candidate selector and a new evidence directory.

Workspace commands after steps 1–4 and the qualified hub transfer:

```sh
sudo -n python3 tools/run-j72-voltage-session35.py --preflight
sudo -n python3 tools/run-j72-voltage-session35.py --run --readcheck PATH_TO_THIS_BOOTS_READCHECK
# Separate follow-up, once the session is running; it waits for test owners:
sudo -n python3 tools/ensure-j72-ios-charging.py --run --voltage-resume35
```

[Host source references](code/charging/voltage-resume35/workspace-reference/).
These require the private research workspace; they are not public turnkey tools.
Do not run the original morning driver or load its original charging module
for this comparison. Storage qualification remains separate: the new
[C I/O core](code/storage/fenced-io/) is host tested, not a native installer.
