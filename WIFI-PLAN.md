# J72 Wi-Fi preparation

## Latest: Wi-Fi connection, HTTPS and SSH passed

The next cold boot succeeded with complete recovery and brighter startup.
Private firmware loaded and re-enumerated; Linux created `wlan0`. Scanning,
WPA2 association, DHCP, DNS, Wi-Fi-bound HTTPS (HTTP 200) and pinned-key Wi-Fi
SSH all passed. Deliberate disconnect/reconnect and an explicit DHCP renewal
also passed, with USB recovery still available. Wi-Fi SSH can control the live
RAM system. The owner confirmed the brighter desktop, touch, menu and keyboard.

The [actual HSIC provider and USB driver source/patches](code/wifi/usb-hsic/)
are now shared with measured limits. The [Wi-Fi bar icon](code/desktop/wifi/)
shows connection, signal and frequency in a tappable popup. Desktop-user HTTPS
also passed after supplying the DHCP resolver through a RAM file bind; the
original desktop image remains unchanged.

The provider is still active: its full stop/restoration, sustained traffic,
charging with Wi-Fi, suspend/resume and repeat cold boots remain unqualified.
The desktop still uses USB/NBD and cannot yet be unplugged. No installation
or internal-storage writes occurred. Earlier preparation and transport-stage
records follow; their “not yet uploaded” statements describe those stages.

## Earlier: J72 Wi-Fi USB enumeration and ROM identity measured

The matched #34 RAM kernel enumerated the internal radio at high speed as
**USB `0a5c:bd1c`**. A strict, complete 24-byte ROM query returned chip
**`0x4324`, revision 6**, **576 KiB RAM**, remap base `0x60000000`.
Linux calls chip `0x4324` **BCM43241**; the owner-local Apple firmware uses
the `4324b5/dureza` naming. Do not replace the observed revision with a
revision inferred from that filename.

No radio firmware has been uploaded. Scan, association and Wi-Fi SSH on this
J72 remain untested. The host stop guard failed and retained its HCD, IRQ,
DMA allocations, GPIO and power owners. Both external USB recovery shells
remained usable. A read-only audit then found RUN still set in the hardware
and cached EHCI command, with its frame counter advancing and interrupts
disabled. The original stop code bypassed the EHCI driver's lock and cached
command; this is a concrete lifecycle defect to fix before firmware testing.
A separate same-boot rescue then called the standard HCD shutdown callback,
verified hardware halt **before** removal, and removed the USB bus. Independent
readback showed RUN clear, HALT set, interrupts disabled and all three ports
companion-owned. The original GPIO/power/device allocations remain retained
until reboot, so full original-state restoration has **not** passed.

The boot also exposed an incomplete recovery-module index in the new overlay.
Matching #34 NCM, FunctionFS, NBD and evdev modules and combined dependency
indexes were supplied in RAM through serial. NCM and serial then both worked,
without another DFU. A future cold-boot payload must include that recovery
closure from the start. The desktop subsequently reported ready with continuous touch active; the owner screen/input check is pending for this #34 boot.

The earlier native PHY, reset and HOST_READY observations remain useful:
HOST_READY high made DEVICE_READY rise, and the standalone handshake diagnostic
restored its original state. That earlier cleanup success does not establish
cleanup of the later enumeration probe.

## Orchard reuse review after the ROM identification

