# Omarchy A optional automatic keyboard focus

A small independently reviewable change against Omarchy A `ace5940`: six
controller lines add `OMARCHY_KEYBOARD_AUTO=1`; unset/0 preserves the existing
manual default. Eight real controller subprocess tests exercise exec arguments,
lazy startup, toggle signals, theme restart and executable/PID identity. The full
unit suite passes 113 tests with no skips. Actual Wayland/client behavior and a
finished image are untested; no new device is marked supported.

[Patch](keyboard-auto.patch), [base/hash/results](RESULT.json),
[integration plan](../../../UPSTREAM-INTEGRATION-PLAN.md).

Apply to that pinned source checkout with `git apply --check`, then `git apply`.
Run its documented unit suite in the correct isolated test environment. The
patch also includes its focus experiment and qualification notes. This is a
source-review artifact, not a claim that a PR has been opened or merged.

Repeated short-tap reopening also depends on the selected terminal/compositor
and input-method activation. The local J72 desktop used experimental Foot
client changes; this switch alone does not establish equivalence.
