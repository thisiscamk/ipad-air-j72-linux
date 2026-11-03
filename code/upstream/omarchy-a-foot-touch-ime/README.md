# Optional Foot touch/IME component

This source-only topic adds a pinned normal Foot 1.28.0 build and explicit
`--foot-tools` selection for the installed release. Signed Arch Foot remains
the default. The component contains corresponding source, patch, license,
compiler/package receipts and the verified AArch64 binary; binaries are not
published here. The official source and patch are pinned by SHA-256.

A short grid tap commits a new input-method disable/enable transaction.
Scrolling, dragging and physical mouse actions retain the normal behaviour.
This carries the earlier working lab client change into a reproducible
component; it does not claim device qualification of the new normal desktop.

The source build, upstream config test, 460 actual C callback/IME protocol-mock
checks and all 117 host tests pass. The separate combined RAM topic passes
133 host tests. Client/compositor/keyboard behaviour still needs a physical
GUI test on the coherent native image. See the included `desktop/foot/README.md`
for precise opt-in commands, limitations and provenance.

Apply to Omarchy A `fa25972a83a279bdd7e5edc9ff6013cd211562fb`, or after the four
patches in [../omarchy-a-ram-desktop](../omarchy-a-ram-desktop). The latter
combination is used by [../omarchy-a-ram-foot](../omarchy-a-ram-foot).
No Apple firmware, unit data or private logs are included.
