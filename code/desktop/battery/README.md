# J72 desktop battery indicator

Quickshell bar widget for the experimental J72 RAM desktop. Reads Linux
`/sys/class/power_supply/j72-bq27545-battery/capacity` and `status` every five
seconds. Displays percentage, a charging glyph for `Charging`, and an urgent
color below or equal to 15% while discharging. A failed read displays an
unknown value rather than retaining the previous reading.

The widget only reads the power supply driver. It does not set charging
current, enable charging, or infer charging from an attached USB cable.
Reported percentage still needs qualification under changing loads; it is
the driver's reading, without an estimated time remaining.

## Integration

Copy `manifest.json` and `BarWidget.qml` into
`$HOME/.config/omarchy/plugins/ipadlinux.battery/` for the tablet desktop user.
Add `{"id":"ipadlinux.battery"}` before the keyboard entry in
`bar.layout.right` in `$HOME/.config/omarchy-ipad/shell.json`.
Then run these commands as that user inside the desktop session:

```sh
omarchy-shell shell rescanPlugins
omarchy-shell shell reloadConfig
omarchy-shell ipadlinux.battery status
```

In the bring-up workspace, `python3 tools/install-j72-desktop-battery.py`
performs this installation over the serialized RAM shell after desktop
startup. It requires a read-only root and a RAM home, and leaves the root
image and existing boot payload unchanged. Run it again after each RAM boot
until the plugin is included in a new pinned boot overlay.

## Validation, 1 November 2026

Loaded in the live Quickshell desktop without restarting the compositor.
The widget's IPC returned the actual kernel-reported percentage and
`Discharging`, and refreshed as the percentage changed. The owner confirmed the widget on screen and its charging symbol during
the subsequent five-minute desktop charging session, which completed with
verified restoration.

New QML source is GPL-2.0-only; see the companion lab's
`code/LICENSES/GPL-2.0.txt`.
