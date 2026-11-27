# -*- coding: utf-8 -*-
"""Genera la bóveda Obsidian `grafo/` con el mapa del proyecto PlanSec-Cloud.

Uso (desde la raíz del repositorio):  python herramientas/generar_grafo.py
- codigo/    una nota por archivo: qué hace, qué usa, quién lo usa, conceptos y controles NIST
- conceptos/ conceptos del proyecto, glosario y los 46 controles NIST del diccionario
- mapas/     flujo, arquitectura, capas, instalación, pruebas, decisiones y diccionario
- notas/     notas propias (pendientes, sesiones): el generador NUNCA las toca
Abre `grafo/` como bóveda en Obsidian y usa la vista de grafo (Ctrl+G): los colores son las capas.
"""
import datetime as dt
import json
import re
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
import diccionario as D  # noqa: E402
import temas as T  # noqa: E402

SALIDA = RAIZ / "grafo"
EXT = {".py", ".sh", ".php", ".js", ".css", ".html", ".md", ".sql", ".env", ""}
EXCLUIR = ("grafo/", ".git/", "__pycache__/", "salida/")

# capa (tag) según la ruta, y su color en el grafo
CAPAS = [
    ("plantillas/app-caso/", "enfoque", "Capa de enfoque (app del caso, web-NN)", 0x16A3B8),
    ("plantillas/sistema/", "informe", "Capa de informe (sistema de gestión, Cloudflare)", 0xE08A3C),
    ("plantillas/instalador/", "instalador", "Instalador (AWS y servidores)", 0x2F9E57),
    ("plantillas/githooks/", "instalador", "", 0x2F9E57),
    ("pruebas/", "pruebas", "Pruebas en WSL", 0x9A9A9A),
    ("herramientas/", "herramientas", "Herramientas", 0x7A7A7A),
    ("plantillas/", "documentos", "Documentos generados (guía y README)", 0xB07CD8),
    ("", "generador", "Generador (Python)", 0x5B6EE1),
]
COLOR_CONCEPTO, COLOR_NIST, COLOR_MAPA = 0xD4B106, 0xC0392B, 0xFFFFFF

