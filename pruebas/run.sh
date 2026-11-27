#!/usr/bin/env bash
# Uso: bash run.sh <prueba> <args...>   — regenera los proyectos si se pide con REGEN=1 y guarda log
S=$(cd "$(dirname "$0")" && pwd)
G=${GENERADOR:-$(cd "$(dirname "$0")/.." && pwd)}
if [[ "${REGEN:-0}" == 1 ]]; then
  (cd $G && python3 generar.py --nn 07 --nombre "Prueba MariaDB" --github test --motor mariadb --firewall ufw --salida /root/v --forzar >/dev/null &&
   python3 generar.py --nn 23 --nombre "Prueba Postgres" --github test --motor postgresql --firewall nftables --salida /root/v --forzar >/dev/null)
fi
PR="$1"; shift
bash "$S/$PR" "$@" > "/root/log-$PR.log" 2>&1
grep -aE "\[OK\]|FALLA|###|⚠" "/root/log-$PR.log"
