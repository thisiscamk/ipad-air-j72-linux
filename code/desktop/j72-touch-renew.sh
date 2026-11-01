#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-only
# Temporary RAM-session bridge for the old #33 driver's 30-minute limit.
# Only a natural, healthy expiry may restart; an explicit stop stays stopped.
set -eu
param=/sys/module/j72_touch_session/parameters
state=/run/j72-touch-renew

eligible() {
 [ "$(cat "$param/session_state")" = 0 ] &&
 [ "$(cat "$param/enabled")" = N ] &&
 [ "$(cat "$param/stop_requested")" = N ] &&
 [ "$(cat "$param/cleanup_ok")" = Y ] &&
 [ "$(cat "$param/firmware_healthy")" = 1 ] &&
 [ "$(cat "$param/capture_seconds")" = 1800 ] &&
 [ "$(cat "$param/xfer_errors")" = 0 ] &&
 [ "$(cat "$param/input_timeouts")" = 0 ] &&
 [ "$(cat "$param/input_frames")" -gt 10 ]
}

desktop_ready() {
 test -f /run/j72/desktop-ready &&
 grep -q ' /mnt/omarchy ext4 ro,' /proc/mounts || return 1
 pid=$(cat /run/j72/desktop.pid)
 case "$pid" in ''|*[!0-9]*) return 1;; esac
 test -d "/proc/$pid"
}

main() {
 [ "$(uname -v)" = '#33 SMP PREEMPT Sat Oct 31 11:57:21 +08 2026' ]
 [ "$(cat /proc/device-tree/model)" = 'Apple iPad Air (Cellular)' ]
 mkdir -p "$state"
 trap 'echo STOPPED > "$state/result"; exit 0' TERM INT
 echo WATCHING > "$state/result"
 read -r begin rest < /proc/uptime
 begin=${begin%.*}
 renewed=0
 while [ "$renewed" -lt 2 ]; do
  desktop_ready || break
  read -r now rest < /proc/uptime
  [ "$((${now%.*} - begin))" -lt 4000 ] || break
  status=$(cat "$param/session_state")
  [ "$status" != 4 ] || { echo FAILED_WORKER > "$state/result"; exit 1; }
  if [ "$status" = 0 ]; then
   eligible || { echo EXPLICIT_STOP_OR_UNHEALTHY > "$state/result"; exit 0; }
   desktop_ready || break
   /sbin/j72-touch-session status > "$state/before-$renewed.txt"
   /sbin/j72-touch-session start
   for event in /sys/class/input/event*; do
    [ -e "$event/device/name" ] || continue
    if [ "$(cat "$event/device/name")" = 'J72 native touchscreen' ]; then
     echo add > "$event/uevent"
     busybox chroot /mnt/omarchy /usr/bin/udevadm test --action=add "$event" >> "$state/udev.log" 2>&1
     busybox chgrp 992 "/dev/input/${event##*/}"
     chmod 660 "/dev/input/${event##*/}"
    fi
   done
   /sbin/j72-touch-session status > "$state/after-$renewed.txt"
   renewed=$((renewed+1))
   echo "$renewed" > "$state/renewed"
  fi
  sleep 1
 done
 echo FINISHED > "$state/result"
}

main
