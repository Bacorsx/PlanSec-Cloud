#!/usr/bin/env bash
# Revisa el repositorio ti3062-{{NN}} antes de cada push: bloquea llaves privadas, secretos TOTP,
# credenciales de BD y otros archivos sensibles. Lo ejecuta .githooks/pre-push y se puede correr a mano.
# Uso (desde la raíz del repositorio): bash instalador/verificar-secretos.sh
set -uo pipefail
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
mal=0; aviso=0
falla() { echo -e "\033[31m✗ $*\033[0m"; mal=$((mal + 1)); }
avisa() { echo -e "\033[33m⚠ $*\033[0m"; aviso=$((aviso + 1)); }

if git rev-parse --git-dir >/dev/null 2>&1; then
  mapfile -t ARCH < <({ git ls-files; git diff --cached --name-only --diff-filter=ACM; } | sort -u)
else
  mapfile -t ARCH < <(find . -type f -not -path './.git/*' | sed 's|^\./||')
fi

# 1. Nombres de archivo que nunca deben versionarse
for f in "${ARCH[@]}"; do
  [[ -f $f ]] || continue
  case "$f" in
    instalador/config.env) ;;   # variables del proyecto, sin secretos
    *.pem|*.key|*.ppk|*.p12|*.pfx) falla "Archivo de llave o certificado privado: $f" ;;
    *id_ed25519|*id_rsa|*/id_ed25519|*/id_rsa) falla "Llave SSH privada: $f" ;;
    *.google_authenticator) falla "Secreto TOTP: $f" ;;
    *db.ini|*.env|*.ti3062-clave-app|*ca-bd.b64|*infra-*.env) falla "Credenciales o configuración local: $f" ;;
    evidencia-*.json) avisa "Paquete de evidencia de la app versionado: $f (revisa que quieras publicarlo)" ;;
  esac
done

# 2. Contenido sensible (solo archivos de texto)
patron='BEGIN ([A-Z]+ )?PRIVATE KEY|otpauth://|AKIA[0-9A-Z]{16}|aws_secret_access_key|^[[:space:]]*password[[:space:]]*=[[:space:]]*"?[^"$[:space:]][^"[:space:]]{5,}'
for f in "${ARCH[@]}"; do
  [[ -f $f ]] || continue
  [[ $f == instalador/verificar-secretos.sh || $f == .githooks/* ]] && continue
  if grep -IqE "$patron" "$f" 2>/dev/null; then
    falla "Posible secreto en $f: $(grep -InE "$patron" "$f" | head -1 | cut -c1-90)"
  fi
done

# 3. Llaves públicas: solo .pub y de tipo ED25519
for f in instalador/llaves/*; do
  [[ -f $f && $f != *LEEME.txt ]] || continue
  [[ $f == *.pub ]] || falla "En instalador/llaves solo van llaves públicas (.pub): $f"
  [[ $f == *.pub ]] && ! grep -q '^ssh-ed25519 ' "$f" && avisa "La llave $f no es ED25519 (la pauta exige ED25519)"
done

# 4. Capturas en el JSON de datos (no se pueden revisar automáticamente)
if [[ -f data/proyecto-{{NN}}.json ]] && grep -q 'data:image' data/proyecto-{{NN}}.json; then
  avisa "data/proyecto-{{NN}}.json contiene capturas: confirma que ninguna muestre llaves, QR TOTP, secretos ni códigos de emergencia"
fi

echo
if (( mal )); then echo -e "\033[31m⛔ $mal problema(s): corrígelos antes de hacer push (git rm --cached <archivo> y agrégalo a .gitignore).\033[0m"; exit 1; fi
echo -e "\033[32m✓ Sin secretos detectados\033[0m ($aviso aviso(s))."
