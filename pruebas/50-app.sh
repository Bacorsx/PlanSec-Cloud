#!/usr/bin/env bash
# Prueba integral de la app del caso: BD con TLS, instalación web, login/roles/bloqueo, reglas del patrón, API en vivo, AU-9.
# Uso: bash 50-app.sh <nn> <motor> <tema>
set -uo pipefail
NNA="$1"; MOT="$2"; TEMA="$3"
G=${GENERADOR:-$(cd "$(dirname "$0")/.." && pwd)}
P=/root/v/ti3062-$NNA
ok() { echo -e "\e[32m[OK]\e[0m $*"; }; bad() { echo -e "\e[31m[FALLA]\e[0m $*"; FALLAS=$((FALLAS+1)); }; FALLAS=0
t() { echo -e "\n\e[1;36m### $*\e[0m"; }
(cd $G && python3 generar.py --nn $NNA --nombre "Prueba $TEMA" --github test --motor $MOT --tema $TEMA --salida /root/v --forzar >/dev/null) || { echo "no genera"; exit 1; }
source $P/instalador/config.env
ip link show aws0 &>/dev/null || ip link add aws0 type dummy
ip addr replace "$WEB_IP/24" dev aws0; ip addr replace "$BD_IP/24" dev aws0; ip link set aws0 up
ip route replace local "$BD_IP" dev aws0 table local proto kernel scope host src "$WEB_IP"
cd $P/instalador
PATRON=$(php -r "require '$P/app-caso/privado/config_tema.php'; echo \$TEMA['patron'];")
t "Tema $TEMA · patrón $PATRON · $MOT"

# base limpia
if [[ $MOT == mariadb ]]; then mariadb -e "DROP DATABASE IF EXISTS $DB_NOMBRE"; else rm -f /etc/postgresql/*/main/conf.d/60-ti3062.conf; sed -i "s/^listen_addresses.*/#listen_addresses = 'localhost'/" /etc/postgresql/*/main/postgresql.conf; systemctl restart postgresql; (cd /tmp && runuser -u postgres -- dropdb --if-exists --force $DB_NOMBRE) || echo "AVISO: dropdb falló"; fi
rm -rf /etc/ti3062 /root/.ti3062-clave-app /root/.ti3062-ca-bd.b64

t "bd/01-configurar-bd.sh"
bash bd/01-configurar-bd.sh > /tmp/bd01.log 2>&1 && ok "configurar-bd" || { bad "configurar-bd"; tail -30 /tmp/bd01.log; exit 1; }
grep -q "servidor.crt: OK" /tmp/bd01.log && ok "certificado de bd verificado por la CA" || bad "cert"
if [[ $MOT == mariadb ]]; then
  G1=$(mariadb -N -e "SHOW GRANTS FOR '$DB_USUARIO'@'$WEB_IP'")
  echo "$G1" | grep -qE "ALL PRIVILEGES|DELETE" && bad "grants excesivos: $G1" || ok "sin ALL ni DELETE"
  echo "$G1" | grep -q "auditoria_app" && echo "$G1" | grep "auditoria_app" | grep -qv UPDATE && ok "auditoria_app solo SELECT, INSERT" || bad "grants auditoria"
  [[ $(mariadb -N -e "SELECT ssl_type FROM mysql.user WHERE User='$DB_USUARIO'") == ANY ]] && ok "REQUIRE SSL" || bad "sin REQUIRE SSL"
  N=$(mariadb -N -e "SELECT COUNT(*) FROM information_schema.REFERENTIAL_CONSTRAINTS WHERE CONSTRAINT_SCHEMA='$DB_NOMBRE'")
else
  N=$(runuser -u postgres -- psql -d $DB_NOMBRE -tAc "SELECT COUNT(*) FROM information_schema.table_constraints WHERE constraint_type='FOREIGN KEY'")
  runuser -u postgres -- psql -d $DB_NOMBRE -tAc "SELECT string_agg(privilege_type, ',') FROM information_schema.role_table_grants WHERE grantee='$DB_USUARIO' AND table_name='auditoria_app'" | grep -qx "INSERT,SELECT\|SELECT,INSERT" && ok "auditoria_app solo SELECT, INSERT" || bad "grants auditoria pg"
  runuser -u postgres -- psql -d $DB_NOMBRE -tAc "SELECT COUNT(*) FROM information_schema.role_table_grants WHERE grantee='$DB_USUARIO' AND privilege_type='DELETE'" | grep -qx 0 && ok "sin DELETE" || bad "tiene DELETE"
