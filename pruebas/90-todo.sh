#!/usr/bin/env bash
# Corre toda la verificación: generador, matriz de la app, LUKS/respaldo y capas (secretos, revisión, tras reinicio).
S=$(cd "$(dirname "$0")" && pwd)
for f in "$S"/*.sh; do sed -i 's/\r$//' "$f"; done
echo "### Generador"; bash "$S/70-generador.sh" | tail -3
echo "### Matriz de la app"; bash "$S/55-matriz.sh"
echo "### LUKS y respaldo (23 postgresql)"; bash "$S/20-luks-respaldo.sh" /root/v/ti3062-23 > /root/log-luks.log 2>&1; grep -a "FALLA\]\|FALLAS:" /root/log-luks.log
echo "### Capas: revisión, secretos y tras reinicio"; bash "$S/80-capas.sh" /root/v/ti3062-23 2>&1 | grep -a "OK\]\|FALLA\|FALLAS:"
