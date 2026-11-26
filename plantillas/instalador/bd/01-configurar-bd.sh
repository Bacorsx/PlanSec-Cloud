#!/usr/bin/env bash
# Configura el motor de BD en bd-NN:
#  - escucha solo en la IP privada y exige TLS (certificado de bd firmado por una CA propia del proyecto, SC-8)
#  - base ti3062_NN con 4 tablas relacionadas (usuarios_app, maestro, operaciones, auditoria_app)
#  - usuario exclusivo de la app solo desde la IP de web-NN, sin ALL, sin DELETE, y auditoría solo INSERT/SELECT (AU-9)
# Uso: sudo bash 01-configurar-bd.sh
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"; source "$DIR/../config.env"
[[ $EUID -eq 0 ]] || { echo "Ejecuta con sudo"; exit 1; }
paso() { echo -e "\n\033[1;34m▶ $*\033[0m"; }
CLAVE_ARCH=/root/.ti3062-clave-app
[[ -s $CLAVE_ARCH ]] || ( umask 077; openssl rand -hex 16 > $CLAVE_ARCH )
CLAVE=$(cat $CLAVE_ARCH)
TABLAS_APP="usuarios_app, {{TABLA_PADRE}}, {{TABLA_HIJO}}"

paso "CA del proyecto y certificado TLS de $BD_HOST (IP $BD_IP)"
TLS=/etc/ti3062/tls; install -d -m 755 /etc/ti3062; install -d -m 700 $TLS
if [[ ! -s $TLS/servidor.crt ]] || ! openssl x509 -in $TLS/servidor.crt -noout -ext subjectAltName 2>/dev/null | grep -q "IP Address:$BD_IP"; then
  openssl req -x509 -newkey rsa:3072 -nodes -days 825 -subj "/O=TI3062-$NN/CN=CA del proyecto TI3062-$NN" \
    -addext "basicConstraints=critical,CA:TRUE" -addext "keyUsage=critical,keyCertSign,cRLSign" \
    -keyout $TLS/ca.key -out $TLS/ca.crt 2>/dev/null
  openssl req -newkey rsa:3072 -nodes -subj "/O=TI3062-$NN/CN=$BD_IP" -keyout $TLS/servidor.key -out $TLS/servidor.csr 2>/dev/null
  printf 'basicConstraints=CA:FALSE\nkeyUsage=critical,digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth\nsubjectAltName=IP:%s,DNS:%s\n' "$BD_IP" "$BD_HOST" > $TLS/ext.cnf
  openssl x509 -req -in $TLS/servidor.csr -CA $TLS/ca.crt -CAkey $TLS/ca.key -CAcreateserial -days 825 -sha256 -extfile $TLS/ext.cnf -out $TLS/servidor.crt 2>/dev/null
  rm -f $TLS/servidor.csr; chmod 600 $TLS/*.key
fi
openssl verify -CAfile $TLS/ca.crt $TLS/servidor.crt
openssl x509 -in $TLS/servidor.crt -noout -subject -enddate -ext subjectAltName | sed 's/^/  /'

if [[ $MOTOR == mariadb ]]; then
  paso "MariaDB: solo $BD_IP y TLS obligatorio"
  install -d -m 750 -o mysql -g mysql /etc/mysql/ti3062-tls
  install -m 644 -o mysql -g mysql $TLS/ca.crt $TLS/servidor.crt /etc/mysql/ti3062-tls/
  install -m 600 -o mysql -g mysql $TLS/servidor.key /etc/mysql/ti3062-tls/
  CNF=/etc/mysql/mariadb.conf.d/50-server.cnf
  sed -i "s/^bind-address.*/bind-address = $BD_IP/" "$CNF"
  grep -q '^skip-name-resolve' "$CNF" || sed -i '/^\[mysqld\]/a skip-name-resolve' "$CNF"
  cat > /etc/mysql/mariadb.conf.d/60-ti3062-tls.cnf <<EOF
# TI3062 $NN — cifrado en tránsito obligatorio (SC-8)
[mysqld]
ssl_ca   = /etc/mysql/ti3062-tls/ca.crt
ssl_cert = /etc/mysql/ti3062-tls/servidor.crt
ssl_key  = /etc/mysql/ti3062-tls/servidor.key
require_secure_transport = ON
tls_version = TLSv1.2,TLSv1.3
EOF
  chmod 644 /etc/mysql/mariadb.conf.d/60-ti3062-tls.cnf
  systemctl restart mariadb
  [[ $(mariadb -N -e "SELECT @@have_ssl") == YES ]] || { echo "MariaDB no activó TLS (revisa journalctl -u mariadb)"; exit 1; }
  paso "Base $DB_NOMBRE y esquema"
  mariadb <<SQL
DELETE FROM mysql.global_priv WHERE User='';
DROP DATABASE IF EXISTS test;
CREATE DATABASE IF NOT EXISTS $DB_NOMBRE CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
SQL
  mariadb "$DB_NOMBRE" < "$DIR/esquema.sql"
  paso "Usuario $DB_USUARIO@$WEB_IP: REQUIRE SSL, sin DELETE y auditoría solo INSERT/SELECT"
  mariadb <<SQL
