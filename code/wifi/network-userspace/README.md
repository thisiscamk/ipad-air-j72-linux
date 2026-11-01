# RAM networking userspace — preparation, not a J72 network result

These scripts provide `iw`/wpa_supplicant control, a wireless-only DHCP hook,
renewal, HTTPS verification and public-key-only Dropbear SSH. They run inside
a separately staged RAM root. They do not enable the radio or install anything
on iPad storage. No firmware, credentials, keys, binaries or archive is included.

The owner-local ARM64 bundle uses Debian wpa_supplicant 2.10, iw 6.9,
Dropbear 2025.89 and curl 8.14.1. Native chroot version checks and a localhost
SSH login passed, with a pinned host key, password authentication disabled and
no client private key staged. A temporary server on loopback was stopped and
reaped afterward. The exact static bootstrap BusyBox also downloaded and
hash-verified the complete private bundle through a localhost test server.
**These host checks do not establish Wi-Fi or SSH operation on the iPad.**

## Reusable parts

- `tools/j72-network-dhcp-hook.sh`: changes only a NIC with `phy80211`, validates
  contiguous subnet masks, configures IPv4/routes/resolver, and removes its
  lease marker on deconfiguration. Its resolver file is inside the RAM root.
- `tools/j72-network-runtime.sh`: explicit scan/connect/status/HTTPS/SSH/stop
  commands. DHCP continues lease renewal after obtaining a lease. SSH binds
  the selected wireless interface, requires keys and disables forwarding.
  Cleanup checks recorded daemon identity before sending TERM and waits for exit.
- `tools/j72_network_userspace.py`: validates a private bundle and serves one
  exact random URL bound to the USB-only address, with the target address
  allowlisted. Download is hash-checked before extraction into the initramfs.
  The WPA2 profile generator accepts explicit SSID/PSK input, uses a known
  PBKDF2 derivation and never includes the plaintext passphrase in its output.
  Its lab-specific staging paths require the owner's private manifest/archive;
  this is not a standalone installer.

## Public offline checks

```sh
python3 code/wifi/network-userspace/tools/test-j72-network-prep.py --logic-only
```

Requires Python 3 and a POSIX shell. Tests exercise the WPA2 known vector,
SSID/input handling, real DHCP shell prefix/renewal/cleanup logic and rejection
of malformed masks, non-wireless interfaces and command-like input. Absolute
paths are redirected to a temporary fixture; the test never configures host
networking. Without `--logic-only`, the lab harness additionally needs the
private archive and extracted bootstrap BusyBox for its loopback transfer test.

The target still needs its exact working kernel/driver/firmware, a live radio,
regulatory configuration appropriate to its location and an owner-supplied
network profile. The first prepared connection test is WPA2 personal/RSN/CCMP;
WPA3, enterprise and roaming are not claimed. USB recovery stays available.
See the [current Wi-Fi plan](../../../WIFI-PLAN.md).
