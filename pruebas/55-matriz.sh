#!/usr/bin/env bash
# Corre 50-app.sh sobre la matriz de temáticas y motores y resume las fallas.
S=$(cd "$(dirname "$0")" && pwd)
truncate -s0 /var/log/apache2/error.log
for c in "07 mariadb ferreteria" "23 postgresql canchas" "07 mariadb hostal" "23 postgresql laboratorio" "07 mariadb datacenter" "23 postgresql armado" "07 mariadb gimnasio" "23 postgresql ferreteria"; do
  set -- $c
  rm -f /etc/ssl/private/ti3062.key
  bash "$S/50-app.sh" "$@" > "/root/log-app-$3-$2.log" 2>&1
  echo "== $3 ($2): $(grep -a 'FALLAS:' /root/log-app-$3-$2.log) $(grep -ac '\[OK\]' /root/log-app-$3-$2.log) OK"
  grep -a "FALLA\]" "/root/log-app-$3-$2.log" | sed 's/^/   /'
done
