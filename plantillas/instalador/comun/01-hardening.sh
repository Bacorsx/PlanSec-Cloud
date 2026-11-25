#!/usr/bin/env bash
# Endurecimiento del SO (Unidad 2): identidades, sudoers, SSH, MFA, auditd y firewall de host.
# Uso: sudo bash 01-hardening.sh web|bd [IP_ADMIN]
#   - IP_ADMIN (solo web): tu IP pública para SSH. Debe coincidir con sg-web-NN.
#   - Coloca antes las llaves públicas ED25519 en ../llaves/<usuario>.pub
# Mantén una segunda sesión SSH abierta mientras lo ejecutas, por si algo falla.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"; source "$DIR/../config.env"
ROL="${1:?Uso: $0 web|bd [IP_ADMIN]}"; ADMIN_IP="${2:-}"
[[ $EUID -eq 0 ]] || { echo "Ejecuta con sudo"; exit 1; }
[[ "$ROL" == web && -z "$ADMIN_IP" ]] && { echo "En web indica tu IP pública: $0 web 190.20.30.40"; exit 1; }
HOST=$([[ $ROL == web ]] && echo "$WEB_HOST" || echo "$BD_HOST")
SVC=$([[ $ROL == web ]] && echo apache2 || ([[ $MOTOR == mariadb ]] && echo mariadb || echo postgresql))
paso() { echo -e "\n\033[1;32m▶ $*\033[0m"; }

paso "Hostname $HOST"
hostnamectl set-hostname "$HOST"
grep -q "$HOST" /etc/hosts || echo "127.0.1.1 $HOST" >> /etc/hosts

paso "Grupos funcionales y usuarios (máximo 3, uno por grupo)"
declare -A GRUPO=( ["$U_ADMIN"]="$G_ADMIN" ["$U_DEV"]="$G_DEV" ["$U_AUDIT"]="$G_AUDIT" )
for g in "$G_ADMIN" "$G_DEV" "$G_AUDIT"; do groupadd -f "$g"; done
for u in "$U_ADMIN" "$U_DEV" "$U_AUDIT"; do
  id "$u" &>/dev/null || useradd -m -s /bin/bash -g "${GRUPO[$u]}" -c "TI3062 $NN" "$u"
  install -d -m 700 -o "$u" -g "${GRUPO[$u]}" "/home/$u/.ssh"
  if [[ -f "$DIR/../llaves/$u.pub" ]]; then
    grep -q "ssh-ed25519" "$DIR/../llaves/$u.pub" || { echo "La llave de $u no es ED25519"; exit 1; }
    install -m 600 -o "$u" -g "${GRUPO[$u]}" "$DIR/../llaves/$u.pub" "/home/$u/.ssh/authorized_keys"
    echo "  llave instalada para $u"
  else
    echo "  ⚠ Falta llaves/$u.pub (genera en tu PC: ssh-keygen -t ed25519 -f ~/.ssh/$u -C $u@$HOST)"
  fi
  if ! passwd -S "$u" | grep -q " P "; then echo "  Contraseña para sudo de $u:"; passwd "$u"; fi
done