CONCEPTOS = {
    "Capa de enfoque": ("La aplicación del negocio (PHP) que corre en web-NN: usuarios por rol, reglas, reportes y auditoría. Distinta del sistema de gestión, como exige la pauta.", r"app-caso|capa de enfoque"),
    "Capa de informe": ("El sistema de gestión (estático) que planifica, documenta y genera el PDF; se publica en Cloudflare Pages y en /gestion.", r"plantillas/sistema|capa de informe|sistema de gesti[oó]n"),
    "Paquete de evidencia": ("JSON que la capa de enfoque exporta (admin/auditor) con datos medidos y que la capa de informe importa sin sobrescribir.", r"evidencia_app|exportar[_ ]evidencia|importarEvidencia|evidencia-ti3062"),
    "Borrador precargado": ("Todo lo que genera la plantilla queda marcado `_base` hasta que el estudiante lo revisa contra su evidencia real.", r"_base"),
    "Diccionario": ("Fuente única de controles NIST, textos base, hallazgos, glosario y contenido mínimo; se publica por plantilla como data/diccionario-NN.json.", r"diccionario"),
    "Patrón de negocio": ("Define las funciones de la app según la temática: inventario, reservas, préstamos, órdenes o membresías.", r"\bpatron\b|PATRON\(\)|RF_PATRON"),
    "Variabilidad por estudiante": ("El NN, nombre y semilla eligen temática, diseño, motor, firewall, grupos, zona, proveedor y controles.", r"elegir_perfil|semilla|variante"),
    "VPC y subredes": ("VPC-NN 10.NN.0.0/16 con subred pública 10.NN.1.0/24 (IGW) y privada 10.NN.2.0/24 sin salida.", r"VPC|subred"),
    "Security Groups": ("sg-web-NN (80/443 abiertos, 22 desde la IP admin) y sg-bd-NN (puerto BD y 22 solo desde sg-web-NN).", r"sg-web|sg-bd|security.group"),
    "NAT temporal": ("Salida a Internet solo para instalar paquetes en bd-NN; se elimina y se evidencia con la tabla de rutas.", r"nat-temporal|NAT temporal|02-nat"),
    "IP elástica": ("IP fija de web-NN para que la URL no cambie entre sesiones de AWS Academy.", r"[Ee]lastic|IP el[aá]stica|WEB_EIP"),
    "TLS web→bd": ("La app se conecta a la BD con TLS 1.2/1.3 y verifica el certificado del servidor (SC-8).", r"ssl_ca|sslmode|require_secure_transport|canal_bd|hostssl"),
    "CA del proyecto": ("CA propia generada en bd-NN que firma el certificado de la BD; la línea base64 se copia a web-NN.", r"ca\.crt|bd-ca|ca-bd|CA del proyecto"),
    "HTTPS": ("Certificado autofirmado en web-NN y redirección HTTP→HTTPS.", r"HTTPS|RewriteCond|default-ssl"),
    "MFA TOTP": ("Segundo factor obligatorio para el grupo administrador en SSH (pam_google_authenticator).", r"google.authenticator|TOTP"),
    "LUKS": ("Volumen cifrado /respaldos en bd-NN; se reabre a mano tras reiniciar el laboratorio.", r"LUKS|cryptsetup|luks"),
    "auditd": ("Auditoría del SO: sudo, passwd, sudoers y sshd_config.", r"auditd|ausearch|aureport|augenrules"),
    "Auditoría de la app": ("Tabla auditoria_app: cada acción con usuario, fecha e IP; la app no puede borrarla (AU-9).", r"auditoria_app|auditar\("),
    "Roles de la app": ("Administrador, operador y auditor, verificados en cada acción del servidor.", r"ROLES|exigir\(|operador"),
    "Bloqueo por intentos": ("5 intentos fallidos bloquean la cuenta 15 minutos (AC-7).", r"MAX_INTENTOS|bloqueado_hasta|cuenta_bloqueada"),
    "Sesión segura": ("Cookie HttpOnly/Secure/SameSite, regeneración del ID, 15 min de inactividad y revalidación de la cuenta en cada petición.", r"session_regenerate_id|SameSite|INACTIVIDAD|iniciar_sesion"),
    "CSRF y CSP": ("Token CSRF en cada formulario y Content-Security-Policy sin scripts en línea.", r"csrf|Content-Security-Policy"),
    "Respaldo cifrado": ("cron diario de la BD hacia /respaldos con sha256, retención y restauración probada.", r"respaldo|pg_dump|mariadb-dump"),
    "Endurecimiento del SO": ("Grupos y usuarios por rol, sudoers específicos, SSH sin root ni contraseña, AllowGroups.", r"sudoers|sshd_config|AllowGroups|01-hardening"),
    "Firewall de host": ("ufw o nftables coherente con los Security Groups.", r"\bufw\b|nftables|FIREWALL"),
    "Manifiesto de scripts": ("MANIFIESTO.sha256 + revisar-instalador.sh detectan scripts modificados antes de instalar.", r"MANIFIESTO|revisar-instalador"),
    "Revisión de secretos": ("verificar-secretos.sh y el hook pre-push bloquean llaves, TOTP, db.ini y claves.", r"verificar-secretos|pre-push|hooksPath"),
    "PDF desde los datos": ("El informe se genera solo desde los datos del sistema (jsPDF); nada fijo en el código.", r"generarPDF|jsPDF|jspdf"),
    "Cloudflare Pages": ("Publica la capa de informe en ti3062-NN.pages.dev.", r"pages\.dev|Cloudflare"),
    "AWS Academy": ("Learner Lab: sin IAM ni CloudTrail, sesiones que detienen las instancias.", r"Academy|Learner Lab|CloudTrail"),
    "Pruebas P1–P13": ("P1–P8 de la pauta y P9–P13 de la app web (TLS, bloqueo, roles, validación, auditoría).", r"\bP(1[0-3]|[1-9])\b"),
}

