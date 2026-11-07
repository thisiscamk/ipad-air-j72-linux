> **Archived before the 7 November cleanup.** Read [current status](../../J72-PROGRESS.md).

# Roadmap to a usable J72 Omarchy A tablet

Updated 3 November 2026. The [full finishing plan](../../FINISHING-PLAN.md) is the
current action list; [DFU-PLAN.md](../../DFU-PLAN.md) tracks proposed boot batches.

## Demonstrated

- RAM Linux boot and an unprivileged desktop with touch, Home/menu, terminal,
  on-screen keyboard, display brightness and battery indicator.
- Internal Wi-Fi association, HTTPS, pinned-key SSH, reconnect and unplugged use.
- A RAM-resident desktop with no host filesystem dependency after startup.
- Native read-only 128 GB storage, repeated aligned reads and both GPT copies.
- Restricted iOS12 RAM recovery, guarded inspection and normal iOS return.
- Brief and longer guarded hub charging results under stated workloads. The
  separate #35 normal-brightness hour and today's fixed-brightness run both
  lost net charge. Today's input/cleanup passed; restart-policy comparison
  is prepared offline and device untested.
- Shared original source/tests; Orchard PR #43 merged documentation and retained
  experiment code in a history tag outside the active tree. Wi-Fi draft PR #53
  shares the converter/configuration; native production integration remains open.

## Finish in this order

1. **Dependable input and stated-workload power:** measure the prepared voltage-hold
   restart candidate, verify net gain across all holds and preserve failure evidence.
2. **Storage engineering:** qualify the iOS12 RAM-scratch/native writer mechanisms,
   interrupted-operation handling and exact first-trial proposal.
3. **First internal base:** separately approved resize/GPT/image installation,
   verified iOS coexistence and a Pi-assisted read-only local-base boot.
4. **Persistent system:** bounded native Linux writes/flush, writable state,
   space budgeting, updates and recovery.
5. **Independent power:** autonomous J72 source identification/withdrawal,
   charging/data transitions, thermal handling and endurance without a Pi lease.
6. **Agreed tablet features:** audio/Bluetooth, orientation, idle dim/wake,
   suspend and other requested hardware; agree explicit deferrals.
7. **PC-free startup:** separately demonstrate an on-device A7/iOS12 handoff and
   a startup route after shutdown. No working route is established here.
8. **Upstream integration and release:** pin the Orchard producer/build contract,
   integrate J72 profile/DT/resources and reproduce the stated feature set.

Compatible work can proceed in parallel on the host and be batched into a
prepared boot. Internal installation and any feature's mutation tests retain
their own exact authorization and qualification gates. The host kernel remains
unchanged; Apple firmware and private calibration are not published.

The owner accepts Pi-assisted startup followed by unplugged use as an interim
milestone. A local read-only base, writable persistence, autonomous charging and
fully PC-free startup each have distinct acceptance evidence.

[Earlier roadmap history](../ROADMAP-BEFORE-2026-11-03.md).
