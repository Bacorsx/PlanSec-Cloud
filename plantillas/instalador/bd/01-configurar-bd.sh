#!/usr/bin/env bash
# Configura el motor de BD en bd-NN: escucha solo en la IP privada, base ti3062_NN, tablas relacionadas
# y usuario exclusivo de la app con privilegios mínimos (sin ALL y sin '%': solo desde la IP de web-NN).
# Uso: sudo bash 01-configurar-bd.sh
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"; source "$DIR/../config.env"
[[ $EUID -eq 0 ]] || { echo "Ejecuta con sudo"; exit 1; }
CLAVE_ARCH=/root/.ti3062-clave-app
[[ -s $CLAVE_ARCH ]] || { umask 077; openssl rand -hex 16 > $CLAVE_ARCH; }
CLAVE=$(cat $CLAVE_ARCH)

if [[ $MOTOR == mariadb ]]; then
  CNF=/etc/mysql/mariadb.conf.d/50-server.cnf
  sed -i "s/^bind-address.*/bind-address = $BD_IP/" "$CNF"
  grep -q '^skip-name-resolve' "$CNF" || sed -i '/^\[mysqld\]/a skip-name-resolve' "$CNF"
  systemctl restart mariadb
  mariadb <<SQL
DELETE FROM mysql.global_priv WHERE User='';
DROP DATABASE IF EXISTS test;
CREATE DATABASE IF NOT EXISTS $DB_NOMBRE CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$DB_USUARIO'@'$WEB_IP' IDENTIFIED BY '$CLAVE';
ALTER USER '$DB_USUARIO'@'$WEB_IP' IDENTIFIED BY '$CLAVE';
GRANT SELECT, INSERT, UPDATE, DELETE ON $DB_NOMBRE.* TO '$DB_USUARIO'@'$WEB_IP';
FLUSH PRIVILEGES;
SQL
  mariadb "$DB_NOMBRE" < "$DIR/esquema.sql"
  echo "== Evidencia"; mariadb -e "SHOW GRANTS FOR '$DB_USUARIO'@'$WEB_IP'; SELECT User,Host FROM mysql.user;"
  mariadb "$DB_NOMBRE" -e "SHOW TABLES;"
else
  PGV=$(ls /etc/postgresql | sort -V | tail -1); C=/etc/postgresql/$PGV/main
  sed -i "s/^#\?listen_addresses.*/listen_addresses = 'localhost,$BD_IP'/" $C/postgresql.conf
  grep -q "$DB_USUARIO" $C/pg_hba.conf || echo "host  $DB_NOMBRE  $DB_USUARIO  $WEB_IP/32  scram-sha-256" >> $C/pg_hba.conf
  systemctl restart postgresql
  runuser -u postgres -- psql -v ON_ERROR_STOP=1 <<SQL
DO \$\$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '$DB_USUARIO') THEN CREATE ROLE $DB_USUARIO LOGIN; END IF;
END \$\$;
ALTER ROLE $DB_USUARIO WITH LOGIN PASSWORD '$CLAVE' NOSUPERUSER NOCREATEDB NOCREATEROLE;
SELECT 'CREATE DATABASE $DB_NOMBRE' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NOMBRE')\gexec
SQL
  runuser -u postgres -- psql -v ON_ERROR_STOP=1 -d "$DB_NOMBRE" -f "$DIR/esquema.sql"
  runuser -u postgres -- psql -v ON_ERROR_STOP=1 -d "$DB_NOMBRE" <<SQL
REVOKE ALL ON DATABASE $DB_NOMBRE FROM PUBLIC;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT CONNECT ON DATABASE $DB_NOMBRE TO $DB_USUARIO;
GRANT USAGE ON SCHEMA public TO $DB_USUARIO;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO $DB_USUARIO;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO $DB_USUARIO;
SQL
  echo "== Evidencia"; grep "$DB_USUARIO" $C/pg_hba.conf
  runuser -u postgres -- psql -d "$DB_NOMBRE" -c '\dt' -c '\dp'
fi
ss -tlnp | grep ":$DB_PORT"
cat <<EOF

✅ $MOTOR_NOMBRE listo en $(hostname) ($BD_IP:$DB_PORT), base $DB_NOMBRE, usuario $DB_USUARIO@$WEB_IP.
La contraseña de la app está en $CLAVE_ARCH (solo root). Para copiarla a web-$NN:
   sudo cat $CLAVE_ARCH
y pégala cuando 01-instalar-web.sh la pida. NO la subas al repositorio ni la incluyas en capturas.
EOF
