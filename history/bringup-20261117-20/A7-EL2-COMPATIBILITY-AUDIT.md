# J72/A7 early EL2 compatibility audit — 18 November 2026

Scope: the exact bounded `init_kernel_el` range `0xf6f10c..0xf6f4ef` and the
immediately following `__cpu_setup` range `0xf6f8b0..0xf6f99b` in the sealed
Image.  This is not a whole-kernel scan.  The audit correlates exact
instructions with the matching Linux `el2_setup.h`, `proc.S`, and ARM64 sysreg
definitions.

## Finding

The modern arm64 EL2 initializer assumes feature-ID fields behave according to
the current architecture.  Apple's ARMv8.0 A7 predates several of those fields.
Live tests prove at least two legacy/unimplemented fields read as values which
look like present features:

- `ID_AA64MMFR4_EL1.E2H0` selected VHE/E2H and stalled at `HCR_EL2`.
- `ID_AA64DFR0_EL1.PMSVer` selected SPE and stalled before the PMS block
  converged.

The remaining instructions contain the same hazard for TRBE and BRBE, both
selected from newer high fields of `ID_AA64DFR0_EL1`.  The entirely new
`ID_AA64PFR2_EL1` similarly gates GICv5.  A test which fixes only PMS therefore
risks consuming several DFU cycles one unsupported block at a time.

## Compatibility disposition

| Range/gate | Facility | A7 disposition | Action in diagnostic |
|---|---|---|---|
| `f6f184..f6f1c8` | VHE / E2H | Postdates A7; live-proven false positive | Keep E2H clear |
| `f6f1dc..f6f21c` | HCRX | Postdates A7 | Force gate absent |
| `f6f25c..f6f284` | SPE / PMS | Postdates A7; live-proven false positive | Force gate absent |
| `f6f288..f6f2a0` | TRBE | Postdates A7; same unreliable DFR0 region | Force gate absent |
| `f6f2a8..f6f2bc` | BRBE | Postdates A7; same unreliable DFR0 region | Force gate absent |
| `f6f2c0..f6f2cc` | LORegions | Postdates A7 | Force gate absent |
| `f6f2d4..f6f2fc` | architectural GIC | J72 uses Apple interrupt hardware | Force gate absent |
| `f6f300..f6f330` | GICv5 / GCIE | Far newer than A7; new ID register | Force gate absent |
| `f6f368..f6f43c` | FGT | Postdates A7 | Force gate absent |
| `f6f440..f6f4a0` | FGT2 | Postdates A7 | Force gate absent |
| `f6f8e0..f6f8ec` | AMU user access | Postdates A7 | Force gate absent |
| `f6f928..f6f934` | hardware AF/DBM | Postdates A7 | Force gate absent |
| `f6f940..f6f974` | permission indirection | New MMFR3 register; postdates A7 | Force gate absent |
| `f6f978..f6f984` | TCR2 | New MMFR3 register; postdates A7 | Force gate absent |

Common ARMv8.0 operations remain unchanged: SCTLR/HCR legacy setup, physical
timer access, PMUv3 counter handling, MDCR, VTTBR, HSTR, VPIDR/VMPIDR, CPTR,
VBAR, SPSR and ERET.  PMUv3 is not disabled because it is an A7 facility and
the live timer ladder already passed its setup.

## Prepared test

`build_j72_a7_el2_watchdog.py` creates a hash-pinned source with exactly the
fourteen listed feature-selection words changed.  Its watchdog ladder distinguishes
legacy HCR, optional-register convergence, debug completion, GIC completion,
FGT completion, ERET, return from `init_kernel_el`, entry to `__cpu_setup`,
completion of its feature-dependent region, and return.  It performs no
storage operation and automatically returns to iOS on a stall.

This is a diagnostic Image substitution, not an upstream or baseline source
change.  Any retained source fix should ultimately express the rule as an
Apple A7 CPU quirk or sanitized early feature view, rather than permanently
editing generic Linux behavior.
