#!/usr/bin/env bash
# Procedimiento tras reiniciar el laboratorio (AWS Academy detiene las instancias al cerrarlo).
# Abre el volumen LUKS (pide la frase; nunca se guarda), monta /respaldos, revisa el cron y la antigüedad
# del último respaldo, ejecuta uno si tiene más de 24 h y deja un resumen listo para la bitácora.
# Uso: sudo bash 05-tras-reinicio.sh
set -uo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"; source "$DIR/../config.env"
[[ $EUID -eq 0 ]] || { echo "Ejecuta con sudo"; exit 1; }
MAP="respaldos_$NN"; ESTADO=/etc/ti3062-luks-dispositivo
paso() { echo -e "\n\033[1;34m▶ $*\033[0m"; }
RES=()

paso "Volumen cifrado /respaldos"
if mountpoint -q /respaldos; then
  echo "  Ya estaba montado."; RES+=("LUKS: ya abierto")
else
  [[ -s $ESTADO ]] || { echo "No existe $ESTADO: primero ejecuta bd/02-luks-respaldos.sh"; exit 1; }
  DEV=$(cat $ESTADO)
  [[ -e /dev/mapper/$MAP ]] || cryptsetup open "$DEV" "$MAP" || { echo "No se pudo abrir el volumen (¿frase incorrecta?)."; exit 1; }
  mount /dev/mapper/$MAP /respaldos && RES+=("LUKS: abierto y montado tras reinicio") || { echo "No se pudo montar /respaldos"; exit 1; }
fi
df -h /respaldos | tail -1

paso "Servicio de base de datos"
SVC=$([[ $MOTOR == mariadb ]] && echo mariadb || echo postgresql)
systemctl is-active --quiet $SVC && { echo "  $SVC activo"; RES+=("$SVC: activo"); } || { systemctl restart $SVC; RES+=("$SVC: reiniciado"); }
ss -tlnp | grep -q ":$DB_PORT" && echo "  Escuchando en $BD_IP:$DB_PORT" || echo "  ⚠ $SVC no escucha en el puerto $DB_PORT"

paso "Respaldo programado"
if [[ -f /etc/cron.d/ti3062-respaldo ]]; then
  echo "  cron: $(cat /etc/cron.d/ti3062-respaldo)"
else
  echo "  ⚠ No hay cron de respaldo: ejecuta bd/03-respaldo-cron.sh"; RES+=("cron: no configurado")
fi
ULT=$(ls -1t /respaldos/${DB_NOMBRE}_*.sql.gz 2>/dev/null | head -1)
EDAD=999999
[[ -n $ULT ]] && EDAD=$(( ( $(date +%s) - $(stat -c %Y "$ULT") ) / 3600 ))
if [[ -z $ULT || $EDAD -ge 24 ]]; then
  echo "  Último respaldo: ${ULT:-ninguno} (${EDAD} h). Se ejecuta uno ahora."
  if [[ -x /usr/local/sbin/respaldo-ti3062.sh ]] && /usr/local/sbin/respaldo-ti3062.sh; then
    ULT=$(ls -1t /respaldos/${DB_NOMBRE}_*.sql.gz | head -1); RES+=("respaldo: ejecutado $(basename "$ULT")")
  else
    RES+=("respaldo: FALLÓ (revisa journalctl -t respaldo-ti3062)")
  fi
else
  echo "  Último respaldo: $(basename "$ULT") (hace ${EDAD} h): al día."; RES+=("respaldo: al día ($(basename "$ULT"))")
fi
[[ -n ${ULT:-} && -f $ULT.sha256 ]] && (cd /respaldos && sha256sum -c "$(basename "$ULT").sha256" --quiet) && RES+=("checksum: OK")

paso "Resumen para la bitácora (Área: Respaldo · Ref.: CP-9 / SC-28)"
echo "Fecha: $(date '+%F %T')   Host: $(hostname)"
printf '  - %s\n' "${RES[@]}"
logger -t respaldo-ti3062 "Procedimiento tras reinicio: ${RES[*]}"
