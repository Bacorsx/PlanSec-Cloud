#!/usr/bin/env bash
# Hardening + P5, P6, P7 con SSH real, TOTP real (oathtool) y auditd
# Uso: bash 30-hardening.sh <proyecto> <web|bd>
set -uo pipefail
P="${1:?proyecto}"; ROL="${2:?web|bd}"; source "$P/instalador/config.env"; cd "$P/instalador"
ok() { echo -e "\e[32m[OK]\e[0m $*"; }; bad() { echo -e "\e[31m[FALLA]\e[0m $*"; FALLAS=$((FALLAS+1)); }; FALLAS=0
t() { echo -e "\n\e[1;36m### $*\e[0m"; }
PW='Clave-Usuario-2026'; K=/root/keys-$NN; mkdir -p $K llaves
SSHO="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"
for u in $U_ADMIN $U_DEV $U_AUDIT; do [[ -f $K/$u ]] || ssh-keygen -q -t ed25519 -N '' -f $K/$u -C $u; cp $K/$u.pub llaves/; done
HOST=$([[ $ROL == web ]] && echo "$WEB_HOST" || echo "$BD_HOST")

t "01-hardening.sh $ROL ($FIREWALL)"
expect <<EOF > /tmp/hard.log 2>&1
set timeout 120
spawn bash comun/01-hardening.sh $ROL 10.$NNIP.0.99
expect {
  "New password:" { send "$PW\r"; exp_continue }
  "Retype new password:" { send "$PW\r"; exp_continue }
  eof
}
catch wait r; exit [lindex \$r 3]
EOF
RC=$?; [[ $RC == 0 ]] && grep -q "Hardening aplicado" /tmp/hard.log && ok "script terminó sin errores" || { bad "hardening rc=$RC"; tail -25 /tmp/hard.log; }
[[ $(hostname) == "$HOST" ]] && ok "hostname $HOST" || bad "hostname $(hostname) (WSL puede impedir hostnamectl)"

t "Identidades y permisos"
for g in $G_ADMIN $G_DEV $G_AUDIT; do getent group $g >/dev/null && ok "grupo $g" || bad "grupo $g"; done
for u in $U_ADMIN $U_DEV $U_AUDIT; do [[ $u == *$NN ]] && id $u >/dev/null 2>&1 && ok "usuario $u (sufijo $NN)" || bad "usuario $u"; done
[[ $(stat -c %a /srv/areas/administracion) == 2770 && $(stat -c %G /srv/areas/desarrollo) == $G_DEV ]] && ok "directorios por área restringidos" || bad "directorios"
runuser -u $U_DEV -- ls /srv/areas/administracion >/dev/null 2>&1 && bad "dev lee área admin" || ok "dev no accede al área de administración"
grep -h "ALL=" /etc/sudoers.d/2*-ti3062-* /etc/sudoers.d/3*-ti3062-* | grep -qE "\) ALL$|NOPASSWD: ALL" && bad "ALL para no administradores" || ok "sin ALL para desarrollo/auditoría"

t "SSH efectivo"
S=$(sshd -T 2>/dev/null)
for kv in "permitrootlogin no" "passwordauthentication no" "maxauthtries 3" "clientaliveinterval 300" "clientalivecountmax 2" "maxsessions 2"; do
  echo "$S" | grep -qx "$kv" && ok "$kv" || bad "$kv → $(echo "$S" | grep "^${kv%% *}")"; done
echo "$S" | grep -q "^allowgroups.*$G_ADMIN" && ok "$(echo "$S" | grep ^allowgroups)" || bad "allowgroups"
sshd -T -C user=$U_ADMIN,host=x,addr=10.$NNIP.0.99 | grep -q "authenticationmethods publickey,keyboard-interactive" && ok "admin exige llave + TOTP" || bad "Match Group admin"

t "Accesos SSH reales"
ssh $SSHO -o BatchMode=yes -i $K/$U_DEV $U_DEV@127.0.0.1 hostname >/dev/null 2>&1 && ok "$U_DEV entra con su llave ED25519" || bad "$U_DEV con llave"
OUT=$(ssh $SSHO -o BatchMode=yes -o PubkeyAuthentication=no $U_DEV@127.0.0.1 true 2>&1); [[ $OUT == *denied* && $OUT != *password* ]] && ok "P5 sin contraseña: $OUT" || bad "P5 password: $OUT"
install -d -m700 /root/.ssh; cp $K/$U_DEV.pub /root/.ssh/authorized_keys
OUT=$(ssh $SSHO -o BatchMode=yes -i $K/$U_DEV root@127.0.0.1 true 2>&1); [[ $OUT == *denied* ]] && ok "P5 root rechazado aun con llave válida" || bad "root: $OUT"; rm -f /root/.ssh/authorized_keys
runuser -u $U_ADMIN -- google-authenticator -t -d -f -r 3 -R 30 -w 3 -Q NONE -q >/dev/null 2>&1
SEC=$(head -1 /home/$U_ADMIN/.google_authenticator)
[[ -n $SEC ]] && ok "TOTP configurado para $U_ADMIN" || bad "google-authenticator"
OUT=$(ssh $SSHO -o BatchMode=yes -i $K/$U_ADMIN $U_ADMIN@127.0.0.1 true 2>&1); [[ $OUT == *denied* ]] && ok "admin solo con llave → rechazado" || bad "admin sin TOTP entró"
totp() { expect <<EOF
set timeout 20
spawn ssh $SSHO -i $K/$U_ADMIN $U_ADMIN@127.0.0.1 true
expect "Verification code:" { send "$1\r" }
expect {
  "Verification code:" { exit 1 }
  "denied" { exit 1 }
  timeout { exit 2 }
  eof
}
catch wait r; exit [lindex \$r 3]
EOF
}
sleep 1; totp 000000 >/dev/null 2>&1 && bad "P6 código incorrecto aceptado" || ok "P6 código TOTP incorrecto → rechazado"
grep -a "Invalid verification code for $U_ADMIN" /var/log/auth.log | tail -1 | grep -q . && ok "P6 registrado: Invalid verification code" || bad "P6 sin registro"
sleep 31; totp "$(oathtool --totp -b "$SEC")" >/dev/null 2>&1 && ok "admin con llave + código TOTP correcto → acceso" || bad "TOTP correcto rechazado"

