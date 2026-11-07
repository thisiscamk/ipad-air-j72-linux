# J72 USB/HSIC Wi-Fi — measured development source

This exact J72/#34 Linux 7.0.12 implementation has now loaded the owner's
private radio firmware, scanned, associated with WPA2, obtained DHCP and
passed Wi-Fi-bound HTTPS plus pinned-key SSH. Disconnect/reconnect and an
explicit DHCP renewal passed in the same boot. USB recovery remained available.
The brighter desktop, touch, menu and on-screen keyboard also work with Wi-Fi
active; the owner confirmed them. Desktop-user HTTPS passed after binding the
RAM DHCP resolver into the read-only desktop.

## Source

- `module/`: exact development HSIC power/reset/GPIO/EHCI owner. It attaches
  the Linux power domain before binding and retains exclusive HOST_READY
  ownership. Persistent mode is explicit. Stop uses synchronized standard
  EHCI shutdown and requires observed halt before releasing controller memory.
- `j72-usb.patch` and `brcmfmac/usb.c`: complete patch and resulting USB driver
  source. Match J72, USB 0a5c:bd1c and observed BCM43241 revision 6. Reject
  short/error control transfers and malformed/out-of-bounds TRX downloads.
  The initial bind gate defaults off; the vendor helper must register first.
- `orchard-port-authorization.patch`: existing Orchard firmware-handshake
  connection notification fix, applied separately to cfg80211.c. Only that
  source changed in the final runtime module update.

The USB adaptation builds on [Project Cascadia at c20b85e](https://github.com/rzxvx/Project-Cascadia/blob/c20b85ebb951c704d7e3a664c378dde8276e3928/patches/tree/0001-cascadia.patch),
reviewed through [Orchard PR #10](https://github.com/OrchardLinux/orchard/pull/10).
The authorization patch is from [Orchard 824bf034](https://github.com/OrchardLinux/orchard/blob/824bf0346ae4c3debd208cd34b053130576af60c/kernel/patches/drivers/wifi/0004-wifi-brcmfmac-Report-port-authorized-after-the-firm.patch).
Retain the original source license and copyright notices.

## Boundaries

This is development code for the exact owner-tested kernel and board, with
matching kernel internals and symbol exports. It is not native Orchard 7.3
integration or a generic loadable driver. Build the provider against the exact
configured kernel, then supply its exported symbol metadata when building the
adapted brcmfmac module. Loading an unrelated build with matching vermagic is
not sufficient. Supply your own matching firmware/board calibration and use
the [validated packer](../usb-firmware/); no firmware, NVRAM, MAC, credentials,
compiled module, kernel image or private capture is included.

**The new provider remains active in this first networking boot. Its complete
stop/restoration is still unqualified.** Sustained traffic, power transitions,
autonomous charging, suspend/resume and repeat cold starts remain open.
The desktop still depends on read-only USB/NBD storage and must be detached
before moving its cable. No internal-storage writes or installation occurred.
See [measured validation](VALIDATION.json) and the [session plan](../../../history/plans-and-reports/DFU-PLAN.md).
