# Experimental J72 SPI2 staging

`0001-j72-spi2-controller-disabled.patch` adds the iPad Air 1 Cellular
SPI2 controller to the J72 device tree with `status = "disabled"`. It has
no touchscreen child. The register range `0x20a088000/0x4000` and AIC
IRQ 138 come from the locally parsed J72 Apple device tree. A read-only
capture of the live J72 iBoot device tree established SPI2 clock ID 0x134
and its table entry at 60 MHz. The disabled node therefore uses a dedicated
60 MHz fixed clock. The earlier isolated controller-registration boot used
a 24 MHz placeholder without any SPI transfers.

This patch alone does not make the existing kernel support the controller.
The owner-local isolated trial applies the S5L8960X SPI driver changes from the
local iPad NixOS reference, builds a separate 4 KiB kernel and stages a
controller-only DTB. It is not part of the
current Orchard J72 profile or the known-good RAM payload. No touch
firmware, calibration, or power sequence is enabled here.
