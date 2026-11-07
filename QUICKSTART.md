# Replicate the J72 work with fewer dead ends

Read [current status](J72-PROGRESS.md) first. This is a staged developer guide,
not an unattended installer. The fastest sensible first milestone is a RAM
console, followed by touch/desktop and networking. Internal storage comes last.

## 1. Confirm the exact hardware and prepare the host

Use an iPad Air 1 **Cellular**, iPad4,2 / J72AP, with iOS 12.5.7 / 16H81 for the
matching firmware recipe. The tested host is a Pi 4 with Debian 13 aarch64,
native ARM64 boot tools and the existing Pi kernel. Use a proven data cable.
Keep the Pi's system SSD plugged in and separate from iPad cable changes.

Expected DFU identity:

```text
CPID: 0x8960
BDID: 0x12
MODEL: J72AP
PRODUCT: iPad4,2
```

J71, J71b, J72b and J82 are different targets. Another model needs its own
resource/firmware/clock review; changing a product string is not a port.

Have iOS charging working before testing. Boot directly from a Pi USB port;
multiple hub handoffs failed even when the same hub worked for charging.
After Linux starts and has no host filesystem dependency, move to the tested
powered port for a separately qualified charging experiment.

## 2. Get the reviewed source, not a moving nightly

```sh
 git clone https://github.com/thisiscamk/ipad-air-j72-linux.git
 cd ipad-air-j72-linux
 export J72_NOTES="$(pwd)"
 python3 tools/check-docs.py
 python3 tools/check-current-source.py
 python3 code/current/charging/tools/test-j72-charge-profile.py
 python3 code/current/charging/tools/test-j72-charge-auto.py
 python3 code/current/charging/tools/test-j72-charge-supervisor.py
```

These are host checks. They do not boot, resize a disk or grant charging.
The commands use Python 3.11+. See [current source](code/current/README.md)
for exact public base revisions and `git apply --check` / `git apply` commands
that reconstruct the Orchard and Linux source snapshots.

Keep source, kernel output, generated firmware and final images distinct.
Use each checkout's `bin/orchard`; the `orchard` on PATH may select a different
nightly. Preserve source receipts/hashes and use matching 4 KiB kernel/modules.
Do not use the 7.0.12/#35 modules with the current 7.3 kernel.

## 3. Prove one ordinary RAM console boot

Use the patched Orchard checkout and its `examples/minimal-boot` project. Its
upstream help/documents define the output path and component overrides:

```sh
./bin/orchard build --help
./bin/orchard run --help
./bin/orchard build examples/minimal-boot --device j72 --kernel-tree ../linux-j72
```

This current example is serial-only (`transport = false`); it does not provide
SSH or mount storage. The historical first native test used an older
`usb-console` example. Do not look for that removed path in this snapshot.
On Linux, supply a verified Pongo binary through the checkout's `--pongo`
override; building Pongo locally requires Apple's toolchain.

Review the build receipt. Select the A7 `checkra1n`/Pongo route used here rather
than assuming another device's default launcher works. The reviewed source
and [first native CLI report](NATIVE-CLI-BOOT-2026-11-03.md) describe the explicit
bootstrap/components. Use `orchard run` with the built project/output named in
that checkout's help; do not invent a prebuilt filename from a historical report.

Only enter DFU when the image and host tools are ready. Run one USB boot process
at a time, check exact identity, bound the attempt, and reap its process group.
If an attempt fails, inspect state and change something concrete before retry.
A loader success message alone is not Linux success: require a new boot ID,
matching kernel, working USB shell and successful normal return to iOS.

## 4. Add native touch and the Omarchy-A desktop

The kernel snapshot carries J72 SPI, D2089 touch supplies, reference clock,
N1 protocol and DT changes. The patched Orchard firmware recipe generates
`apple/j72-fwstart.z2fw` from the matching official iOS input using the native
N1 converter. Read the patched `docs/bring-up/j72-firmware.md`.

