#!/bin/sh
# Inside the RAM-only network root; no USB/root mounts or charger writes.
set -efu
PATH=/usr/bin:/usr/sbin:/bin
export PATH
command=${1:-status}
interface=${2:-wlan0}
wireless() {
 case "$interface" in *[!a-zA-Z0-9_-]*|'') exit 1;; esac
 [ -e "/sys/class/net/$interface/phy80211" ] || exit 1
}
stop_pid() {
 file=$1
 expected=$2
 [ -f "$file" ] || return 0
 pid=$(cat "$file")
 case "$pid" in ''|*[!0-9]*) exit 1;; esac
 if [ -r "/proc/$pid/cmdline" ]; then
  /bin/busybox tr '\000' '\n' < "/proc/$pid/cmdline" | /bin/busybox head -n 1 | /bin/busybox grep -qx "$expected"
  kill -TERM "$pid"
 fi
 attempts=0
 while [ -e "/proc/$pid" ]; do
  attempts=$((attempts+1)); [ "$attempts" -lt 5 ] || exit 1
  sleep 1
 done
 rm -f "$file"
}
case "$command" in
 inspect)
  iw dev
  iw phy
  ;;
 scan)
  wireless
  ip link set "$interface" up
  iw dev "$interface" scan
  ;;
 connect)
  wireless
  [ -s /etc/wpa_supplicant.conf ]
  [ ! -f /run/wpa.pid ] || exit 1
  mkdir -p /run/wpa_supplicant
  ip link set "$interface" up
  wpa_supplicant -D nl80211 -i "$interface" -c /etc/wpa_supplicant.conf -C /run/wpa_supplicant -P /run/wpa.pid -f /run/wpa.log -B
  attempts=0
  while ! wpa_cli -p /run/wpa_supplicant -i "$interface" status | /bin/busybox grep -qx wpa_state=COMPLETED; do
   attempts=$((attempts+1)); [ "$attempts" -lt 30 ] || exit 1
   sleep 1
  done
  [ ! -f /run/udhcpc.pid ] || exit 1
  # Background only after a lease succeeds, then retain normal renewal.
  udhcpc -i "$interface" -n -t 5 -T 3 -p /run/udhcpc.pid -s /usr/sbin/j72-dhcp-hook > /run/dhcp.log 2>&1
  [ -s /run/lease-info ]
  wpa_cli -p /run/wpa_supplicant -i "$interface" status
  ;;
 ssh)
  wireless
  [ ! -f /run/dropbear.pid ] || exit 1
  /usr/sbin/dropbear -E -s -j -k -l "$interface" -P /run/dropbear.pid -r /etc/dropbear/hostkey > /run/dropbear.log 2>&1
  ;;
 https)
  wireless
  curl -4 --interface "$interface" --fail --silent --show-error --max-time 20 --cacert /etc/ssl/certs/ca-certificates.crt -o /run/https-response -w 'http_code=%{http_code}\nbytes=%{size_download}\n' https://www.kernel.org/
  ;;
 status)
  wireless
  iw dev "$interface" link
  wpa_cli -p /run/wpa_supplicant -i "$interface" status
  ip -4 address show dev "$interface"
  ip -4 route show
  ;;
 stop)
  wireless
  stop_pid /run/udhcpc.pid udhcpc
  # The supplicant owns its control socket; let it terminate itself.
  if [ -S "/run/wpa_supplicant/$interface" ]; then wpa_cli -p /run/wpa_supplicant -i "$interface" terminate; fi
  stop_pid /run/dropbear.pid /usr/sbin/dropbear
  ip -4 address flush dev "$interface"
  ip -4 route flush dev "$interface"
  # Do not hand the radio owner back until each recorded daemon has exited.
  for file in /run/wpa.pid /run/udhcpc.pid /run/dropbear.pid; do
   [ -f "$file" ] || continue
   pid=$(cat "$file")
   case "$pid" in ''|*[!0-9]*) exit 1;; esac
   attempts=0
   while [ -e "/proc/$pid" ]; do
    attempts=$((attempts+1)); [ "$attempts" -lt 5 ] || exit 1
    sleep 1
   done
  done
  rm -f /run/wpa.pid
  ;;
 *) exit 2;;
esac
