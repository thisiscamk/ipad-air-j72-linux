# Remaining ANS1 audit before a J72 device test

Source: Orchard `97dccd13fc4af182a48d4e59198ad72acbfc201c`, Hoolock
`0032-Add-ANS1-storage.patch`, SHA-256
`9522985e68957b0906d8ef1b7b0fb224ec54cb4e7132ab2bb6cad110b7548b40`.
Reviewed 1 November 2026. Candidates are inactive and host-tested only.

## Loader findings

| Area | Evidence / candidate | Remaining gate |
| --- | --- | --- |
| Normal shutdown | Original `ans1_shutdown` frees `cmd` twice; 0001 removes duplicate. Actual-function allocator/UBSan regression passes. | Full loader and hardware shutdown remain untested. |
| Command admission | Original executor lacks a positive media-opcode allowlist. 0002 restricts it to Identify and one user-area read. | Review every mailbox/setup path in the complete source series, not just this helper. |
| Geometry and buffers | 0002 measures formatted namespace size, accepts only the existing 4096-byte format, and checks LBA/PFN widths and alignment before encoding. | Firmware reply validity, completion format/status and exact J72 geometry need hardware evidence. No automatic 512-byte adaptation. |
| Early init failure | Power enable followed by AKF allocation/map/command allocation can return without unwinding prior owners. Later error labels release RTKit/command resources but leave AKF/power/state unresolved. | Explicit acquired-state accounting and injected failure at every acquisition/transition; audit the actual AKF/RTKit APIs before choosing destructors. |
| Failure during Identify | Candidate adds a possible failure after command buffers are exposed to firmware; existing `out_shutdown` is inherited. | Prove stop/quiescence before reclaiming DMA-visible memory, including timeouts. The opcode guard does not fix this ownership issue. |
| Timeout and retry | Host stubs return success/failure synchronously. Original shutdown comments that quiesce crashes on restart. | Late/stale completions, tag reuse, failed sleep, retries and re-init need a defined policy and fault tests. Do not free/reuse live DMA buffers on an unproved stop. |
| Firmware handoff | Public import uses iBoot-preloaded AKF firmware. Cached J72 registry identifies an A7 ANS node. | Exact firmware memory/DT reservations, mailbox, clocks, power ownership and recovery through our Pongo chain remain unverified. Do not substitute A8X constants. |

The candidate's command-level read-only policy cannot prove that controller
firmware performs no autonomous media maintenance. Initial qualification
means no host-issued media writes/unlock, not a forensic write blocker.

## Linux driver is a separate port

The reviewed Orchard tree has the loader import and firmware handoff patch,
but no Linux ASP implementation to enable in our existing kernel. The
[J81 reference](https://github.com/micro23/ipadair2-omarchy/tree/e2203b83f45726c825b39dd17fbab405c2a90e5b/experimental/j81-storage)
and [submission audit](https://github.com/mattonik/ipad-nixos/blob/main/research/j81-ans1-submission-audit.md)
are useful source material. They are not J72 qualification.

Before adapting that driver:

- Check tags before indexing/copying into the command array.
- Return SGL construction errors to the submitter; do not submit partial
  lists after a void helper reports capacity exhaustion.
- Reject zero/malformed lengths, arithmetic wrap, unaligned/truncated DMA
  addresses, excess segments and requests beyond measured namespace size.
- Distinguish Linux's 512-byte sector accounting from device logical blocks.
- Establish request completion ownership, timeout/cancel/late-reply behavior,
  cleanup and repeated initialization.
- Fence all writes/unlock/discard/format/passthrough during the first port;
  a block-device read-only flag alone does not enforce this.
- Qualify flush/durability and power-loss behavior separately before any
  write-capable build. Another board's write range must never become ours.

## First device observer contract

Build only after resolving the loader failure-path gates above. Keep a RAM
root and USB recovery; do not pivot root to an unproved storage driver.
Identify first, then minimal repeated aligned reads; validate headers before
following their entry-array locations. Cap metadata allocation (the offline
checker permits at most 4 MiB per GPT array). Save exact captures privately,
compare repeated hashes, restore reviewed volatile ownership and verify a
normal iOS boot. On any unexpected status/timeout/geometry, stop rather than
retrying new commands against uncertain controller state.

No complete observer payload exists yet. No new DFU is requested by this audit.
