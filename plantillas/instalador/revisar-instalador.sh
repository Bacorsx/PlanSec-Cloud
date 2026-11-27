#!/usr/bin/env bash
# Revisión previa de los scripts generados para NN {{NN}}: ejecútala en CloudShell y en cada instancia ANTES de instalar.
# Verifica el manifiesto (cambios no esperados), la sintaxis, los permisos y muestra lo que se va a aplicar.
# Uso: bash instalador/revisar-instalador.sh
set -uo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"; cd "$DIR"; source ./config.env
ok() { echo -e "  \033[32m✓\033[0m $*"; }; mal() { echo -e "  \033[31m✗\033[0m $*"; F=$((F + 1)); }; F=0
t() { echo -e "\n\033[1;36m== $*\033[0m"; }

t "1. Integridad (MANIFIESTO.sha256)"
if [[ -f MANIFIESTO.sha256 ]]; then
  if OUT=$(sha256sum -c MANIFIESTO.sha256 2>&1); then ok "Todos los scripts coinciden con lo generado"
  else mal "Hay archivos modificados respecto de lo generado (revísalos antes de ejecutar):"; echo "$OUT" | grep -v ': OK$' | sed 's/^/      /'; fi
else mal "Falta MANIFIESTO.sha256"; fi

t "2. Sintaxis de los scripts"
while IFS= read -r f; do bash -n "$f" 2>/dev/null && ok "$f" || mal "Error de sintaxis en $f"; done < <(find . -name '*.sh' | sort)
grep -rlI $'\r' --include='*.sh' . >/dev/null && mal "Hay scripts con fin de línea Windows (CRLF): usa .gitattributes o dos2unix" || ok "Fin de línea LF"

t "3. Permisos"
[[ -z $(find . -perm -o+w -type f) ]] && ok "Ningún archivo escribible por otros" || mal "Archivos escribibles por otros: $(find . -perm -o+w -type f | tr '\n' ' ')"
ls llaves/ 2>/dev/null | grep -v -E '\.pub$|LEEME\.txt$' | grep -q . && mal "llaves/ contiene archivos que no son .pub" || ok "llaves/ solo contiene llaves públicas"

t "4. Variables (config.env)"
grep -v '^#' config.env | grep -v '^$' | sed 's/^/    /'

t "5. Lo que se aplicará"
cat <<EOF
  Red AWS          VPC-$NN $VPC_CIDR · pública $PUB_CIDR · privada $PRIV_CIDR · zona $ZONA
  Security Groups  sg-web-$NN: 80/443 desde 0.0.0.0/0 · 22 desde tu IP /32
                   sg-bd-$NN:  $DB_PORT y 22 solo desde sg-web-$NN
  Firewall host    $FIREWALL (deny por defecto)
                   web-$NN: 80, 443 abiertos · 22 solo desde tu IP
                   bd-$NN:  $DB_PORT y 22 solo desde $WEB_IP
  Instancias       $WEB_HOST ($WEB_IP, IP elástica) · $BD_HOST ($BD_IP, sin IP pública)
  Base de datos    $MOTOR_NOMBRE en $BD_IP:$DB_PORT con TLS obligatorio · base $DB_NOMBRE · usuario $DB_USUARIO@$WEB_IP sin DELETE
  Grupos/usuarios  $G_ADMIN → $U_ADMIN (sudo ALL + TOTP) · $G_DEV → $U_DEV (solo su servicio) · $G_AUDIT → $U_AUDIT (solo lectura de registros)
  SSH              sin root, sin contraseña, MaxAuthTries 3, AllowGroups $G_ADMIN $G_DEV $G_AUDIT
  Respaldo         cron "$CRON_RESPALDO" hacia /respaldos (LUKS2), retención $RETENCION_DIAS días
EOF
for r in 0.0.0.0/0; do grep -n "FromPort=22\|FromPort=$DB_PORT" aws/01-crear-infra.sh | grep -q "$r" && mal "Una regla de 22 o $DB_PORT queda abierta a $r" || ok "22 y $DB_PORT no se abren a $r en los Security Groups"; done

echo
(( F )) && { echo -e "\033[31m⛔ $F observación(es). Revísalas antes de ejecutar los instaladores.\033[0m"; exit 1; }
echo -e "\033[32m✓ Instalador revisado: puedes continuar.\033[0m"
