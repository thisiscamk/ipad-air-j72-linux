> **Historical report / superseded plan.** Start with the [current status](J72-PROGRESS.md) and [replication guide](QUICKSTART.md). Statements below describe their original session, not current support.

# J72 native battery and charging integration: next work

Offline source review, 3 November 2026. This is a plan, not a native J72
power qualification. No device commands, boot, register probes or builds were
performed for this review. Leave iOS charging while the owner is away.

## Source baseline

- Native kernel: `linux-j72-spi`,
  local qualification topic `4c8cee77d7d020a68cf8c27f6e1b0384349cfabe`, reviewed
  without edits. This kernel topic is not yet an exported upstream patch series.
- Orchard CLI: `6ae6dfc7afa9756977f7fe96a15141d4f03250d5`.
- Published J72 research: `ipad-air-j72-linux`,
  `8770625de9e1f2a95a872f4d398c67bce24f955e`; especially `code/battery/`,
  `code/charging/maintain35/`, `code/charging/voltage-resume35/` and
  `ORCHARD-POWER-PLAN.md`.
- Local DT preparation reference: `tools/prepare-j72-battery-uart.py`.
  This is historical evidence, not the native producer to retain.

Native paths below are relative to the kernel revision above. Public lab
results describe the earlier research kernel and workload, not this kernel.

## What already exists and can be reused

| Native source | Useful implementation | Remaining J72 boundary |
| --- | --- | --- |
| `drivers/w1/masters/w1-uart.c`; `Documentation/devicetree/bindings/w1/w1-uart.yaml` | `ti,hdq-uart`, exact 57600 baud, 8N2, bounded BREAK/echo/response handling, optional `hdq` mux ownership. | Add and qualify J72 UART5/HDQ DT. Do not duplicate the lab UART driver or old serdev stop-bits patch. |
| `drivers/power/supply/bq27xxx_battery_hdq.c` and `bq27xxx_battery.c` | BQ27545 compatible, serialized high/low/high word reads, asynchronous cache, signed current and standard battery properties. Cached property reads do not perform HDQ I/O. | J72 capacity profile and freshness contract; generic BQ27545 does not select remaining-capacity pairing. |
| `drivers/mfd/simple-mfd-i2c.c` | `apple,i2c-pmic` already supplies shared 16-bit-address/8-bit-value regmap and child enumeration. | Describe verified D2089 power functions as children of the existing Anya PMIC. Avoid a second raw-I2C owner. |
| `drivers/power/supply/apple_tristar_charger.c` | CBTL1610 source classification, CRC/capability checks, source epochs, bounded ramp/readback, pack guards, withdrawal and cleanup. | Implementation and binding assume D2365-family banks, ADC, events and current encoding; J72 is D2089. |
| `drivers/gpio/gpio-apple-d2365.c` | Shared PMIC event ownership; line notification before read-to-clear dispatch; bounded errors/storm handling. | No D2089 match or demonstrated D2089 event/mask/IRQ mapping. Reuse architecture only after evidence. |
| `drivers/usb/dwc2/gadget.c`; `drivers/usb/gadget/composite.c` | Asynchronous `usb-psy-name` allowance reporting, including Apple host grant lifetime handling. | J72 supply/role graph absent; an enumerated gadget alone is not a qualified high-current source. |

`apple_d2365_charger.c` has useful supplier/status separation but its D2365
registers and J172 policy are not J72 support. Existing D2089 touch regulators
own touch supplies only; they do not provide charger or PMU-event support.
`apple-mfi-fastcharge.c` is a USB **host** driver for iOS devices, not a Linux
iPad PMIC driver. Changing the Pi kernel is neither required nor authorized.

## Battery: small, separable first topic

The J72/air1 DT currently describes Anya RTC/backlight/nvmem, with added touch
supplies, but has no UART5, HDQ gauge, battery information or charger node.
`s5l8960x.dtsi` defines only UART0. `s5l8960x-pmgr.dtsi` already has `ps_uart5`.
Existing J71 reference topology is in `t8010-ipad6.dtsi` and
`t8010-ipad7.dtsi`; copy the UART → HDQ → gauge structure, not board values.

1. Add disabled SoC UART5 and a J72-only enable/HDQ/gauge description.
   Historical J72 evidence identifies `0x20a0b4000`, AIC 145 level-high,
   24 MHz reference and UART5 PMGR domain. Verify clocks, pinctrl and exact
   UART binding before enabling. The J72 preparation script and adaptation
   header identify AP GPIO44/function1; a reused generic comment still says
   GPIO34. Resolve against retained J72 evidence, not the generic comment.
   The lab preserved inherited pad state; a native description must account
   for its pin ownership and restoration explicitly.
2. Reuse native `ti,bq27545-hdq` transport. Saved lab identity evidence is
   DEVICE_TYPE `0x0545`. Native HDQ supplies only `bus.read`; it does not
   reproduce the lab's sealed-safe Control DEVICE_TYPE write/query. Do not
   silently add that command to ordinary cache reads. If re-identification
   is necessary, review a separate bounded operation first.
