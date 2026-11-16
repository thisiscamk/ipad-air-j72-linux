# Guarded charging source and reusable qualification

These sources preserve the measured policy; they do not provide permission
to start a session on an unmeasured source. Current physical results are in
[current status](../../../J72-PROGRESS.md#charging-autonomous-on-device-qualification).

- `autonomous/`: qualified on-device controller, runtime service, synthetic
  test and sanitized result.
- `tools/`: earlier host supervisor/source-admission helpers and synthetic tests.
- `config/j72-charging/`: shared hardware pins, per-installation profile
  workflow and systemd templates. Start with
  [its instructions](config/j72-charging/README.txt); run the relative commands
  from this `code/current/charging` directory.
- `kernel/`: read-only external-power reporter; loading it is not charging.
- Controller/gauge/HDQ/PMIC source is in the [kernel snapshot](../kernel/).

The owner-qualified runtime used the earlier compatibility endpoint. The
reusable profile path was prepared and host-tested, not independently deployed
and cold-boot-qualified on another installation. Templates start `PENDING`.
Synthetic test identities were substituted before publication.

Qualified policy: nominal 1,050 mA input, not battery current; a paired
5 V/1,500 mA powered JCH377 source; retained source leases, restore/stop,
temperature hysteresis and voltage/SOC windows. Arbitrary hubs, direct Pi power
and higher current limits are not qualified. File hashes do not certify that
someone performed a test.

The later host-supervisor watchdog failure is addressed by the autonomous
on-device controller. Its physical ten-minute charge, unplug restoration,
automatic reconnect and explicit stop tests passed. The exact service is
installed and enabled; automatic startup still needs observation on the next
natural Omarchy boot. The older host admission services are disabled.
