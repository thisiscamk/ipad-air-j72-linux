# Remaining DFU batches — 3 November 2026

The current Linux observation is complete. Normal cleanup passed and iOS reboot
was requested. After PIN entry, the owner and two iOS diagnostic readings
confirm charging at 81% on the powered hub. The next comparison is prepared;
its boot uses the proven direct-Pi connection. See the [full finishing plan](FINISHING-PLAN.md)
and [session record](SESSION-2026-11-03.md).

## Completed boot

- [x] Direct-Pi DFU and unchanged #35 RAM payload.
- [x] Revised touch worker self-check and owner desktop/input checks.
- [x] Wi-Fi/HTTPS/SSH and hub transfer with USB recovery.
- [x] ASP-absent and ASP-present idle recordings; native read-only checks.
- [x] Complete 90-minute observation: input/normal cleanup pass; **net charge fails**.
- [x] Analyse holds: five voltage pauses, four restarts; final warm restart blocked.
- [x] Independent restoration to `02`, normal cleanup and iOS reboot request.
- [x] Confirm iOS is visible and charging on the powered hub; owner and diagnostics pass.
- [x] Build/test separate voltage-hold restart candidate; **device untested**.

No internal filesystem was mounted or written. Natural thermal restart,
net gain for this workload and unattended charging remain open.

## Future boot ledger

Each row is a proposed **batch**, not a promise of exactly one successful DFU.
All new tools must be ready before asking the owner to move a cable or press buttons.

| Batch | Work in that boot | Readiness / condition |
| --- | --- | --- |
| C0 — Known-hub power comparison | Same #35 RAM boot and qualified touch worker; only voltage/SOC-hold restart eligibility changes. Fixed brightness 802, Wi-Fi/read-only ASP, full current integration and final restoration. | [Prepared runbook](NEXT-POWER-COMPARISON.md); warning-free build, 49 core scenarios and two branch replays pass. Device untested. iOS/source checks pass; direct-Pi DFU is the next physical action. |
| Q1 — Recovery/RAM scratch qualification | Exact RAM recovery identity, owned-media inventory and guarded disposable RAM APFS/native-I/O experiment. | New harness not built/qualified yet. Preserve the proven v3 rescue image. No internal mutation. |
| Q2 — Conditional follow-up qualification | Resolve a measured Q1/backend issue or finish native writer/flush testing on disposable media. | Only if required. Explain the concrete change; combine compatible checks in Q1 where possible. |
| W1 — Approved installation recovery | With internal APFS unmounted, verify the approved shrink, commit exact GPT changes and write/fully verify the image. | Requires qualified backend, refreshed evidence and separate exact internal-write approval. A proposed normal-iOS resize precedes this boot. |
| L1 — First internal read-only base | Bound the Linux extent, verify the installed base, run desktop/Wi-Fi/input, unplug and return to iOS. | Only after installation and normal iOS coexistence verification. First runtime upper layer stays in RAM. |
| R1 — Repeat launch and endurance | Repeat the pinned local-base boot and normal cleanup, with the required integrated workload. | Needed after first success; does not establish writable persistence. |
| P — Native persistence | Qualify bounded Linux writes/flush, state, updates and recovery. | Separate backend and owner-reviewed trials; boot count not established. |
| C — Autonomous charging | Native J72 source/withdrawal owner; known-source, data/host-loss and endurance tests. | Source observer/event/mux qualification first. Current host lease remains required. |
| F — Other tablet features | Audio/Bluetooth, orientation, idle dim/wake, suspend, GPU and agreed sensors/features. | Scope/priorities to agree; counts depend on actual drivers. Batch opt-in checks when compatible. |
| U — PC-free startup | Exact A7/iOS12 on-device Linux handoff, launcher availability, cold/low-battery/recovery behaviour. | No working route established. Internal storage alone does not provide it. |

Three future boot stages are the best-case route to the first internal read-only
desktop: Q1, W1 and L1. Allow **4–6 DFUs while qualifying those stages**, not a
cap or guarantee. R1 and later persistence/power/startup qualification are
additional; their boot counts cannot yet be predicted honestly.

## Work that does not inherently need another DFU

- Analyse completed results; build/test code and images on the host. The new
  C fenced-I/O core passes host/memory/file tests and an iOS12 object compile;
  native media identity/flush and the RAM ownership harness remain open.
- Normal-iOS root queries after the owner reapplies Amethyst.
- Fresh geometry/GPT/minimum/recovery review in the qualified environment.
- The proposed normal-iOS explicit resize, **only after separate approval** and
  qualification; it is not authorized merely because it needs no DFU.
- Runtime module/userspace checks that preserve the running kernel's qualified
  ownership and cleanup rules. Do not unload/reprobe a failed ASP controller.

## Rules for a request

State the changed artifact or experiment, its preflight result, the exact test
and its stop/cleanup conditions before requesting DFU. Use the proven direct-Pi
boot path; the unchanged hub handoff has failed. Reap the one boot owner before
starting another. Keep firmware/calibration and identifying captures local.

[Earlier dated checklist history](history/DFU-PLAN-BEFORE-2026-11-03.md).
