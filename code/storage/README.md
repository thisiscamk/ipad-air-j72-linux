# Offline ANS1 cleanup candidate

While reviewing Orchard for J72 storage, we found two `free(cmd)` calls in
one normal `ans1_shutdown()` invocation in the
[pinned imported ANS1 source](https://github.com/OrchardLinux/orchard/blob/824bf0346ae4c3debd208cd34b053130576af60c/boot/m1n1/patches/hoolock/0032-Add-ANS1-storage.patch#L463).
No later patch in that reviewed series changes the function. Original
ANS1 code is Nick Chan / Hoolock m1n1, SPDX MIT. The new one-line delta
follows that MIT license; the new Python reproducer is GPL-2.0-only.

The [candidate patch](0001-ans1-Avoid-freeing-the-command-buffer-twice.patch)
removes only the duplicate free. It is **not applied to an active loader**,
and no full m1n1 build or hardware storage test has run with it. Other
initialization/error-path ownership and J72 integration still need auditing.
This changes no device storage policy and does not enable writes.

## Reproduce without hardware

Use a local Orchard source checkout at commit
`824bf0346ae4c3debd208cd34b053130576af60c`. The tool verifies the exact
import-patch hash, extracts the real function, applies the candidate to a
temporary source file, and compiles both with stubbed allocator/RTKit/power
calls. It does not modify that checkout or contact an iPad.

```sh
python3 -B code/storage/verify-j72-ans1-cleanup.py \
  --orchard-tree /path/to/pinned-orchard \
  --candidate code/storage/0001-ans1-Avoid-freeing-the-command-buffer-twice.patch
```

Measured host result:

- Original: expected duplicate-allocation-free assertion reproduced.
- Candidate: each allocation freed once; RTKit cleanup and power-down retained.
- Repeated shutdown: returns without extra cleanup.
- UBSan candidate run: passed.

This is a narrow source regression test, not proof that the full controller
starts, reads safely, shuts down correctly on J72, or preserves data after
power loss. It is shared here for review; the existing Orchard PR #43 remains
unchanged. See [the storage plan](../../INTERNAL-STORAGE-PLAN.md).
