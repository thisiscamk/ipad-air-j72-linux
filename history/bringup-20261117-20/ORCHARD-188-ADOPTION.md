# Orchard PR 188: conservative J72 adoption plan

Orchard PR 188 merged as `4f5055b` on 20 November 2026. It provides the shared
ANS1/ASP kernel driver and the normal Orchard install/launch plumbing. It does
not enable A7 boards, deliberately, because their device-tree data and ANS
RTKit protocol were not hardware-qualified.

## Reuse unchanged after baseline resync

- ASP block driver and bindings.
- A7/A8X ANS mailbox match and the opt-in RTKit endpoint-map callback.
- `CONFIG_APPLE_ASP=m` and apple-4k initrd loading of `asp`.
- Installer recognition of the writable `asp<N>n1` user namespace.
- Orchard's ASP udev rules for PARTUUID/UUID links.
- Auxiliary namespace write/flush refusal and the normal Orchard
  RAM/read-only/read-write/install test order.

## J72-specific work still required

1. Add s5l8960x ANS, mailbox and board enablement nodes using measured J72 ADT
   addresses, interrupts, power domain and reset data. Do not copy t7001 values.
2. Add the `asp` alias and a no-map firmware reservation whose address and size
   the loader fills. Verify the loader actually populates it before Linux.
3. Read the ANS RTKit protocol version without issuing storage commands. PR 188
   supports the endpoint-0x20 path for RTKit 11+ and intentionally omits
   Hoolock's RTKit 10 behavior. If J72 reports 10.x, port and review that support
   before probing ASP.
4. Prove discovery and namespace classification read-only. Confirm only n1 is
   writable and every auxiliary namespace rejects writes and flushes.
5. Qualify reads, then bounded writes plus flush/fsync strictly inside the
   released Linux partition, before allowing `orchard install`.

Hoolock/ipad-nixos already contains a useful A7 draft: the same ANS and mailbox
MMIO bases, AIC interrupts 52-55, and `s5l8960x-ans`. It is a template, not yet
qualified evidence: its power-domain line is marked `/*?*/` and it forces the
ANS power domain always-on. Those two choices, the four interrupts and the
firmware reservation must be checked against the captured J72 ADT and loader
behavior before retaining them.

The active Orchard baseline was not fetched, merged or changed. The review used
a disposable clone and the merged upstream commit only; no upstream action was
taken.
