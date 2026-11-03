# Native touch and Omarchy build preparation

**4 November update:** the [first native device test](NATIVE-TOUCH-BOOT-2026-11-04.md)
now passes touch startup, gestures, clean stop/restart and supply/clock cleanup.
The owner verified the desktop after documented RAM-only userspace fixes.
The host-preparation notes below describe the earlier build state; use the
device result for current qualification and remaining limits.

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
| N1 input driver | Saved contact reports, strict packet/contact validation, startup and cleanup fault fixtures | Full source kernel, DT and 71 modules build; complete console/GUI payload checks pass; hardware untested |

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
The native kernel and complete console/GUI payloads now build successfully.
Native touch, desktop lifecycle, working memory and input on this new
source-built combination remain unqualified.

The [terminal touch/IME component](code/upstream/omarchy-a-foot-touch-ime) also
builds successfully from pinned official Foot source. Its upstream config test
and 460 actual C callback/IME checks pass. The [combined RAM profile](code/upstream/omarchy-a-ram-foot)
passes 133 host tests and builds a **105.83 MiB** SquashFS with the patched
terminal selected explicitly. Its default still uses signed Arch Foot.
Repeated tap/keyboard behaviour in this native combination remains untested.

## Complete native payloads

The full native kernel, device tree and 71 modules now build through the normal
Orchard producer. The source is `4c8cee77d`, with a coherent
`7.3.0-rc1-orchard-apple-4k` ABI. The first-tested m1n1 and Pongo bootstrap files
are retained through supported build overrides; the new kernel is untested.

Normal console and combined Omarchy RAM desktop builds, followed by independent
artifact inspection, pass:

| Payload | Complete upload size | Hardware status |
| --- | ---: | --- |
| Native touch console | 15,125,358 bytes | Untested |
| Native touch + normal Omarchy desktop/Foot | 125,378,798 bytes | Untested |

The GUI fits the unchanged 128 MiB uploader cap with 8,838,930 bytes spare. It
contains the independently checked 105.83 MiB SquashFS, all matching modules,
normal static USB/SSH tools and privately supplied model firmware. The driver requires bootloader-supplied unit calibration; none is baked into
the desktop.
Rescue PID1 and both USB transports remain outside the manually started GUI.
Automatic module loading and automatic desktop startup are disabled.

The first GUI assembly correctly failed the size limit because the standard
module stager included DWARF. A small **local, unsubmitted Orchard packaging
topic** now removes debug information from unsigned staged copies, retaining
all 71 modules and leaving original builds intact. Signed inputs remain
unchanged. All actual modules preserve every allocated section, module metadata,
BTF and nondebug relocation semantics, with identical vermagic. Staged modules
shrink from 143,763,464 to 12,009,120 bytes; Image and DTB hashes are unchanged.
The cache producer generation advances, so old bundles cannot be confused with
new ones. The isolated Orchard suite passes **519 tests**, with no skips.

One earlier full CLI attempt finished its kernel but failed when the native
host lacked a Rust target for an additional quiet-loader build. That failure
was retained; the completed commands use the exact verified loader already
booted successfully. No host kernel or global toolchain change was made.
These are host preparation results. They do not qualify the native touch,
GUI, Wi-Fi, battery or charging implementation on the device.

## Next qualification

After the owner returns, one changed boot will first establish normal Orchard
serial and SSH, then explicitly load the native touch driver. If startup and
health checks pass, record taps, holds, swipes and releases; inspect normal
cleanup and return to iOS for charging. The complete GUI candidate can then be started manually once its native
input and baseline checks pass. No internal-storage installation is authorized.

## Native power follow-up

The [source-based power plan](NATIVE-POWER-INTEGRATION-PLAN.md) identifies the
existing HDQ/BQ27545 pieces and the missing J72 DT/capacity/freshness work.
Charging also needs verified D2089 event/ADC/current handling before reusing
the D2365 Tristar policy. These changes are separate from the touch build;
unattended Linux charging is not yet qualified.