MAPAS = {
    "Flujo": """# Flujo: del generador a la defensa

1. [[generar]] lee [[catalogo]], [[temas]] y [[diccionario]] y elige la variante del estudiante ([[Variabilidad por estudiante]]).
2. Escribe el repositorio `ti3062-NN`: la [[Capa de informe]] en la raíz, la [[Capa de enfoque]] en `app-caso/`, el instalador y `data/` (proyecto + diccionario).
3. El repositorio se publica en GitHub ([[Revisión de secretos]] antes de cada push) y la capa de informe en [[Cloudflare Pages]].
4. En AWS ([[AWS Academy]]): [[revisar-instalador (sh)]] → [[01-crear-infra (sh)]] ([[VPC y subredes]], [[Security Groups]], [[IP elástica]]) → [[02-nat-temporal (sh)]].
5. bd-NN: [[00-paquetes (sh)]] → [[01-configurar-bd (sh)]] ([[TLS web→bd]], [[CA del proyecto]]) → [[02-luks-respaldos (sh)]] ([[LUKS]]) → [[03-respaldo-cron (sh)]] → [[04-probar-restauracion (sh)]].
6. web-NN: [[01-instalar-web (sh)]] ([[HTTPS]], primer administrador) → [[01-hardening (sh)]] ([[Endurecimiento del SO]], [[MFA TOTP]], [[auditd]], [[Firewall de host]]).
7. La app ([[Capa de enfoque]]) exporta el [[Paquete de evidencia]]; el sistema ([[Capa de informe]]) lo importa, se revisan los [[Borrador precargado|borradores]] y se genera el PDF ([[PDF desde los datos]]).
8. Tras cada reinicio del laboratorio: [[05-tras-reinicio (sh)]].

Ver [[Arquitectura]] · [[Instalación]] · [[Pruebas]]""",
    "Arquitectura": """# Arquitectura (colores del grafo)

- **Generador (azul)**: [[generar]], [[catalogo]], [[temas]], [[diccionario]].
- **Capa de enfoque (turquesa)**: webroot [[index (php)]], [[api (php)]], [[app (js) · enfoque]], [[estilo (css)]]; fuera del webroot [[nucleo (php)]], [[patrones (php)]], [[evidencia (php)]], [[vista_equipo (php)]], [[crear-usuario (php)]].
- **Capa de informe (naranjo)**: [[index (html)]], [[app (js) · informe]], [[styles (css)]].
- **Instalador (verde)**: scripts de AWS, bd, web y comunes; [[revisar-instalador (sh)]], [[verificar-secretos (sh)]], [[pre-push]].
- **Documentos (lila)**: [[PASO-A-PASO (md)]], [[README (md) · estudiante]].
- **Pruebas (gris)**: ver [[Pruebas]].
- **Conceptos (amarillo)** y **controles NIST (rojo)**.

Ver [[Capas de la app]] · [[Flujo]] · [[Decisiones]]""",
    "Capas de la app": """# Una aplicación, dos capas

La pauta exige que el sistema de gestión (Cloudflare Pages) y la app del caso (web-NN) sean **distintos**. Por eso es un solo producto y un solo repositorio con dos capas:

| | [[Capa de enfoque]] | [[Capa de informe]] |
|---|---|---|
| Qué es | App del negocio ([[Patrón de negocio]]) | Gestión, planificación y PDF |
| Dónde | web-NN + bd-NN (AWS) | ti3062-NN.pages.dev y /gestion |
| Código | `plantillas/app-caso/` | `plantillas/sistema/` |
| Datos | BD con 4 tablas, [[Auditoría de la app]] | `data/proyecto-NN.json`, [[Diccionario]] |
| Seguridad | [[Roles de la app]], [[Sesión segura]], [[CSRF y CSP]], [[TLS web→bd]] | [[Borrador precargado]], [[Revisión de secretos]] |

Se comunican solo con el [[Paquete de evidencia]] (sin compartir código, sesión ni base de datos).""",
    "Instalación": """# Orden de instalación

| Paso | Dónde | Script |
|---|---|---|
| 0 | PC / CloudShell | [[revisar-instalador (sh)]] |
| 1 | CloudShell | [[01-crear-infra (sh)]] y [[02-nat-temporal (sh)]] crear |
| 2 | bd-NN | [[00-paquetes (sh)]] bd → NAT eliminar → [[01-configurar-bd (sh)]] |
| 3 | web-NN | [[00-paquetes (sh)]] web → [[01-instalar-web (sh)]] |
| 4 | ambas | [[01-hardening (sh)]] → TOTP → [[99-cerrar-ubuntu (sh)]] |
| 5 | bd-NN | [[02-luks-respaldos (sh)]] → [[03-respaldo-cron (sh)]] → [[04-probar-restauracion (sh)]] |
| 6 | CloudShell | [[03-snapshots-y-evidencias (sh)]] (snapshots + AMI) |
| Siempre | bd-NN | [[05-tras-reinicio (sh)]] tras reiniciar el laboratorio |
| Evidencias | ambas | [[evidencias (sh)]] |""",
    "Pruebas": """# Pruebas

**Del informe (pauta + app):** [[Pruebas P1–P13]], precargadas en el módulo Validación.

**Del generador (WSL Ubuntu 24.04, `pruebas/`):** [[90-todo (sh)]] corre [[70-generador (sh)]], [[55-matriz (sh)]] (8 combinaciones de [[50-app (sh)]]), [[20-luks-respaldo (sh)]] y [[80-capas (sh)]]; [[30-hardening (sh)]] prueba SSH, TOTP y sudo.

Últimos resultados (2026-11-27): generador 30/30, matriz 8/8 sin fallas, LUKS 0 fallas, capas 0 fallas. Pendiente: ver [[Pendientes]].""",
    "Decisiones": """# Decisiones y por qué

- **Dos capas en un repositorio** ([[Capas de la app]]): la pauta exige que la app del caso sea distinta del sistema de gestión.
- **BD en EC2 bd-NN** (no RDS): la pauta fija la topología web/bd con subred privada sin salida.
- **Ubuntu 24.04**: 26.04 trae sudo-rs, que no acepta las directivas de registro de sudo.
- **Llaves ED25519** por usuario y [[MFA TOTP]] solo para administración: lo pide la pauta.
- **[[NAT temporal]]**: la subred privada debe quedar sin salida al final.
- **[[IP elástica]]**: AWS Academy detiene las instancias y la IP automática cambia.
- **[[TLS web→bd]] con [[CA del proyecto]]** y verificación estricta: SC-8 en tránsito entre instancias.
- **Usuario de BD sin DELETE** y auditoría solo INSERT/SELECT: AC-6 y AU-9.
- **[[Diccionario]] como fuente única** y **[[Borrador precargado]]**: sugerir sin reemplazar la evidencia real.
- **[[Paquete de evidencia]]** en vez de conexión directa: las capas no comparten sesión (SameSite=Strict) ni dominio.
- **Controles en el SO**: AWS Academy no permite IAM ni CloudTrail (hallazgo HZ-01).""",
}