3. Add the smallest reviewed J72 gauge profile/binding adjustment: pair
   RemainingCapacity `0x10` with FullChargeCapacity `0x12`. Native D11/D111
   profiles already use `cache_use_remaining_capacity`; generic BQ27545
   still chooses NAC `0x0c`. Preserve cache-only reads and error semantics;
   do not adopt another phone's property subset or guessed design capacity.
4. Define freshness before any charging consumer depends on this gauge.
   Native BQ27545 refreshes every 30 seconds; the lab guard expected a fresh
   vector within six seconds. A cached read returning successfully does not
   prove that age or coherence. Review bounded refresh cadence plus an
   explicit stale/error refusal, preserving nonblocking property reads and
   a charger rollback deadline independent of potentially stalled HDQ work.

First qualification is telemetry only: no charger consumer, no PMIC current
write, standard serial/SSH recovery retained. Compare supported properties,
signed current, RC/FCC consistency and cache error/timeout behaviour. The
normal desktop battery widget can then consume standard `power_supply` data;
its presence is not evidence that charging works.

## Charging: evidence before a D2089 match

Published J72 evidence identifies Anya/D2089 input limit `0x04c0`, configured
battery-current ceiling `0x04ce`, CBTL1610 revision 137 on I2C2 address `0x1a`,
and BrickID tied to D2089 ADC channel 6. Detection sequencing, conversion
scaling, source events and mux ownership remain unqualified. D2365 reference
ADC channel 1, status `0x42`, control offset `+3`, 500 mA fallback and
`75 + 12.5 × code` encoding must not be assumed valid on D2089.

Required evidence inventory, using saved owner-local iOS inputs first:

- Exact J72 event-status/mask/ack semantics, external PMIC IRQ, source/ADC
  events and ownership shared with RTC/backlight/touch. Event reads may
  clear state; do not discover the layout through register sweeps.
- D2089 ADC selection/completion/result layout, calibration/scaling and
  Tristar routing/restoration order, including protection of active USB data.
- Input-limit encoding and allowed range, baseline/readback semantics,
  battery ceiling meaning, board source maximum and PMIC reset behaviour.
  A nominal lab 1050 mA setting is not proof of the entire D2365 encoding.
- Which capabilities the marked hub, direct Pi and wall charger actually
  advertise, and how attach/detach invalidates them. Keep private addresses,
  raw DT, unit calibration and original captures local.

Minimal source topics, in dependency order:

1. **Battery/DT profile** above, independently reviewable and usable without
   active charging.
2. **D2089 PMIC providers/bindings** for the evidence-supported event/ADC
   functions; shared parent regmap, a single event owner and bounded cleanup.
3. **Tristar D2089 variant**: separate register/encoding/ADC operations or
   match data where necessary; retain common attachment, capability, ramp,
   readback and fault machinery. Preserve or tighten the J72 protective
   limits. Keep unsupported variants refused and existing boards unchanged.
4. **J72 charger/USB DT links**, only after provider and variant gates:
   actual Tristar, PMIC resources, battery dependency, board limit,
   `usb-psy-name` and USB role endpoints. No auto-enabled charger before
   qualification: current Tristar probe can lower a limit, change USB role
   and schedule detection/mux work; binding it is not a read-only experiment.
5. **Distribution reporting**, using standard supply properties and separate
   source/charging/error states. A programmed input ceiling or positive USB
   allowance must not override negative measured battery current.

Do not transplant the whole research maintenance module: it hardcodes the old
kernel/PMIC path, host-renewed source lease and exact register profile. Reuse
its guard/rollback fixtures and measured limits as review evidence. The native
driver must establish source safety itself before a PC-independent result.

## Evidence limits and future device gates

The latest published 90-minute lab run lost **181.13 mAh**, mean **−120.81 mA**,
including voltage holds (brightness 802, Wi-Fi/touch/read-only ASP active).
Baseline `02` restoration and cleanup passed. Earlier reduced-workload net
gain does not qualify this workload. The separate voltage-resume candidate
has only loaded disabled; its active restart policy remains device-untested.
Neither source autonomy nor unattended Linux charging is qualified.

Future gates after the owner returns, with a changed, reviewed artifact:

- Host first: schema/DT, focused actual-C transport/cache/variant fixtures,
  register-range and fault/rollback tests, compatible-selected behaviour;
  preserve the already tested CLI recovery transport and exact build receipt.
- Device A: native gauge only; supported telemetry, coherent refresh,
  disconnected/stale/error behaviour and unchanged PMIC baseline.
- Device B: evidence-bounded source/provider classification with active
  charging disabled; restoration, attach epochs and USB data continuity.
- Device C: short explicitly armed current trial on a qualified source;
  fresh pack guards, independent baseline readback and normal iOS return.
- Device D and later: sustained **integrated net charge including holds**,
  real thermal/voltage restart, source swaps, USB reset/suspend/disconnect,
  gauge failure, PMIC mismatch and cleanup under the intended desktop load.
  Only measured passes can justify leaving the policy active unattended.

These are evidence gates, not a promised DFU count. Combine compatible checks
within a safe boot where possible; failures may require another changed build.
Internal-storage installation remains outside this plan and unauthorized.
