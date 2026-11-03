# Latest: 3 November 90-minute net-charge failure, safe restoration

At fixed brightness 802 with Wi-Fi, touch and read-only ASP active, the run
lost **181.13 mAh**. Five voltage holds and four restarts occurred. The final
restart was blocked above 36.5°C; peak temperature was 36.7°C, without an
actual thermal trip above 38°C. Independent final baseline restoration and
normal input/desktop/radio cleanup pass. iOS reboot was requested; charging
confirmation is pending. [Measured result](NINETY-MINUTE-RESULT.json),
[session diagnosis](../../../SESSION-2026-11-03.md),
[separate device-untested restart candidate](../voltage-resume35/).

The earlier result below is retained as a distinct experiment.

# #35 hour complete: restoration passes, net charging fails

The owner-qualified JCH377 test lasted **3600.535 seconds**, with 1704 fresh
vectors covering 3598.354 seconds. Integrated net battery current was
**−97.30 mAh** (mean **−97.35 mA**), including the protective hold. The battery
indicator moved 39% → 34%; gauge transients are not used to infer charge gain.
This run does **not** qualify sustained charging at normal brightness.

The initial charging phase lasted about 44.7 minutes, with positive readings
up to +199 mA. The unchanged thermal guard entered a hold at **38.1°C**.
Independent readback confirmed the original input limit `02`, without a fault.
The pack did not cool to the restart threshold before the observation ended;
**automatic thermal restart remains unproved**. Brightness was temporarily
reduced from 1604 to 401 during the hold, then restored to1604. The controller
was disabled and its original input limit independently verified at the end.

A separate 60-second `conservative` CPU-governor comparison during the hold
showed no isolated saving; `schedutil` was restored and frequency limits stayed
unchanged. Touch failed during that comparison after its seventh cumulative
recovery; causality is unproved. The [touch record](../../touch/LONG-RUN-20261102.md)
distinguishes acquisition failure from reported hardware restoration.

The desktop unmounted normally. The overall stop wrapper refused its touch
check; evidence was preserved and the remaining radio shutdown was performed
separately with independent hardware readback. Normal iOS return and charging
are owner-confirmed. No internal storage was changed.

The earlier [#34 result](../maintain34/) remains a separate positive test with
reduced brightness and different thermal conditions. Neither test establishes
autonomous source detection, general charger support or unattended charging.

[Final measurements](ONE-HOUR-RESULT.json), [source/build status](RESULT.json).

## Earlier preparation and disabled stage

# Matched #35 charging adapter — disabled load passes

The matching #35 maintenance module was already built with the combined payload.
This host adapter is now prepared and passes pinned-source/module preflight.
The actual policy headers are byte-identical to the #34 controller that passed
the full-hour net-gain and automatic voltage-hold restart test. The #35 module now loads **disabled**, with the original input limit unchanged.
At that earlier checkpoint it was not armed; the active test above supersedes that state. The initial host path
selected the old #34 manifest and the exact-build check refused before upload.
The private path was corrected and explicit #35 manifest/build assertions added
before the successful disabled stage.

The adapter requires a **new** private `qualified-hub-source35.json`. The hub
moved to another host path, so the earlier receipt is not reused. The source
must again be measured/qualified on the marked JCH377 charging/data port before
any current override. The actual physical path, revision, self-powered state,
configured gadget and host boot remain checked for the short source lease.

The known RAM desktop markers, active touch and Wi-Fi, detached NBD and absence
of block-backed root mounts remain required. A container export receipt blocks
activation until normal cleanup. The current USB container desktop does not
qualify this workload. Do not raise or remove guards to make it pass.

Only module identity/build and host paths change from #34; PMIC ceilings,
voltage/current/temperature checks, rollback, lease and fault behavior remain.
Standalone source classification, thermal restart and longer charging endurance
remain separate work. The old input handler's internal diagnostic label still
contains `34`; the actual kernel module namespace is `j72_charge_maintain35`.

[Preflight status](RESULT.json), [host reference](host-reference.py),
[measured #34 result](../maintain34/).
