#!/usr/bin/env bash
# Despliega en web-NN (AWS) la aplicación del caso y una copia del sistema de gestión en /gestion.
# Credenciales de BD en /etc/ti3062/db.ini (fuera del webroot y del repositorio).
# Uso: sudo bash 01-instalar-web.sh
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"; source "$DIR/../config.env"
RAIZ="$(cd "$DIR/../.." && pwd)"   # raíz del repositorio ti3062-NN
[[ $EUID -eq 0 ]] || { echo "Ejecuta con sudo"; exit 1; }
paso() { echo -e "\n\033[1;34m▶ $*\033[0m"; }

paso "Credenciales de la app (fuera del código)"
install -d -m 750 -o root -g www-data /etc/ti3062
if [[ ! -s /etc/ti3062/db.ini ]]; then
  read -rsp "Pega la contraseña de $DB_USUARIO (obtenida en bd-$NN con: sudo cat /root/.ti3062-clave-app): " CLAVE; echo
  cat > /etc/ti3062/db.ini <<EOF
driver = $DB_DRIVER
host = $BD_IP
port = $DB_PORT
dbname = $DB_NOMBRE
user = $DB_USUARIO
password = "$CLAVE"
EOF
fi
chown root:www-data /etc/ti3062/db.ini; chmod 640 /etc/ti3062/db.ini
ls -l /etc/ti3062/db.ini

paso "Apache + PHP endurecidos"
a2enmod ssl headers rewrite >/dev/null
cat > /etc/apache2/conf-available/ti3062-seguridad.conf <<'EOF'
ServerTokens Prod
ServerSignature Off
TraceEnable Off
Header always set X-Content-Type-Options "nosniff"
Header always set X-Frame-Options "SAMEORIGIN"
Header always set Referrer-Policy "strict-origin-when-cross-origin"
<DirectoryMatch "/\.git">
    Require all denied
</DirectoryMatch>
EOF
a2enconf ti3062-seguridad >/dev/null
PHPINI=$(php -r 'echo php_ini_loaded_file();' | sed 's/cli/apache2/')
sed -i 's/^expose_php.*/expose_php = Off/; s/^display_errors.*/display_errors = Off/' "$PHPINI"

paso "Certificado TLS autofirmado para HTTPS (CN=$WEB_HOST)"
if [[ ! -f /etc/ssl/private/ti3062.key ]]; then
  openssl req -x509 -nodes -newkey rsa:2048 -days 365 -subj "/CN=$WEB_HOST/O=TI3062-$NN" \
    -keyout /etc/ssl/private/ti3062.key -out /etc/ssl/certs/ti3062.crt
  chmod 600 /etc/ssl/private/ti3062.key
fi
sed -i 's#SSLCertificateFile.*#SSLCertificateFile /etc/ssl/certs/ti3062.crt#; s#SSLCertificateKeyFile.*#SSLCertificateKeyFile /etc/ssl/private/ti3062.key#' /etc/apache2/sites-available/default-ssl.conf
a2ensite default-ssl >/dev/null

paso "Publicar la app del caso en / y el sistema de gestión en /gestion"
rm -f /var/www/html/index.html
install -m 644 "$RAIZ"/app-caso/*.php "$RAIZ"/app-caso/*.css /var/www/html/
install -d /var/www/html/gestion/data
install -m 644 "$RAIZ"/index.html "$RAIZ"/app.js "$RAIZ"/styles.css /var/www/html/gestion/
install -m 644 "$RAIZ"/data/proyecto-$NN.json /var/www/html/gestion/data/
chown -R root:www-data /var/www/html; find /var/www/html -type d -exec chmod 755 {} +
apache2ctl configtest && systemctl restart apache2

paso "Prueba de conexión web → BD con el usuario de la aplicación (P3)"
php -r '$i=parse_ini_file("/etc/ti3062/db.ini");
$d=$i["driver"]=="pgsql"?"pgsql:host={$i["host"]};port={$i["port"]};dbname={$i["dbname"]}":"mysql:host={$i["host"]};port={$i["port"]};dbname={$i["dbname"]}";
try{$p=new PDO($d,$i["user"],$i["password"]);echo "Conexión OK como {$i["user"]} desde ".gethostname()."\n";}catch(Exception $e){echo "FALLO: ".$e->getMessage()."\n";exit(1);}'
curl -sk -o /dev/null -w "HTTP local: %{http_code}\n" https://localhost/
echo -e "\n✅ App publicada: http://<IP_PUBLICA>/  ·  https://<IP_PUBLICA>/  ·  gestión: /gestion/"