fi
[[ $N -ge 2 ]] && ok "tablas relacionadas: $N claves foráneas" || bad "FK $N"

t "web/01-instalar-web.sh"
CLAVE=$(cat /root/.ti3062-clave-app); CAB=$(cat /root/.ti3062-ca-bd.b64); PW='Admin-Prueba-2026'
expect <<EOF > /tmp/web01.log 2>&1
set timeout 180
spawn bash web/01-instalar-web.sh
expect "Pega la línea de la CA" { send "$CAB\r" }
expect "Pega la contraseña" { send "$CLAVE\r" }
expect "Usuario administrador" { send "admin$NNA\r" }
expect "Contraseña (mín" { send "$PW\r" }
expect "Repite" { send "$PW\r" }
expect eof
catch wait r; exit [lindex \$r 3]
EOF
[[ $? == 0 ]] && ok "instalar-web" || { bad "instalar-web"; tail -25 /tmp/web01.log; }
grep -aq "Conexión OK.*TLSv1\.[23].*verificado: sí" /tmp/web01.log && ok "$(grep -a 'Conexión OK' /tmp/web01.log)" || { bad "conexión TLS"; grep -a "Conexión\|FALLO" /tmp/web01.log; tail -5 /var/log/apache2/error.log; }
grep -aq "HTTP local:  301" /tmp/web01.log && ok "HTTP redirige a HTTPS" || bad "sin redirección"
[[ $(stat -c '%a %U:%G' /etc/ti3062/db.ini) == "640 root:www-data" ]] && ok "db.ini 640 root:www-data" || bad "permisos db.ini"
[[ -f /var/www/html/nucleo.php || -f /var/www/html/config_tema.php ]] && bad "lógica dentro del webroot" || ok "lógica fuera del webroot"
grep -rq "$CLAVE" /var/www/html /var/www/ti3062 $P && bad "clave en código" || ok "credencial fuera del código"
for f in /var/www/ti3062/*.php /var/www/html/*.php; do php -l $f >/dev/null || bad "lint $f"; done; ok "php -l"

U=https://localhost; J=/tmp/cj-$NNA; rm -f $J
tok() { curl -sk -c $J -b $J "$U/$1" | grep -oP 'name="csrf" value="\K[^"]+' | head -1; }
post() { local v=$1; shift; curl -sk -c $J -b $J -o /tmp/r.html -w '%{http_code}' --data-urlencode "csrf=$(tok "?v=cuenta")" "$@" "$U/?v=$v"; curl -sk -c $J -b $J "$U/?v=$v" > /tmp/r2.html; }
login() { rm -f $J; local tk; tk=$(curl -sk -c $J -b $J "$U/" | grep -oP 'name="csrf" value="\K[^"]+'); curl -sk -c $J -b $J -o /dev/null -w '%{http_code}' --data-urlencode "csrf=$tk" -d accion=login --data-urlencode "usuario=$1" --data-urlencode "clave=$2" "$U/"; }
msg() { { grep -oP 'class="msg mal"[^>]*>\K[^<]+' /tmp/r.html; grep -oP 'class="msg [a-z]+"[^>]*>\K[^<]+' /tmp/r2.html; } | head -1; }
sqlq() { if [[ $MOT == mariadb ]]; then mariadb -N $DB_NOMBRE -e "$1"; else runuser -u postgres -- psql -d $DB_NOMBRE -tAc "$1"; fi; }

t "Cabeceras e ingreso"
HD=$(curl -skI $U/)
echo "$HD" | grep -qi "content-security-policy: default-src 'self'" && ok "CSP" || bad "CSP"
echo "$HD" | grep -qi "strict-transport-security" && ok "HSTS" || bad "HSTS"
echo "$HD" | grep -qi "set-cookie:.*httponly.*samesite=strict\|set-cookie:.*samesite=strict.*httponly" && echo "$HD" | grep -qi "set-cookie:.*secure" && ok "cookie Secure/HttpOnly/SameSite" || bad "cookie: $(echo "$HD" | grep -i set-cookie)"
curl -sk $U/ | grep -q "Uso exclusivo para personal autorizado" && ok "aviso AC-8" || bad "AC-8"
[[ $(curl -sk -o /dev/null -w '%{http_code}' $U/api.php) == 401 ]] && ok "API sin sesión → 401" || bad "API abierta"
[[ $(login admin$NNA "$PW") == 303 ]] && ok "login admin" || bad "login admin"

t "Usuarios y roles"
post usuarios -d accion=crear -d usuario=oper$NNA -d "nombre=Operador Prueba" -d rol=operador --data-urlencode "clave=Operador-Clave-2026" >/dev/null
post usuarios -d accion=crear -d usuario=audi$NNA -d "nombre=Auditor Prueba" -d rol=auditor --data-urlencode "clave=Auditor-Clave-2026" >/dev/null
[[ $(sqlq "SELECT COUNT(*) FROM usuarios_app") == 3 ]] && ok "3 usuarios (admin, operador, auditor)" || bad "usuarios: $(msg)"
post usuarios -d accion=crear -d usuario=debil -d "nombre=X" -d rol=operador -d clave=corta >/dev/null
[[ $(msg) == *"al menos 12"* ]] && ok "clave débil rechazada (IA-5(1))" || bad "clave débil: $(msg)"
sqlq "SELECT hash FROM usuarios_app WHERE usuario='oper$NNA'" | grep -q '^\$argon2id\|^\$2y' && ok "contraseña guardada como hash" || bad "hash"

t "Maestro y operaciones (patrón $PATRON)"
FORM=$(php -r '
require $argv[1]; $out = [];
foreach (["padre","hijo"] as $r) { $d = [];
  foreach ($TEMA[$r]["campos"] as [$k,$t,$l]) $d[$k] = str_starts_with($t,"select:") ? explode("|",substr($t,7))[0] : ($t=="date" ? date("Y-m-d") : ($t=="number" ? "4" : ($t=="email" ? "p@ejemplo.cl" : ($t=="tel" ? "+56 9 1234 5678" : "Prueba $r $k"))));
  echo http_build_query($d), "\n"; }' $P/app-caso/privado/config_tema.php)
FP=$(echo "$FORM" | sed -n 1p); FH=$(echo "$FORM" | sed -n 2p)
EXTRA_P=""; case $PATRON in inventario) EXTRA_P="precio=1500&stock_minimo=3";; membresias) EXTRA_P="valor=25000&duracion_dias=30";; esac
post padre -d accion=crear -d "$FP" ${EXTRA_P:+-d "$EXTRA_P"} >/dev/null
post padre -d accion=crear -d "$(echo "$FP" | sed 's/Prueba+padre/Segundo+padre/g; s/Prueba%20padre/Segundo%20padre/g')" ${EXTRA_P:+-d "$EXTRA_P"} >/dev/null
NP=$(sqlq "SELECT COUNT(*) FROM $(php -r "require '$P/app-caso/privado/config_tema.php'; echo \$TEMA['padre']['tabla'];")")
[[ $NP == 2 ]] && ok "2 registros maestros creados" || bad "maestro: $(msg)"
PT=$(php -r "require '$P/app-caso/privado/config_tema.php'; echo \$TEMA['padre']['tabla'];"); HT=$(php -r "require '$P/app-caso/privado/config_tema.php'; echo \$TEMA['hijo']['tabla'];"); FK=$(php -r "require '$P/app-caso/privado/config_tema.php'; echo \$TEMA['hijo']['fk'];")
ID1=$(sqlq "SELECT MIN(id) FROM $PT")
HOY=$(TZ=America/Santiago date +%F)
case $PATRON in
  inventario)
    T1=$(php -r "require '$P/app-caso/privado/config_tema.php'; echo \$TEMA['vocab']['tipos'][0][0];"); T2=$(php -r "require '$P/app-caso/privado/config_tema.php'; echo \$TEMA['vocab']['tipos'][1][0];")
    post operar -d accion=registrar -d "$FK=$ID1" --data-urlencode "tipo=$T1" -d cantidad=10 -d "$FH" >/dev/null; [[ $(msg) == *"Stock"*"10"* ]] && ok "entrada: $(msg)" || bad "entrada: $(msg)"
    post operar -d accion=registrar -d "$FK=$ID1" --data-urlencode "tipo=$T2" -d cantidad=8 -d "$FH" >/dev/null; [[ $(msg) == *"crítico"* ]] && ok "salida deja stock crítico: $(msg)" || bad "salida: $(msg)"
    post operar -d accion=registrar -d "$FK=$ID1" --data-urlencode "tipo=$T2" -d cantidad=50 -d "$FH" >/dev/null; [[ $(msg) == *"insuficiente"* ]] && ok "regla: $(msg)" || bad "stock negativo permitido: $(msg)"
    [[ $(sqlq "SELECT stock FROM $PT WHERE id=$ID1") == 2 ]] && ok "stock final 2 (transacción consistente)" || bad "stock $(sqlq "SELECT stock FROM $PT WHERE id=$ID1")";;
  reservas)
    MODO=$(php -r "require '$P/app-caso/privado/config_tema.php'; echo \$TEMA['vocab']['modo'];")
    if [[ $MODO == bloque ]]; then B=$(php -r "require '$P/app-caso/privado/config_tema.php'; echo \$TEMA['vocab']['bloques'][0];"); R="fecha=$HOY&bloque=$B"; else R="fecha=$HOY&fecha_fin=$(date -d "$HOY +2 day" +%F)"; fi
    post operar -d accion=registrar -d "$FK=$ID1" -d "$R" -d "$FH" >/dev/null; [[ $(msg) == *"confirmada"* ]] && ok "reserva: $(msg)" || bad "reserva: $(msg)"
    post operar -d accion=registrar -d "$FK=$ID1" -d "$R" -d "$FH" >/dev/null; [[ $(msg) == *"se cruza"* ]] && ok "regla: $(msg)" || bad "doble reserva permitida: $(msg)"
    post operar -d accion=registrar -d "$FK=$ID1" -d "fecha=2020-01-01&bloque=x&fecha_fin=2020-01-02" -d "$FH" >/dev/null; [[ $(msg) == *"pasada"* ]] && ok "fecha pasada rechazada" || bad "pasada: $(msg)"
    IDH=$(sqlq "SELECT MAX(id) FROM $HT"); post operar -d accion=completar -d id=$IDH >/dev/null; [[ $(sqlq "SELECT estado FROM $HT WHERE id=$IDH") == Completada ]] && ok "completar: $(msg)" || bad "completar: $(msg)"
    curl -sk -b $J "$U/?v=disponibilidad&f=$HOY" | grep -qE 'class="ocupado"|Ocupada|Disponible' && ok "vista de disponibilidad" || bad "disponibilidad";;
  prestamos)
    post operar -d accion=registrar -d "$FK=$ID1" -d "fecha_compromiso=$(date -d "$HOY +3 day" +%F)" -d "$FH" >/dev/null; [[ $(msg) == *"Préstamo registrado"* ]] && ok "$(msg)" || bad "prestar: $(msg)"
    post operar -d accion=registrar -d "$FK=$ID1" -d "fecha_compromiso=$(date -d "$HOY +3 day" +%F)" -d "$FH" >/dev/null; [[ $(msg) == *"no cumple"* ]] && ok "regla: no se presta lo ya prestado" || bad "doble préstamo: $(msg)"
    IDH=$(sqlq "SELECT MAX(id) FROM $HT"); post operar -d accion=devolver -d id=$IDH >/dev/null; [[ $(msg) == *"a tiempo"* && $(sqlq "SELECT estado_item FROM $PT WHERE id=$ID1") == Disponible ]] && ok "devolución libera el ítem" || bad "devolver: $(msg)";;
  ordenes)
    N1=$(php -r "require '$P/app-caso/privado/config_tema.php'; echo end(\$TEMA['vocab']['niveles']);")
    post operar -d accion=registrar -d "$FK=$ID1" --data-urlencode "nivel=$N1" -d monto=50000 -d "$FH" >/dev/null; [[ $(msg) == *"abierto"* ]] && ok "$(msg)" || bad "abrir: $(msg)"
    IDH=$(sqlq "SELECT MAX(id) FROM $HT"); for i in 1 2 3 4; do post operar -d accion=avanzar -d id=$IDH >/dev/null; done
    [[ -n $(sqlq "SELECT cerrado_en FROM $HT WHERE id=$IDH AND cerrado_en IS NOT NULL") ]] && ok "flujo completo hasta cierre: $(msg)" || bad "avanzar: $(msg)"
    post operar -d accion=avanzar -d id=$IDH >/dev/null; [[ $(msg) == *"no aplica"* ]] && ok "no avanza más allá del cierre" || bad "avanza cerrado: $(msg)"
    curl -sk -b $J "$U/?v=equipo" | grep -q 'data-parte="cpu"' && ok "vista Cómo funciona (equipo animado)" || echo "  (sin vista equipo en este tema)";;
  membresias)
    post operar -d accion=registrar -d "$FK=$ID1" -d "fecha_inicio=$HOY" -d "$FH" >/dev/null; [[ $(msg) == *"vigente hasta"* ]] && ok "$(msg)" || bad "inscribir: $(msg)"
    IDH=$(sqlq "SELECT MAX(id) FROM $HT"); post operar -d accion=renovar -d id=$IDH >/dev/null; [[ $(msg) == *"renovada hasta"*  ]] && ok "$(msg)" || bad "renovar: $(msg)"
    post operar -d accion=suspender -d id=$IDH >/dev/null; [[ $(sqlq "SELECT estado FROM $HT WHERE id=$IDH") == Suspendida ]] && ok "suspender" || bad "suspender";;
esac
for v in panel operar padre reportes auditoria usuarios cuenta; do
  c=$(curl -sk -b $J -o /tmp/v.html -w '%{http_code}' "$U/?v=$v"); [[ $c == 200 ]] && ! grep -q 'class="msg mal"' /tmp/v.html && ok "vista $v" || { bad "vista $v ($c)"; grep -oP 'class="msg mal"[^>]*>\K[^<]+' /tmp/v.html; }
done
curl -sk -b $J "$U/?v=exportar" | head -c 3 | od -An -tx1 | grep -q "ef bb bf" && ok "exportar CSV" || bad "CSV"

t "API en vivo y canal TLS (SC-8)"
API=$(curl -sk -b $J $U/api.php); echo "  $API" | cut -c1-220
echo "$API" | grep -q '"tls":"TLSv1\.[23]"' && echo "$API" | grep -q '"verificado":true' && ok "canal web→bd cifrado y verificado" || bad "canal"
if [[ $MOT == mariadb ]]; then
  mariadb --skip-ssl -h $BD_IP -u $DB_USUARIO -p"$CLAVE" $DB_NOMBRE -e "SELECT 1" >/dev/null 2>&1 && bad "conexión sin TLS aceptada" || ok "conexión sin TLS rechazada"
  mariadb --ssl-ca=/etc/ti3062/bd-ca.pem --ssl-verify-server-cert -h $BD_IP -u $DB_USUARIO -p"$CLAVE" $DB_NOMBRE -e "DELETE FROM auditoria_app" </dev/null 2>&1 | { grep -q "denied"; } ; [[ ${PIPESTATUS[1]} == 0 ]] && ok "AU-9: DELETE en auditoria_app denegado" || bad "AU-9"
else
  PGPASSWORD=$CLAVE psql "host=$BD_IP dbname=$DB_NOMBRE user=$DB_USUARIO sslmode=disable" -c "SELECT 1" >/dev/null 2>&1 && bad "conexión sin TLS aceptada" || ok "conexión sin TLS rechazada"
  PGPASSWORD=$CLAVE psql "host=$BD_IP dbname=$DB_NOMBRE user=$DB_USUARIO sslmode=verify-full sslrootcert=/etc/ti3062/bd-ca.pem" -c "DELETE FROM auditoria_app" </dev/null 2>&1 | { grep -q "denied"; } ; [[ ${PIPESTATUS[1]} == 0 ]] && ok "AU-9: DELETE en auditoria_app denegado" || bad "AU-9"
fi

t "XSS e inyección (SI-10)"
XSS=$(echo "$FP" | sed -E "s/^([a-z_]+)=[^&]*/\1=%3Cscript%3Ealert(1)%3C%2Fscript%3E%27+OR+%271%27%3D%271/")
post padre -d accion=crear -d "$XSS" ${EXTRA_P:+-d "$EXTRA_P"} >/dev/null
curl -sk -b $J "$U/?v=padre" | grep -q "&lt;script&gt;alert(1)&lt;/script&gt;&#039; OR &#039;1&#039;=&#039;1" && ok "guardado como texto y mostrado escapado" || bad "XSS"

