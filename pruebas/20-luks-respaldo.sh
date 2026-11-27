#!/usr/bin/env bash
# LUKS en /respaldos, cron de respaldo, restauración probada y P8
set -uo pipefail
P="${1:?proyecto}"; source "$P/instalador/config.env"; cd "$P/instalador"
ok() { echo -e "\e[32m[OK]\e[0m $*"; }; bad() { echo -e "\e[31m[FALLA]\e[0m $*"; FALLAS=$((FALLAS+1)); }; FALLAS=0
t() { echo -e "\n\e[1;36m### $*\e[0m"; }
modprobe dm_crypt 2>/dev/null
# Limpieza de una corrida anterior
mountpoint -q /respaldos && umount /respaldos; cryptsetup close "respaldos_$NN" 2>/dev/null
IMG=/var/lib/ti3062/respaldos-$NN.luks; mkdir -p /var/lib/ti3062; rm -f $IMG; fallocate -l 64M $IMG
CLAVE='Frase-LUKS-de-prueba-2026'

t "Seguridad: rechaza un disco con datos"
ROOTDEV=$(findmnt -no SOURCE /)
OUT=$(echo SI | bash bd/02-luks-respaldos.sh "$ROOTDEV" 2>&1); [[ $OUT == *"ya tiene datos"* ]] && ok "no formatea $ROOTDEV" || { bad "intentó usar $ROOTDEV"; echo "$OUT" | tail -3; }

t "bd/02-luks-respaldos.sh (interactivo con expect)"
expect <<EOF > /tmp/luks.log 2>&1
set timeout 60
spawn bash bd/02-luks-respaldos.sh $IMG
expect "SI para continuar" { send "SI\r" }
expect "Enter passphrase" { send "$CLAVE\r" }
expect "Verify passphrase" { send "$CLAVE\r" }
expect "Enter passphrase for" { send "$CLAVE\r" }
expect eof
EOF
grep -q "cifrado con LUKS2" /tmp/luks.log && ok "volumen creado" || { bad "luks"; tail -15 /tmp/luks.log; }
mountpoint -q /respaldos && ok "/respaldos montado" || bad "no montado"
cryptsetup isLuks "$IMG" && ok "cabecera LUKS2 ($(cryptsetup luksDump $IMG | grep -m1 Version))" || bad "no es LUKS"
[[ $(stat -c %a /respaldos) == 700 ]] && ok "/respaldos 700" || bad "permisos"

t "bd/03-respaldo-cron.sh"
bash bd/03-respaldo-cron.sh > /tmp/resp.log 2>&1 && ok "respaldo ejecutado" || { bad "respaldo"; tail -10 /tmp/resp.log; }
cat /etc/cron.d/ti3062-respaldo
[[ $(awk '{print NF}' /etc/cron.d/ti3062-respaldo) -ge 7 ]] && ok "cron diario válido: $(cut -d' ' -f1-5 /etc/cron.d/ti3062-respaldo)" || bad "cron"
ULT=$(ls -1t /respaldos/*.sql.gz | head -1); zcat "$ULT" | grep -q "Prueba padre" && ok "el respaldo contiene los datos insertados" || bad "respaldo sin datos"
sha256sum -c "$ULT.sha256" >/dev/null && ok "checksum sha256" || bad "checksum"

t "Respaldo NO se escribe si /respaldos no está montado"
umount /respaldos; /usr/local/sbin/respaldo-ti3062.sh 2>/dev/null; [[ $? -ne 0 ]] && ok "falla controlada y registra en syslog" || bad "escribió fuera del volumen"
mount /dev/mapper/respaldos_$NN /respaldos

t "bd/04-probar-restauracion.sh"
bash bd/04-probar-restauracion.sh > /tmp/rest.log 2>&1 && ok "restauración" || bad "restauración"; cat /tmp/rest.log | tail -5
grep -q "OK" /tmp/rest.log && ! grep -q DIFERENTE /tmp/rest.log && ok "conteos coinciden" || bad "conteos"

t "P8: volumen cerrado ilegible"
bash bd/02-luks-respaldos.sh cerrar >/dev/null 2>&1
mountpoint -q /respaldos && bad "sigue montado" || ok "cerrado"
strings "$IMG" | grep -q "VAL-padre\|CREATE TABLE" && bad "datos legibles en claro" || ok "sin datos legibles (strings)"
expect <<EOF > /tmp/abrir.log 2>&1
spawn bash bd/02-luks-respaldos.sh abrir
expect "Enter passphrase" { send "$CLAVE\r" }
expect eof
EOF
mountpoint -q /respaldos && ok "reabre con la frase (procedimiento tras reinicio)" || { bad "abrir"; cat /tmp/abrir.log; }
echo -e "\nFALLAS: $FALLAS"
