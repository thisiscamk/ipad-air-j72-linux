# Project Cascadia components staged for J72

This is an isolated, local staging area for components derived from Project
Cascadia commit `ad28ba40ba6f2a1d244ab51b637ceb31155fa126`. It is published as
experimental reference source and is not part of the Orchard baseline.

`apple_fb_earlycon_j72.c` adapts Cascadia's GPL-2.0 A13 framebuffer early
console to the iPad4,2/J72 bootloader framebuffer.  J72 facts already proven
by the local display gate are used: physical base `0x83d200000`, 1536x2048,
stride `0x1800`, 32-bit pixels.  The unverified A13 UART path is deliberately
removed.  The console starts at `parse_early_param()`, so it cannot diagnose
the current pre-virtual-entry `head.S` stop; keep the watchdog checkpoints
until that boundary is crossed.

Future integration requirements:

- Build with `CONFIG_SERIAL_EARLYCON`, `CONFIG_FONTS`, `CONFIG_FONT_8x16`,
  `CONFIG_DRM_SIMPLEDRM`, and `CONFIG_FRAMEBUFFER_CONSOLE`.
- Link the source into the kernel and use `earlycon=j72fb keep_bootcon
  console=tty0 ignore_loglevel loglevel=8`.
- Confirm the device tree simple-framebuffer node has base `0x83d200000`,
  size `0xc00000`, width 1536, height 2048, stride 6144, and the matching
  32-bit pixel format before enabling it in a boot candidate.
- Preserve the GPL-2.0 SPDX tag and credit Project Cascadia in any eventual
  patch or PR. Upstream submission still requires separate owner review.

Upstream source:
`devices/a13/kernel/extras/apple_fb_earlycon.c` in
https://github.com/rzxvx/Project-Cascadia