The controller needs **your own device's calibration**, handed through the
boot path. A same-model firmware blob is not replacement panel calibration.
Do not publish or copy someone else's unit data. Use published loader binaries;
this repository does not build or modify m1n1 sources.

Use the unchanged Omarchy-A producer/desktop and normal Orchard platform
layers where possible. The older bounded-RAM profile and Foot experiment are
in [the source map](code/README.md); those are separate research topics, not
requirements to patch every current installation.

Acceptance: portrait desktop, menu/Home, terminal typing, keyboard hide/tap/
reopen, brightness, fresh battery readings, normal cleanup and iOS return.
Get these working before storage writes or a long power test.

## 5. Connect the internal Wi-Fi

Use the J72 HSIC transport and brcmfmac changes in the kernel snapshot plus
[the hardware-ordering service](code/current/wifi/README.md). Supply your own
verified BCM43241 rev-6 firmware and private firmware hash metadata. Use normal
NetworkManager for association; never commit its connection credentials.

Confirm interface creation, association, HTTPS, SSH and reconnect. Only remove
the host cable after proving the root/desktop is independent of host exports.

## 6. Measure power before relying on it

Read [the measured policy and failure](J72-PROGRESS.md#charging-measured-results-and-present-failure)
and [the reusable profile instructions](code/current/charging/config/j72-charging/README.txt).
A profile starts `PENDING`. It requires this installation's own physical-source
rating, descriptors, identity, timing, failure/restoration and net-charge evidence.
The template does not inherit the owner's qualification.

Do not enable 1,050 mA on direct Pi power or an unmeasured charger. Start with
fresh battery data and a charged device, keep tests bounded, and return to iOS
before depletion. A supervisor timing failure is a stop, not an invitation to
clear faults or relax watchdog/temperature limits. Linux overnight charging
is not qualified.

## 7. Approach internal storage as a separate operation

The owner completed snapshot investigation, APFS shrink, native write/flush
qualification and installation before the successful local-storage boot.
The old “snapshot blocks shrink” diagnosis is history; deleting a stock
snapshot retires that restore path and is not a routine prerequisite for every iPad.

The existing device retained iOS and released approximately 50 GB. Do **not**
copy its GPT numbers, partition UUIDs, minimum-size result or resize command.
Measure your own disk, preserve recovery options and approve an exact layout.
Source patches expose experimental writes but do not make that transaction safe
or automatic. Normal Orchard install/start services are the integration target.

The working startup here used a RAM recovery followed by the ordinary
existing-root start request. Direct bare-loader installed launch currently
fails with a heap error. “Internal root” does not mean fully PC-free startup.

## 8. Speakers and browser testing

[Audio source/build instructions](code/current/audio/README.md) cover the actual
48 kHz stereo playback implementation. The matching private A7 SmartIO firmware
is still required. Unchanged PipeWire/WirePlumber discovers the resulting card.
The enabled development service has not passed a new boot yet.

Firefox/YouTube is **not** a passing benchmark: the 1 GB device ran out of memory,
and the later low-memory/swap experiment remained slow. Extra swap was temporary,
not an established default. Safari is an iOS browser, not the Linux test browser.
A quiet tone, a completed PCM transfer and usable browser video are separate gates.

## What is not yet a one-command recipe

- A complete, clean-checkout release integrating the latest Orchard, kernel,
  Omarchy-A platform layer and local runtime service provisioning.
- Generic per-device private firmware/calibration provisioning for every feature,
  including the A7 audio extractor and complete installed service packaging.
- A reviewed automatic APFS/GPT resize/install transaction for another iPad.
- Reliable charging under browser pressure, low-battery fallback and cold-start
  qualification of charging/audio automation.
- A working iOS-app or PC-free boot path.

Those are real remaining tasks, not implicit private commands the reader is
expected to guess. Use the source and milestone gates now; a turnkey installed
release should be labelled reproducible only after another clean deployment.
