#!/bin/sh
# Exact J72 RAM desktop, original host image mounted read-only, RAM state.
set -eu
[ "$(uname -v)" = "#35 SMP PREEMPT Mon Nov 2 07:00:00 +08 2026" ] || exit 1
root=/mnt/omarchy
state=/run/j72
mkdir -p "$state"
[ "$(uname -r)" = 7.0.12-j72spi2 ] || exit 1
[ "$(cat /proc/device-tree/model)" = 'Apple iPad Air (Cellular)' ] || exit 1
mounted() { grep -q " $1 " /proc/mounts; }
user() {
 busybox chroot "$root" /usr/bin/setpriv --reuid=1000 --regid=1000 --init-groups \
 /usr/bin/env HOME=/home/tablet USER=tablet LOGNAME=tablet LANG=C.utf8 LC_ALL=C.utf8 \
 XDG_RUNTIME_DIR=/run/user/1000 XDG_SESSION_TYPE=wayland WAYLAND_DISPLAY=wayland-0 \
 LIBSEAT_BACKEND=seatd SEATD_SOCK=/run/seatd.sock WLR_BACKENDS=drm,libinput \
 WLR_RENDERER=pixman WLR_LIBINPUT_NO_DEVICES=1 OMARCHY_PATH=/opt/omarchy-ipad \
 QT_QPA_PLATFORM=wayland QT_QUICK_BACKEND=software QSG_RENDER_LOOP=basic \
 PATH=/opt/omarchy-ipad/bin:/usr/bin:/bin "$@"
}
stop() {
 rm -f "$state/desktop-ready"
 if mounted "$root"; then
  # UID1000 is dedicated to this temporary desktop, including its children.
  busybox chroot "$root" /usr/bin/pkill -TERM -u 1000 || true
  sleep 1
  for f in udev seatd; do
   if [ -f "$state/$f.pid" ]; then
    pid=$(cat "$state/$f.pid")
    case "$pid" in ''|*[!0-9]*) return 1;; esac
    if [ -d "/proc/$pid" ]; then
     exe=$(busybox readlink "/proc/$pid/exe")
     case "$f" in
      udev) expected=$(busybox readlink -f "$root/usr/lib/systemd/systemd-udevd");;
      seatd) expected=$(busybox readlink -f "$root/usr/bin/seatd");;
     esac
     if [ "$exe" = "$expected" ]; then kill -TERM "$pid";
     else echo "Refusing stale $f PID" >&2; return 1; fi
    fi
   fi
  done
  sleep 1
  for path in etc/resolv.conf usr/bin/foot opt/omarchy-ipad/bin/omarchy-keyboard dev/shm dev/pts dev proc sys run tmp home; do
   if mounted "$root/$path"; then umount "$root/$path"; fi
  done
  umount "$root"
 fi
 if [ -f "$state/container-loop" ]; then
  loop=$(cat "$state/container-loop")
  case ${loop#/dev/loop} in ''|*[!0-9]*) return 1;; esac
  [ "$(cat "/sys/class/block/${loop##*/}/ro")" = 1 ] || return 1
  [ "$(cat "/sys/class/block/${loop##*/}/loop/backing_file")" = /mnt/j72-store/base/desktop-A.squashfs ] || return 1
  busybox losetup -d "$loop"
  rm "$state/container-loop"
 fi
 if mounted /mnt/j72-store; then umount /mnt/j72-store; fi
 if [ "$(cat /sys/block/nbd2/size)" != 0 ]; then nbd -d /dev/nbd2; fi
 [ "$(cat /sys/block/nbd2/size)" = 0 ]
}
nbd() {
 [ "$(busybox sha256sum /run/j72-fetch/busybox | busybox awk '{print $1}')" = 999cb969d09093a71716cfc747bb53cdada3f332c05eb5046c56e0f66a4d6d22 ] || return 1
 /run/j72-fetch/busybox nbd-client "$@"
}
start() {
 [ ! -f "$state/desktop-ready" ] || return 0
 mounted "$root" && { echo 'Partial desktop exists; stop it before retrying.' >&2; return 1; }
 [ "$(cat /sys/module/j72_touch_session/parameters/session_state)" = 2 ] || return 1
 [ "$(cat /sys/block/nbd2/size)" = 0 ] || return 1
 mkdir -p "$root"
 i=0
 until nbd 10.0.0.1 10832 /dev/nbd2; do
  i=$((i+1)); [ "$i" -lt 60 ] || return 1; sleep 2
 done
 i=0
 while [ "$(cat /sys/block/nbd2/size)" = 0 ]; do
  i=$((i+1)); [ "$i" -lt 50 ] || return 1; sleep 0.1
 done
 [ "$(cat /sys/block/nbd2/size)" = 3145728 ] || return 1
 [ "$(cat /sys/block/nbd2/ro)" = 1 ] || { echo 'NBD must be read-only' >&2; return 1; }
 store=/mnt/j72-store
 mounted "$store" && return 1
 [ ! -e "$state/container-loop" ] || return 1
 mkdir -p "$store"
 mount -t ext4 -o ro,noload,nodev,nosuid,noexec /dev/nbd2 "$store"
 grep -q '^/dev/nbd2 /mnt/j72-store ext4 ro,' /proc/mounts || return 1
 [ "$(busybox sha256sum "$store/j72-root-contract.json" | busybox awk '{print $1}')" = 12aba553f1a47ad56db6cecf63e0a4ba7c60e961eafcf4378e0f15a79999442f ] || return 1
 [ "$(busybox stat -c %s "$store/base/desktop-A.squashfs")" = 572002304 ] || return 1
 loop=$(busybox losetup -f)
 case ${loop#/dev/loop} in ''|*[!0-9]*) return 1;; esac
 [ ! -e "/sys/class/block/${loop##*/}/loop/backing_file" ] || return 1
 busybox losetup -r "$loop" "$store/base/desktop-A.squashfs"
 echo "$loop" > "$state/container-loop"
 [ "$(cat "/sys/class/block/${loop##*/}/ro")" = 1 ] || return 1
 mount -t squashfs -o ro "$loop" "$root"
 [ "$(busybox stat -f -c %T "$root")" = squashfs ] || return 1
 for path in dev dev/pts dev/shm proc sys; do mount --bind "/$path" "$root/$path"; done
 mount -t tmpfs -o mode=755,size=64m tmpfs "$root/run"
 mount -t tmpfs -o mode=1777,size=128m tmpfs "$root/tmp"
 mount -t tmpfs -o mode=755,size=128m tmpfs "$root/home"
 if [ -f /opt/j72-network/etc/resolv.conf ]; then chmod 644 /opt/j72-network/etc/resolv.conf; mount --bind /opt/j72-network/etc/resolv.conf "$root/etc/resolv.conf"; fi
 mkdir -p "$root/home/tablet/.config/labwc" "$root/home/tablet/.config/omarchy-ipad" \
  "$root/home/tablet/.config/foot" "$root/home/tablet/.local/bin" \
  "$root/home/tablet/.local/state/omarchy/current/theme" "$root/run/user/1000" "$root/run/udev/rules.d"
 chmod 700 "$root/run/user/1000"
 cp /opt/j72/keyboard /opt/j72/omarchy-keyboard "$root/home/tablet/.local/bin/"
 mv "$root/home/tablet/.local/bin/keyboard" "$root/home/tablet/.local/bin/j72-wvkbd-auto"
 cp /opt/j72/foot-touch "$root/home/tablet/.local/bin/foot-touch"
 chmod 755 "$root/home/tablet/.local/bin/"*
 mount --bind "$root/home/tablet/.local/bin/omarchy-keyboard" "$root/opt/omarchy-ipad/bin/omarchy-keyboard"
 mount --bind "$root/home/tablet/.local/bin/foot-touch" "$root/usr/bin/foot"
 cp /etc/j72-session/rc.xml "$root/home/tablet/.config/labwc/rc.xml"
 cp /opt/j72-compressed/autostart "$root/home/tablet/.config/labwc/autostart"
 chmod 755 "$root/home/tablet/.config/labwc/autostart"
 cp /etc/j72-session/shell.json "$root/home/tablet/.config/omarchy-ipad/shell.json"
 printf '[main]\nfont=monospace:size=12\n' > "$root/home/tablet/.config/foot/foot.ini"
 cp "$root/opt/omarchy-ipad/theme/colors.toml" "$root/opt/omarchy-ipad/theme/shell.toml" "$root/home/tablet/.local/state/omarchy/current/theme/"
 ln -s /opt/omarchy-ipad/assets/0-liftoff-ipad-1536x2048.webp "$root/home/tablet/.local/state/omarchy/current/background"
 mkdir -p "$root/home/tablet/.config/omarchy/plugins/ipadlinux.battery"
 cp /opt/j72/battery/manifest.json /opt/j72/battery/BarWidget.qml "$root/home/tablet/.config/omarchy/plugins/ipadlinux.battery/"
 mkdir -p "$root/home/tablet/.config/omarchy/plugins/ipadlinux.wifi"
 cp /opt/j72/wifi-widget/manifest.json /opt/j72/wifi-widget/BarWidget.qml "$root/home/tablet/.config/omarchy/plugins/ipadlinux.wifi/"
 chown -R 1000:1000 "$root/home/tablet" "$root/run/user/1000"
 cp /etc/j72-session/input.rules "$root/run/udev/rules.d/99-j72-input.rules"
 busybox chroot "$root" /usr/lib/systemd/systemd-udevd --resolve-names=never > "$state/udev.log" 2>&1 &
 echo $! > "$state/udev.pid"
 for event in /sys/class/input/event*; do
  [ -e "$event/device/name" ] || continue
  case $(cat "$event/device/name") in
   'gpio-keys'|'J72 native touchscreen')
    echo add > "$event/uevent"
    busybox chroot "$root" /usr/bin/udevadm test --action=add "$event" >> "$state/udev-test.log" 2>&1
    busybox chgrp 992 "/dev/input/${event##*/}"; chmod 660 "/dev/input/${event##*/}";;
  esac
 done
 busybox chroot "$root" /usr/bin/seatd -g seat > "$state/seatd.log" 2>&1 &
 echo $! > "$state/seatd.pid"
 i=0
 while [ ! -S "$root/run/seatd.sock" ]; do i=$((i+1)); [ "$i" -lt 50 ] || return 1; sleep 0.1; done
 user /usr/bin/dbus-run-session -- /usr/bin/labwc -d -C /home/tablet/.config/labwc > "$state/labwc.log" 2>&1 &
 echo $! > "$state/desktop.pid"
 i=0
 while [ ! -f "$root/run/user/1000/j72-shell-started" ]; do
  i=$((i+1)); [ "$i" -lt 200 ] || return 1; sleep 0.2
 done
 busybox touch "$state/desktop-ready"
 echo 'J72_DESKTOP_STARTED; owner screen check still required'
}
case ${1:-status} in
 start)
  trap 'rc=$?; if [ "$rc" -ne 0 ]; then echo "Desktop start failed; preserving logs in /run/j72" >&2; stop || true; fi' EXIT
  start;;
 stop) stop;;
 status) [ -f "$state/desktop-ready" ] && echo started || { echo stopped; exit 1; };;
 *) echo 'usage: j72-desktop-session {start|stop|status}' >&2; exit 2;;
esac
