> **Historical report / superseded plan.** Start with the [current status](../../J72-PROGRESS.md) and [replication guide](../../QUICKSTART.md). Statements below describe their original session, not current support.

# Completing J72 power support

Prepared 2 November; current status updated 3 November 2026. The bounded Linux
input/storage/power observation is complete: input/restoration pass and net
charge fails. iOS charging at 81% is now confirmed after PIN entry by the owner
and two diagnostic readings. Follow the
[session record](SESSION-2026-11-03.md) and [finishing plan](FINISHING-PLAN.md).
[Next session ordering](NEXT-SESSION-PLAN.md) batches input, native-storage idle
measurements and guarded charging into one Linux boot.

The follow-up charging candidate loaded disabled, but three touch layout
rejections stopped precharge checks before arming. No power observation ran.
Normal cleanup/iOS charging after unlock pass. The [next changed batch](NEXT-POWER-COMPARISON.md)
tests the separate state-1 inactive candidate after a captured native report
identified that refusal. The prior resync trial recovered no frames in 495
extra retries and stopped before charging. Capture-before-shutdown and normal
cleanup now pass on device. Input gates remain strict.

## 1. A repeatable known-hub workload

The #34 reduced-brightness hour integrated positive net charge; the #35
normal-brightness hour lost 97.30 mAh after a thermal hold. Source, temperature,
brightness and storage-controller state differ. Compare measured conditions
before attributing the difference to one component.

The 3 November fixed-brightness 802/ASP-active run lost 181.13 mAh over 90 minutes.
All five active pauses began at 4.201 V. Four restarts passed; after the fifth,
the pack remained above the common 36.5°C restart threshold. Peak temperature
was 36.7°C, below the actual thermal-trip cutoff. The final warm wait dominated
the tail of the run; this is a cause identified in the trace, not proof that a
policy change will produce net gain.

The separate [restart candidate](../../code/charging/voltage-resume35/) permits only
voltage/SOC-hold restart in the existing active 36.6–38°C range. Initial starts,
expired windows and actual thermal recovery retain the cool gate. Actual
thermal history is latched. Hard active cutoffs, source/current/window/fault
and restoration rules remain intact. Host tests/build pass; **device untested**.
Keep brightness, governor, Wi-Fi, ASP and the qualified touch worker fixed for
the comparison; integrate every hold. The current touch changes mean this is
a combined-workload qualification, not an isolated power-policy comparison.

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
own lease. The 2 November #35 loss followed an actual thermal hold. The 3 November
loss followed voltage holds and a warm restart wait below the thermal cutoff.
Keep these experiments distinct when inspecting input-limit and load changes.

## 3. Power for the first internal-storage milestone

The [first internal base](INSTALL-TRANSACTION-PLAN.md) remains read-only, with
RAM runtime and Pi-assisted startup. Its power test must include the retained
storage controller. Later writable persistence adds flash/flush and power-loss
qualification. Fully PC-free startup remains a separate boot-chain milestone.
