# Native touch and Omarchy build preparation

3 November 2026. These are **host results**, separate from the measured
[native Orchard console boot](NATIVE-CLI-BOOT-2026-11-03.md). The iPad is in iOS
on its powered hub; its last actual charging check passed at 96%. The owner is
away overnight, so there will be no device tests until they return.

## Native touch

The new source uses Linux's SPI, clock, regulator, GPIO, pinctrl, firmware and
input frameworks. The working laboratory image remains a reference. Its raw
hardware owners are not being installed as native startup services.

| Piece | Completed host work | Device status |
| --- | --- | --- |
| Firmware converter | Existing Z2FW format; 37 targeted tests and byte comparisons with the working setup | New native combination untested |
| SPI provider | 72 actual C transfer scenarios; ARM64 4k/16k object builds | Untested |
| Clock and power providers | 1,047 actual provider scenarios, readback/fault checks, 4k/16k builds and selected bindings | Untested |
| N1 input driver | Saved contact reports, strict packet/contact validation, startup and cleanup fault fixtures | Selected source/object/DT gates pass; full kernel build running |

The [source-only firmware converter](code/upstream/orchard-j72-n1-firmware)
contains no Apple bytes or unit calibration. The public J72 recipe keeps its
outputs empty until the driver, providers, device tree and firmware work
together on hardware. Kernel topic branches will be exported through Orchard's
normal tooling after the applicable device gates; patch numbers are not being
reserved by hand.

The regulator framework's shared-bias sequencing is a new hardware test, and
cleanup errors must remain errors. Unknown physical state after a failed write
will stop optional work and require return to iOS, without retrying the driver.

## Building normal Omarchy components

All four normal source components built on the Pi from Omarchy source
`fa25972a83a279bdd7e5edc9ff6013cd211562fb`:

- Desktop payload, patched wvkbd keyboard, Omafox integration package and
  patched wlroots: component `ae4ace0fcc906d53`.
- Cursor helper: `713468b477b09460`.
- Bluetooth support library: `c6d859a489126183`.
- Patched Labwc: `d2c7b8328773bfb4`.

These are successful builds, not proof of native GUI, Bluetooth or keyboard
operation on this new kernel. The source includes the optional keyboard-auto
change, whose default remains disabled.

Normal Omarchy `orchard run` currently boots installer recovery. Its full
installed root is too large to unpack into the iPad's 1 GB RAM. We are preparing
a reusable distribution-owned RAM desktop project from the **normal Omarchy
components and Arch root**, using gzip SquashFS and bounded writable RAM.
The tested USB console stays outside its manually started desktop chroot.

The normal signed Arch root has built successfully. Its 1,265,877,734-byte
archive alone exceeds the iPad's RAM, so the full installed root stays on the
host. The [compact RAM producer](code/upstream/omarchy-a-ram-desktop) now builds
a **104.64 MiB gzip SquashFS** from those normal inputs. Its selected expanded
files total 293,944,222 bytes. All 128 host tests pass, including 15 RAM fixtures;
independent extraction checks confirm critical file hashes and ownership.
The native kernel is still compiling. Native touch, desktop lifecycle, working
memory and input on this new source-built combination remain unqualified.

The working terminal touch/IME change is also being prepared as a separate,
opt-in source component. Its actual C callback checks pass; compilation and
integration are in progress. Normal signed Foot remains the default.

## Next qualification

After the owner returns, one changed boot will first establish normal Orchard
serial and SSH, then explicitly load the native touch driver. If startup and
health checks pass, record taps, holds, swipes and releases; inspect normal
cleanup and return to iOS for charging. A compact native desktop follows once
its root and input gates pass. No internal-storage installation is authorized.
