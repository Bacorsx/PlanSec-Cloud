#!/usr/bin/env bash
# Instala el respaldo automático diario de la BD hacia /respaldos (volumen LUKS) y lo ejecuta una vez.
# Uso: sudo bash 03-respaldo-cron.sh
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"; source "$DIR/../config.env"
[[ $EUID -eq 0 ]] || { echo "Ejecuta con sudo"; exit 1; }

if [[ $MOTOR == mariadb ]]; then
  DUMP="mariadb-dump --single-transaction --routines $DB_NOMBRE"
else
  DUMP="runuser -u postgres -- pg_dump --clean --if-exists $DB_NOMBRE"
fi

cat > /usr/local/sbin/respaldo-ti3062.sh <<EOF
#!/usr/bin/env bash
# Respaldo diario de $DB_NOMBRE — generado para TI3062 NN $NN
set -euo pipefail
umask 077
if ! mountpoint -q /respaldos; then
  logger -t respaldo-ti3062 "ERROR: /respaldos (LUKS) no está montado; respaldo NO realizado"; exit 1
fi
ARCH=/respaldos/${DB_NOMBRE}_\$(date +%F_%H%M).sql.gz
$DUMP | gzip -9 > "\$ARCH"
sha256sum "\$ARCH" > "\$ARCH.sha256"
find /respaldos -name '${DB_NOMBRE}_*.sql.gz*' -mtime +$RETENCION_DIAS -delete
logger -t respaldo-ti3062 "OK \$ARCH \$(du -h "\$ARCH" | cut -f1)"
EOF
chmod 750 /usr/local/sbin/respaldo-ti3062.sh

echo "$CRON_RESPALDO root /usr/local/sbin/respaldo-ti3062.sh" > /etc/cron.d/ti3062-respaldo
chmod 644 /etc/cron.d/ti3062-respaldo

/usr/local/sbin/respaldo-ti3062.sh
echo "== Evidencia"; cat /etc/cron.d/ti3062-respaldo; ls -lh /respaldos; journalctl -t respaldo-ti3062 --no-pager | tail -3
echo -e "\n✅ Respaldo programado ($CRON_RESPALDO) en $(hostname). Retención: $RETENCION_DIAS días."
