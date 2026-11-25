#!/usr/bin/env bash
# Restauración probada: carga el último respaldo en una base temporal y compara conteos con la base real.
# Uso: sudo bash 04-probar-restauracion.sh
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"; source "$DIR/../config.env"
[[ $EUID -eq 0 ]] || { echo "Ejecuta con sudo"; exit 1; }
ULT=$(ls -1t /respaldos/${DB_NOMBRE}_*.sql.gz | head -1)
PRUEBA=${DB_NOMBRE}_restore
echo "Fecha: $(date)  Host: $(hostname)"; echo "Respaldo: $ULT"; sha256sum -c "$ULT.sha256"

if [[ $MOTOR == mariadb ]]; then
  mariadb -e "DROP DATABASE IF EXISTS $PRUEBA; CREATE DATABASE $PRUEBA;"
  zcat "$ULT" | mariadb "$PRUEBA"
  for T in {{TABLA_PADRE}} {{TABLA_HIJO}}; do
    A=$(mariadb -N -e "SELECT COUNT(*) FROM $DB_NOMBRE.$T"); B=$(mariadb -N -e "SELECT COUNT(*) FROM $PRUEBA.$T")
    echo "$T: original=$A restaurada=$B $([[ $A == "$B" ]] && echo OK || echo 'DIFERENTE (hubo inserciones después del respaldo)')"
  done
  mariadb -e "DROP DATABASE $PRUEBA;"
else
  runuser -u postgres -- dropdb --if-exists "$PRUEBA"; runuser -u postgres -- createdb "$PRUEBA"
  zcat "$ULT" | runuser -u postgres -- psql -q -d "$PRUEBA" >/dev/null
  for T in {{TABLA_PADRE}} {{TABLA_HIJO}}; do
    A=$(runuser -u postgres -- psql -tA -d "$DB_NOMBRE" -c "SELECT COUNT(*) FROM $T"); B=$(runuser -u postgres -- psql -tA -d "$PRUEBA" -c "SELECT COUNT(*) FROM $T")
    echo "$T: original=$A restaurada=$B $([[ $A == "$B" ]] && echo OK || echo 'DIFERENTE (hubo inserciones después del respaldo)')"
  done
  runuser -u postgres -- dropdb "$PRUEBA"
fi
echo "✅ Restauración verificada (base temporal eliminada)."
