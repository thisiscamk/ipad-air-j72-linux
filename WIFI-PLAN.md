# J72 Wi-Fi preparation

Reviewed 1 November 2026 against Orchard
[`824bf0346ae4c3debd208cd34b053130576af60c`](https://github.com/OrchardLinux/orchard/tree/824bf0346ae4c3debd208cd34b053130576af60c).
This is an offline preparation record. No WLAN firmware was uploaded.
See the [current session plan](DFU-PLAN.md) for N1 boot readiness; the
Wi-Fi bus/transport work below remains unfinished.

## Exact device and present result

- iPad Air 1 Cellular, J72 / iPad4,2, A7, iOS 12.5.7.
- Owner-local iOS records identify BCM4324B5, module `dureza`, vendor USI,
  on internal EHCI/HSIC. The iOS-observed USB identity is `0a5c:bd1c`;
  Linux descriptors are not yet captured.
- A read-only EHCI capability observation passed: EHCI 1.0, three ports,
  with the Linux-owned power domain restored afterward. This did not start
  the host or enumerate WLAN.
- The separate #34 target kernel enables cfg80211, rfkill and USB brcmfmac.
  It is built, not boot-qualified. The tested #33 image disables wireless.
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
