# J72 exact kernel-entry state comparison

## Result so far

The requested exact comparison is not yet available from the archived records.
The two best records were taken at different boundaries:

- Computer-free: the Apple `start_cpu` wake hook, before the custom gather and
  loader. It records EL1, all interrupt masks set, MMU/caches off, zero TTBRs,
  and Apple's live TCR/VBAR/SP state.
- Tethered: m1n1's proxy positive control, before m1n1 tears down its own
  translation regime. It records EL1, interrupts unmasked, MMU/caches on, and
  m1n1 page tables. This is not Linux kernel entry and must not be used to infer
  the missing A7 setup.

Later returning checkpoints establish selected post-teardown facts, including
EL1 and SCTLR M/C/I clear, but do not contain the full register set at the
kernel's first instruction. The next useful device test is therefore one paired
capture, not another instruction-by-instruction boot mutation.

## Exact next capture

Use the same small, stackless recorder immediately before the branch to the
Linux Image on both paths. It must capture, without changing them:

`CurrentEL`, `MPIDR_EL1`, `DAIF`, `SCTLR_EL1`, `TCR_EL1`, `TTBR0_EL1`,
`TTBR1_EL1`, `MAIR_EL1`, `VBAR_EL1`, `CPACR_EL1`, `SP_EL1`, and the timer
control state that is architecturally readable at the active EL. Capture x0-x3
as well to verify the DT pointer and zeroed argument contract. Apple
implementation-defined registers should be added only after identifying reads
already used safely by m1n1 on A7.

The tethered recorder should return to the USB proxy after publishing its
record. The computer-free recorder should publish the identical record format
before its existing terminal branch. A nonce, version, complement and checksum
must reject stale RAM. Compare records with `tools/compare-j72-entry-state.py`.

## DFU reduction

Keep m1n1 and its proxy alive for register reads, uploads, DT generation,
returning recorder tests and pre-branch validation. A fresh DFU remains
unavoidable after a one-way Linux branch, watchdog reset, MMU lockup or USB
teardown. Therefore every candidate should pass the returning proxy capture
first, and only the final entry test should consume a DFU cycle.

## Existing evidence used

- Owner-local returning wake register capture from 10 November.
- Owner-local v75 kernel-entry proxy checkpoint from 13 November.
- Owner-local v85 post-init-EL checkpoint from 14 November.
- The owner-local terminal observer source from 13 November.

No device or storage access was performed for this review.
