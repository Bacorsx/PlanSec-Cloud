#!/usr/bin/env bash
# Pruebas de: verificar-secretos + pre-push, revisar-instalador y 05-tras-reinicio (LUKS).
# Uso: bash 80-capas.sh <proyecto con LUKS ya configurado>
set -uo pipefail
P="${1:?proyecto}"; source "$P/instalador/config.env"
ok() { echo -e "\e[32m[OK]\e[0m $*"; }; bad() { echo -e "\e[31m[FALLA]\e[0m $*"; FALLAS=$((FALLAS+1)); }; FALLAS=0
t() { echo -e "\n\e[1;36m### $*\e[0m"; }

t "revisar-instalador.sh"
R=/tmp/rev-$NN; rm -rf $R; cp -r $P $R
bash $R/instalador/revisar-instalador.sh > /tmp/rev.log 2>&1 && ok "proyecto recién generado: revisión OK" || { bad "revisión falló"; tail -15 /tmp/rev.log; }
echo "# cambio no esperado" >> $R/instalador/comun/01-hardening.sh
bash $R/instalador/revisar-instalador.sh > /tmp/rev2.log 2>&1 && bad "no detectó el script modificado" || { grep -q "01-hardening.sh" /tmp/rev2.log && ok "detecta el script modificado (manifiesto)"; }

t "verificar-secretos.sh + pre-push"
G=/tmp/repo-$NN; B=/tmp/remoto-$NN.git; rm -rf $G $B; cp -r $P $G; git init -q --bare $B
cd $G && git init -q -b main && git config user.email prueba@ejemplo.cl && git config user.name prueba && git config core.hooksPath .githooks
chmod +x .githooks/pre-push && git remote add origin $B && git add -A && git commit -qm "inicial"
bash instalador/verificar-secretos.sh > /tmp/sec.log 2>&1 && ok "repositorio limpio pasa ($(tail -1 /tmp/sec.log | sed 's/\x1b\[[0-9;]*m//g'))" || { bad "repo limpio rechazado"; cat /tmp/sec.log; }
git push -q origin main 2>/tmp/push1.log && ok "push limpio permitido" || { bad "push limpio bloqueado"; cat /tmp/push1.log; }
printf -- '-----BEGIN OPENSSH PRIVATE KEY-----\nAAAA\n-----END OPENSSH PRIVATE KEY-----\n' > instalador/llaves/admin.pub
echo "otpauth://totp/x?secret=ABC" > notas.txt
git add -A && git commit -qm "secreto de prueba"
git push -q origin main > /tmp/push2.log 2>&1 && bad "push con secretos permitido" || ok "push con llave privada y otpauth bloqueado"
grep -q "PRIVATE KEY" /tmp/push2.log && grep -q "otpauth" /tmp/push2.log && ok "el bloqueo indica los archivos" || { bad "mensaje del bloqueo"; cat /tmp/push2.log; }
touch db.ini; git add -f db.ini; bash instalador/verificar-secretos.sh >/dev/null 2>&1 && bad "db.ini no detectado" || ok "db.ini detectado"
cd /

t "05-tras-reinicio.sh (LUKS cerrado como tras reiniciar el laboratorio)"
cd $P/instalador
CLAVE='Frase-LUKS-de-prueba-2026'
mountpoint -q /respaldos || bash bd/02-luks-respaldos.sh abrir <<<"$CLAVE" >/dev/null 2>&1
[[ -x /etc/update-motd.d/99-ti3062-luks ]] && ok "aviso de inicio de sesión instalado" || bad "falta /etc/update-motd.d/99-ti3062-luks"
bash bd/02-luks-respaldos.sh cerrar >/dev/null 2>&1
/etc/update-motd.d/99-ti3062-luks | grep -q "CERRADO" && ok "el aviso aparece con el volumen cerrado" || bad "sin aviso con el volumen cerrado"
touch -d '30 hours ago' /respaldos 2>/dev/null
expect <<EOF > /tmp/reinicio.log 2>&1
set timeout 120
spawn bash bd/05-tras-reinicio.sh
expect "passphrase" { send "$CLAVE\r" }
expect eof
EOF
mountpoint -q /respaldos && ok "volumen abierto y montado" || { bad "no montó /respaldos"; tail -20 /tmp/reinicio.log; }
grep -aq "Resumen para la bitácora" /tmp/reinicio.log && ok "resumen para la bitácora: $(grep -a '  - ' /tmp/reinicio.log | tr -d '\r' | tr '\n' ' ' | cut -c1-200)" || bad "sin resumen"
/etc/update-motd.d/99-ti3062-luks | grep -q "CERRADO" && bad "aviso con el volumen abierto" || ok "sin aviso con el volumen abierto"
echo -e "\nFALLAS: $FALLAS"