def capa_de(rel):
    for pref, tag, _, _ in CAPAS:
        if rel.startswith(pref):
            return tag
    return "generador"


def nombre_nota(rel, ambiguos):
    p = Path(rel)
    base = p.stem if p.suffix else p.name
    if rel in ("generar.py", "catalogo.py", "temas.py", "diccionario.py"):
        return base
    nombre = f"{base} ({p.suffix[1:]})" if p.suffix else base
    if nombre in ambiguos:
        nombre += " · " + ({"enfoque": "enfoque", "informe": "informe", "documentos": "estudiante", "generador": "generador"}.get(capa_de(rel), capa_de(rel)))
    return nombre


def descripcion(texto, suf):
    t = texto.lstrip("﻿")
    if suf == ".py":
        m = re.search(r'"""(.+?)"""', t, re.S)
        if m:
            return " ".join(m.group(1).split())[:600]
    if suf == ".md":
        lineas = [x for x in t.splitlines() if x.strip() and not x.startswith("|")]
        return " ".join(lineas[:4])[:400]
    if suf in (".php", ".js", ".css"):
        m = re.search(r"/\*(.+?)\*/", t, re.S)
        if m:
            return " ".join(m.group(1).replace("*", " ").split())[:600]
    lineas = []
    for x in t.splitlines()[:14]:
        if x.startswith("#!"):
            continue
        if x.startswith("#"):
            lineas.append(x.lstrip("# ").strip())
        elif lineas:
            break
    return " ".join(lineas)[:600]


