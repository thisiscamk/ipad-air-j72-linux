# Reusing Orchard charging support for J72

Reviewed Orchard `main` at `4f15a70b9c59687fe8cd72b6ea2fbb2823c54d92`
on 2026-10-31; the GitHub head matched the local checkout. This review does
not change the running J72 kernel or charging trial.

## Implementation to reuse

| Orchard component | What it contributes | J72 work before use |
| --- | --- | --- |
| [`drivers/usb/0003`: `usb-psy-name` binding](https://github.com/OrchardLinux/orchard/blob/4f15a70b9c59687fe8cd72b6ea2fbb2823c54d92/kernel/patches/drivers/usb/0003-dt-bindings-usb-dwc2-Add-usb-psy-name.patch) | Associates the USB controller with the charger power supply. | Add the correct J72 supply/link in reviewed DT. |
| [`drivers/usb/0004`: DWC2 VBUS draw reporting](https://github.com/OrchardLinux/orchard/blob/4f15a70b9c59687fe8cd72b6ea2fbb2823c54d92/kernel/patches/drivers/usb/0004-usb-dwc2-gadget-Report-the-VBUS-draw-to-a-power-supp.patch) | For generic PHYs, forwards the host allowance to a power supply from a work item, avoiding sleeping in the USB callback. This addresses the same missing bridge found in our development source. | Port to the measured kernel or integrate with Orchard's normal stack; qualify configure/reset/suspend/disconnect behavior. |
| [`drivers/usb/0005`: Apple host grant](https://github.com/OrchardLinux/orchard/blob/4f15a70b9c59687fe8cd72b6ea2fbb2823c54d92/kernel/patches/drivers/usb/0005-usb-gadget-composite-Report-an-Apple-host-s-current-.patch) | Reports a valid Apple host allowance through the same path. | Do not assume the Pi or this hub supplies an Apple vendor grant; neither was observed in our Linux session. |
| [`drivers/power/0008`: Tristar host allowance](https://github.com/OrchardLinux/orchard/blob/4f15a70b9c59687fe8cd72b6ea2fbb2823c54d92/kernel/patches/drivers/power/0008-power-supply-apple_tristar_charger-Grant-what-the-US.patch) | Limits host allowances to their attachment epoch and avoids mux sampling during active data. | Verify J72 source events, port-controller matching and PMIC ownership. |
| [`drivers/power/0009`: BC1.2 detection](https://github.com/OrchardLinux/orchard/blob/4f15a70b9c59687fe8cd72b6ea2fbb2823c54d92/kernel/patches/drivers/power/0009-power-supply-apple_tristar_charger-Detect-BC1.2-char.patch) | Classifies charging ports early, before enumeration, and preserves a valid result for that session. | Confirm J72 controller/mux/ADC mapping before any detection writes. Do not disturb tonight's active NCM session. |
| [`drivers/power/0013`: PMIC reset/readback handling](https://github.com/OrchardLinux/orchard/blob/4f15a70b9c59687fe8cd72b6ea2fbb2823c54d92/kernel/patches/drivers/power/0013-power-supply-apple_tristar_charger-Restore-the-input.patch) | Rechecks the programmed ceiling and handles an unexpected PMIC change instead of trusting a cached limit. | Verify whether D2089 exhibits the documented D2365 reset behavior; retain conservative rollback on mismatch. |

## Board differences and qualification

Orchard's [charging record](https://github.com/OrchardLinux/orchard/blob/4f15a70b9c59687fe8cd72b6ea2fbb2823c54d92/docs/bring-up/charging/README.md)
is mainly measured on J71b: D2365/CBTL1610, with input limit at `0x0a03`.
Our independently audited J72 input limit is D2089 `0x04c0`; its configured
battery-current ceiling is `0x04ce`. Do not copy the reference register map,
ADC mux, interrupt/event layout, thresholds or board maximum unchanged.
The J72 port controller is now confirmed as **CBTL1610, revision 137** by
owner-local iOS records. It is on I²C2 at address `0x1a`; the board's BrickID
function refers to D2089 ADC channel 6. Detection sequences, event ownership
and ADC interpretation still require verification before control writes.

Orchard documents remaining limits too: BC1.2 classification depends on
running before enumeration, USB-PD is not implemented, and charging suspend
has unqualified parts. A useful architecture is not proof of a complete
J72 charger implementation.

## Planned integration order

1. Retain the measured short hub-current test as a baseline and preserve
   signed current, PMIC readback and data continuity evidence.
2. Verify J72 port-controller identity, PMIC source-event/ADC path and
   board limit/calibration using owner-local inputs and normal iOS evidence.
3. Adapt the existing driver architecture with bindings and match data,
   preserving original authorship and upstream patch layering.
4. Connect DWC2 to the J72 charger supply, identify a charging source before
   enumeration and withdraw elevated limits when the source changes.
5. Build/test the exact revision; qualify bounded then sustained charging,
   data continuity, source transitions and the desktop workload.

No source-detection/mux changes were made during tonight's live trial.
The prototype's explicit source qualification and 30-second rollback remain
separate from this future automatic policy.

## 1 November preparation

Fresh paired iOS observations confirm a 5 V / 1.5 A allowance with data active
on the same powered hub. A separate 1,250 mA / 30-second diagnostic worker is
built against the unchanged #33 kernel. It requires both a configured
high-speed gadget and a lease renewed by a host that checks the qualified
physical hub port. Lease expiry or loss of the required USB state requests
rollback; an independent software deadline still bounds the trial. This is
an interim host-qualified experiment, not autonomous BC1.2 detection.

A separate five-minute variant refuses staging until a captured short result
shows positive current samples, no errors and verified restoration. Neither
new variant has run on the device yet. Kernel builds/modpost, actual-kernel
export/ABI checks, rollback and pack guards, lease expiry, simulated USB
states, host topology refusals and pinned-image preflight passed.

Orchard `main` was rechecked at
`824bf0346ae4c3debd208cd34b053130576af60c`; its power and USB patches are
unchanged from the review above. Wi-Fi preparation also found useful HSIC
transport and firmware-packaging work in
[Project Cascadia](https://github.com/rzxvx/Project-Cascadia/tree/0237307d0d74910b7a682200252403d0fe5809b7).
Its BCM4334/A5 implementation requires adaptation to this J72's BCM4324B5/A7;
its register addresses, GPIOs and device IDs must not be copied unchanged.
Matching owner-local J72 firmware and board data have been extracted and
remain private; no WLAN firmware upload or enumeration is claimed.