t "sudo por rol y P7 con auditd"
systemctl is-active --quiet auditd && ok "auditd activo" || bad "auditd inactivo"
for k in cambios_passwd cambios_sudoers cambios_sshd uso_sudo; do auditctl -l | grep -q "key=$k" && ok "regla auditd $k" || bad "regla $k"; done
echo "$PW" | runuser -u $U_DEV -- sudo -S cat /etc/shadow >/dev/null 2>&1 && bad "P7 dev leyó /etc/shadow" || ok "P7 $U_DEV: sudo cat /etc/shadow denegado"
grep -q "$U_DEV.*command not allowed\|$U_DEV : command not allowed" /var/log/auth.log /var/log/sudo.log 2>/dev/null && ok "denegación en auth.log/sudo.log" || bad "denegación no registrada"
sleep 1; ausearch -k uso_sudo -i 2>/dev/null | grep -q "auid=$U_DEV" && ok "P7 registrado en auditd (ausearch -k uso_sudo)" || bad "auditd no registró"
SVC=$([[ $ROL == web ]] && echo apache2 || ([[ $MOTOR == mariadb ]] && echo mariadb || echo postgresql))
echo "$PW" | runuser -u $U_DEV -- sudo -S /usr/bin/systemctl status $SVC >/dev/null 2>&1; [[ $? -le 3 ]] && ok "$U_DEV puede operar $SVC" || bad "dev no opera $SVC"
echo "$PW" | runuser -u $U_AUDIT -- sudo -S /usr/sbin/aureport --summary >/dev/null 2>&1 && ok "$U_AUDIT lee aureport" || bad "auditor aureport"
echo "$PW" | runuser -u $U_AUDIT -- sudo -S /usr/bin/systemctl restart ssh >/dev/null 2>&1 && bad "auditor reinició ssh" || ok "auditor no puede reiniciar servicios"
aureport -l -i 2>/dev/null | tail -3 | grep -q . && ok "accesos SSH en auditd (aureport -l)" || bad "aureport -l vacío"

t "Firewall de host ($FIREWALL)"
if [[ $FIREWALL == ufw ]]; then
  ufw status | grep -q "Status: active" && ok "ufw activo" || bad "ufw"
  ufw status | tr -s ' ' | grep -q "^22/tcp ALLOW $([[ $ROL == web ]] && echo 10.$NNIP.0.99 || echo $WEB_IP)" && ok "22 solo desde origen permitido" || bad "regla 22"
  [[ $ROL == bd ]] && { ufw status | grep -q "^$DB_PORT/tcp.*$WEB_IP" && ok "$DB_PORT solo desde $WEB_IP" || bad "regla BD"; }
  [[ $ROL == web ]] && { ufw status | grep -q "^80/tcp.*Anywhere" && ok "80/443 abiertos" || bad "80"; }
else
  nft list ruleset | grep -q "policy drop" && ok "nftables policy drop" || bad "nft"
  nft list ruleset | grep -q "ip saddr $([[ $ROL == web ]] && echo 10.$NNIP.0.99 || echo $WEB_IP) tcp dport 22 accept" && ok "22 solo desde origen permitido" || bad "regla 22"
  systemctl is-enabled --quiet nftables && ok "nftables persistente" || bad "nft no habilitado"
fi

t "99-cerrar-ubuntu.sh (como $U_ADMIN)"
rm -rf /srv/areas/administracion/ti3062-$NN; cp -r "$P" /srv/areas/administracion/; chgrp -R $G_ADMIN /srv/areas/administracion/ti3062-$NN
echo "$PW" | runuser -u $U_ADMIN -- sudo -S bash /srv/areas/administracion/ti3062-$NN/instalador/comun/99-cerrar-ubuntu.sh > /tmp/cerrar.log 2>&1 && ok "cuenta ubuntu bloqueada" || { bad "cerrar ubuntu"; tail /tmp/cerrar.log; }
passwd -S ubuntu | grep -q " L " && ok "ubuntu: L (bloqueada)" || bad "ubuntu no bloqueada"
sshd -T | grep "^allowgroups" | grep -qw ubuntu && bad "ubuntu sigue en AllowGroups" || ok "AllowGroups sin ubuntu"
N=$(awk -F: '$3>=1000 && $3<60000 && $7 ~ /sh$/' /etc/passwd | while IFS=: read u _; do passwd -S $u | grep -q " L " || echo $u; done | wc -l)
[[ $N -le 3 ]] && ok "usuarios interactivos activos: $N (máx. 3)" || bad "$N usuarios activos"

t "Re-ejecución idempotente (cambio de IP admin) no re-habilita ubuntu"
bash comun/01-hardening.sh $ROL 10.$NNIP.0.98 > /tmp/hard2.log 2>&1 && ok "segunda ejecución OK" || { bad "segunda ejecución"; tail -5 /tmp/hard2.log; }
sshd -T | grep "^allowgroups" | grep -qw ubuntu && bad "ubuntu re-agregado" || ok "ubuntu sigue fuera"
echo -e "\nFALLAS: $FALLAS"
