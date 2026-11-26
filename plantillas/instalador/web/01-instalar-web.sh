#!/usr/bin/env bash
# Despliega en web-NN la aplicación del caso y una copia del sistema de gestión en /gestion.
#  - Webroot (/var/www/html): solo index.php, api.php, app.js y estilo.css
#  - Lógica y configuración fuera del webroot (/var/www/ti3062); credenciales en /etc/ti3062/db.ini (640 root:www-data)
#  - Conexión a bd-NN por TLS verificando el certificado con la CA del proyecto (SC-8); HTTPS con redirección desde HTTP
#  - Crea el primer usuario administrador de la aplicación
# Uso: sudo bash 01-instalar-web.sh
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"; source "$DIR/../config.env"
RAIZ="$(cd "$DIR/../.." && pwd)"   # raíz del repositorio ti3062-NN
[[ $EUID -eq 0 ]] || { echo "Ejecuta con sudo"; exit 1; }
paso() { echo -e "\n\033[1;34m▶ $*\033[0m"; }
PRIV=/var/www/ti3062

paso "Credenciales y CA de la base de datos (fuera del código)"
install -d -m 750 -o root -g www-data /etc/ti3062
if [[ ! -s /etc/ti3062/bd-ca.pem ]]; then
  read -rp "Pega la línea de la CA (en bd-$NN: sudo cat /root/.ti3062-ca-bd.b64): " CAB64
  echo "$CAB64" | base64 -d > /etc/ti3062/bd-ca.pem 2>/dev/null || true
  openssl x509 -in /etc/ti3062/bd-ca.pem -noout 2>/dev/null || { rm -f /etc/ti3062/bd-ca.pem; echo "La CA pegada no es un certificado válido."; exit 1; }
fi
chmod 644 /etc/ti3062/bd-ca.pem
openssl x509 -in /etc/ti3062/bd-ca.pem -noout -subject -enddate | sed 's/^/  CA: /'
if [[ ! -s /etc/ti3062/db.ini ]] || ! grep -q '^ssl_ca' /etc/ti3062/db.ini; then
  read -rsp "Pega la contraseña de $DB_USUARIO (en bd-$NN: sudo cat /root/.ti3062-clave-app): " CLAVE; echo
  [[ $CLAVE =~ ^[A-Za-z0-9]+$ ]] || { echo "Contraseña con formato inesperado."; exit 1; }
  cat > /etc/ti3062/db.ini <<EOF
driver = $DB_DRIVER
host = $BD_IP
port = $DB_PORT
dbname = $DB_NOMBRE
user = $DB_USUARIO
password = "$CLAVE"
ssl_ca = /etc/ti3062/bd-ca.pem
EOF
fi
chown root:www-data /etc/ti3062/db.ini; chmod 640 /etc/ti3062/db.ini
ls -l /etc/ti3062/

paso "Apache + PHP endurecidos"
a2enmod ssl headers rewrite >/dev/null
cat > /etc/apache2/conf-available/ti3062-seguridad.conf <<'EOF'
ServerTokens Prod
ServerSignature Off
TraceEnable Off
Header always set X-Content-Type-Options "nosniff"
Header always set X-Frame-Options "DENY"
Header always set Referrer-Policy "no-referrer"
<DirectoryMatch "/\.git">
    Require all denied
</DirectoryMatch>
<Directory /var/www/ti3062>
    Require all denied
</Directory>
EOF
a2enconf ti3062-seguridad >/dev/null
PHPINI=$(php -r 'echo php_ini_loaded_file();' | sed 's/cli/apache2/')
sed -i 's/^expose_php.*/expose_php = Off/; s/^display_errors.*/display_errors = Off/; s/^;\?session.cookie_httponly.*/session.cookie_httponly = 1/; s/^;\?session.use_strict_mode.*/session.use_strict_mode = 1/' "$PHPINI"

