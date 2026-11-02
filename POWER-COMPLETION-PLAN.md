# Completing J72 power support

Prepared 2 November 2026. The iPad remains in iOS charging overnight.
[Next session ordering](NEXT-SESSION-PLAN.md) batches input, native-storage idle
measurements and guarded charging into one Linux boot.

## 1. A repeatable known-hub workload

The #34 reduced-brightness hour integrated positive net charge; the #35
normal-brightness hour lost 97.30 mAh after a thermal hold. Source, temperature,
brightness and storage-controller state differ. Compare measured conditions
before attributing the difference to one component.

Next session: keep governor and brightness fixed, record actual Wi-Fi power-save
state, screen idle consumption before/after the native storage probe, then run
up to 90 minutes of guarded charging with storage active. The new supervisor
interrupts its charging watcher on input/workload failure. All current, thermal,
voltage, source and independent-restoration guards remain unchanged.

Completion evidence for this workload:

- Positive integrated net current with margin across charging **and every hold**.
- Stable owner-verified input, no unexpected restart and advancing frame counters.
- Fresh gauge coverage and independently verified final baseline restoration.
- Separate records of natural voltage/thermal protection and automatic restart.
  A missing thermal event leaves its hardware restart test open.

This qualifies a stated Pi-supervised hub configuration. Longer bounded endurance,
source-loss/host-loss behavior and repeatability remain before leaving it active
for unattended use. A successful short run alone is insufficient.

## 2. Charging after the Pi is removed

The current module needs a renewed host source lease. It cannot independently
identify an arbitrary wall charger. Local storage does not remove that dependency.
Autonomous charging needs a J72-specific source/withdrawal owner, pack protection,
verified input-limit restoration and coordination with USB/data transitions.

Reusable Orchard references, pinned at 824bf0346ae4c3debd208cd34b053130576af60c:

- [Charging bring-up](https://github.com/OrchardLinux/orchard/blob/824bf0346ae4c3debd208cd34b053130576af60c/docs/bring-up/charging/README.md)
  separates source identification, pack policy and withdrawal handling.
- [Tristar transport](https://github.com/OrchardLinux/orchard/blob/824bf0346ae4c3debd208cd34b053130576af60c/docs/bring-up/charging/tristar-cbtl1610.md)
  explains cached cable identity, CRC/orientation checks and why active mux
  sampling can disrupt an enumerated USB connection.
- The same pinned power patch series includes host-current grants, BC1.2
  identification and input-limit readback after a PMIC reset.

Those experiments target J71b/J71t hardware and D2365/CBTL1610 combinations.
J72's measured PMIC is D2089; confirm its exact port-controller/event paths
against its own stock implementation before adapting register-level behavior.
Do not copy another board's register map, current encoding or attach timing.

Proposed sequence:

1. Map the exact J72 port-controller, existing resource owners and stock source/
   event behavior from already-local evidence. No bus sweep or exploratory read
   of registers with unknown side effects.
2. Build a read-only observer for known-safe presence/configuration evidence,
   without changing mux routes or charging current.
3. Qualify one fixed source first. On detach or uncertain evidence, restore the
   measured baseline and discard the old source identity.
4. Add only the identified, bounded source grant and unchanged battery guards.
   Verify concurrent USB data and independent withdrawal/restoration.
5. Test both cable orientations, reattach/source changes, failure paths, thermal
   holds/restarts and longer endurance before broadening source support.

Keep the native source policy separate from a host supervisor extending its
own lease. The current measured #35 loss followed a thermal hold; preserve that
diagnosis when inspecting input-limit readback and load changes.

## 3. Power for the first internal-storage milestone

The [first internal base](INSTALL-TRANSACTION-PLAN.md) remains read-only, with
RAM runtime and Pi-assisted startup. Its power test must include the retained
storage controller. Later writable persistence adds flash/flush and power-loss
qualification. Fully PC-free startup remains a separate boot-chain milestone.