Rechecked current Orchard main at
[`824bf034`](https://github.com/OrchardLinux/orchard/tree/824bf0346ae4c3debd208cd34b053130576af60c),
including current pull requests and relevant issue discussions. The old
`OrchardLinux/hardware` URL redirects to `OrchardLinux/orchard`.

| Existing work | What to reuse | J72 boundary |
| --- | --- | --- |
| [P105 contribution, PR #10](https://github.com/OrchardLinux/orchard/pull/10), source head `407c9101` | Its source-pinned Cascadia USB/HSIC firmware path is the closest transport reference. | P105 is A5/BCM4334, USB `0a5c:bd1a`; its platform addresses, firmware and power sequence are different. This closed PR's code is not present in the reviewed main tree. |
| [Cascadia USB patch at the P105 pin](https://github.com/rzxvx/Project-Cascadia/blob/c20b85ebb951c704d7e3a664c378dde8276e3928/patches/tree/0001-cascadia.patch) | Boot commands with `wValue=1`, HOST_READY around startup, skipping the incompatible reset-config path, USB reset/re-enumeration, interrupt notification draining and appended-NVRAM download length. | These are adaptation candidates, not measured BCM43241 firmware behavior. J72's strict GETVER with `wValue=1` has now passed. Preserve attribution and narrow quirks to the observed device. |
| [Cascadia TRX/NVRAM packer](https://github.com/rzxvx/Project-Cascadia/blob/c20b85ebb951c704d7e3a664c378dde8276e3928/scripts/trx-add-nvram.py) | Board settings as NUL-separated, aligned NVRAM with length token; update TRX lengths and CRC; use the owner's actual MAC. | Use matching private J72 firmware and board inputs. Do not use P105's firmware, reference MAC or calibration. Bounds and malformed-input refusals need strengthening before use. |
| [A7 J85 field report](https://github.com/OrchardLinux/orchard/blob/824bf0346ae4c3debd208cd34b053130576af60c/docs/bring-up/j85.md) and [PR #5 discussion](https://github.com/OrchardLinux/orchard/pull/5) | Another A7 device reportedly reached brcmfmac, wlan0, DHCP and Wi-Fi SSH. Useful feasibility evidence. | The merged contribution is documentation. No reproducible J85 Wi-Fi implementation is included, and it does not establish this J72's chip/revision or settings. |
| [Common Orchard Wi-Fi patches](https://github.com/OrchardLinux/orchard/tree/824bf0346ae4c3debd208cd34b053130576af60c/kernel/patches/drivers/wifi) | Review reset-work cleanup and firmware-handshake port authorization for our kernel. | Source versions differ; these do not add the missing J72 USB ID/firmware mapping. |
| [OTP/NVRAM selection, PR #3](https://github.com/OrchardLinux/orchard/pull/3) | Exact board/vendor selection and refusal of unrelated fallback firmware. | Its implementation is PCIe. Our radio is USB/HSIC. |
| [Firmware-specific P2P exclusions, PR #20](https://github.com/OrchardLinux/orchard/pull/20), and [issue #22](https://github.com/OrchardLinux/orchard/issues/22) | Match quirks by actual firmware identity; load the vendor helper before first bind. | Their BCM4355 IDs and failed PCIe re-probe are not J72 measurements. |

No ready-made J72 `0a5c:bd1c` / BCM43241 USB implementation was found in the
reviewed main tree or listed PRs. Mainline names the chip and has BCM43241
**SDIO** firmware mappings, including revision 6 in its B5 range; those SDIO
files are not a USB firmware solution.

### Next implementation batch

1. Fix EHCI shutdown through the owning driver's synchronized lifecycle,
   and attach its power domain before binding the platform driver.
2. Include the complete matching recovery-module closure in the next payload.
3. Adapt a narrowly matched USB ID and chip/revision firmware mapping from
   the reviewed Cascadia transport, preserving strict transfer-length checks.
4. Build a validated private J72 TRX/NVRAM image using the owner's board data
   and MAC. Retain CRC, bounds and length-token checks.
5. Qualify download, startup, re-enumeration and clean failure in one boot;
   only then scan, associate, obtain DHCP and test Wi-Fi SSH/HTTPS.

## Next firmware test prepared

The v3 candidate builds for the same exact #34 kernel. It incorporates the
measured standard-driver shutdown path, attaches the power domain before
binding, and can leave the radio host active for several same-boot checks.
Firmware binding is explicitly disabled until the host has verified the ROM,
private firmware and vendor-helper readiness. The next overlay includes the
complete recovery-module set and starts at owner-requested brightness 1604/2047.

Offline verification passes 84 actual-source HCD/lifecycle cases under UBSan,
plus USB transfer/ROM/TRX checks and [18 synthetic packer cases](code/wifi/usb-firmware/).
The private J72 image passes CRC/layout/size checks. **Cold boot and radio
firmware startup with this candidate remain untested.**

The owner confirmed the menu and on-screen keyboard in the repaired #34
desktop; brightness was then raised from 802 to 1604 in that live session.

## Same-boot network preparation completed

The desktop image lacks Wi-Fi tools and an SSH server. A separate RAM-only
userspace bundle is now staged privately, without modifying that image. Native
ARM64 tool checks, pinned-key localhost SSH and exact-bootstrap BusyBox bundle
transfer passed. The reusable [network scripts and offline checks](code/wifi/network-userspace/)
are published; no archive, credentials, keys or firmware are included.

Orchard's [firmware-handshake port-authorization fix](https://github.com/OrchardLinux/orchard/blob/824bf0346ae4c3debd208cd34b053130576af60c/kernel/patches/drivers/wifi/0004-wifi-brcmfmac-Report-port-authorized-after-the-firm.patch)
now builds in a separate exact-#34 driver copy. Sixteen actual-source
connection/authorization combinations pass under UBSan. Only `cfg80211.c`
changed from our previous candidate; the USB implementation is identical.
The updated module will replace its RAM file **before first load**; the
already pinned cold-boot payload is unchanged. This fix reports successful
firmware PSK/SAE handshakes to userspace; it is not evidence of association.

Next boot: verify recovery and brighter startup, stage the RAM network tools,
qualify firmware startup, then scan. If scanning succeeds, obtain the owner's
network profile and test association, DHCP/renewal, DNS, Wi-Fi-bound HTTPS and
pinned-key Wi-Fi SSH in the same boot. Keep USB recovery available. Original
power/GPIO owners from the previous boot were released by restarting to iOS,
which the host now confirms. Full cleanup of the new provider remains untested.
**No radio firmware has yet been uploaded; none of these iPad network checks
has passed.**

## Earlier: HSIC register and power-owner observation passed

A same-boot diagnostic read control `0x4`, configuration `0x153`, and four
USB clock configuration words already set to `0x108`. The existing kernel
power-domain owner restored HSIC1 and its USB2HOST0 parent after the read.
HSIC1 enters automatic clock gating after a successful resume; the diagnostic
now recognizes the owning driver's state semantics without raw gate writes.
[Source, host fault tests and measured limits](code/wifi/hsic-phy-observer/).

The next step is a bounded native PHY transition with exact restoration of
control `0x4`. Radio reset/ready sequencing, USB enumeration, chip/firmware
adaptation and scan/association remain open. No radio firmware or calibration
has been published; this observation did not enable the radio.


Reviewed 1 November 2026 against Orchard
[`824bf0346ae4c3debd208cd34b053130576af60c`](https://github.com/OrchardLinux/orchard/tree/824bf0346ae4c3debd208cd34b053130576af60c).
This includes offline preparation and explicitly bounded live observations. No WLAN firmware was uploaded.
See the [current session plan](DFU-PLAN.md) for N1 boot readiness; the
Wi-Fi bus/transport work below remains unfinished.

## Exact device and present result

- iPad Air 1 Cellular, J72 / iPad4,2, A7, iOS 12.5.7.
- Owner-local iOS records identify BCM4324B5, module `dureza`, vendor USI,
  on internal EHCI/HSIC. The iOS-observed USB identity is `0a5c:bd1c`;
  Linux now confirms the same USB identity; ROM chip `0x4324`, revision 6.
- A read-only EHCI capability observation passed: EHCI 1.0, three ports,
  with the Linux-owned power domain restored afterward. This did not start
  the host or enumerate WLAN.
- The separate #34 target kernel enables cfg80211, rfkill and USB brcmfmac.
  It has booted and performed the USB/ROM query above. Its desktop packaging still needs correction. The earlier #33 image disables wireless.
- Matching owner firmware and board data passed a local TRX CRC/format check.
  They remain private. No radio firmware startup, scan or connection is claimed.

## What Orchard can supply

| Starting point | Reuse for J72 | Boundary |
| --- | --- | --- |
| [Common brcmfmac fixes](https://github.com/OrchardLinux/orchard/tree/824bf0346ae4c3debd208cd34b053130576af60c/kernel/patches/drivers/wifi) | Review reset cleanup and connection authorization handling against the J72 kernel. | Patch context differs between our 7.0.12 development kernel and current Orchard. |
| [OTP/NVRAM selection, PR #3](https://github.com/OrchardLinux/orchard/pull/3) | Preserve board/vendor-specific firmware selection. | Its implementation changes PCIe code; our radio is on USB/HSIC. |
| [Firmware-specific P2P exclusions, PR #20](https://github.com/OrchardLinux/orchard/pull/20) | Diagnose advertised-but-unsupported features by exact firmware version. | BCM4355 firmware IDs do not establish a BCM4324B5 quirk. |
| [J81 profile](https://github.com/OrchardLinux/orchard/blob/824bf0346ae4c3debd208cd34b053130576af60c/devices/j81/device.toml) | Firmware recipes and scan/association qualification sequence. | Air 2 BCM4350 is PCIe; its power sequence cannot enable J72 HSIC. |
| [Second-unit J71b report, issue #22](https://github.com/OrchardLinux/orchard/issues/22) | Ensure the vendor helper is available during the first probe and preserve recovery access. | A failed PCIe re-probe reset that unit; this is a useful failure warning, not a measured J72 result. |

The reviewed Orchard tree has no J72 HSIC/BCM4324B5 implementation. The
[Project Cascadia USB changes](https://github.com/rzxvx/Project-Cascadia/blob/0237307d0d74910b7a682200252403d0fe5809b7/patches/tree/0001-cascadia.patch)
are a closer bus-level reference: they address HSIC host-ready signaling,
USB download requests, firmware re-enumeration and NVRAM carriage. Their
A5/BCM4334 device ID, register addresses and timing are not J72 qualification.
Keep original attribution when adapting any code.

## Concrete preparation completed

The [offline staging helper](code/wifi/prepare-j72-wifi.py) now:

1. Checks the pinned kernel image, configuration, symbol table and existing
   module hashes. The two development kernels share a release string, so
   release/vermagic alone cannot select the correct touch module.
2. Selects the continuous-touch candidate pinned to the exact #34 configuration.
3. Checks vermagic, all strong imported symbols and the staged module dependency
   closure for rfkill, cfg80211, brcmutil, brcmfmac, **brcmfmac-wcc** and touch.
   CRC-based ABI checking is unavailable because CONFIG_MODVERSIONS is disabled;
   this checks exports and recorded build provenance, not arbitrary compatibility.
4. Builds a private module directory and depmod indexes without installing host
   modules or loading anything. The vendor helper was missing from the earlier
   shortlist of four wireless modules; it is now included.
5. Checks original private TRX CRC and board-data format, retains them as private
   inputs, and produces hashes for the staged files. It does not transform the
   firmware, invent a MAC address or place it under a guessed driver filename.
6. Reports that the built brcmfmac USB aliases **do not match** the identity seen
   in iOS. A successful kernel build therefore remains `probe_ready=false`.

The real local candidate passed these offline checks. Seven synthetic refusal
tests cover changed inputs, incomplete receipts, path/symlink escapes, bad TRX,
already-packed input and overwriting a pinned candidate. The
[sanitized preparation receipt](code/wifi/VALIDATION.json) contains no firmware,
calibration, credentials or device-specific identifiers.

This is a module/input staging area, **not a complete boot payload**. Kernel
selection, DT/PHY integration, matching battery/charging components, the root
overlay and a pinned launcher bundle remain to be composed and checked.

## Remaining work, in order

- [ ] Audit exact J72 reset polarity and initial state, AP/DEVICE_READY signaling,
  HSIC PHY controls, clock gates and power-domain dependencies. The PMU GPIO
  register mapping and read-only baseline are known; that does not authorize
  guessing its write sequence. Keep the external USB gadget usable.
- [ ] Implement J72-specific PHY/DT ownership and bounded startup/rollback.
  Use existing Linux domain owners; avoid competing direct power writes.
- [ ] Compose one matched boot bundle with continuous touch, the battery widget,
  recovery USB and Wi-Fi modules. First inspect internal USB descriptors with
  WLAN binding held back. Require stable enumeration and successful cleanup.
- [ ] Adapt only the measured BCM4324B5 USB download path: ID/chip/revision match,
  firmware request naming, board NVRAM, host-ready and re-enumeration behavior.
  Do not force-bind the unchanged brcmfmac driver to bypass missing support.
- [ ] Make `brcmfmac-wcc` available for the first bind. Its dependency is
  brcmfmac itself: normal module-request support and complete indexes, or an
  explicitly deferred binding sequence, are needed. A simplistic preload
  ordering is not a substitute for understanding that dependency.
- [ ] Stage a signed regulatory database trusted by this target kernel, plus
  network userspace. Retain calibration/country data; do not bypass regulation.
- [ ] Test firmware startup, interface creation, scan, association, DHCP, DNS,
  HTTPS, sustained traffic, disconnect/reconnect and Wi-Fi SSH in that order.
- [ ] Qualify the combined desktop, continuous touch and guarded charging with
  Wi-Fi active; measure idle power and thermal behavior.

Where the prepared code permits, several checks share one RAM boot. A kernel
or DT change needs another DFU. A new DFU will be requested only after the
concrete change and artifact checks are ready.

Wi-Fi alone does not make the current desktop unplug-safe: its filesystem is
still served over USB. See the [independent-operation plan](INDEPENDENCE-PLAN.md).
