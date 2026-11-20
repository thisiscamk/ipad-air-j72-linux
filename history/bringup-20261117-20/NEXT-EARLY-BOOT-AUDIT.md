# J72/A7 next early-boot compatibility audit — 18 November 2026

Bounded scope: `__cpu_setup`, `__enable_mmu`, `__primary_switch`,
`__primary_switched`, and `finalise_el2`. This is source-correlated inspection
of the exact nearby Image ranges, not a whole-kernel binary scan.

## Likely compatibility boundaries

1. `__cpu_setup` originally probes AMU, HAFDBS, MMFR3 permission indirection,
   and TCR2. The consolidated J72 image already forces those post-A7 features
   absent. Its PMUv3, MAIR, base TCR and physical-address-size work remains.
2. `__cpu_setup` returns modern `INIT_SCTLR_EL1_MMU_ON` value
   `0x0200002034f4d91d`. It contains post-A7 fields including ITFSB and EPAN in
   addition to legacy MMU/cache/access controls. `__enable_mmu` later writes
   this value and synchronizes it. It must be reduced to an A7-qualified mask,
   preferably derived from a live m1n1 SCTLR read plus the required legacy
   M/C/I/SA controls, before attempting the write.
3. `__primary_switched` writes the virtual Linux vector address to `VBAR_EL1`
   and executes ISB. Since the analogous EL2 vector replacement stalled, this
   boundary needs an explicit checkpoint. Unlike VBAR_EL2, VBAR_EL1 cannot be
   permanently preserved because Linux needs its own EL1 exception vectors.
4. `finalise_el2_state` repeats modern feature selection for MPAM, GCS, SVE and
   related EL2 state. J72 must take the fixed nVHE/feature-absent path rather
   than trusting legacy A7 values as current architectural feature IDs.
5. Only after these boundaries pass should the ladder enter `start_kernel`.
   At that point the debugging channel should switch from per-instruction
   watchdog checkpoints to larger milestones: early console, IRQ controller,
   timer, memory allocator, initramfs, root mount, and PID 1.

## Next-test policy

Capture the live loader `SCTLR_EL1` value before branch, preserve it during the
MMU-off EL2-to-EL1 transition, and record it in the receipt. Do not guess an
A7-safe MMU-on value from modern bit names. Add explicit checkpoints around
the eventual MMU-on SCTLR write, EL1 VBAR synchronization, and fixed-nVHE
finalization. This batches known future risks while retaining watchdog return
and zero storage access.
