# J72 Wi-Fi bar icon

Installed in the live RAM desktop. The owner opened its status popup; IPC and
an actual Wayland screenshot show connected, signal strength and frequency.
Tap the icon to open/close details, or tap Close. It uses the same bar-plugin
interface as the [battery widget](../battery/).

`collect-status.sh` runs in the RAM initramfs, queries the staged `iw` and
atomically writes numeric link status to the desktop's temporary runtime
folder every five seconds. The QML plugin polls that file. It exposes no SSID,
MAC, IP or credentials. Signal strengths select the icon; missing input gives
a disconnected/unknown state. It provides status only, not network selection.
No desktop disk image was modified. Include the manifest/QML in the tablet
user's `~/.config/omarchy/plugins/ipadlinux.wifi/`, add `{"id":"ipadlinux.wifi"}`
to the right bar layout, and run the collector only with the matching RAM
network root and desktop. Its paths are specific to this lab environment.
