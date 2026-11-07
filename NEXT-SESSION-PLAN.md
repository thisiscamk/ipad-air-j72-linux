> **Historical report / superseded plan.** Start with the [current status](J72-PROGRESS.md) and [replication guide](QUICKSTART.md). Statements below describe their original session, not current support.

# Next session: one boot for input, storage power and charging

Prepared 2 November 2026; executed in the 3 November morning session. This is the
preparation/runbook record. For current completed/pending checks, use the
[session record](SESSION-2026-11-03.md) and [finishing plan](FINISHING-PLAN.md).
**The steps below are the historical preparation for that completed run.**
For the next changed power test, use [the current comparison runbook](NEXT-POWER-COMPARISON.md).
Its candidate and session driver replace section E below. No internal-storage
write, resize, snapshot mutation or erase is authorized. The host kernel stays unchanged.

## Ready now

- Separate #35 touch recovery-window module: build, import closure, bounded-window
  and actual recovery-branch host tests pass. Device untested.
- Bounded observation supervisor: 12 host tests pass, including real signals,
  watcher-group cleanup and child reaping. Device untested.
- Read-only before/after storage idle recorder: syntax/input preflight prepared;
  device untested. It changes no power settings.
- Storage preparation: 44 host test methods pass. A new host-file transaction
  rehearses the proposed GPT order and the full 1.5 GiB image with fsync, exact
  metadata/full-image readback and unchanged outside-extent sentinels.
- Exact-stock recovery image contains RAM-disk and APFS tools. A guarded scratch
  experiment is planned, **not built or ready to execute**.

[Touch candidate](code/touch/recovery-window35/),
[observation supervisor](code/charging/observation35/),
[storage write rehearsal](code/storage/native-root-preparation/HOST-WRITE-RESULT.json).

## A — Before the next DFU

1. Verify host/source receipts and that no boot process or export remains.
2. If the Pi restarted or the hub/adapter/marked port changed, obtain fresh source
   evidence in iOS before the next Linux charging test. Preserve source guards.
3. Use the proven data cable directly on the Pi for boot; the unchanged hub
   handoff has already failed. Do not change the SSD or Pi power connection.
4. Recheck the exact J72 DFU identity and run one boot owner at a time.

Owner action: direct connection and DFU when the owner returns. No overnight prompt.

## B — Boot and new input self-check

Use the proven cold payload and unchanged loader, DT and kernel. The changed
experiment is the separately loaded touch module:

```sh
sudo -n python3 tools/j72-pongo-boot.py --require-direct-pi --confirm-pongo
sudo -n python3 tools/j72-pongo-pmic-boot.py --desktop-storage35 --log-path private/j72-touch/j72-desktop-storage35-UNIQUE-SESSION-pongoterm.log
```

Replace `UNIQUE-SESSION` with a new session identifier: the uploader deliberately
refuses an existing log instead of overwriting it. Reap the first process group
before starting the second. Verify both recovery
shells and configure the discovered matching USB network interface; do not
start a host filesystem export. Before any existing touch/radio/desktop helper:

```sh
sudo -n python3 tools/run-j72-touch-recovery35.py --stage
```

Require its existing start/stop self-check and separate physical-restoration
readback. A failure stops progression; do not restart a failed worker or loosen
cleanup checks. The original cold module file stays unchanged.

## C — Desktop and fixed-workload baseline

Stage the known networking bundle with the #35 bootstrap helper, start the
radio, connect using the existing private profile and establish a fresh pinned
Wi-Fi SSH receipt. Stage/start the known RAM desktop with the #35 wrapper.

```sh
sudo -n python3 tools/stage-j72-network35.py
sudo -n python3 tools/run-j72-wifi-v3.py --storage35 --run
# connect/HTTPS/SSH use run-j72-network.py --storage35 and the private profile
sudo -n python3 tools/run-j72-ram-desktop35.py stage --storage35
sudo -n python3 tools/run-j72-ram-desktop35.py start --storage35
```

Owner check: portrait bar, menu, Foot typing and keyboard hide/tap/reopen. Use
1604/2047 for verification. Then propose 802/2047 for a fixed lower-load power
measurement, subject to readability. Keep `schedutil`; do not repeat the governor
comparison. Query Wi-Fi power save once and record it; the source already defaults
to power saving, so do not claim a new setting without a live reading.

**Do not load the charging module yet.** The native storage probe refuses while
that module is present, even disabled. Ordering these steps avoids another boot.

## D — Measure idle consumption before/after native storage

At fixed brightness, governor and desktop state:

1. Collect a five-minute read-only idle baseline with ASP absent.
2. Capture a fresh same-boot firmware/reservation inventory, probe the existing
   read-only ASP driver and run its bounded read checks. No filesystem mounts.
3. Allow activity from the probe/read checks to settle, then collect another
   five-minute baseline with ASP present.

