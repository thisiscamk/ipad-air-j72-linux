# Orchard source review — 3 November 2026

Read-only review at Orchard head
[`27203f58a218a31ef5bdeb69928608219d40622a`](https://github.com/OrchardLinux/orchard/tree/27203f58a218a31ef5bdeb69928608219d40622a).
The running J72 #35 kernel, module inputs, source grants and policy were not changed.

## Charger and USB role coordination

[`03bf67feb3a0`](https://github.com/OrchardLinux/orchard/commit/03bf67feb3a0d5e6b09d6d34cd7f7f8d22006795)
links the Lightning charger to the USB role switch on the iPad5/iPad6 targets.
Identification precedes data enable; a source event during data uses capability
identity rather than blindly sampling the mux. An epoch distinguishes a new
attachment from an allowance retained for an earlier one. USB recovery has a
bounded fallback if the connector driver does not set a role.

[`38f43b7fbd59`](https://github.com/OrchardLinux/orchard/commit/38f43b7fbd59fdcf5fc339937316361cf236458a)
implements peripheral hold using the pull-up rather than B-valid override on its
target. These are useful architecture and failure-path references for J72's
CBTL1610/D2089 source owner. They are not measured J72 source detection or a fix
for the checkra1n/Pongo handoff through our hub. Its PMIC map, current encoding,
event/ADC details and board grants still need exact J72 review.

## Touch: bounded header/data resynchronisation

[`ec1a4e1ad1d7`](https://github.com/OrchardLinux/orchard/commit/ec1a4e1ad1d76ff60f3576df9573ec6ec7f30566)
adds one data-phase retry for J71b when that phase returns another length header.
The [runtime diagnosis](https://github.com/OrchardLinux/orchard/blob/b5cbeed2fe8ecb868a5c8630cd8cf305f7041a5a/docs/bring-up/touch-runtime.md)
explains why interrupts can continue while no valid input is emitted.

An **offline** review of our archived 2 November J72 anomaly ring found:

| Retained wire records | Data-phase records | Valid 16-byte E1 headers in the data phase |
| --- | --- | --- |
| 32 | 30 | 19; each advertises length 26 |

This supports investigating the same class of phase mismatch. It does not prove
that the J71b patch works unchanged on J72 or explain all 30,547 earlier wire
anomalies: only the last 32 wire records were retained. No raw packets or
calibration are published. Today's rolling-window worker remains unchanged.

Proposed follow-up: a separately built, once-only resync with exact short-header
checksum/length validation, unchanged tags and packet/layout/contact gates,
bounded buffers and unchanged health/cleanup/recovery budgets. First replay
archived private records and malformed/short/oversized/second-header cases
offline. Then compare on J72 in a changed session; do not introduce it halfway
through today's fixed-workload observation.

## Resize/writer references

Reviewed Resize APFS at
[`ac1658923378dcb800523d7dcd45002fc2bc5862`](https://github.com/OrchardLinux/resize-apfs/tree/ac1658923378dcb800523d7dcd45002fc2bc5862),
particularly its [native helper](https://github.com/OrchardLinux/resize-apfs/blob/ac1658923378dcb800523d7dcd45002fc2bc5862/Sources/NativeSystem/NativeSystem.c).
Descriptor restrictions, cache synchronisation and a gated detached worker are
useful references. Each needs iOS12/J72-specific qualification; source review
does not qualify the newer app as our installer.

Hoolock's [tools documentation](https://github.com/HoolockLinux/docs/blob/23ebe1fbc375599221553a7e1815e5de182a6b42/tools/README.md)
and [resizer](https://github.com/HoolockLinux/docs/blob/23ebe1fbc375599221553a7e1815e5de182a6b42/tools/resize.c)
describe explicit sizes, online-I/O freezing, older-iOS size-zero hazards and
SEP prerequisites. The RAM APFS proposal must prove owned-media identity and
real memory/geometry before formatting. It cannot qualify encrypted internal
shrink or real media durability. No snapshot deletion or internal mutation is
part of the review.

## Reproducible integration

The reviewed Orchard head includes new component/producer and distribution-input
contracts. Future J72 integration should pin this interface and record explicit
kernel, loader and tool inputs; it should not substitute a moving nightly into
today's measured build. Wi-Fi draft PR #53 remains separate from native HSIC/DT
and registered-profile integration.