paso "HTTPS (certificado autofirmado CN=$WEB_HOST) y redirección HTTP → HTTPS"
if [[ ! -f /etc/ssl/private/ti3062.key ]]; then
  openssl req -x509 -nodes -newkey rsa:2048 -days 365 -subj "/CN=$WEB_HOST/O=TI3062-$NN" \
    -addext "basicConstraints=critical,CA:FALSE" -addext "subjectAltName=DNS:$WEB_HOST,DNS:localhost" \
    -keyout /etc/ssl/private/ti3062.key -out /etc/ssl/certs/ti3062.crt 2>/dev/null
  chmod 600 /etc/ssl/private/ti3062.key
fi
sed -i 's#SSLCertificateFile.*#SSLCertificateFile /etc/ssl/certs/ti3062.crt#; s#SSLCertificateKeyFile.*#SSLCertificateKeyFile /etc/ssl/private/ti3062.key#' /etc/apache2/sites-available/default-ssl.conf
a2ensite default-ssl >/dev/null
if ! grep -q 'TI3062 redireccion' /etc/apache2/sites-available/000-default.conf; then
  sed -i '/<VirtualHost \*:80>/a\    # TI3062 redireccion a HTTPS (SC-8)\n    RewriteEngine On\n    RewriteCond %{HTTPS} off\n    RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [R=301,L]' /etc/apache2/sites-available/000-default.conf
fi

paso "Publicar la app del caso en / (lógica en $PRIV) y el sistema de gestión en /gestion"
rm -f /var/www/html/index.html /var/www/html/config_tema.php /var/www/html/estilo.css.bak
install -d -m 750 -o root -g www-data $PRIV
install -m 640 -o root -g www-data "$RAIZ"/app-caso/privado/*.php $PRIV/
install -m 644 "$RAIZ"/app-caso/publico/* /var/www/html/
install -d /var/www/html/gestion/data
install -m 644 "$RAIZ"/index.html "$RAIZ"/app.js "$RAIZ"/styles.css /var/www/html/gestion/
install -m 644 "$RAIZ"/data/proyecto-$NN.json "$RAIZ"/data/diccionario-$NN.json /var/www/html/gestion/data/
chown -R root:www-data /var/www/html; find /var/www/html -type d -exec chmod 755 {} +
apache2ctl configtest && systemctl restart apache2

paso "Prueba de conexión web → BD con TLS verificado (P3 / P9)"
runuser -u www-data -- php -r '
require "/var/www/ti3062/nucleo.php";
try { $c = canal_bd(); if (!$c["ok"]) throw new Exception("sin conexión");
  echo "Conexión OK como " . ini()["user"] . " desde " . gethostname() . " · " . ($c["tls"] ?: "SIN TLS") . " · " . $c["cipher"] . " · certificado verificado: " . ($c["verificado"] ? "sí" : "no") . "\n";
  if (!$c["tls"]) exit(1);
} catch (Throwable $e) { echo "FALLO: revisa el log de PHP (/var/log/apache2/error.log)\n"; exit(1); }'

paso "Primer usuario administrador de la aplicación"
if [[ $(runuser -u www-data -- php -r 'require "/var/www/ti3062/nucleo.php"; echo valor("SELECT COUNT(*) FROM usuarios_app WHERE rol = ?", ["admin"]);') == 0 ]]; then
  read -rp "Usuario administrador de la app [admin$NN]: " UAPP; UAPP=${UAPP:-admin$NN}
  while :; do
    read -rsp "Contraseña (mín. 12, letras y números): " C1; echo
    read -rsp "Repite la contraseña: " C2; echo
    [[ "$C1" == "$C2" ]] || { echo "No coinciden."; continue; }
    printf '%s' "$C1" | runuser -u www-data -- php $PRIV/crear-usuario.php "$UAPP" admin "Administrador $NN" && break
  done
  unset C1 C2
else
  echo "  Ya existe un administrador de la app."
fi
curl -sk -o /dev/null -w "HTTPS local: %{http_code}\n" https://localhost/
curl -s -o /dev/null -w "HTTP local:  %{http_code} (debe ser 301 → HTTPS)\n" http://localhost/
echo -e "\n✅ App publicada: https://<IP_ELASTICA_WEB>/  ·  gestión: /gestion/  ·  crea más usuarios desde Usuarios (rol administrador)"