```sh
sudo -n python3 tools/record-j72-idle35.py --seconds 300 --asp absent --brightness 802
sudo -n python3 tools/run-j72-storage-observer.py inventory --desktop-storage35
# Use the new exact inventory receipt for probe; its resulting receipt for check.
sudo -n python3 tools/run-j72-native35-readcheck.py probe --receipt PATH_TO_NEW_INVENTORY
sudo -n python3 tools/run-j72-native35-readcheck.py check --receipt PATH_TO_NEW_PROBE
sudo -n python3 tools/record-j72-idle35.py --seconds 300 --asp present --brightness 802
```

The before/after comparison is exploratory: time, battery voltage and temperature
can drift, and gauge cache values can repeat. It cannot establish a causal saving
by itself. Keep the storage controller active for the subsequent power run so
the workload includes a prerequisite of the eventual internal-storage desktop.
Do not unload or reprobe ASP if it fails; preserve DMA/logs and use normal recovery.

A fully charged pack may still be above the restart criteria. Continue ordinary
input/idle observation until eligible; do not add an artificial drain workload.

## E — Powered hub and bounded observation

Move only the iPad cable to the same marked powered JCH377 data/charging port.
Verify the live path and fresh source receipt, USB recovery and Wi-Fi control.
Stage the original maintenance module disabled and independently verify baseline 02.

Measurement entry: SOC at most 90%, voltage at most 4.1 V and temperature at most
36.5°C, with valid lower bounds. Prefer a cooler initial pack for comparison.
The kernel still obtains its own fresh vector and enforces all existing limits.
The owner checks the menu, keyboard and charging indicator after charging starts.

```sh
sudo -n python3 tools/run-j72-charge-maintain35.py stage
sudo -n python3 tools/run-j72-observation35.py --observe --seconds 5400 --brightness 802
```

The supervisor reads health over Wi-Fi; only the unchanged charging watcher
renews the serialized USB source lease. Fixed brightness and governor prevent
an unexplained workload change during integration. Input failure or another
health regression interrupts that watcher and checks independent restoration.

Success needs advancing native frames, working input, no controller fault,
complete fresh-gauge coverage, positive integrated net charge with margin,
and independent final restoration. Count every protective hold in the net result.
Record natural voltage/thermal holds and restarts separately. No observed thermal
hold/restart means that hardware gate remains open. Do not force one by heating
the device or raising thresholds.

Finish with normal desktop/input/radio cleanup and iOS charging. If a cleanup
API fails, preserve evidence and classify physical restoration separately.
No failed-worker restart, current escalation or unattended extension is automatic.

## F — Storage installation path after preparation and review

[The transaction plan](INSTALL-TRANSACTION-PLAN.md) retains the conditional
1536 MiB layout, iOS and its rollback snapshot. Remaining work:

1. Qualify native helper mechanics and the iOS12 resize prerequisites. Investigate
   a [disposable RAM APFS experiment](RAM-APFS-REHEARSAL-PLAN.md) first.
2. Finish an exact-device, region-fenced native writer, flush/readback and
   interrupted-operation inspection procedure. Host-file success is not native
   qualification. No generic automatic repair or resume is proposed.
3. Refresh device/layout/minimum/image evidence, state recovery limits and present
   the exact first internal resize/write trial for separate approval. Host/scratch
   testing cannot prove the first encrypted internal resize in advance.
4. After that approval, normal jailbroken iOS is a candidate for the explicit
   online APFS resize, using its initialized SEP state. It can freeze filesystem
   I/O; use a detached, durably identified operation and never interpret loss of
   SSH as permission to retry or reboot. Verify actual state afterward.
5. A separate RAM-recovery boot would perform the approved GPT/image operation
   with internal APFS unmounted, then full readback and iOS validation.
6. A changed Linux boot would read the installed base through a bounded read-only
   view. Confirm no host export is used and demonstrate unplugged operation.

These backend choices remain proposals, not qualified execution commands.
If online resize or RAM recovery is unsuitable, revise the procedure before
requesting an internal operation; do not substitute an unreviewed route.

## DFU forecast and later milestones

| Boot stage | Current status |
| --- | --- |
| Next Linux input/storage-power/charging session | Host preparation ready; new runtime tools device untested. |
| Storage recovery qualification and approved GPT/image installation | Native backend not ready. May need separate qualification and installation boots. |
| First desktop from the internal base | Requires verified installed layout/image; Pi still starts Linux. |
| Persistence and repeat cold-start qualification | Additional work and boot count not yet established. |
| Fully PC-free startup | Separate unproved A7 boot-chain project. |

Three boot stages are a best-case path to the **first read-only internal base**.
The earlier 4–6 DFU forecast is a planning allowance, not a cap or a promise. It
excludes a promise of writable persistence or PC-free startup. Native resize/
writer problems can require more investigation or prevent that proposed layout.
Normal-iOS queries and online preparation do not inherently consume a DFU.

Later work includes native writable state and flush/power-loss qualification,
updates/rollback, the full application set and available space, autonomous
charging, and unqualified tablet features such as audio/Bluetooth/rotation/suspend.
Keep these separate from the first internal read-only desktop milestone.
