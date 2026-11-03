# First native Orchard CLI boot on J72

On 3 November 2026 the iPad Air 1 Cellular booted a native Orchard RAM console
through the normal checkout's `orchard build` and `orchard run` commands.

## Exact tested inputs

| Input | Identity |
| --- | --- |
| Orchard runtime and descriptor | `e9946443f4901125fc24a5895aa3c9a70629d665` |
| Published kernel, loader and tools | `nightly-20261103-6b5fca68c568` |
| Running kernel | `7.3.0-rc1-orchard-apple-4k` |
| RAM payload | `examples/usb-console`, 11,852,965 bytes |
| Payload SHA-256 | `6291d9a311dfc743b47e8f3bc7efd507101b17ebbb0e4bbf69a1a6b304da9948` |
| Bootstrap | Official pinned checkra1n 0.1337.3; explicit PongoOS 2.6.3 |
| Host path | Pi 4 direct USB port, dynamically verified |

The source recipe, component keys and checksums were verified before boot.
The complete Orchard suite passes 510 tests. The result-only descriptor/docs
commit `6ae6dfc` marks USB serial and NCM networking available; its nine schema
checks pass. It changes no runtime code.

## Measured checks

- `orchard run ... --no-build --yes` completes in one owner-authorized attempt.
- The native kernel exposes the standard Orchard ACM/NCM RAM gadget.
- First `orchard exec` pins the device SSH key through the actual serial shell.
- Authenticated `exec` reads the expected kernel release, uptime, mount list
  and dmesg.
- `orchard push` and `orchard pull` return a 4,096-byte synthetic file exactly.
- `orchard pull --serial` independently returns the same file exactly.
- Returned SHA-256: `c8f5d0341d54d951a71b136e6e2afcb14d11ed8489a7ae126a8fee0df6ecf193`.
- The mount inventory contains rootfs and virtual/RAM filesystems only.
- A normal `reboot -f` request disconnects Linux; normal iOS USB returns.

The owner confirmed unlocked iOS charging on the powered hub. Two independent
iOS diagnostic reads 30 seconds apart confirm external charge-capable power
and active charging at 96%. The device remains in iOS on that hub.

## Limits

This is one native console boot. The host recorded transient USB protocol
errors and an onboard USB2-hub reset during handoff; the same attempt recovered
without a manual reconnect or another bootstrap. Repeatability and an external
hub bootstrap are not qualified. The inherited external USB supply nodes still
report dummy regulators.

The native image has no desktop, touch worker, Wi-Fi firmware or charging
policy. Display has not been visually checked. The new native SPI source topic
is not part of this first published kernel. Those features remain separate
integration work; the previous lab desktop is their measured reference.
No development-kernel modules, internal-storage mounts or storage writes were
used. Source, public recipe metadata and sanitized results are shared; Apple
firmware, device identifiers, SSH keys and raw logs remain local.

## Upstream drafts

Implementation is submitted as [shared tooling #58](https://github.com/OrchardLinux/orchard/pull/58)
and [J72 console #59](https://github.com/OrchardLinux/orchard/pull/59). Both remain
drafts; the device draft documents its dependency and exact measured scope.

## Next integration gates

1. Retain the proven native console as a fallback; iOS charging is confirmed.
2. Port native touch dependencies: A7 SPI match data, clock/regulator/reset/
   attention ownership, N1 firmware conversion and `apple_z2` support.
3. Integrate the measured HSIC Wi-Fi path through normal kernel providers and
   private firmware inputs; resolve source/ready/reset lifecycle ownership.
4. Integrate battery and source-aware charging, then qualify desktop endurance.
5. Build Omarchy A through Orchard's normal producer contract and test the
   exact combined image before proposing storage installation separately.

Suggested future changelog wording: “Add experimental iPad Air 1 Cellular
(J72) RAM console support with an explicit A7 bootstrap and USB serial/SSH.”
The curated upstream changelog is unchanged pending owner approval.
