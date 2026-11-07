# Guarded charging source and reusable qualification

These sources preserve the measured policy; they do not provide permission
to start a session on an unmeasured source. The latest failure is documented in
[current status](../../../J72-PROGRESS.md#charging-measured-results-and-present-failure).

- `tools/`: actual supervisor/source-admission helpers and synthetic tests.
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

A later supervisor status-read delay/watchdog stopped charging. The failure is
not fixed by these sources. Its battery snapshot then became stale; do not use
old controller values to infer remaining runtime. A low-battery test guard and
power reliability work remain before recommending overnight Linux charging.
