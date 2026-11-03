# Native touch and Omarchy RAM desktop: first device result

4 November 2026, Singapore time. One owner-authorized RAM boot on the
iPad Air 1 Cellular, iPad4,2 / J72AP. Internal storage was not mounted or
written. The host kernel was unchanged.

## What ran

Ordinary Orchard `build` / `run` / `exec` / `push` / `pull` commands used the
source-native kernel, device tree and matching modules. Native Linux SPI,
clock, regulator, GPIO, pinctrl, firmware and input providers started touch;
the earlier laboratory register owners were not used.

- Kernel source: `4c8cee77d7d020a68cf8c27f6e1b0384349cfabe`.
- Kernel release: `7.3.0-rc1-orchard-apple-4k`.
- Orchard source: `b6269f701b2186fe0148225fc9ec221688bc5d51`.
- RAM payload SHA-256:
  `dbedeea398c04eceb786c1c180c28b0f9c611b1793e2fadc7ce630e9e272ecbd`.
- Normal Omarchy components, compact Arch root and opt-in source-built Foot.
- Model firmware stayed private. Unit calibration came from the live bootloader
  handoff; its contents were neither logged nor embedded in the desktop.

## Measured results

| Check | Result |
| --- | --- |
| Ordinary RAM boot | Pass, one DFU attempt |
| Standard serial and SSH | Pass |
| SSH transfer and forced serial transfer | Matching 4,096-byte test files |
| Native touch startup | Pass; normal `apple_z2` binding and input device |
| First gesture capture | 715 events, 11 contacts and 11 releases; two simultaneous contacts observed |
| Clean touch stop and restart | Pass in the same RAM boot |
| Second gesture capture | 797 events, seven contacts and seven releases; longest contact 2.2 seconds |
| Contact completion | No dropped events or contacts remaining in either capture |
| Home key | One complete `KEY_HOMEPAGE` press/release captured; two menu toggles were not qualified |
| Owner desktop check | Menu, terminal, keyboard and automatic keyboard opening on terminal taps work |
| Touch shutdown, twice | All three supplies read back disabled with zero users; clock runtime users return to zero and clock reports suspended |
| Separate SPI controller detach | Normal unbind succeeds; runtime usage zero, status `unsupported` after driver removal; no idle-pin restoration error logged |
| Return to iOS | Owner confirms unlocked and charging on the powered hub |

No new touch, clock-restoration or supply-cleanup errors were observed.
The seven PMIC device-tree cell-count warnings match the earlier boot baseline;
they remain an issue to address. SPI runtime accounting and absence of a pinctrl
error do not independently measure physical pad state or prove that its power
domain is off.

## Desktop fixes found during the run

The GUI required RAM-only userspace fixes before the owner's successful check:

- Set the desktop's umask explicitly: the rescue shell's private umask had
  made its overlay root inaccessible to the unprivileged desktop user.
- Use the mount table for cleanup; the rescue BusyBox lacks `mountpoint`.
- Supply the standard `/dev/fd` and stdio links needed by Bash.
- Describe existing input/DRM devices inside the chroot without bus coldplug.
- Include normal shell IPC tools and the libinput fuzz helper in the compact
  dependency closure.

Desktop shutdown also required an explicit helper to send normal TERM to
detached processes rooted in its overlay, verifying process identity first.
All desktop mounts were then verified gone. Follow-up source fixes incorporate
that ownership check, ordinary process-exit races and BusyBox-compatible group
signaling. The new source passes **136 host tests**, including a detached-process
regression fixture. [Source patches](code/upstream/omarchy-a-ram-foot/).

The tested session was the original payload plus those documented RAM fixes.
A rebuilt image containing all fixes has not yet been tested on the device.
This is first native qualification, not an endurance result.

## Next

The owner confirmed the baseline should track current Orchard and Omarchy A
with J72 adaptations applied before testing. A fresh upstream check found
Orchard `28799cf612840ec80fe76b25ffe9a866f07e4d01` and Omarchy A
`8da19229836c25010634d86af906945c4f6d258b`. Both are now integrated into
separate local candidate branches, preserving the tested source revisions.
The 17 measured native kernel commits have been exported into the candidate
through Orchard's normal export tool. Latest-series application, a fresh build
and device qualification are still required. This does not make the tested
payload a build of those refreshed upstream revisions.

1. Build and inspect a revised RAM image from that refreshed upstream base;
   verify its startup and normal
   cleanup without manual userspace repair.
2. Export the measured kernel topics through Orchard's normal kernel-tree
   workflow and finish the private-firmware recipe integration.
3. Integrate and qualify Wi-Fi and battery/charging on this native kernel.
   Their earlier laboratory results do not qualify this new image.

Native Wi-Fi, battery, charging and storage drivers were not enabled in this
test. No internal installation is authorized. The device is back in iOS for
charging while the next image is prepared.
