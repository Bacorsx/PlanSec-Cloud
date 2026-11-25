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
  apt-get install -y $COMUNES apache2 php libapache2-mod-php "$PHP_EXT" openssl nmap $( [[ $MOTOR == mariadb ]] && echo mariadb-client || echo postgresql-client )
else
  apt-get install -y $COMUNES "$DB_PAQUETE"
fi
apt-get -y upgrade
echo "✅ Paquetes instalados en $(hostname)"
