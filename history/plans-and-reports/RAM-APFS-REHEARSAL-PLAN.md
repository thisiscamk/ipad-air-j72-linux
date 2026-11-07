> **Historical report / superseded plan.** Start with the [current status](../../J72-PROGRESS.md) and [replication guide](../../QUICKSTART.md). Statements below describe their original session, not current support.

# Proposed disposable RAM APFS experiment

Prepared 2 November 2026. **Design only; no experiment or new capsule is ready.**
The iPad remains charging in iOS. No storage command from this document is to be
run against an internal device or the existing recovery root.

## Purpose and evidence

We need to test the exact iOS12 APFS API and native write/flush mechanics before
proposing the first internal operation. A disposable RAM-backed APFS container
could exercise these mechanisms without changing the original container.
It would not reproduce encrypted internal APFS, snapshots, SEP/keybag handling,
flash behavior or power-loss durability.

[Hoolock documents](https://github.com/HoolockLinux/docs/blob/master/tools/README.md)
RAM-disk creation with `hdik` on older iOS and separate resize prerequisites.
A host-only inspection of the exact stock J72 restore image confirms `hdik`,
`newfs_apfs`, `fsck_apfs` and `mount_apfs` are present. Its `hdik` offers a
no-mount mode and drive-key option; the formatter includes a block-size option.
Presence and static usage strings do not prove a working RAM-device workflow.
Apple binaries and extracted strings stay private.

The existing recovery capsule v3 and its inspect/diagnose/reboot restriction
remain unchanged. Any scratch variant must be separately built and audited.
No generic shell, format endpoint or caller-supplied device path is proposed.

## Identity and ownership guards to implement first

Before creating anything:

- Exact J72/build/root identity, known HFS RAM recovery root and no internal
  APFS mounts; retain the existing inspector's guards.
- Record all pre-existing media and their registry identities. In particular,
  preserve the internal disk, its children, and the recovery root device.
- Measure real memory headroom. Choose a bounded scratch size only after
  accounting for the recovery image, kernel and format/check working memory.
  Do not assume a 256 MiB allocation fits safely.

After a no-mount RAM attach:

- Require exactly one new expected media object with a verified IOHDIX ancestry,
  RAM backing and a unique identity created by this invocation.
- Determine whether the tool's drive key can bind that identity; confirm it
  through actual registry properties rather than assuming the option suffices.
- Reject every pre-existing/internal/root device, symlink substitution, unexpected
  child, partitioned image or ambiguous result. Device-name spelling alone is
  insufficient, even if it looks like `disk1` or `md1`.
- Bind all further operations to that verified object and geometry. No fallback
  target, path argument, guessed disk number or internal test write is allowed.

Only an independently reviewed implementation of those guards should format
the disposable RAM object. Formatting is never an identity-discovery technique.

## Proposed bounded test sequence

1. Create and identify the owned RAM medium; record its logical/physical block
   sizes. A 4096-byte APFS block setting is not proof of 4096-byte media geometry.
2. Format an unencrypted scratch APFS container. Verify its superblock identity,
   size and checksum; do not mount an internal filesystem.
3. Query its minimum and select an explicit nonzero, aligned shrink target that
   fits above that measured minimum. No size-zero resize or snapshot deletion.
4. Invoke the exact API with that scratch identity. Record result and independently
   inspect the resulting checkpoint/container state, including on an error.
5. If successful, test an explicit grow only within the known RAM backing size;
   never rely on a maximum-size shortcut.
6. Exercise native aligned short-I/O handling and supported flush/readback only
   on a separately fenced scratch range whose ownership is proved. A RAM flush
   return is ABI/mechanism evidence, not a NAND durability test.
7. Unmount only any owned scratch mount, detach only the owned object, verify its
   disappearance, and reread original internal metadata for non-change.

Retain failure evidence. A timeout or lost SSH session does not establish that
nothing changed; there is no automatic retry, root-target fallback or repair.
A failure to detach the owned scratch medium ends the experiment; normal reboot
can reclaim RAM after evidence capture and device-state review.

## What still remains even after a scratch pass

- The original container's encrypted/snapshot state and real resize behavior.
- Native writer access while internal APFS is unmounted, actual flash flush and
  complete readback of the approved image and both GPT copies.
- Device-specific recovery limitations and the exact first internal-trial review.

[Orchard's native helper](https://github.com/OrchardLinux/resize-apfs/blob/main/Sources/NativeSystem/NativeSystem.c)
provides API/flush/process-lifecycle references. Its [documented target](https://github.com/OrchardLinux/resize-apfs#requirements)
is newer iOS and different hardware; it is not a J72/iOS12 qualification result.
Host and RAM tests inform the first reviewed trial; they cannot prove that first
internal resize in advance. It still requires separate exact write approval.
