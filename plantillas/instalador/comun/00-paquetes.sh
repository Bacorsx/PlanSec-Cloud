#!/usr/bin/env bash
# Instala TODOS los paquetes que necesita la instancia. En bd-NN ejecútalo mientras exista la NAT temporal.
# Uso: sudo bash 00-paquetes.sh web|bd
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"; source "$DIR/../config.env"
ROL="${1:?Uso: $0 web|bd}"; [[ $EUID -eq 0 ]] || { echo "Ejecuta con sudo"; exit 1; }
export DEBIAN_FRONTEND=noninteractive
COMUNES="auditd audispd-plugins libpam-google-authenticator cryptsetup $FIREWALL curl"
apt-get update
if [[ "$ROL" == web ]]; then
  CLIENTE_BD=$([[ $MOTOR == mariadb ]] && echo mariadb-client || echo postgresql-client)
  apt-get install -y $COMUNES apache2 php libapache2-mod-php php-mbstring "$PHP_EXT" openssl nmap "$CLIENTE_BD"
else
  apt-get install -y $COMUNES "$DB_PAQUETE"
fi
apt-get -y upgrade
echo "✅ Paquetes instalados en $(hostname)"