def main():
    archivos = []
    for f in sorted(RAIZ.rglob("*")):
        rel = f.relative_to(RAIZ).as_posix()
        if not f.is_file() or any(rel.startswith(e) or f"/{e}" in "/" + rel for e in EXCLUIR):
            continue
        if f.suffix not in EXT or rel.startswith(".") or "/." in rel and "githooks" not in rel:
            continue
        archivos.append(rel)
    bases = {}
    for rel in archivos:
        p = Path(rel)
        b = f"{p.stem} ({p.suffix[1:]})" if p.suffix else p.name
        bases.setdefault(b, []).append(rel)
    ambiguos = {b for b, v in bases.items() if len(v) > 1}
    nota = {rel: nombre_nota(rel, ambiguos) for rel in archivos}
    textos = {rel: (RAIZ / rel).read_text(encoding="utf-8", errors="replace") for rel in archivos}

    # dependencias: menciones de otros archivos o módulos
    usa = {rel: set() for rel in archivos}
    for rel, txt in textos.items():
        for otro in archivos:
            if otro == rel:
                continue
            p = Path(otro)
            claves = [p.name] if p.suffix else [p.name]
            if otro in ("catalogo.py", "temas.py", "diccionario.py"):
                claves.append(f"import {p.stem}")
                claves.append(f"from {p.stem} import")
            if any(k in txt for k in claves):
                if p.name in {Path(x).name for x in archivos if x != otro} and capa_de(otro) != capa_de(rel):
                    continue   # mismo nombre en otra capa (p. ej. app.js): solo dentro de la propia capa
                usa[rel].add(otro)
    usado_por = {rel: {o for o, d in usa.items() if rel in d} for rel in archivos}

    nist = {c["codigo"]: c for c in D.todos_los_controles()}
    re_nist = re.compile(r"\b(" + "|".join(re.escape(k) for k in sorted(nist, key=len, reverse=True)) + r")\b")

    nota_concepto = {k: set() for k in CONCEPTOS}
    nota_nist = {k: set() for k in nist}

    if SALIDA.exists():
        for sub in ("codigo", "conceptos", "mapas"):
            shutil.rmtree(SALIDA / sub, ignore_errors=True)
    for sub in ("codigo", "conceptos/NIST", "mapas", "notas", ".obsidian"):
        (SALIDA / sub).mkdir(parents=True, exist_ok=True)

    for rel in archivos:
        txt, capa = textos[rel], capa_de(rel)
        conc = sorted(k for k, (_, rx) in CONCEPTOS.items() if re.search(rx, txt, re.I if k not in ("Pruebas P1–P13",) else 0))
        ctrl = sorted(set(re_nist.findall(txt)))
        for k in conc:
            nota_concepto[k].add(nota[rel])
        for k in ctrl:
            nota_nist[k].add(nota[rel])
        destino = SALIDA / "codigo" / Path(rel).parent / (nota[rel] + ".md")
        destino.parent.mkdir(parents=True, exist_ok=True)
        cuerpo = [
            "---", f"tags: [codigo, {capa}]", f"archivo: {rel}", "---", f"# {Path(rel).name}", "",
            descripcion(txt, Path(rel).suffix) or "(sin descripción en el encabezado)", "",
            f"[Abrir el archivo](<file:///{(RAIZ / rel).as_posix()}>)", "",
        ]
        if usa[rel]:
            cuerpo += ["## Usa", ""] + [f"- [[{nota[o]}]]" for o in sorted(usa[rel])] + [""]
        if usado_por[rel]:
            cuerpo += ["## Lo usan", ""] + [f"- [[{nota[o]}]]" for o in sorted(usado_por[rel])] + [""]
        if conc:
            cuerpo += ["## Conceptos", "", " · ".join(f"[[{k}]]" for k in conc), ""]
        if ctrl:
            cuerpo += ["## Controles NIST", "", " · ".join(f"[[{k}]]" for k in ctrl), ""]
        cuerpo += [f"Capa: [[Arquitectura]] · {capa}"]
        destino.write_text("\n".join(cuerpo) + "\n", encoding="utf-8")

    for k, (desc, _) in CONCEPTOS.items():
        usos = sorted(nota_concepto[k])
        (SALIDA / "conceptos" / f"{k}.md").write_text("\n".join(
            ["---", "tags: [concepto]", "---", f"# {k}", "", desc, "", "## Dónde aparece", ""] + [f"- [[{u}]]" for u in usos] +
            ["", "Ver [[Flujo]] · [[Diccionario del proyecto]]"]) + "\n", encoding="utf-8")
    for termino, definicion in D.GLOSARIO:
        archivo = SALIDA / "conceptos" / (re.sub(r'[\\/:*?"<>|]', "-", termino) + ".md")
        if not archivo.exists():
            archivo.write_text(f"---\ntags: [concepto, glosario]\n---\n# {termino}\n\n{definicion}\n\nVer [[Diccionario del proyecto]]\n", encoding="utf-8")
    for cod, c in nist.items():
        fam, desc, ev, pr = D.DETALLE[cod]
        usos = sorted(nota_nist[cod])
        (SALIDA / "conceptos" / "NIST" / f"{cod}.md").write_text("\n".join(
            ["---", "tags: [nist]", "---", f"# {cod} · {c['nombre']}", "", f"**Familia:** {fam} · **Capa:** {c['capa']}", "", desc, "",
             f"- **Riesgo que mitiga:** {c['riesgo']}", f"- **Punto de aplicación (plantilla):** {c['punto']}",
             f"- **Evidencia sugerida:** {ev}", f"- **Prueba asociada:** {pr or '—'}", "", "## Dónde aparece en el código", ""] +
            [f"- [[{u}]]" for u in usos] + ["", "Ver [[Diccionario del proyecto]]"]) + "\n", encoding="utf-8")

    for nombre, texto in MAPAS.items():
        (SALIDA / "mapas" / f"{nombre}.md").write_text(f"---\ntags: [mapa]\n---\n{texto}\n", encoding="utf-8")
    patrones = {}
    for t in T.TEMAS:
        patrones.setdefault(t["patron"], []).append(f"{t['nombre_app']} ({t['clave']})")
    (SALIDA / "mapas" / "Diccionario del proyecto.md").write_text("\n".join(
        ["---", "tags: [mapa]", "---", "# Diccionario del proyecto", "",
         f"Fuente: [[diccionario]] · {len(nist)} controles NIST · {len(D.GLOSARIO)} términos · {len(D.REQUISITOS)} requisitos de contenido mínimo.", "",
         "## Controles por familia", ""] +
        [f"- **{fam}**: " + " · ".join(f"[[{c}]]" for c in sorted(k for k in nist if D.DETALLE[k][0] == fam)) for fam in sorted({v[0] for v in D.DETALLE.values()})] +
        ["", "## Patrones y temáticas", ""] + [f"- **{p}**: {', '.join(v)}" for p, v in patrones.items()] +
        ["", "## Conceptos", ""] + [" · ".join(f"[[{k}]]" for k in CONCEPTOS)]) + "\n", encoding="utf-8")

    hoy = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    (SALIDA / "00 Inicio.md").write_text(f"""---
tags: [mapa]
---
# PlanSec-Cloud · mapa del proyecto

Bóveda generada desde el código con `python herramientas/generar_grafo.py` ({hoy}).
Abre la **vista de grafo** (Ctrl+G): los colores son las capas.

## Para continuar en otra sesión
- [[Continuar aquí]] — estado, cómo retomar y qué sigue
- [[Pendientes]] — lo que falta

## Mapas
- [[Flujo]] — del generador a la defensa
- [[Arquitectura]] — partes y archivos
- [[Capas de la app]] — una aplicación, dos capas
- [[Instalación]] — orden de los scripts
- [[Pruebas]] — P1–P13 y pruebas del generador
- [[Decisiones]] — qué se decidió y por qué
- [[Diccionario del proyecto]] — controles NIST, patrones y conceptos

## Contenido
- `codigo/`: {len(archivos)} notas, una por archivo
- `conceptos/`: {len(CONCEPTOS) + len(D.GLOSARIO)} conceptos y {len(nist)} controles NIST
- `notas/`: tus notas (el generador no las toca)

> `codigo/`, `conceptos/` y `mapas/` se regeneran: no edites ahí.
""", encoding="utf-8")

    grupos = [{"query": f"tag:#{tag}", "color": {"a": 1, "rgb": rgb}} for _, tag, desc, rgb in CAPAS if desc]
    grupos += [{"query": "tag:#nist", "color": {"a": 1, "rgb": COLOR_NIST}}, {"query": "tag:#concepto", "color": {"a": 1, "rgb": COLOR_CONCEPTO}},
               {"query": "tag:#mapa", "color": {"a": 1, "rgb": COLOR_MAPA}}]
    (SALIDA / ".obsidian" / "graph.json").write_text(json.dumps({"colorGroups": grupos, "showTags": False, "showAttachments": False,
                                                                  "hideUnresolved": True, "showOrphans": False}, indent=1), encoding="utf-8")
    app = SALIDA / ".obsidian" / "app.json"
    if not app.exists():
        app.write_text("{}\n", encoding="utf-8")
    print(f"Bóveda en {SALIDA}: {len(archivos)} archivos, {len(CONCEPTOS)} conceptos, {len(nist)} controles NIST.")


if __name__ == "__main__":
    main()
