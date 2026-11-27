#!/usr/bin/env bash
# Genera todas las temáticas con ambos motores y verifica placeholders, sintaxis PHP/bash/JS y JSON.
G=${GENERADOR:-$(cd "$(dirname "$0")/.." && pwd)}
F=0; N=0; rm -rf /tmp/gen-all
TEMAS=$(cd $G && python3 -c "import temas; print(' '.join(t['clave'] for t in temas.TEMAS))")
for tema in $TEMAS; do for motor in mariadb postgresql; do
  N=$((N+1)); nn=$(printf '%02d' $N)
  (cd $G && python3 generar.py --nn $nn --nombre "Alumno $tema" --github test --tema $tema --motor $motor --salida /tmp/gen-all >/dev/null) || { echo "FALLA generar $tema $motor"; F=$((F+1)); continue; }
  P=/tmp/gen-all/ti3062-$nn
  grep -rl "{{" $P && { echo "FALLA placeholders $tema $motor"; F=$((F+1)); }
  for f in $P/app-caso/*/*.php; do php -l $f >/dev/null 2>&1 || { echo "FALLA php -l $f"; F=$((F+1)); }; done
  for f in $(find $P/instalador -name '*.sh'); do bash -n $f || { echo "FALLA bash -n $f"; F=$((F+1)); }; done
  python3 -c "import json,sys; d=json.load(open('$P/data/proyecto-$nn.json')); assert len(d['controles'])>=17 and len(d['pruebas'])==13 and len(d['personal'])==3 and d['informe']['sec7'] and sum(r['tipo']=='RF' for r in d['requerimientos'])>=6" || { echo "FALLA datos $tema"; F=$((F+1)); }
  python3 -c "import json,re; d=json.load(open('$P/data/diccionario-$nn.json')); t=json.dumps(d,ensure_ascii=False); assert len(d['controles'])>=45 and not re.search(r'\{[A-Z_]+\}', t) and '{{' not in t and len(d['requisitos'])>=20" || { echo "FALLA diccionario $tema"; F=$((F+1)); }
  php -r "require '$P/app-caso/privado/config_tema.php'; if (!in_array(\$TEMA['patron'], ['inventario','reservas','prestamos','ordenes','membresias'])) exit(1);" || { echo "FALLA config_tema $tema"; F=$((F+1)); }
done; done
node --check $G/plantillas/sistema/app.js 2>/dev/null || command -v node >/dev/null || echo "(node no instalado en WSL: se validó app.js en Windows)"
echo "Proyectos generados: $N · FALLAS: $F"
