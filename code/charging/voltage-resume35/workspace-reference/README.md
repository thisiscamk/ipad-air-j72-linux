# Research workspace references

These are reviewed host orchestration sources, not a standalone installer or
portable charging tool. They expect the existing private bring-up workspace,
exact #35 payload/module manifests, pinned Wi-Fi SSH, source qualification and
owned storage-read receipts. No private inputs or device identifiers are included.
Paths are intentionally preserved so source hashes match the tested originals.
Copying this directory alone does not reproduce a bootable device environment.

`run-j72-voltage-session35.py --preflight` checks the prepared inputs without
device contact. `--run --readcheck ...` requires this boot's native read-only
receipt, qualified hub and RAM desktop. It waits for the unchanged initial
entry gate, runs a 90-minute fixed workload, verifies restoration and requests
normal iOS return after normal cleanup. Failures stop progression.

The charging-return helper must use `--voltage-resume35` for this candidate;
its default selects the separate original controller. It waits until test
owners finish. Missing USB remains explicitly unverified; no recovery command
is sent merely because a port is absent. Diagnostics can require unlock.
This helper is not evidence that iOS is currently charging.

The live candidate and original controller share a module namespace: never load
both. Source detection remains restricted to the qualified Pi/hub lease.