paso "Directorios por área con permisos restringidos"
install -d -m 2770 -o root -g "$G_ADMIN" /srv/areas/administracion
install -d -m 2770 -o root -g "$G_DEV"   /srv/areas/desarrollo
install -d -m 2750 -o root -g "$G_AUDIT" /srv/areas/auditoria
chmod 755 /srv/areas
ls -ld /srv/areas/*

paso "sudoers por rol (comandos específicos; ALL solo para administración)"
cat > /etc/sudoers.d/10-ti3062-admin <<EOF
# Administración: control total (AC-6 con MFA obligatorio en SSH)
%$G_ADMIN ALL=(ALL:ALL) ALL
EOF
cat > /etc/sudoers.d/20-ti3062-desarrollo <<EOF
# Desarrollo: solo operar el servicio de su área
%$G_DEV ALL=(root) /usr/bin/systemctl status $SVC, /usr/bin/systemctl restart $SVC, /usr/bin/systemctl reload $SVC, /usr/bin/journalctl -u $SVC --no-pager
EOF
cat > /etc/sudoers.d/30-ti3062-auditoria <<EOF
# Auditoría: solo lectura de registros
%$G_AUDIT ALL=(root) /usr/sbin/ausearch, /usr/sbin/aureport, /usr/bin/tail -n 200 /var/log/auth.log, /usr/bin/journalctl -u ssh --no-pager, /usr/bin/last
EOF
cat > /etc/sudoers.d/00-ti3062-defaults <<'EOF'
Defaults logfile="/var/log/sudo.log"
Defaults log_input, log_output
Defaults passwd_tries=3
EOF
chmod 440 /etc/sudoers.d/*-ti3062-*
for f in /etc/sudoers.d/*-ti3062-*; do visudo -cf "$f"; done

paso "SSH endurecido"
DEF_UB=$(passwd -S ubuntu 2>/dev/null | awk '{print $2}' | grep -q '^L' && echo no || echo si)
INCLUIR_UBUNTU="${INCLUIR_UBUNTU:-$DEF_UB}"   # se quita al final con 99-cerrar-ubuntu.sh
EXTRA=$([[ $INCLUIR_UBUNTU == si ]] && echo " ubuntu" || echo "")
cat > /etc/ssh/sshd_config.d/10-ti3062.conf <<EOF
# TI3062 NN $NN — $HOST
PermitRootLogin no
PasswordAuthentication no
PermitEmptyPasswords no
PubkeyAuthentication yes
KbdInteractiveAuthentication yes
UsePAM yes
MaxAuthTries 3
MaxSessions 2
LoginGraceTime 30
ClientAliveInterval 300
ClientAliveCountMax 2
X11Forwarding no
AllowTcpForwarding $([[ $ROL == web ]] && echo yes || echo no)
LogLevel VERBOSE
AllowGroups $G_ADMIN $G_DEV $G_AUDIT$EXTRA
Banner /etc/issue.net

Match Group $G_ADMIN
    AuthenticationMethods publickey,keyboard-interactive
EOF
echo "Acceso exclusivo para personal autorizado del proyecto TI3062-$NN. Toda actividad es registrada." > /etc/issue.net

paso "MFA TOTP para el grupo $G_ADMIN (pam_google_authenticator)"
cp -n /etc/pam.d/sshd /etc/pam.d/sshd.bak-ti3062
sed -i 's/^@include common-auth/#@include common-auth  # TI3062: la llave reemplaza la contraseña; el 2º factor es TOTP/' /etc/pam.d/sshd
grep -q pam_google_authenticator /etc/pam.d/sshd || echo "auth required pam_google_authenticator.so nullok" >> /etc/pam.d/sshd
sshd -t && systemctl restart ssh
sshd -T | grep -Ei "permitrootlogin|passwordauthentication|maxauthtries|maxsessions|clientalive|allowgroups"
echo "  ➜ Ahora $U_ADMIN debe iniciar sesión y ejecutar: google-authenticator -t -d -f -r 3 -R 30 -w 3"
echo "    (no captures el QR, el secreto ni los códigos de emergencia)"

paso "auditd"
cat > /etc/audit/rules.d/50-ti3062.rules <<'EOF'
## TI3062 — reglas de auditoría
-w /etc/passwd -p wa -k cambios_passwd
-w /etc/shadow -p wa -k cambios_passwd
-w /etc/group -p wa -k cambios_grupos
-w /etc/sudoers -p wa -k cambios_sudoers
-w /etc/sudoers.d/ -p wa -k cambios_sudoers
-w /etc/ssh/sshd_config -p wa -k cambios_sshd
-w /etc/ssh/sshd_config.d/ -p wa -k cambios_sshd
-w /usr/bin/sudo -p x -k uso_sudo
-w /var/log/sudo.log -p wa -k uso_sudo
-w /var/log/faillog -p wa -k accesos
-w /var/log/lastlog -p wa -k accesos
-w /var/run/utmp -p wa -k sesiones
-w /var/log/wtmp -p wa -k sesiones
-w /var/log/btmp -p wa -k sesiones
EOF
systemctl enable --now auditd
augenrules --load
auditctl -l

paso "Firewall de host: $FIREWALL (coherente con los Security Groups)"
if [[ $ROL == web ]]; then
  REGLAS_TCP=("80:any" "443:any" "22:$ADMIN_IP")
else
  REGLAS_TCP=("$DB_PORT:$WEB_IP" "22:$WEB_IP")
fi
if [[ $FIREWALL == ufw ]]; then
  ufw --force reset >/dev/null
  ufw default deny incoming; ufw default allow outgoing
  for r in "${REGLAS_TCP[@]}"; do p=${r%%:*}; o=${r#*:}
    if [[ $o == any ]]; then ufw allow "$p/tcp"; else ufw allow from "$o" to any port "$p" proto tcp; fi
  done
  ufw logging on; ufw --force enable; ufw status verbose
else
  systemctl disable --now ufw 2>/dev/null || true
  {
    echo '#!/usr/sbin/nft -f'; echo 'flush ruleset'
    echo 'table inet filtro_ti3062 {'
    echo '  chain entrada { type filter hook input priority 0; policy drop;'
    echo '    ct state established,related accept'; echo '    iif lo accept'; echo '    ip protocol icmp accept'
    for r in "${REGLAS_TCP[@]}"; do p=${r%%:*}; o=${r#*:}
      if [[ $o == any ]]; then echo "    tcp dport $p accept"; else echo "    ip saddr $o tcp dport $p accept"; fi
    done
    echo '    log prefix "nft-drop: " counter drop'; echo '  }'
    echo '  chain reenvio { type filter hook forward priority 0; policy drop; }'
    echo '  chain salida { type filter hook output priority 0; policy accept; }'
    echo '}'
  } > /etc/nftables.conf
  nft -c -f /etc/nftables.conf && systemctl enable nftables && systemctl restart nftables && nft list ruleset
fi

echo -e "\n✅ Hardening aplicado en $HOST. Prueba en OTRA terminal antes de cerrar esta sesión."
