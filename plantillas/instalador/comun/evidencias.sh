#!/usr/bin/env bash
# Muestra en pantalla (con hostname y fecha) la evidencia de cada control para capturar.
# Uso: sudo bash evidencias.sh [seccion]    secciones: identidad ssh mfa sudo auditd sesiones tls firewall red bd luks respaldo todo
set -uo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"; source "$DIR/../config.env"
S="${1:-todo}"
t() { echo -e "\n\033[1;35m═══ [$(hostname)] $* — $(date '+%F %T')\033[0m"; }
en() { [[ $S == todo || $S == "$1" ]]; }
en identidad && { t "Grupos y usuarios"; getent group "$G_ADMIN" "$G_DEV" "$G_AUDIT"; id "$U_ADMIN" "$U_DEV" "$U_AUDIT"; ls -ld /srv/areas/*; }
en sudo      && { t "sudoers"; for f in /etc/sudoers.d/*ti3062*; do echo "# $f"; cat "$f"; done; sudo -l -U "$U_DEV"; sudo -l -U "$U_AUDIT"; }
en ssh       && { t "SSH efectivo"; mkdir -p /run/sshd; sshd -T | grep -Ei "^(permitrootlogin|passwordauthentication|maxauthtries|maxsessions|clientaliveinterval|clientalivecountmax|allowgroups|authenticationmethods)"; ls -l /home/*/.ssh/authorized_keys; }
en mfa       && { t "MFA (PAM)"; grep -n "google\|common-auth" /etc/pam.d/sshd; grep -A1 "^Match" /etc/ssh/sshd_config.d/10-ti3062.conf; }
en auditd    && { t "auditd"; auditctl -l; aureport --summary 2>/dev/null | head -20; ausearch -k uso_sudo -i 2>/dev/null | tail -8; t "Accesos SSH (auditd)"; aureport -l -i 2>/dev/null | tail -10; }
en sesiones  && { t "Sesiones exitosas con IP de origen"; last -i -n 30 | grep -v '^reboot' | head -15; t "Intentos fallidos"; lastb -i -n 15 2>/dev/null || echo "(sin registros)";
                  t "Usuarios conectados ahora"; who -a; t "Último acceso por usuario (Never logged in = cuenta sin uso)"; lastlog 2>/dev/null || lastlog2 2>/dev/null; }
en tls       && { t "Cifrado en tránsito web ↔ bd (SC-8)"
                  if [[ -f /etc/ti3062/tls/servidor.crt ]]; then
                    openssl x509 -in /etc/ti3062/tls/servidor.crt -noout -subject -issuer -enddate -ext subjectAltName
                    if [[ $MOTOR == mariadb ]]; then mariadb -e "SHOW GLOBAL VARIABLES WHERE Variable_name IN ('have_ssl','require_secure_transport','tls_version'); SELECT User, Host, ssl_type FROM mysql.user WHERE User='$DB_USUARIO';"
                    else runuser -u postgres -- psql -tAc "SHOW ssl" ; runuser -u postgres -- psql -tAc "SHOW ssl_min_protocol_version"; grep -v '^#' /etc/postgresql/*/main/pg_hba.conf | grep "$DB_USUARIO\|hostnossl"; fi
                  else
                    ls -l /etc/ti3062/; openssl x509 -in /etc/ti3062/bd-ca.pem -noout -subject -enddate
                    runuser -u www-data -- php -r 'require "/var/www/ti3062/nucleo.php"; print_r(canal_bd());'
                  fi; }
en firewall  && { t "Firewall de host ($FIREWALL)"; if [[ $FIREWALL == ufw ]]; then ufw status verbose; else nft list ruleset; fi; }
en red       && { t "Red"; ip -br a; ip route; ss -tlnp; }
if [[ $(hostname) == "$BD_HOST" ]]; then
  en red     && { t "P4 salida a Internet desde bd (debe fallar)"; ping -c 2 -W 2 8.8.8.8; curl -m 5 -sS https://aws.amazon.com -o /dev/null; echo "código salida: $?"; }
  en luks    && { t "LUKS"; lsblk -f; cryptsetup status "respaldos_$NN"; df -h /respaldos; }
  en respaldo && { t "Respaldo"; cat /etc/cron.d/ti3062-respaldo; ls -lh /respaldos; journalctl -t respaldo-ti3062 --no-pager | tail -5; }
fi
exit 0
