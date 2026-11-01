#!/bin/sh
# RAM-only status producer. Never publishes SSID, addresses or credentials.
set -eu
PATH=/bin:/sbin:/usr/bin:/usr/sbin
export PATH
while :; do
 if [ -f /run/j72/desktop-ready ] && [ -d /mnt/omarchy/run/user/1000 ]; then
  connected=false
  signal=-127
  frequency=0
  if [ -e /sys/class/net/wlan0/carrier ] && [ "$(cat /sys/class/net/wlan0/carrier)" = 1 ]; then
   connected=true
   link=$(busybox chroot /opt/j72-network /usr/bin/iw dev wlan0 link 2>/dev/null) || link=
   signal=$(printf '%s\n' "$link" | busybox awk '/^[ \t]*signal:/ && $2 ~ /^-[0-9]+$/ {print $2; exit}')
   frequency=$(printf '%s\n' "$link" | busybox awk '/^[ \t]*freq:/ && $2 ~ /^[0-9]+([.][0-9]+)?$/ {print int($2); exit}')
   signal=${signal:--127}
   frequency=${frequency:-0}
  fi
  output=/mnt/omarchy/run/user/1000/j72-wifi-status.json
  printf '{"connected":%s,"signal_dbm":%s,"frequency_mhz":%s}\n' "$connected" "$signal" "$frequency" > "$output.next"
  chmod 644 "$output.next"
  chown 1000:1000 "$output.next"
  mv "$output.next" "$output"
 fi
 sleep 5
done
