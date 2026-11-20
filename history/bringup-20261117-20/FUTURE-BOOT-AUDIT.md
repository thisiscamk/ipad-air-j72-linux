# J72 future boot audit — 2026-11-20

## Scope and safety

This is an offline review performed while the iPad charges.  It does not write
the iPad, alter the retained iOS APFS partition, change the host kernel, or
start a USB boot process.  Orchard upstream was fetched for comparison only;
no upstream branch, PR, or review state was changed.

## Most important finding

The archived kernel that previously booted this exact J72 is Linux
`7.0.12-j72spi2` and uses `CONFIG_ARM64_VA_BITS_48=y`, four page-table levels,
and 4 KiB pages.  Consequently, A7/J72 is demonstrably capable of booting a
VA48 kernel.  VA39 should remain a diagnostic experiment, not become the
assumed product configuration.

The current 7.3 diagnostic image reaches `__pi_map_kernel` but has not reached
the checkpoint before its first `idmap_cpu_replace_ttbr1`.  Its first nested
`__pi_map_range` consists of integer and page-table memory operations, with no
system-register or TLBI instruction.  If the prepared 55-second entry marker
appears but the 65-second post-call marker does not, the leading hypothesis is
a bad page-table address, allocation geometry, or unwritable table page—not an
unsupported A7 opcode.

The working 7.0.12 binary has a simpler/inlined early mapping layout, while the
7.3 binary contains a distinct `__pi_map_kernel` path.  This is a strong reason
to compare the bounded early-map implementations and kernel-version changes.
It is not yet proof of which upstream commit caused the regression.

One initially suspicious upstream change, Linux commit `fb0f3ef5601a`
(`arm64: mm: Unmap kernel data/bss entirely from the linear map`), is not the
early-boot cause: its changes run later through `mark_rodata_ro()` and
hibernation notification, after the present failure point.

## Current next test (already prepared)

Use the existing two-stage image after charging; make no other variable change:

- entry to `__pi_map_kernel` at Image offset `0xf8625c`: 55-second marker
- immediately after its first mapping call at `0xf8632c`: 65-second marker
- image: `early-linux-j72-a7-va39-map-kernel-first-call-Image.bin`
- SHA-256: `04e5deaad3b1223c2786d5cd7010122564ec50de92efcd23d0131f550534ec7`

Interpretation:

- 55 only: instrument the first `__pi_map_range` inputs and table allocator
  addresses, or reproduce that bounded call against the working 7.0.12 map
  logic.
- 55 and 65: move the paired marker around the next mapping call.  Do not
  revisit already-excluded TTBR/TLBI sites until the earlier call boundary is
  known.
- neither: revalidate the exact loaded image/hash and branch/readback evidence;
  do not request an unchanged DFU retry.

## Remaining boot path and proactive risks

| Stage | Principal J72/A7 risk | Prepared mitigation/check |
|---|---|---|
| Finish early kernel mappings | 7.3 table allocation/geometry regression | Bisect the six bounded mapping calls; compare with proven 7.0.12 VA48 path |
| Replace TTBR1 and enable final mappings | A7 TLBI/ordering and target translation | Keep watchdog markers; validate final `AT S1E1R`; make any real source fix symmetric for secondary CPUs |
| `__primary_switched` to `start_kernel` | A7 feature-register and alternatives probing | Keep early framebuffer console plus watchdog; checkpoint vectors, feature probing and alternatives |
| Early console | Console starts only after early-parameter parsing | Retain pre-console watchdog; verify simplefb address, stride and pixel format before relying on text |
| Device tree/platform | No official J72 profile; existing `j72t/j72s/j72b` names are later iPads | Use J72AP-specific compatible/ADT evidence; audit display reserved memory warning |
| Initramfs/root handoff | Bootargs, storage identity, USB availability | First reach a RAM shell; validate root selection without writing storage |
| SMP | Secondary CPUs repeat EL/MMU setup | Convert proven primary A7 workarounds into source/config logic before enabling SMP |
| Local storage | ANS queue/flush correctness and APFS preservation | Qualify native ASP reads, writes and flushes only in released space before install |
| Charging/power | Linux charging is not yet reliable | Keep iOS bootable as the charging fallback |
| Installed/autoboot | Manual loader and waits are unsuitable for daily use | Adopt Orchard BLS/autoboot only after RAM boot and charging/storage qualification |

## Latest Orchard review

Fetched `OrchardLinux/orchard` through commit `179689c` (2026-11-19) without
merging it into the experimental worktree.  The upstream Linux and m1n1 pins
are unchanged from the local base, so the update does not contain a drop-in
kernel fix for the present early-MMU stop.

Useful changes to stage after the current diagnostic boundary is stable:

1. `c672304`: enable ARM64 CRC32 emulation.  A7 lacks CRC32 instructions, so
   this is directly useful when EL0 userland starts.  It cannot fix the current
   `head.S` failure.
2. `cdd1295`: faster m1n1 bulk upload and independent USB startup.  This may
   shorten the test loop materially, but changes transport behavior and should
   be validated separately rather than mixed into the current mapping probe.
3. `83f8ebc`: boot the default BLS entry/autoboot.  This is useful for the final
   daily boot flow and may eliminate manual delay, after reliable boot exists.
4. `33901f5`: free the ANS1 command queue on shutdown.  Carry this into later
   local-storage qualification.

Recent charging, suspend and display work is mostly for A9/A10 iPads.  Do not
copy it to J72 without register/DT/hardware evidence.  Current Orchard still
does not provide an official J72 image; the J85 document proves another A7 RAM
boot but describes a private/non-reproducible kernel lineage.

## Recommended order after the next marker result

1. Complete the already-prepared 55/65 mapping-call localization.
2. If that call hangs, capture its arguments/table destination with bounded
   instrumentation and compare only the relevant 7.0.12 versus 7.3 functions.
3. Build a control boot around the archived proven VA48 7.0.12 kernel and known
   loader inputs, with early display diagnostics if feasible, but no storage
   writes.
4. Resolve the early mapping regression in source/configuration; retire binary
   patches as each workaround gains a supported implementation.
5. Reach a RAM shell, then enable CRC32 emulation and validate CPU features,
   timer/IRQ, initramfs, USB, framebuffer and SMP in that order.
6. Separately validate faster m1n1 upload, then BLS/autoboot to reduce the test
   loop and remove the user-facing wait.
7. Only after RAM boot is repeatable: qualify ASP writes/flushes in the released
   50 GB, reliable charging, normal Orchard install/launch, and rollback to iOS.
