# J72 integration with Orchard and Omarchy A

Prepared 3 November 2026. This is an implementation and review
plan, not a support declaration. No internal-storage writes are authorized.
The latest device trial stopped before charging on seven captured state-2 reports; normal cleanup and iOS charging pass.

## Prepared native CLI candidate

The [source review bundle](code/upstream/orchard-j72-cli/) contains the
experimental descriptor, verified firmware recipe, explicit A7 bootstrap and
standard USB console, plus a separately scoped shared-tools reuse fix.
A real 11.9 MB image builds through the checkout's `orchard build` command
using verified components from the exact matching nightly. Its first hardware
qualification now passes `orchard run`, serial/SSH, command execution and
4 KiB RAM-only file transfer over SSH and forced serial. Normal reboot returns
iOS USB. This qualifies the USB console only; repeatability and desktop
hardware integration remain open. [Measured result](NATIVE-CLI-BOOT-2026-11-03.md).

Native SPI actual-function fixtures pass 72 cases, with 4 KiB/16 KiB object and
binding gates passed. A separate generic brcmfmac USB reply-validation topic
passes 1,056 actual-function checks; native Wi-Fi PHY/ready/power ownership and
DT integration remain open. Neither source topic has been hardware-qualified
or exported into Orchard's applied series. The larger new-SPI kernel build
was stopped deliberately once the matching published base was verified; its
incremental output is retained, not recorded as a completed full build.

## Agreed destination

Build the iPad Air 1 Cellular (`iPad4,2`, J72AP, CPID `0x8960`, BDID `0x12`)
using Orchard's normal hardware producers and Omarchy A's normal desktop
producer. Preserve the present RAM-only lab image as a recovery/reference
build until the replacement passes the same exact-revision checks.

Two milestones must be distinguished:

1. An Orchard-built J72 RAM boot running the Omarchy A desktop, with private
   firmware supplied by the owner and no dependency on lab bootstrap scripts.
2. An authorized, separately qualified internal-root install. A local root
   does not solve PC-free cold startup; A7 startup still needs an exploit or
   separately engineered on-device handoff. Do not enable install merely
   because reads from native storage pass.

**Acceptance for build integration:** a developer starts from clean, pinned
Orchard and Omarchy A checkouts plus documented owner-local input recipes.
The normal producers build J72 kernel, DT, matching modules, initramfs and
rootfs. The resulting exact build cold-boots repeatedly from RAM, with
verified input, Wi-Fi, brightness, battery and normal cleanup. Neither build
nor runtime depends on this private workspace, a private prebuilt desktop
image, unpublished manual register writes or the owner's development keys.
Generated private firmware/calibration layers remain owner-local inputs;
they are not public release contents. Hardware results and remaining limits
are recorded against those exact source and artifact receipts.

## Upstream sources examined

Fresh, separate clones were made; old `hardware/cli` submodule instructions
do not describe the current architecture.

