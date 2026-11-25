#!/usr/bin/env bash
# Deja la instancia con un máximo de 3 usuarios interactivos: bloquea la cuenta inicial "ubuntu".
# Ejecutar SOLO después de comprobar que el administrador entra con llave + TOTP y puede usar sudo.
# Uso: sudo bash 99-cerrar-ubuntu.sh
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"; source "$DIR/../config.env"
[[ $EUID -eq 0 ]] || { echo "Ejecuta con sudo"; exit 1; }
[[ "${SUDO_USER:-}" == "$U_ADMIN" ]] || { echo "Ejecuta este script como $U_ADMIN (no como ubuntu) para comprobar que su acceso funciona."; exit 1; }
[[ -s /home/$U_ADMIN/.google_authenticator ]] || { echo "$U_ADMIN aún no configura TOTP. Abortando."; exit 1; }
sed -i 's/^\(AllowGroups .*\) ubuntu$/\1/' /etc/ssh/sshd_config.d/10-ti3062.conf
sshd -t && systemctl restart ssh
usermod -L -e 1 ubuntu
rm -f /etc/sudoers.d/90-cloud-init-users
grep AllowGroups /etc/ssh/sshd_config.d/10-ti3062.conf
echo "Usuarios con shell interactiva:"; awk -F: '$7 ~ /(bash|sh)$/ && $3>=1000 {print " - "$1}' /etc/passwd
passwd -S ubuntu
echo "✅ Cuenta ubuntu bloqueada en $(hostname)."
