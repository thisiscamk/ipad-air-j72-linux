# Installed J72 Wi-Fi ordering

These are the actual source-only hardware startup/shutdown helper and unit
used with the combined J72 kernel. They prepare the internal HSIC radio before
unchanged NetworkManager; they do not contain a network name or password.

The measured ROM is BCM43241, revision 6, with 576 KiB RAM. The kernel's
opt-in transport and brcmfmac adaptation are in the current kernel patch.
The helper expects private firmware at
`/usr/lib/firmware/brcm/brcmfmac43241-j72-usb.bin` and metadata at
`/etc/orchard/j72-hardware.json`:

```json
{
  "kernel_release": "7.3.0-rc1-j72-pw1-orchard-apple-4k",
  "wifi_firmware_sha256": "REPLACE_WITH_SHA256_OF_YOUR_VERIFIED_PRIVATE_FIRMWARE"
}
```

The firmware converter/configuration research is in
[the Wi-Fi source index](../../wifi/README.md). These services are not a
firmware extractor or installer. Provision the matching kernel modules,
firmware and metadata first; review the helper's ROM and lifecycle checks.
Then use NetworkManager's normal interactive connection flow. Keep credentials
and extracted firmware outside Git. Do not disable brcmfmac authorization or
replace J72 parameters with those of a similarly named iPad.
