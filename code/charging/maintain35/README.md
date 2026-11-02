# Matched #35 charging adapter — disabled load passes

The matching #35 maintenance module was already built with the combined payload.
This host adapter is now prepared and passes pinned-source/module preflight.
The actual policy headers are byte-identical to the #34 controller that passed
the full-hour net-gain and automatic voltage-hold restart test. The #35 module now loads **disabled**, with the original input limit unchanged.
It is not armed; actual #35 charging is still untested. The initial host path
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
