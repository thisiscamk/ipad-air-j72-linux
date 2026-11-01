# Plan for running without the Pi

Updated 1 November 2026. The owner accepts **using the Pi to start Linux after
a shutdown, then running the iPad unplugged** as the first independence
milestone. Fully independent startup remains the later goal. Internal writes,
partition changes and iOS erasure are not authorized.

## What has to become independent

| Dependency today | Required change |
| --- | --- |
| Pi serves a read-only desktop root over USB/NBD | A fully RAM-resident root, or a qualified internal root |
| USB supplies debugging and network access | Working internal Wi-Fi and a recovery strategy |
| Input is a bounded diagnostic worker | Boot-qualified continuous input with explicit stop and fault handling |
| Charging relies on a known hub and a host-renewed source lease | Autonomous source/protection policy and acceptable Linux power use |
| Pi starts checkm8/Pongo/m1n1 after restart | Retain this for the first milestone; research a separate untethered boot chain later |

Do not unplug the existing desktop on the assumption that Wi-Fi or cached
files remove the NBD dependency. Storage must be detached cleanly first.

## Milestones and planned boot batches

These are dependencies, not a promise that each row takes exactly one DFU.
Prepare code and userspace offline, combine independent checks, and reuse a
running kernel for compatible runtime changes. Do not repeat an unchanged boot.

| Batch | Prepare and test | Completion evidence |
| --- | --- | --- |
| N1: dependable input and power | Package continuous touch; check the three-second finite fallback against five seconds in opt-in continuous mode, then stop/health/cleanup/restart. Add the battery widget to startup. Measure lower-brightness/idle operation and guarded hub charging. | Touch outlives the old diagnostic deadline; explicit stop and failures still work; measured power/temperature remain acceptable. Keep the existing conservative guards. |
| N2: internal WLAN bus | Matched Wi-Fi kernel/modules and J72 PHY/DT/reset sequence; keep recovery USB independent. Enumerate descriptors before WLAN binding. | Stable internal USB identity, correct driver selection and clean rollback; external debugging survives. |
| N3: radio and networking | Matching private firmware/board data, USB protocol adaptation, vendor helper, signed regdb and network userspace. | Scan, association, DHCP, DNS, HTTPS, traffic/reconnect and Wi-Fi SSH. Can share N2's boot if the required transport changes are already present. |
| N4: short unplugged RAM session | Build a deliberately small local root with recovery tools, Wi-Fi, touch and a minimal desktop. Measure actual RAM and package footprint before selecting it; the current multi-gigabyte image cannot simply be copied into the Air 1's memory. | All executable/library/font/config dependencies are local, no USB-backed mounts remain, Wi-Fi management works, and an owner-confirmed desktop runs after a controlled unplug. RAM data is lost on reboot. This option depends on measured memory headroom. |
| N5: integrated usability | Repeat boots, power controls, charging/source withdrawal, network reconnect and the owner's required tablet features. Test host-backed persistence/updates before iPad writes. | A stated, owner-agreed feature set works together; recovery and power/thermal behavior are repeatable. Audio/Bluetooth/rotation and other requested hardware remain explicit work, not assumed complete. |
| S1: read-only J72 ANS1 | Adapt the storage references after N5; verify firmware handoff, mailbox/DMA, exact geometry, bounded reads and both GPT copies. | Write-unlock/output/passthrough refused in loader and driver; stable read hashes and normal iOS recovery. No journal-replay mount. |
| S2: storage rehearsal | Verify backups/recovery, prove iOS 12 coexistence, harden the write path and simulate layout/image decisions. Produce exact preserved/changed ranges. | A reviewable dry-run plan based on measured J72 geometry; still no device writes. |
| S3: separately approved install | Only after explicit approval of S2: install a small local root, retaining rescue boot and the agreed iOS layout. | Filesystem checks, persistent data, desktop, networking and recovery pass. |
| S4: installed use | Pi-assisted launch, unplugged use, charge/data transitions, updates, return to iOS and repeat cold launches. | The Pi no longer serves the root or maintains charging policy. Starting Linux after shutdown still uses the Pi. |
| U1: fully independent startup | Separately investigate a boot chain for this exact A7/iOS 12 combination, recovery and boot selection. | Demonstrated start after shutdown without another machine. No working route is established by the current Orchard sources. |

N4 is an interim demonstration, not a replacement for persistent internal
storage. If its memory budget fails, retain the host-backed desktop until S3;
do not sacrifice recovery or silently call a network-served root independent.

## Current Orchard starting points

- [Orchard bootloader design](https://github.com/OrchardLinux/orchard/blob/824bf0346ae4c3debd208cd34b053130576af60c/docs/bring-up/bootloader/README.md):
  host starts m1n1; installed boot entries and kernels can be read locally.
- [J81 internal-root follow-up](https://github.com/OrchardLinux/orchard/blob/824bf0346ae4c3debd208cd34b053130576af60c/docs/integration/j81-2026-10-29-followup/NATIVE-ROOT.md):
  experimental Air 2 internal ext4/systemd/desktop and fresh-boot persistence.
  Cold start still needs a host. This is a source reference, not J72 support.
- [Wi-Fi preparation and applicability](WIFI-PLAN.md) and
  [J72 storage gates and source map](INTERNAL-STORAGE-PLAN.md).

**Now:** the continuous-input hub round ended with clean shutdown after
approximately 34 minutes of input and a 27.2-minute charging run. The voltage
test guard stopped charging and restoration is independently verified. HSIC
power/domain/register observation passed in the same boot; radio enumeration
remains open. The root still requires the host whenever the desktop is
running. Autonomous power policy and HSIC Wi-Fi remain open; storage is
planning only.


## RAM desktop candidate prepared after Wi-Fi/charging milestone

A host-only ELF/QML/font audit and read-only image extraction produced a
private desktop subset around282 MB, compressed around100 MB. All selected
image files match their source hashes; native labwc, Foot, Quickshell, fonts,
UID1000 startup and D-Bus checks pass. The image and host kernel are unchanged.
This is not yet a device result: runtime data/plugin completeness, live RAM
headroom, input/keyboard behavior and an unplugged owner test remain open.
The network/SSH tools already run from a separate RAM root. No internal
storage writes or installation are authorized.
