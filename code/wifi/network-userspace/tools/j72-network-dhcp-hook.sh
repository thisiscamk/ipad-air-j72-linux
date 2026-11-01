#!/bin/sh
# Runs inside the RAM network root. Only the selected wireless NIC is changed.
set -efu
[ -n "${interface:-}" ] && [ -e "/sys/class/net/$interface/phy80211" ] || exit 1
case "$interface" in *[!a-zA-Z0-9_-]*|'') exit 1;; esac
case "${1:-}" in
 deconfig)
  /bin/ip -4 address flush dev "$interface"
  /bin/ip -4 route flush dev "$interface"
  rm -f /run/lease-info
  ;;
 bound|renew)
  case "${ip:-}/${subnet:-}" in *[!0-9./]*|/|*/ ) exit 1;; esac
  prefix=0
  tail=0
  old_ifs=$IFS; IFS=.; set -- $subnet; IFS=$old_ifs
  [ "$#" = 4 ] || exit 1
  for octet do
   case "$octet" in 255) bits=8;;254)bits=7;;252)bits=6;;248)bits=5;;240)bits=4;;224)bits=3;;192)bits=2;;128)bits=1;;0)bits=0;;*)exit 1;;esac
   [ "$tail" = 0 ] || [ "$bits" = 0 ] || exit 1
   [ "$bits" = 8 ] || tail=1
   prefix=$((prefix + bits))
  done
  /bin/ip -4 address replace "$ip/$prefix" dev "$interface"
  for gateway in ${router:-}; do
   case "$gateway" in *[!0-9.]*|'') continue;; esac
   /bin/ip -4 route replace default via "$gateway" dev "$interface" metric 600
   break
  done
  : > /etc/resolv.conf
  for server in ${dns:-}; do
   case "$server" in *[!0-9.]*|'') continue;; esac
   printf 'nameserver %s\n' "$server" >> /etc/resolv.conf
  done
  printf 'interface=%s\nip=%s\nprefix=%s\n' "$interface" "$ip" "$prefix" > /run/lease-info
  ;;
 *) exit 0;;
esac