t "Rol auditor (AC-3) y bloqueo (AC-7)"
[[ $(login audi$NNA "Auditor-Clave-2026") == 303 ]] && ok "login auditor" || bad "login auditor"
post operar -d accion=registrar -d "$FK=$ID1" -d "$FH" >/dev/null; [[ $(msg) == *"rol no permite"* ]] && ok "auditor no puede registrar" || bad "auditor registró: $(msg)"
[[ $(sqlq "SELECT COUNT(*) FROM auditoria_app WHERE accion='acceso_denegado'") -ge 1 ]] && ok "acceso_denegado registrado" || bad "sin acceso_denegado"
curl -sk -b $J "$U/?v=evidencia" -o /tmp/evidencia-$NNA.json
python3 - /tmp/evidencia-$NNA.json <<'PY' && ok "auditor exporta evidencia válida (TLS, P13 denegado, sin hashes ni contraseñas)" || bad "evidencia exportada"
import json, sys
d = json.load(open(sys.argv[1])); t = json.dumps(d)
assert d["tipo"] == "evidencia-ti3062" and d["canal_bd"]["tls"].startswith("TLSv1.") and d["canal_bd"]["certificado_verificado"]
assert not any(x in t for x in ("$2y$", "$argon2", '"hash"', "password", "clave"))
assert any(p["id"] == "P13" and "DENEGADO" in p["obtenido"] for p in d["pruebas"]) and d["controles"]["AU-9"]
PY
[[ $(sqlq "SELECT COUNT(*) FROM auditoria_app WHERE accion='exportar_evidencia'") -ge 1 ]] && ok "exportar_evidencia queda auditado" || bad "exportar_evidencia sin auditar"
cp $J /tmp/cj-aud-$NNA
[[ $(login admin$NNA "$PW") == 303 ]] || bad "relogin admin"
IDA=$(sqlq "SELECT id FROM usuarios_app WHERE usuario='audi$NNA'")
post usuarios -d accion=activo -d id=$IDA >/dev/null
[[ $(curl -sk -b /tmp/cj-aud-$NNA -o /dev/null -w '%{http_code}' $U/api.php) == 401 ]] && ok "AC-2: la sesión de un usuario desactivado se corta de inmediato" || bad "usuario desactivado conserva la sesión"
[[ $(login oper$NNA "Operador-Clave-2026") == 303 ]] || bad "login operador"
curl -sk -b $J "$U/?v=evidencia" | grep -q "Solo administración y auditoría pueden exportar evidencia" && ok "el operador no puede exportar evidencia" || bad "operador exportó evidencia"
for i in 1 2 3 4 5; do login oper$NNA "mala-clave-$i" >/dev/null; done
[[ $(login oper$NNA "Operador-Clave-2026") == 200 ]] && ok "cuenta bloqueada tras 5 intentos (clave correcta rechazada)" || bad "sin bloqueo"
[[ $(sqlq "SELECT COUNT(*) FROM auditoria_app WHERE accion='cuenta_bloqueada'") == 1 && $(sqlq "SELECT COUNT(*) FROM auditoria_app WHERE accion='login_fallido'") -ge 5 ]] && ok "eventos login_fallido y cuenta_bloqueada" || bad "eventos de bloqueo"
grep -i "PHP \(Warning\|Notice\|Fatal\|Deprecated\)" /var/log/apache2/error.log | tail -5 | grep . && bad "avisos de PHP en el log" || ok "log de PHP sin avisos"
echo -e "\nFALLAS: $FALLAS"
