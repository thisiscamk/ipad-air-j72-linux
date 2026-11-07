# Current J72 source snapshot — 7 November 2026

Start at [the replication guide](../../QUICKSTART.md). These are source
snapshots, not a supported-device release or an unattended installer.
The manifest pins the public bases and source hashes. Upstream changes require
the owner's separate review; publishing here does not submit a PR.

| Directory | Contents | Evidence and boundary |
| --- | --- | --- |
| [orchard](orchard/) | Current Orchard integration diff against a pinned public base | Native CLI, firmware recipe and recovery/storage service work; feature metadata in the historical snapshot predates later hardware tests |
| [kernel](kernel/) | Combined J72 kernel diff and separate gauge-cache wait delta | Installed ext4/FAT boot, touch, Wi-Fi, battery and bounded charging on the tested device; includes experimental storage writes |
| [wifi](wifi/) | Hardware-ordering service used before NetworkManager | Connected Wi-Fi on the installed system; firmware and network credentials are supplied privately |
| [charging](charging/) | Supervisor, source admission, reusable profile templates, tests and read-only external-power reporter | Positive-charge qualification passed; later browser-load supervisor watchdog failure remains unresolved |
| [audio](audio/) | Actual MCA-v1, SmartIO variant, DMA dependencies and DT overlay source | Both channels heard, ALSA and PipeWire playback pass; next-boot service verification remains open |

The 7.0.12/#33–35 experiments elsewhere under `code/` remain useful historical
reference. Do not combine their modules, firmware containers or runtime
assumptions with this 7.3 kernel.

## Rebuild the source trees

Clone this repository first. Set `J72_NOTES` to its absolute path. Run the
following commands in a separate working directory with enough disk space:

```sh
git clone --filter=blob:none https://github.com/OrchardLinux/orchard.git orchard-j72
git -C orchard-j72 checkout --detach a6ffc904bf8acb7af2fd0fc94f84ca194bd82ed2
git -C orchard-j72 apply --check "$J72_NOTES/code/current/orchard/0001-j72-orchard-integration-snapshot.patch"
git -C orchard-j72 apply "$J72_NOTES/code/current/orchard/0001-j72-orchard-integration-snapshot.patch"

git clone --filter=blob:none https://github.com/OrchardLinux/linux.git linux-j72
git -C linux-j72 checkout --detach 4cec5aa77c69ac1fd7c605ab8159714ea9024a08
git -C linux-j72 apply --check "$J72_NOTES/code/current/kernel/0001-j72-installed-kernel-snapshot.patch"
git -C linux-j72 apply "$J72_NOTES/code/current/kernel/0001-j72-installed-kernel-snapshot.patch"
git -C linux-j72 apply --check "$J72_NOTES/code/current/kernel/0002-j72-gauge-cache-wait.patch"
git -C linux-j72 apply "$J72_NOTES/code/current/kernel/0002-j72-gauge-cache-wait.patch"
```

These commands reconstruct source, not an installed iPad. Read each patched
project's build documentation and use its own `bin/orchard`, not an unrelated
nightly on PATH. Build with `--kernel-tree` through Orchard's normal producer
interface. Retain 4 KiB pages and the exact module/kernel ABI. The release
used on the device was `7.3.0-rc1-j72-pw1-orchard-apple-4k`.

The kernel patch includes J72 ANS1 writes and device-specific policy. Applying
it does not authorize resizing a disk or enabling charging. See
[the replication boundaries](../../QUICKSTART.md#what-is-not-yet-a-one-command-recipe).

## Host-only checks

Python 3.11+ is required for the reusable qualification helper.

```sh
python3 code/current/charging/tools/test-j72-charge-profile.py
python3 code/current/charging/tools/test-j72-charge-auto.py
python3 code/current/charging/tools/test-j72-charge-supervisor.py
python3 tools/check-docs.py
python3 tools/check-current-source.py
```

The tests use synthetic identities. They never grant real charging
qualification. Each installation needs its own evidence, ECID and physical
source checks. The source admission system intentionally refuses blind
restart after timing/read failures.

Existing SPDX notices and upstream copyright/license notices apply to copied
kernel source. GPL text is in [code/LICENSES](../LICENSES/). No Apple firmware,
unit calibration, compiled module, raw capture or credential is included.