DROP USER IF EXISTS '$DB_USUARIO'@'$WEB_IP';
CREATE USER '$DB_USUARIO'@'$WEB_IP' IDENTIFIED BY '$CLAVE' REQUIRE SSL;
GRANT SELECT, INSERT, UPDATE ON $DB_NOMBRE.usuarios_app TO '$DB_USUARIO'@'$WEB_IP';
GRANT SELECT, INSERT, UPDATE ON $DB_NOMBRE.{{TABLA_PADRE}} TO '$DB_USUARIO'@'$WEB_IP';
GRANT SELECT, INSERT, UPDATE ON $DB_NOMBRE.{{TABLA_HIJO}} TO '$DB_USUARIO'@'$WEB_IP';
GRANT SELECT, INSERT ON $DB_NOMBRE.auditoria_app TO '$DB_USUARIO'@'$WEB_IP';
FLUSH PRIVILEGES;
SQL
  echo "== Evidencia"
  mariadb -e "SHOW GRANTS FOR '$DB_USUARIO'@'$WEB_IP'; SELECT User, Host, ssl_type FROM mysql.user WHERE User='$DB_USUARIO'; SHOW GLOBAL VARIABLES LIKE 'require_secure_transport'; SHOW GLOBAL VARIABLES LIKE 'tls_version';"
  mariadb "$DB_NOMBRE" -e "SHOW TABLES; SELECT TABLE_NAME, CONSTRAINT_NAME, REFERENCED_TABLE_NAME FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA='$DB_NOMBRE' AND REFERENCED_TABLE_NAME IS NOT NULL;"
else
  PGV=$(ls /etc/postgresql | sort -V | tail -1); C=/etc/postgresql/$PGV/main
  paso "PostgreSQL $PGV: solo $BD_IP y TLS obligatorio"
  install -m 644 -o postgres -g postgres $TLS/servidor.crt $C/ti3062-servidor.crt
  install -m 600 -o postgres -g postgres $TLS/servidor.key $C/ti3062-servidor.key
  sed -i "s/^#\?listen_addresses.*/listen_addresses = '$BD_IP'/" $C/postgresql.conf
  install -d -m 755 -o postgres -g postgres $C/conf.d
  cat > $C/conf.d/60-ti3062.conf <<EOF
# TI3062 $NN — solo IP privada y cifrado en tránsito (SC-8)
listen_addresses = '$BD_IP'
ssl = on
ssl_cert_file = '$C/ti3062-servidor.crt'
ssl_key_file = '$C/ti3062-servidor.key'
ssl_min_protocol_version = 'TLSv1.2'
password_encryption = 'scram-sha-256'
EOF
  chown postgres:postgres $C/conf.d/60-ti3062.conf
  sed -i '/# TI3062 inicio/,/# TI3062 fin/d; /# TI3062: la app solo desde web/d; /'"$DB_USUARIO"'/d' $C/pg_hba.conf
  cat >> $C/pg_hba.conf <<EOF
# TI3062 inicio — la app solo desde web-$NN y solo cifrado; cualquier otro origen o conexión sin TLS se rechaza
hostnossl  all          all           0.0.0.0/0     reject
hostssl    $DB_NOMBRE   $DB_USUARIO   $WEB_IP/32    scram-sha-256
host       all          $DB_USUARIO   0.0.0.0/0     reject
# TI3062 fin
EOF
  systemctl restart postgresql
  paso "Base $DB_NOMBRE, esquema y privilegios mínimos"
  runuser -u postgres -- psql -v ON_ERROR_STOP=1 <<SQL
DO \$\$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '$DB_USUARIO') THEN CREATE ROLE $DB_USUARIO LOGIN; END IF;
END \$\$;
SET password_encryption = 'scram-sha-256';
ALTER ROLE $DB_USUARIO WITH LOGIN PASSWORD '$CLAVE' NOSUPERUSER NOCREATEDB NOCREATEROLE;
SELECT 'CREATE DATABASE $DB_NOMBRE' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NOMBRE')\gexec
SQL
  runuser -u postgres -- psql -v ON_ERROR_STOP=1 -d "$DB_NOMBRE" < "$DIR/esquema.sql"   # stdin: postgres no lee /home
  runuser -u postgres -- psql -v ON_ERROR_STOP=1 -d "$DB_NOMBRE" <<SQL
REVOKE ALL ON DATABASE $DB_NOMBRE FROM PUBLIC;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM $DB_USUARIO;
GRANT CONNECT ON DATABASE $DB_NOMBRE TO $DB_USUARIO;
GRANT USAGE ON SCHEMA public TO $DB_USUARIO;
GRANT SELECT, INSERT, UPDATE ON $TABLAS_APP TO $DB_USUARIO;
GRANT SELECT, INSERT ON auditoria_app TO $DB_USUARIO;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO $DB_USUARIO;
SQL
  echo "== Evidencia"; sed -n '/# TI3062 inicio/,/# TI3062 fin/p' $C/pg_hba.conf
  runuser -u postgres -- psql -tAc "SHOW ssl" ; runuser -u postgres -- psql -tAc "SHOW ssl_min_protocol_version"
  runuser -u postgres -- psql -d "$DB_NOMBRE" -c '\dt' -c '\dp'
fi
ss -tlnp | grep ":$DB_PORT"
( umask 077; base64 -w0 $TLS/ca.crt > /root/.ti3062-ca-bd.b64 )
cat <<EOF

✅ $MOTOR_NOMBRE listo en $(hostname) ($BD_IP:$DB_PORT), base $DB_NOMBRE, usuario $DB_USUARIO@$WEB_IP (solo TLS).
Para instalar la app en web-$NN necesitarás DOS datos de este servidor:
  1) Contraseña de la app (SECRETA: no la captures ni la subas):   sudo cat $CLAVE_ARCH
  2) Certificado de la CA en una línea (público, no es secreto):    sudo cat /root/.ti3062-ca-bd.b64
Pégalos cuando 01-instalar-web.sh los pida.
EOF