| Repository | Exact revision inspected | Role |
| --- | --- | --- |
| [OrchardLinux/orchard](https://github.com/OrchardLinux/orchard/tree/6b5fca68c56868651113ede0063a3061d0b22914) | `6b5fca68c56868651113ede0063a3061d0b22914` | Hardware, recipes, initramfs, host CLI and component contracts |
| [OrchardLinux/omarchy-a](https://github.com/OrchardLinux/omarchy-a/tree/ace594051492b1121794a5a6ed98d01719451753) | `ace594051492b1121794a5a6ed98d01719451753` | Desktop, root filesystem, distro policy and release assembly |
| OrchardLinux/linux generated `main` | `df7c930f80abd32a054617cd30ea450b7acfb3e0` | Normal kernel source branch base; do not commit to generated main |
| OrchardLinux/m1n1 generated `main` | `bd689a19a22c84dcf18a270ea44f79dc7d951f50` | Loader source base |
| [Orchard Wi-Fi PR #53](https://github.com/OrchardLinux/orchard/pull/53) | head `8f136183a785ad3fdc7bfb5a56db59419ba70d90` | Open draft, converter/private mixin and measured requirements |

Orchard's current apple-4k config says Linux **7.3.0-rc1**; upstream lock is
`cee9395acd8043be0644b25c34bfa86623f2b935`. The local tested kernel is
7.0.12-j72spi2, build #35. Copying its `.ko` files into a new platform layer
would violate the kernel ABI contract and would not qualify a port.

### What PR #43 actually merged

The [maintainer's merge comment](https://github.com/OrchardLinux/orchard/pull/43#issuecomment-6561657667)
says the active tree kept `docs/bring-up/j72.md`. The lab implementation was
removed from the active patch series/tree and preserved in history under
`contrib/thisiscamk-j72`. The annotated tag object is
`6b289bcabd03e16bd3373caf3e19b5f4e64f4f17`, peeled commit
`cd0d5459c3f064e0b0c3d90e0a3b3a3a3c21c837`.
There is still no `devices/j72/device.toml`. Do not describe the merged PR
as native, active J72 runtime support. Newer touch/power lab changes also
postdate that historical snapshot.

## Current build contract to target

[Orchard's distribution contract](https://github.com/OrchardLinux/orchard/blob/6b5fca68c56868651113ede0063a3061d0b22914/docs/distribution-contract.md)
is commands plus files. Omarchy A imports none of Orchard's Python internals
in its build. Its `orchard.toml` delegates to `tools/build.py`; the chosen
Orchard checkout supplies `ORCHARD_CHECKOUT`.

1. `orchard.inputs --output FILE --platform apple-4k` resolves the exact
   kernel bundle, board/DTB mapping, loader, Pongo and static tools.
2. `orchard.image.platform apple-4k` makes `platform-apple-4k.tar.gz` with
   the matching kernel, all described boards' DTBs, modules and hardware
   defaults. `devices/j72/device.toml` must map into that bundle.
3. `desktop/build-sources` and `desktop/build` build the keyboard, shell,
   compositor-related components and desktop payload; `system/build-rootfs`
   builds signed Arch Linux ARM userspace. Do not install `linux-aarch64`.
4. Omarchy A's `release.build` combines the userspace with Orchard component
   inputs and per-platform recoveries. Firmware and credentials stay out of
   the public release; owner-private layers are prepared separately.
5. `release.audit`, Orchard manifest validation, artifact smoke/input checks
   and then an exact-revision physical RAM boot qualify the result.

Use `/path/to/our-orchard/bin/orchard`, not the PATH launcher which tracks
the latest nightly. Pin both Git commits and component receipts. A test of
the old #35 payload cannot qualify a freshly built 7.3 kernel or new root.

## Integration map

All proposed paths below are targets, not claims that an implementation
already exists. Kernel source changes start on topic branches/worktrees of
OrchardLinux/linux; use `tools/kernel-tree/export.py` after hardware testing
to export into Orchard's driver/device patch layers. Do not reserve patch
numbers or edit imported Hoolock patches.

| Working lab component / remaining gap | Upstream destination | Required migration and gate |
| --- | --- | --- |
| Exact J72 identity, direct Pi boot, 4 KiB kernel | `devices/j72/device.toml`, `platforms/apple-4k.toml`, kernel board DT, `src/orchard/apple/{device,boot,replug}.py` | Add experimental descriptor with `install=false`; select measured J72 compatible/DTB. Native A7 boot method must preserve exact identity, native ARM64 tools, one owner and process-group cleanup. Current normal bootstrap uses palera1n, whereas measured J72 uses checkra1n0.1337.3/HoolockPongo2.6.3. Qualify or implement the A7 backend explicitly; do not assume equivalence. |
| SPI explicit payload and bit order | Linux `drivers/spi/spi-apple.c` and binding `Documentation/devicetree/bindings/spi/apple,spi.yaml`; exported `kernel/patches/drivers/spi/` | Add `apple,s5l8960x-spi` match data using measured FIFO/PIO behavior. Reuse current T7000/S8000 implementation shape; preserve other compatibles and regression-test T7000/S8000/T8010. |
| Touch N1 upload, native contact decoder, bounded recovery | Linux `drivers/input/touchscreen/apple_z2.c`, input binding; exported `kernel/patches/drivers/input/` | J72 personality/layout through match data. Transfer the complete packet checks, release/timeout behavior and bounded health recovery. The state1 candidate passed initial input checks but later hub health rejected captured state2 reports before charging; longer-run layout coverage remains incomplete. Neither state interpretation is production-qualified. Do not copy diagnostic module parameters or raw MMIO worker into distro startup. |
| Touch analog07, clock, reset, IRQ, sync | Linux regulator/clock/pinctrl providers, J72 DT; exported `drivers/{regulator,clk,input}` and `devices/s5l8960x/` layers | Model D2089 shared analog dependency and board-owned resources. No startup shell register writes. Audit display-sync/PWM ownership and cleanup on failure; no copied J81 GPIOs. |
| Private touch firmware and per-unit calibration | `devices/j72/firmware.json`, `src/orchard/apple/{z2fw,z2packet}.py`, `src/orchard/recipe.py`, m1n1 calibration forwarding | Start from existing Gen1/data-form/packet recipes and normal DT calibration providers, verify the exact N1 constructed-packet/start sequence. The lab include renderer is not a complete extractor. Do not reuse N61 addresses or assume J72 personality fits unchanged. Public synthetic fixtures, real private byte comparison, missing-input refusal and cold startup required. |
| Battery UART/BQ27545 and capacity pairing | Linux `drivers/w1/masters/w1-uart.c`, `drivers/power/supply/bq27xxx_battery{,_hdq}.c`, serial core if still needed, bindings and J72 UART DT | Prefer existing upstream w1-uart/HDQ ownership. Audit two-stop-bit framing and BQ27545 match data; compensated remaining/full pairing as chip data, no machine check. Verify current sign/units and full-but-discharging status. |
| Source-aware sustainable charging | Existing `apple_tristar_charger`/PMIC policy owners and DT bindings, `kernel/patches/drivers/power/` | D2089 register data and encoding still need verification. Reuse USB/BC1.2/source-current and USB-role ownership already implemented for other boards. Preserve source-change fallback, thermal/voltage/current bounds, rollback and fault semantics. Lab host leases and direct PMIC workers are evidence/reference, not finished autonomous policy. |
| Wi-Fi BCM43241 ROM/HSIC | `drivers/net/wireless/broadcom/brcm80211/brcmfmac/usb.c`, owning HSIC PHY/EHCI/PMGR/reset/GPIO DT/driver paths, exported `drivers/{wifi,usb,...}` | ROM0a5c:bd1c/chip4324rev6 needs revision-specific control values and bounded TRX+NVRAM upload, firmware re-enumeration and synchronized EHCI stop. Keep other USB Broadcom radios unaffected. No parallel raw owner, permanent polling overlay or unsafe direct-stop. |
| Private Wi-Fi converter | Existing draft #53: `src/orchard/apple/brcm_usb.py`, CLI in `src/orchard/command.py`, `tests/test_brcm_usb.py` | Already creates normal private data-only mixin and matches device-tested bytes privately. No board descriptor or automatic recipe today. Per-unit MAC in appended NVRAM prevents a universal public output hash; design a bounded private per-unit conversion contract rather than hardcode owner values. |
| Recovery USB NCM/ACM and reconnect | Orchard `boot/initramfs/{recovery,nfs}/usb-gadget`, `src/orchard/usb-session`, native DWC2/USB-role owners | Match standard product/identity/boot receipts and preserve both rescue paths. Today's manual guarded same-UDC rebind is not automatic reconnect support; qualify cable/source transitions without remounting external root. |
| Omarchy shell, menu, Home and software rendering | Existing Omarchy `desktop/{stage.py,configuration/login-session,configuration/labwc-autostart}`, `desktop/shell/labwc-rc.xml` | Upstream already uses Labwc/pixman/seatd and KEY_HOMEPAGE binding. Use its live logind/user D-Bus session and greeter; remove chroot-specific manual D-Bus/udev startup. Verify J72 maps touch to portrait panel at scale2; do not replace generic rotation with hardcoded J72 values. |
| Keyboard repeated short-tap activation | Omarchy `desktop/shell/bin/omarchy-keyboard`, `desktop/keyboard/wvkbd-0.20.patch`, optional separately pinned Foot recipe | Upstream already builds patched wvkbd0.20 but controller omits `--auto`. Local working keyboard uses `--auto`; repeated Foot tap also uses experimental client IME changes. Preserve theme handling/drag-to-dismiss; isolate those dependencies and test real client/compositor before default behavior changes. |
| Battery/Wi-Fi bar | Existing Omarchy shell plugins `omarchy.network`, `omarchy.monitor`/power services, packaged NetworkManager/UPower | Prefer their standard APIs and existing configuration; lab's standalone sysfs/status-file widgets duplicate distro infrastructure. Confirm they show truthful net current/charging and private network details aren't leaked in published evidence. Add only a demonstrated generic missing capability. |
| Foot locale/rootfs completeness | Omarchy `system/{packages.txt,assemble-rootfs}`, `desktop/configuration/`, artifact tests | Build full signed userspace with Python/dbus/NetworkManager/UPower and generated/selected locale rather than deploy the stripped lab root's missing-library/language workaround. Check Foot launch and shell prompt in finished artifact. |
| RAM desktop independent of USB | Omarchy/Orchard explicit root-source contract and RAM example first | Current root is a copied subset with RAM state, not an official full installed system. At 1GiB RAM, measure full desktop compression/working-set/ZRAM headroom; do not silently unpack multi-GB installed userspace into RAM. A new compressed-root source is a separate Orchard runtime-path PR if needed. |
| Native ASP storage/install | Native kernel storage driver/DT, `src/orchard/apple/apfs.py`, `src/orchard/install_{layout,device,remote}.py`, root initramfs | Existing NVMe paths for other SoCs do not qualify A7 ASP or iOS12 APFS resize. Read-only 4KiB checks and host scratch rehearsals are insufficient for durability/resize/install. Keep descriptor `install=false` until all write/recovery gates and explicit authorization. |

## Focused PR sequence

Contributing says one **device** topic includes its descriptor, firmware
recipe, DT, drivers, configs and host support; shared tooling and new root
sources are separate topics. Therefore avoid a dozen disconnected driver
PRs that imply a usable device before there is one. Split logical commits
inside the device PR, and dependent PRs only where contracts/topics warrant.

1. **Existing Orchard #53, firmware preparation.** Preserve its limited
   scope and draft status. At inspection GitHub reports mergeable/clean;
   rebasing is not the missing integration work. Re-run converter/full CLI
   tests on the selected base before updating. Its private mixin already
   uses the normal data-only archive shape; do not import distro Python.
2. **Omarchy keyboard opt-in code, independently reviewable.** Small local
   branch `agent/keyboard-auto` adds `OMARCHY_KEYBOARD_AUTO=1` support to the
   existing controller; manual default remains. Actual subprocess tests
   use native fixture exec/identity/signals, including lazy launch and
   restart. No J72 descriptor claim, default-focus claim or Foot patch is
   bundled. Exact Wayland/device test remains before requesting merge.
3. **Orchard A7/J72 native RAM device PR.** Build the normal apple-4k
   profile; logical commits for base DT/boot, providers/SPI, touch/firmware,
   battery, HSIC/USB Wi-Fi, source policy and descriptor/evidence. Declare
   incomplete features honestly, keep install disabled. Can stage an early
   RAM console subset as experimental with later feature commits, but each
   claimed feature requires the submitted revision's physical evidence.
   Depend on #53 only when its converter is actually consumed by the recipe.
4. **Orchard shared contract/root-source PR only if required.** A new RAM
   desktop root path or A7 adapter contract belongs here, with both
   distributions updated if producer arguments/files change. Avoid adding
   an experimental #35 payload escape hatch into normal release assembly.
5. **Omarchy finished-image/J72 desktop PR.** Add only gaps demonstrated by
   fresh artifact tests: client IME behavior, memory policy, supported
   resolution/scale and UI capability presentation. Link the exact Orchard
   dependency and merge it first; no duplicate hardware drivers in Omarchy.
6. **Orchard A7 storage/install PR, later.** Native read/write/flush/error
   handling, iOS12 APFS compatibility, plan/recovery qualification, then
   authorized installation and exact cold launch. This remains separate
   from the RAM device milestone and is not authorized now.

## Reproducible-build and qualification gates

- Public source inputs: pinned Orchard/Omarchy/kernel/loader commits,
  resolved configs, attributed logical changes, signed userspace package
  receipts, component hashes and build commands. Private inputs: Apple
  firmware, per-unit MAC/calibration/ADT and local images remain private.
- Build native AArch64 with Orchard's toolchain containers; no host-kernel
  replacement. Reuse published components/cache where inputs match. Check
  disk space before large builds and never delete another session's cache.
- First dry run: resolve a J72 board without device access, build DTBs and
  binding validation, compare resolved config changes for apple-4k **and**
  apple-16k, build modules against the same kernel, check imports/vermagic,
  run firmware synthetic tests and private owner-byte equivalence.
- Run Orchard unit and distribution-contract tests; Omarchy unit tests,
  `release.audit`, Orchard `manifests --verify-local`, finished-artifact
  desktop smoke/input checks. No test result from lab kernel #35 replaces
  an exact-revision cold boot.
- First new-stack physical boot: direct Pi, one owner/process group, both
  ACM/NCM rescue shells, exact model/kernel/boot receipt, display/brightness,
  touch press/release/multi-contact/idle recovery, Home, keyboard repeats,
  Wi-Fi/HTTPS, normal teardown. Stop at first integrity/cleanup failure.
- Second physical stage: qualified hub and unplug/replug/source changes,
  sustained net energy gain under the real desktop, independent baseline
  restoration, fault/thermal recovery, input and USB continuity. Do not
  label a charging icon or isolated positive sample a sustained power pass.
- Only after RAM qualification: design/authorize native scratch writes,
  durability and failure recovery, root-size/media planning, reversible
  install and normal launch. Treat fully PC-free cold startup as another
  boot-chain engineering milestone.

These are engineering gates, not one DFU each. Repack userspace and stage
matching modules in one healthy boot where ownership permits; reserve DFU
for loader/kernel/DT changes and cold-start confirmation. Build and host-test
every candidate before requesting a physical sequence.

## First native Orchard engineering action

Start one source-only **J72 SPI topic branch** from pinned generated Linux
`df7c930f80abd32a054617cd30ea450b7acfb3e0` under Orchard's documented kernel
worktree directory. Port the two measured facts (explicit payload transfer
and bit-order semantics) into the current `spi-apple.c` match-data model and
its binding; no new behavior for existing compatibles. Preserve attribution
to the lab baseline and the current native controller implementation.

When the Pi has no deadline-sensitive charging lease and sufficient free
disk, run build-only checks with `O=.orchard-out`: resolve
`orchard_apple4k_defconfig`, compile the changed driver and its dependency
closure with warnings enabled, and run binding/schema checks. Resolve the
same logical config change for `orchard_apple16k_defconfig` and review the
diff. Add parser/transfer fixture checks where they establish the bounded
FIFO behavior; do not label compilation as a controller regression test.

The next dependent source work is the measured J72 base/DT/providers and
normal A7 boot adapter, so the same branch series can eventually build
through Orchard's `--kernel-tree DIR` path in an explicit RAM example.
`--platform apple-4k` alone currently builds only registered boards, not
J72. Create the descriptor/DTB mapping before claiming a J72 artifact.
`--explain` reports build commands; it is not a promise of no execution.
Export the tested topic with `tools/kernel-tree/export.py` only after the
native exact-revision hardware gate. No new DFU is required for source and
build-only work.

## Host-checked desktop code ready for review

The independent Omarchy commit `fa25972a83a279bdd7e5edc9ff6013cd211562fb`
adds six controller lines, a keyboard-focus experiment document and eight
real-controller tests. Its full Omarchy unit suite passes **113 tests** on
this host against the inspected Orchard source. No tests were skipped.
The fixture compiles with `-Wall -Wextra -Werror`; the tests exercise actual
process exec, signals and `/proc` executable identity. No Wayland session,
new full root image or physical device is tested by that result.

Before this can become the default tablet experience, test the built
keyboard plus signed/selected Foot and actual Labwc together. The manual
default in the candidate allows useful source sharing without representing
the known lab/client combination as already integrated.

## Source review and host results

The isolated Omarchy change is supplied as a [reviewable patch](code/desktop/upstream-keyboard-auto/) against the exact revision above. Its full unit suite passes 113 tests; eight are new controller subprocess tests. It has not been tested in the actual Wayland session or a freshly assembled desktop artifact, and no upstream PR was opened by this preparation.

Wi-Fi PR #53 replayed cleanly onto Orchard `6b5fca6` in an isolated local worktree. Eleven converter tests and five producer/distribution-contract tests pass. The remote PR branch is unchanged. A broad Orchard-suite run used an uninstalled checkout and was stopped/reaped after isolated subprocess imports failed; it is not a full-suite pass. Final whole-suite qualification needs a correctly installed isolated test environment.

The immediate hardware follow-up is the [separate inactive-state candidate](code/touch/inactive1235/), which passes host replay/build/preflight but is device untested. Its lab result will inform native driver work; it will not qualify a newer Orchard kernel by itself.
