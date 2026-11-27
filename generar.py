#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generador automático del Proyecto Integrador TI3062 (Evaluación 4).

Crea, para cada estudiante, un repositorio ti3062-NN listo para GitHub + Cloudflare Pages + AWS:
  - Sistema web de gestión/planificación que genera el PDF desde los datos (raíz del repo)
  - data/proyecto-NN.json precargado (borrador a completar con evidencia real)
  - app-caso/: aplicación PHP con 2 tablas relacionadas para web-NN
  - instalador/: scripts para AWS (VPC, SG, EC2, NAT temporal, snapshots) y para las instancias
  - PASO-A-PASO.md personalizado con el NN, nombres y comandos exactos

Cada combinación (temática, colores, tipografía, distribución, motor de BD, firewall, nombres de
grupos, proveedor alternativo, controles, riesgos, horario de respaldo...) se elige de forma
determinista a partir del NN + nombre + semilla, así dos estudiantes no obtienen la misma página.

Uso:
  python generar.py --nn 07 --nombre "Nombre Apellido" --github usuario
  python generar.py --nn 07 --nombre "..." --github usuario --tema dental --motor postgresql
  python generar.py --lote alumnos.csv          (columnas: nn,nombre,github[,tema][,motor])
  python generar.py --listar-temas
"""
import argparse, csv, datetime as dt, hashlib, json, os, random, re, shutil, sys, unicodedata
from pathlib import Path

import catalogo as C
import diccionario as D

BASE = Path(__file__).resolve().parent
PLANT = BASE / "plantillas"


# ------------------------------------------------------------------ utilidades
def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def render(texto, ctx, origen=""):
    def rep(m):
        k = m.group(1)
        if k not in ctx:
            raise KeyError(f"Placeholder sin valor: {k} en {origen}")
        return str(ctx[k])
    return re.sub(r"\{\{([A-Z0-9_]+)\}\}", rep, texto)


def php_valor(v, ind=0):
    pad = "    " * (ind + 1)
    if isinstance(v, dict):
        return "[\n" + "".join(f"{pad}{php_valor(k)} => {php_valor(x, ind + 1)},\n" for k, x in v.items()) + "    " * ind + "]"
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(php_valor(x, ind + 1) for x in v) + "]"
    if isinstance(v, (int, float)):
        return str(v)
    return "'" + str(v).replace("\\", "\\\\").replace("'", "\\'") + "'"


# ------------------------------------------------------------------ variantes
def elegir_perfil(nn, nombre, github, semilla="", tema=None, motor=None, usados=None, firewall=None):
    h = hashlib.sha256(f"{nn}|{slug(nombre)}|{github}|{semilla}".encode()).hexdigest()
    r = random.Random(int(h, 16))
    if tema:
        t = next((x for x in C.TEMAS if x["clave"] == tema), None)
        if not t:
            sys.exit(f"Tema desconocido: {tema}. Usa --listar-temas")
    else:
        libres = [x for x in C.TEMAS if not usados or x["clave"] not in usados] or C.TEMAS
        t = r.choice(libres)
    m = next((x for x in C.MOTORES if x["clave"] == motor), None) if motor else r.choice(C.MOTORES)
    if motor and not m:
        sys.exit("Motor debe ser mariadb o postgresql")
    tarjeta = r.choice(C.ESTILOS_TARJETA)
    perfil = {
        "rng": r, "tema": t, "motor": m,
        "paleta": r.choice(C.PALETAS), "fuente": r.choice(C.FUENTES), "layout": r.choice(C.LAYOUTS),
        "tarjeta": tarjeta, "radio": {"redondeada": "14px", "recta": "2px", "sombra": "8px", "borde": "6px"}[tarjeta],
        "grafico": r.choice(C.ESTILOS_GRAFICO), "pdf": r.choice(C.ESTILOS_PDF),
        "nombre_sistema": r.choice(C.NOMBRES_SISTEMA), "grupos": r.choice(C.NOMBRES_GRUPOS),
        "firewall": r.choice(C.FIREWALLS), "zona": r.choice(C.ZONAS), "alt": r.choice(C.PROVEEDORES_ALT),
        "variante_app": r.choice("abc"), "cron": f"{r.randint(0, 59)} {r.randint(1, 4)} * * *",
        "retencion": r.choice([7, 10, 14]),
    }
    if firewall:
        perfil["firewall"] = firewall
    return perfil


# ------------------------------------------------------------------ datos del proyecto
OBLIG = ["SC-7", "AC-6", "IA-2(1)", "SC-28", "AU-2", "CP-9", "AC-12"]
REQMAP = {"SC-7": "RNF-01", "IA-2(1)": "RNF-02", "AC-6": "RNF-03", "CP-9": "RNF-04", "CP-10": "RNF-04", "CM-7": "RNF-05", "AU-2": "RNF-06", "AU-6": "RNF-06", "SC-28": "RNF-04", "IA-5": "RNF-03", "AC-17": "RNF-02", "AC-12": "RNF-08",
          "AC-3": "RF-06", "AC-7": "RNF-08", "AC-8": "RF-06", "IA-2": "RF-06", "IA-5(1)": "RNF-08", "SC-8": "RNF-07", "SC-23": "RNF-08", "SI-10": "RF-02", "SI-11": "RF-02", "AU-9": "RNF-06",
          "AC-2": "RF-06", "AC-5": "RNF-03", "AC-11": "RNF-08", "AU-3": "RNF-06", "AU-8": "RNF-06", "AU-11": "RNF-06", "AU-12": "RNF-06", "CM-2": "RNF-04", "CM-6": "RNF-01",
          "CP-2": "RNF-04", "CP-4": "RNF-04", "CP-6": "RNF-04", "CP-7": "RNF-04", "IR-4": "RNF-06", "IR-6": "RNF-06", "RA-3": "RNF-01", "RA-5": "RNF-01", "SC-5": "RNF-05",
          "SC-12": "RNF-07", "SC-13": "RNF-07", "SI-2": "RNF-01", "SI-4": "RNF-06", "AU-9(2)": "RNF-06", "IA-2(2)": "RNF-02"}
ALT_COSTO = {"Microsoft Azure": "≈ 19,50 (2×B1s + discos + IP pública) — verificar",
             "Google Cloud": "≈ 16,00 (2×e2-micro + discos + IP externa) — verificar",
             "Oracle Cloud (OCI)": "≈ 0 en Always Free / ≈ 12 de pago — verificar"}


def construir_datos(p, nn, nombre, github, inicio, pools=None):
    pools = {} if pools is None else pools
    r, t, m = p["rng"], p["tema"], p["motor"]
    g = p["grupos"]
    nnip = str(int(nn))
    ua, ud, uu = f"{g['u_admin']}{nn}", f"{g['u_dev']}{nn}", f"{g['u_audit']}{nn}"
    url_sis, url_repo = f"https://ti3062-{nn}.pages.dev", f"https://github.com/{github}/ti3062-{nn}"
    P, H = t["padre"], t["hijo"]
    d = lambda n: (inicio + dt.timedelta(days=n)).isoformat()

    hitos = [
        {"id": "H1", "nombre": "Análisis y diseño", "fecha": d(5), "criterio": "Problemática, requerimientos, comparativa cloud y controles NIST registrados"},
        {"id": "H2", "nombre": "Implementación segura en AWS", "fecha": d(13), "criterio": "VPC, SG, instancias endurecidas, app del caso operativa y respaldo cifrado"},
        {"id": "H3", "nombre": "Validación y cierre", "fecha": d(19), "criterio": "Pruebas P1–P13, hallazgos, análisis CIA, riesgos y PDF generado"},
    ]
    resp = lambda rol: nombre   # se elige desde "Equipo y roles" en el sistema
    tareas_base = [
        ("Levantar problemática, actores y requerimientos RF/RNF", "H1", "Auditoría", 0, 2, ""),
        ("Comparar AWS vs " + p["alt"]["nombre"] + " con calculadoras oficiales", "H1", "Administración", 1, 3, "T01"),
        ("Seleccionar controles NIST y mapear a requerimientos", "H1", "Auditoría", 3, 5, "T01"),
        ("Crear VPC-%s, subredes, IGW y tablas de rutas" % nn, "H2", "Administración", 5, 6, "T02"),
        ("Configurar sg-web-%s y sg-bd-%s con mínimo privilegio" % (nn, nn), "H2", "Administración", 6, 6, "T04"),
        ("Lanzar web-%s y bd-%s; instalar paquetes con NAT temporal y retirarla" % (nn, nn), "H2", "Administración", 6, 7, "T05"),
        (f"Desarrollar app {t['nombre_app']} ({P['tabla']}/{H['tabla']} + usuarios y auditoría) y desplegar en web-{nn} con HTTPS", "H2", "Desarrollo", 5, 9, "T06"),
        (f"Configurar {m['nombre']} con TLS (CA propia), usuario app_{nn} de mínimo privilegio y auditoría inmutable", "H2", "Desarrollo", 7, 8, "T06"),
        ("Endurecer SO: grupos, sudoers, SSH, TOTP y firewall de host", "H2", "Administración", 8, 11, "T06"),
        ("Configurar auditd y revisar registros", "H2", "Auditoría", 10, 11, "T09"),
        ("Volumen LUKS /respaldos, cron de respaldo y restauración probada", "H2", "Administración", 11, 12, "T08"),
        ("Snapshots de volúmenes y justificación de AZ", "H2", "Administración", 12, 13, "T11"),
        ("Ejecutar pruebas P1–P13 y registrar hallazgos", "H3", "Auditoría", 14, 16, "T12"),
        ("Análisis CIA, riesgos residuales, Gobierno TI y mejoras", "H3", "Auditoría", 16, 18, "T13"),
        ("Generar PDF, revisar README y preparar defensa", "H3", "Desarrollo", 18, 19, "T14"),
    ]
    tareas = [{"id": f"T{i+1:02d}", "nombre": n, "hito": h, "rol": rol, "responsable": resp(rol), "inicio": d(a), "fin": d(b),
               "dependencia": dep, "estado": "Pendiente"} for i, (n, h, rol, a, b, dep) in enumerate(tareas_base)]

    caract_pool = [
        (f"Servicio web transaccional: {t['procesos'][1].lower()} requiere escritura y lectura concurrente en la BD", "Se separa la capa web (subred pública) de la BD (subred privada)"),
        ("Datos personales de " + t["actores"][2].lower() + "s sujetos a la Ley 21.719 de protección de datos", "Cifrado en reposo de respaldos (LUKS) y acceso mínimo a la BD"),
        ("Acceso administrativo remoto desde Internet", "SSH solo con llave ED25519 desde IP del administrador y MFA TOTP"),
        ("Necesidad de continuidad operativa: hoy no existe respaldo", "Respaldo diario automatizado, restauración probada y snapshots EBS"),
        ("Múltiples roles con distinto nivel de acceso", "Grupos funcionales con sudoers específicos y separación de funciones"),
        ("Presupuesto limitado y entorno AWS Academy sin IAM/CloudTrail", "Controles a nivel de SO y Security Groups; instancias t3.micro"),
    ]
    pools["caracteristicas"] = [{"id": f"C{i+1}", "descripcion": a, "diseno": b} for i, (a, b) in enumerate(caract_pool)]
    sel = r.sample(caract_pool, r.choice([4, 5]))
    caracteristicas = [{"id": f"C{i+1}", "descripcion": a, "diseno": b} for i, (a, b) in enumerate(sel)]

    V = t.get("vocab", {})
    pat = t["patron"]
    fmt = {"P": P["titulo"].lower(), "P2": P["titulo"].lower(), "p": P["singular"], "H2": H["titulo"].lower(), "h": H["singular"],
           "precio": " y precio" if V.get("precio") else "", "tipos": ", ".join(x[0] for x in V.get("tipos", [])),
           "franja": "un bloque horario" if V.get("modo") == "bloque" else "un rango de fechas (entrada y salida)",
           "regla": "mismo día y bloque" if V.get("modo") == "bloque" else "fechas superpuestas", "completar": str(V.get("completar", "")).lower(),
           "estados": " → ".join(V.get("estados", [])), "nivel": str(V.get("nivel", "prioridad")).lower(),
           "extra": (" y compararlo con el RTO del activo" if V.get("rto") else "") + (" y el monto facturado" if V.get("monto") else "")}
    requerimientos = [{"id": f"RF-{i+1:02d}", "tipo": "RF", "categoria": "Funcional", "descripcion": txt.format(**fmt), "control": ctl}
                      for i, (txt, ctl) in enumerate(C.RF_PATRON[pat])]
    requerimientos.append({"id": "RF-06", "tipo": "RF", "categoria": "Funcional", "descripcion": "Ingresar con usuario y contraseña; el administrador gestiona usuarios y roles (administrador, operador, auditor).", "control": "AC-3"})
    if V.get("vista_equipo"):
        requerimientos.append({"id": "RF-07", "tipo": "RF", "categoria": "Funcional", "descripcion": "Mostrar al cliente, de forma animada, cómo funciona cada componente del equipo (ventiladores, flujo de aire, CPU, GPU, RAM, fuente y almacenamiento).", "control": "SI-10"})
    requerimientos += [
        {"id": "RNF-01", "tipo": "RNF", "categoria": "Seguridad", "descripcion": f"La BD no tiene IP pública y solo acepta el puerto {m['puerto']} desde sg-web-{nn}.", "control": "SC-7"},
        {"id": "RNF-02", "tipo": "RNF", "categoria": "Seguridad", "descripcion": "El acceso administrativo al SO exige llave ED25519 y código TOTP.", "control": "IA-2(1)"},
        {"id": "RNF-03", "tipo": "RNF", "categoria": "Seguridad", "descripcion": f"La app usa app_{nn} con SELECT/INSERT/UPDATE solo sobre ti3062_{nn} (sin DELETE) y credenciales fuera del código.", "control": "AC-6"},
        {"id": "RNF-04", "tipo": "RNF", "categoria": "Disponibilidad", "descripcion": "Respaldo diario cifrado con restauración probada (RPO 24 h, RTO < 2 h).", "control": "CP-9"},
        {"id": "RNF-05", "tipo": "RNF", "categoria": "Rendimiento", "descripcion": "El panel en vivo se actualiza cada 5 s y cada consulta web→bd responde en menos de 200 ms en t3.micro.", "control": "CM-7"},
        {"id": "RNF-06", "tipo": "RNF", "categoria": "Seguridad", "descripcion": "Los cambios en cuentas, sudoers y SSH (auditd) y cada acción en la app (auditoria_app) quedan registrados.", "control": "AU-2"},
        {"id": "RNF-07", "tipo": "RNF", "categoria": "Seguridad", "descripcion": "Todo el tráfico va cifrado: HTTPS hacia el usuario y TLS 1.2/1.3 con certificado verificado entre web y bd.", "control": "SC-8"},
        {"id": "RNF-08", "tipo": "RNF", "categoria": "Seguridad", "descripcion": "La sesión expira a los 15 min de inactividad y la cuenta se bloquea 15 min tras 5 intentos fallidos.", "control": "AC-7"},
    ]
    dependencias = [
        {"id": "D1", "componente": f"{m['nombre']} en bd-{nn}", "descripcion": f"Almacena {P['tabla']}, {H['tabla']}, usuarios_app y auditoria_app", "impacto": "Punto único de falla: requiere respaldo y snapshot"},
        {"id": "D2", "componente": f"VPC-{nn} y tablas de rutas", "descripcion": "Segmentación pública/privada", "impacto": "Define qué es alcanzable desde Internet"},
        {"id": "D6", "componente": "CA propia del proyecto (TLS web→bd)", "descripcion": f"Firma el certificado TLS de bd-{nn}", "impacto": "Si el certificado vence o cambia la IP de bd, la app deja de conectar (verificación estricta)"},
        {"id": "D3", "componente": "Security Groups y firewall de host", "descripcion": "Filtrado en dos capas", "impacto": "Deben ser coherentes o se pierde conectividad"},
        {"id": "D4", "componente": "Sesión de AWS Academy", "descripcion": "El laboratorio se detiene al expirar la sesión", "impacto": f"web-{nn} conserva su IP elástica; tras reiniciar hay que abrir el volumen LUKS de bd-{nn}"},
        {"id": "D5", "componente": "GitHub + Cloudflare Pages", "descripcion": "Publican el sistema de gestión", "impacto": "Disponibilidad del informe ligada a servicios externos"},
    ]
    limitaciones = [
        {"id": "L1", "tipo": "Entorno", "descripcion": "AWS Academy no permite administrar IAM, CloudTrail ni cifrado EBS.", "impacto": "Se compensa con identidad, MFA, LUKS y auditd a nivel de SO"},
        {"id": "L2", "tipo": "Normativa", "descripcion": "Ley 21.719 (protección de datos personales) y Ley 21.663 (Marco de Ciberseguridad, ANCI).", "impacto": "Exige minimizar acceso a datos personales y registrar incidentes"},
        {"id": "L3", "tipo": "Normativa", "descripcion": "Alineación con NIST SP 800-53 Rev. 5.", "impacto": "Cada control debe justificarse con su código y evidencia"},
        {"id": "L4", "tipo": "Técnica", "descripcion": "Instancias t3.micro (2 vCPU, 1 GB RAM) en una sola AZ.", "impacto": "Sin alta disponibilidad real: se documenta como riesgo residual"},
    ]

    aws_costo = "≈ 20,30 (2×t3.micro 15,18 + EBS 1,44 + IPv4 pública 3,65) — verificar"
    alt_costo = ALT_COSTO[p["alt"]["nombre"]]
    proveedores = [
        {"nombre": "AWS", "servicio": "Amazon EC2 t3.micro (Ubuntu 24.04) + VPC con subred pública/privada, IGW y Security Groups",
         "seguridad": "Security Groups con estado, subred privada sin ruta a Internet; (en Academy) sin IAM/CloudTrail: controles a nivel SO",
         "disponibilidad": "SLA EC2 99,5% por instancia; múltiples AZ en us-east-1; snapshots EBS",
         "costo": aws_costo, "fuente": "https://calculator.aws/",
         "beneficios": "Créditos AWS Academy, documentación amplia, experiencia previa del curso",
         "limitaciones": "Permisos restringidos en Academy; sesiones de laboratorio con tiempo limitado",
         "riesgos": "Pérdida de IP pública al reiniciar; recursos detenidos al terminar la sesión"},
        dict(p["alt"], costo=alt_costo),
    ]
    pools["proveedores"] = proveedores[:1] + [dict(a, costo=ALT_COSTO[a["nombre"]]) for a in C.PROVEEDORES_ALT]
    zona, zona_j = p["zona"]
    seleccion = {
        "proveedor": "AWS",
        "justificacion": f"AWS cumple RF-01 a RF-05 con EC2 + {m['nombre']} y permite implementar RNF-01 (subred privada y SG por referencia), RNF-02/RNF-03 (control de identidad en el SO) y RNF-04 (snapshots + respaldo). {p['alt']['nombre']} ofrece capacidades equivalentes, pero el curso dispone de créditos AWS Academy y la topología exigida está definida sobre AWS.",
        "gobierno": "Se alinea con los ejes de Gobierno TI: identidad (usuarios nominativos por rol), acceso (mínimo privilegio y MFA), monitoreo (auditd), continuidad y respaldo (cron + LUKS + snapshots).",
        "zona": zona, "zonaJustificacion": zona_j.replace("NN", nn),
    }
    componentes = [
        {"componente": "Usuarios del SO", "acceso": f"{ua}, {ud}, {uu} vía SSH con llave", "control": "Grupos funcionales, AllowGroups, llaves ED25519", "rol": "Identifica a cada persona (IA-2)"},
        {"componente": "Roles (grupos)", "acceso": f"{g['admin']}_{nn} / {g['dev']}_{nn} / {g['audit']}_{nn}", "control": "sudoers por rol con comandos específicos", "rol": "Separación de funciones (AC-5, AC-6)"},
        {"componente": "Endpoint SSH (22)", "acceso": f"Solo desde IP del administrador a web-{nn}; bd-{nn} solo vía web-{nn}", "control": "SG + firewall de host + TOTP para admin", "rol": "Acceso remoto controlado (AC-17)"},
        {"componente": "Endpoint web (80/443)", "acceso": "Público; HTTP redirige a HTTPS", "control": "TLS, CSP y cabeceras seguras, validación de entradas, CSRF", "rol": "Protege la capa de aplicación (SI-10, SC-8, SC-23)"},
        {"componente": "Usuarios de la aplicación", "acceso": "Administrador / Operador / Auditor", "control": "Contraseña ≥12 con hash, bloqueo tras 5 intentos, sesión de 15 min, permisos por rol", "rol": "Identificación y control de acceso en la app (IA-2, AC-3, AC-7, AC-12)"},
        {"componente": "Registro de auditoría de la app", "acceso": "Solo lectura para el auditor", "control": "auditoria_app con INSERT/SELECT (sin UPDATE/DELETE para la app)", "rol": "Trazabilidad no repudiable (AU-2, AU-9)"},
        {"componente": f"Base de datos ({m['puerto']})", "acceso": f"Solo app_{nn} desde {'10.' + nnip + '.1.10'} con TLS obligatorio", "control": f"sg-bd-{nn} con origen sg-web-{nn}, GRANT mínimo, TLS con certificado verificado", "rol": "Mínimo privilegio y cifrado en tránsito (AC-6, SC-7, SC-8)"},
        {"componente": "API/consola AWS", "acceso": "Cuenta AWS Academy del estudiante", "control": "Credenciales temporales de la sesión del laboratorio", "rol": "Limitación del entorno (L1)"},
    ]
    oblig = OBLIG
    extra = r.sample([c for c in C.CONTROLES if c["codigo"] not in oblig], r.choice([1, 2]))
    reqmap = REQMAP
    controles = []
    for c in [x for x in C.CONTROLES if x["codigo"] in oblig] + C.CONTROLES_APP + extra:
        controles.append({"codigo": c["codigo"], "nombre": c["nombre"], "riesgo": c["riesgo"], "punto": c["punto"].replace("NN", nn),
                          "capa": c["capa"], "req": reqmap.get(c["codigo"], ""), "impacto": "", "estado": "Planificado"})
    r.shuffle(controles)

    fw = p["firewall"]
    sg = [
        {"grupo": f"sg-web-{nn}", "puerto": "80/443", "origen": "0.0.0.0/0", "host": f"{fw}: allow 80,443/tcp", "justificacion": "Publicación de la app del caso (P1)"},
        {"grupo": f"sg-web-{nn}", "puerto": "22", "origen": "IP de administración /32", "host": f"{fw}: 22 solo desde IP admin", "justificacion": "Administración remota restringida (AC-17)"},
        {"grupo": f"sg-bd-{nn}", "puerto": str(m["puerto"]), "origen": f"sg-web-{nn}", "host": f"{fw}: {m['puerto']} solo desde 10.{nnip}.1.10", "justificacion": "BD accesible solo desde la app (SC-7)"},
        {"grupo": f"sg-bd-{nn}", "puerto": "22", "origen": f"sg-web-{nn} (bastión)", "host": f"{fw}: 22 solo desde 10.{nnip}.1.10", "justificacion": "Administración vía bastión"},
    ]
    B = lambda area, conf, cmd, ref, ev: {"fecha": "", "area": area, "configuracion": conf, "comando": cmd, "responsable": nombre, "ref": ref, "evidencia": ev, "descripcion": "", "imagen": ""}
    bitacora = [
        B("Red / VPC", f"VPC-{nn} 10.{nnip}.0.0/16, subredes y IGW-{nn}", "instalador/aws/01-crear-infra.sh", "T04 / SC-7", "Mapa de recursos de la VPC"),
        B("Red / VPC", "Tabla de rutas privada sin salida (tras retirar NAT)", "instalador/aws/02-nat-temporal.sh eliminar", "T06 / SC-7", "rt-privada sin 0.0.0.0/0"),
        B("Security Groups", f"Reglas de sg-web-{nn} y sg-bd-{nn}", "instalador/aws/03-snapshots-y-evidencias.sh evidencias", "T05 / SC-7", "Reglas de entrada de ambos SG"),
        B("Base de datos", f"{m['nombre']} escuchando en 10.{nnip}.2.10 y usuario app_{nn}", "instalador/bd/01-configurar-bd.sh", "T08 / AC-6", "GRANTs del usuario de la app"),
        B("Base de datos", f"TLS obligatorio en {m['nombre']} con certificado firmado por la CA del proyecto (IP 10.{nnip}.2.10)", "instalador/bd/01-configurar-bd.sh", "T08 / SC-8", "Conexión mostrando versión TLS y cifrado"),
        B("Aplicación", f"App {t['nombre_app']} desplegada: lógica fuera del webroot, credenciales en /etc/ti3062/db.ini, HTTPS con redirección", "instalador/web/01-instalar-web.sh", "T07 / IA-5", "Panel en vivo con canal TLS verificado"),
        B("Aplicación", "Usuarios de la app con roles, bloqueo por intentos y sesión de 15 min; primer administrador creado por consola", "instalador/web/01-instalar-web.sh + crear-usuario.php", "T07 / AC-3", "Pantalla de usuarios y auditoría de la app"),
        B("Hardening SO", "Grupos, usuarios y directorios por área", "instalador/comun/01-hardening.sh", "T09 / AC-2", "id de usuarios y permisos de /srv/areas"),
        B("Hardening SO", "sudoers por rol", "/etc/sudoers.d/*-ti3062-*", "T09 / AC-6", "sudo -l de desarrollo y auditoría"),
        B("Hardening SO", "sshd endurecido", "/etc/ssh/sshd_config.d/10-ti3062.conf", "T09 / AC-17", "sshd -T filtrado"),
        B("MFA", f"TOTP obligatorio para {g['admin']}_{nn}", "/etc/pam.d/sshd + Match Group", "T09 / IA-2(1)", "Login pidiendo Verification code"),
        B("Firewall host", f"{fw} coherente con SG", "instalador/comun/evidencias.sh firewall", "T09 / SC-7", f"Estado de {fw}"),
        B("Auditoría", "Reglas auditd sobre sudo, passwd, sudoers y sshd_config", "/etc/audit/rules.d/50-ti3062.rules", "T10 / AU-2", "auditctl -l"),
        B("Cifrado LUKS", "Volumen LUKS2 montado en /respaldos", "instalador/bd/02-luks-respaldos.sh", "T11 / SC-28", "lsblk -f y cryptsetup status"),
        B("Respaldo", f"cron diario ({p['cron']}) hacia /respaldos", "instalador/bd/03-respaldo-cron.sh", "T11 / CP-9", "cron y archivos de respaldo"),
        B("Respaldo", "Restauración probada en base temporal", "instalador/bd/04-probar-restauracion.sh", "T11 / CP-10", "Conteos original vs restaurada"),
        B("Disponibilidad", "Snapshots de los volúmenes de web y bd", "instalador/aws/03-snapshots-y-evidencias.sh snapshots", "T12 / CP-9", "Listado de snapshots"),
    ]
    ca = "/etc/ti3062/bd-ca.pem"
    if m["clave"] == "mariadb":
        dbcli = f"mariadb --ssl-ca={ca} --ssl-verify-server-cert -h 10.{nnip}.2.10 -u app_{nn} -p ti3062_{nn} -e \"SHOW SESSION STATUS LIKE 'Ssl_version'; SELECT COUNT(*) FROM {H['tabla']}\""
        sincifrar = f"mariadb --skip-ssl -h 10.{nnip}.2.10 -u app_{nn} -p ti3062_{nn}"
        borrar = f"mariadb --ssl-ca={ca} --ssl-verify-server-cert -h 10.{nnip}.2.10 -u app_{nn} -p ti3062_{nn} -e 'DELETE FROM auditoria_app'"
    else:
        cs = f"host=10.{nnip}.2.10 dbname=ti3062_{nn} user=app_{nn} sslmode=verify-full sslrootcert={ca}"
        dbcli = f"psql \"{cs}\" -c 'SELECT ssl, version, cipher FROM pg_stat_ssl WHERE pid = pg_backend_pid()' -c 'SELECT COUNT(*) FROM {H['tabla']}'"
        sincifrar = f"psql \"host=10.{nnip}.2.10 dbname=ti3062_{nn} user=app_{nn} sslmode=disable\""
        borrar = f"psql \"{cs}\" -c 'DELETE FROM auditoria_app'"
    Pz = lambda i, o, c, e, ctl: {"id": i, "objetivo": o, "comando": c, "esperado": e, "obtenido": "", "estado": "Pendiente", "control": ctl, "imagen": ""}
    pruebas = [
        Pz("P1", "Acceso a la app desde Internet (80/443)", f"Navegador: http://<IP_PUBLICA_WEB>/ (redirige a HTTPS) ; ingresar, registrar {P['singular']} y {H['singular']} y verlos listados", "App operativa, inserta y lista datos desde la BD", "SC-7"),
        Pz("P2", f"Escaneo de puertos a bd-{nn} desde el exterior", f"nmap -Pn -p 22,{m['puerto']} 10.{nnip}.2.10  (desde el PC) ; aws ec2 describe-instances (sin PublicIpAddress)", "Sin acceso; sin IP pública", "SC-7"),
        Pz("P3", "Conexión web → BD con el usuario de aplicación", f"En web-{nn}: {dbcli} ; repetir desde bd-{nn} con el mismo usuario (debe fallar)", f"Conexión cifrada exitosa solo desde web-{nn}", "AC-6"),
        Pz("P4", f"Salida a Internet desde bd-{nn}", "ping -c 3 8.8.8.8 ; curl -m 5 https://aws.amazon.com", "Falla", "SC-7"),
        Pz("P5", "SSH con contraseña o como root", f"ssh -o PubkeyAuthentication=no -o PreferredAuthentications=password {ud}@<IP_PUBLICA_WEB> ; ssh root@<IP_PUBLICA_WEB>", "Rechazado", "AC-17"),
        Pz("P6", "SSH administrativo sin código TOTP", f"ssh -i ~/.ssh/{ua} {ua}@<IP_PUBLICA_WEB>  (ingresar código incorrecto)", "Rechazado", "IA-2(1)"),
        Pz("P7", "Comando no autorizado en sudoers", f"Como {ud}: sudo cat /etc/shadow ; luego como {uu}: sudo ausearch -k uso_sudo -i | tail", "Denegado y registrado en auditd", "AC-6"),
        Pz("P9", "Cifrado en tránsito web → bd", f"En bd-{nn}: sudo tcpdump -i any -A -c 60 port {m['puerto']} | grep -i '<texto que acabas de registrar>' (registrar algo en la app mientras corre) ; en web-{nn}: {sincifrar} (debe rechazarse)", "No aparece texto legible; la conexión sin TLS es rechazada", "SC-8"),
        Pz("P10", "Bloqueo de la cuenta por intentos fallidos", "En la app: 5 contraseñas incorrectas para un usuario ; intentar con la correcta ; revisar Auditoría (login_fallido, cuenta_bloqueada)", "Cuenta bloqueada 15 min y eventos registrados", "AC-7"),
        Pz("P11", "Control de acceso por rol en la app", f"Ingresar como auditor e intentar registrar un {H['singular']} (o enviar el formulario con curl usando su sesión)", "Acción denegada y registrada como acceso_denegado", "AC-3"),
        Pz("P12", "Validación de entradas (XSS / inyección SQL)", f"Registrar un {P['singular']} con <script>alert(1)</script> y con ' OR '1'='1 en el nombre ; ver el listado y el código fuente", "Se guarda como texto y se muestra escapado; la consulta no se altera", "SI-10"),
        Pz("P13", "Registro de auditoría inmutable", f"En web-{nn}: {borrar}", "Permiso denegado para el usuario de la app", "AU-9"),
        Pz("P8", "Lectura del volumen LUKS cerrado", "sudo bash instalador/bd/02-luks-respaldos.sh cerrar ; sudo strings $(cat /etc/ti3062-luks-dispositivo) | head ; sudo cryptsetup isLuks -v $(cat /etc/ti3062-luks-dispositivo)", "Datos ilegibles", "SC-28"),
    ]
    pruebas.sort(key=lambda x: int(x["id"][1:]))
    cia = [
        {"dimension": "Confidencialidad", "controles": "SC-7 (subred privada + SG), SC-8 (HTTPS y TLS web→bd), AC-3/AC-6 (roles en la app, GRANT mínimo, sudoers), IA-2(1) (TOTP), SC-28 (LUKS)", "verificacion": "P2, P3, P6, P8, P9, P11", "impacto": ""},
        {"dimension": "Integridad", "controles": "SI-10 (validación y consultas preparadas), SC-23 (CSRF y sesión), reglas de negocio en transacciones, AU-2/AU-9 (auditd y auditoria_app inmutable)", "verificacion": "P7, P12, P13", "impacto": ""},
        {"dimension": "Disponibilidad", "controles": "CP-9 (respaldo diario), CP-10 (restauración probada), snapshots EBS, AZ " + zona, "verificacion": "P1, restauración, snapshots", "impacto": ""},
    ]
    riesgos = [dict(x, id=f"R{i+1}") for i, x in enumerate(r.sample(C.RIESGOS_RESIDUALES, r.choice([3, 4])))]
    gobierno = [
        {"eje": "Identidad", "practica": f"Una cuenta nominativa por rol ({ua}, {ud}, {uu}); cuenta ubuntu bloqueada", "evidencia": "Bitácora: grupos y usuarios"},
        {"eje": "Acceso", "practica": "Mínimo privilegio en sudoers, BD y Security Groups; MFA para administración", "evidencia": "P3, P5, P6, P7"},
        {"eje": "Monitoreo", "practica": "auditd con claves por evento y revisión por el rol de auditoría", "evidencia": "auditctl -l, ausearch"},
        {"eje": "Continuidad", "practica": f"AZ {zona} justificada, snapshots y procedimiento de recuperación", "evidencia": "Snapshots y restauración"},
        {"eje": "Respaldo", "practica": f"Respaldo diario cifrado ({p['cron']}) con retención de {p['retencion']} días", "evidencia": "cron + /respaldos"},
    ]
    mejoras = [dict(x, id=f"M{i+1}", evidencia="") for i, x in enumerate(r.sample(C.MEJORAS, r.choice([3, 4])))]

    return {
        "version": 1,
        "meta": {"estudiante": nombre, "nn": nn, "carrera": "Ingeniería en Informática", "sede": "La Serena", "docente": "Daniel Ruz Moreno",
                 "urlSistema": url_sis, "urlRepo": url_repo, "github": github},
        "personal": [
            {"id": "P1", "nombre": nombre, "cargo": "Jefe de proyecto y administrador de infraestructura", "rol": "Administración", "correo": "",
             "responsabilidades": f"VPC-{nn}, Security Groups, instancias, hardening, MFA, cifrado y respaldos"},
            {"id": "P2", "nombre": nombre, "cargo": "Desarrollador de la aplicación", "rol": "Desarrollo", "correo": "",
             "responsabilidades": f"App {t['nombre_app']}, base de datos {m['nombre']}, TLS web→bd y despliegue en web-{nn}"},
            {"id": "P3", "nombre": nombre, "cargo": "Auditor de seguridad", "rol": "Auditoría", "correo": "",
             "responsabilidades": "Requerimientos, controles NIST, auditd y auditoría de la app, pruebas P1–P13 y evaluación final"},
        ],
        "informe": {
            "titulo": "Proyecto Integrador de Seguridad en Infraestructura Cloud y Redes",
            "subtitulo": f"{t['nombre_app']}: {t['titulo']}",
            "asignatura": "TI3062 · Gestión de Seguridad de la Información",
            "mostrarEquipo": "Sí",
            "estado": "Estado al generar: avance {avance}% · {controlesImpl}/{controlesTot} controles implementados · {aprobadas}/{pruebasTot} pruebas aprobadas · {riesgos} riesgos residuales.",
            "incluirIntro": "Sí", "introTitulo": "Introducción",
            "proposito": f"Diseñar, implementar y validar en AWS una solución cloud segura para {t['titulo'].lower()}, que mejore la disponibilidad de acceso aplicando controles NIST SP 800-53 Rev. 5 en las capas de identidad, red, aplicación y proveedor.",
            "alcance": f"Incluye la VPC-{nn} con subred pública y privada, las instancias web-{nn} y bd-{nn}, la aplicación {t['nombre_app']} con usuarios por rol y conexión cifrada a {m['nombre']}, el endurecimiento del sistema operativo (MFA, sudoers, auditd, firewall), el cifrado y respaldo de la base de datos, y la validación con las pruebas P1 a P13. No incluye alta disponibilidad multi-AZ, que se propone como mejora.",
            "escenario": t["contexto"],
            "sec1": "1. Planificación y gestión", "intro1": "",
            "sec2": "2. Problemática, requerimientos, dependencias y limitaciones", "intro2": "",
            "sec3": "3. Alternativas cloud y selección", "intro3": "",
            "sec4": "4. Controles NIST SP 800-53 Rev. 5", "intro4": "",
            "sec5": "5. Implementación", "intro5": "",
            "sec6": "6. Validación", "intro6": "",
            "sec7": "7. Evaluación final", "intro7": "",
            "incluirRef": "Sí", "refTitulo": "Referencias",
            "referencias": [
                "National Institute of Standards and Technology. (2020). Security and Privacy Controls for Information Systems and Organizations (SP 800-53 Rev. 5). https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final",
                "Ley N° 21.663 Marco de Ciberseguridad. (2024). Biblioteca del Congreso Nacional de Chile. https://www.bcn.cl/leychile/navegar?idNorma=1202434",
                "Ley N° 21.719 que regula la protección y el tratamiento de los datos personales. (2024). Biblioteca del Congreso Nacional de Chile. https://www.bcn.cl/leychile",
                "Gobierno de Chile. (2017). Política Nacional de Ciberseguridad 2017–2022. https://www.interior.gob.cl/media/2017/04/politica-nacional-de-ciberseguridad.pdf",
                "CSIRT de Gobierno de Chile. (2023). Guías y recomendaciones de seguridad para infraestructura y servicios tecnológicos. https://www.csirt.gob.cl",
                "Amazon Web Services. (2024). AWS Well-Architected Framework: Security Pillar. https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html",
            ],
            "pie": "TI3062 · {estudiante} · NN {nn} · {sistema}",
        },
        "hitos": hitos, "tareas": tareas,
        "problema": {"titulo": f"{t['nombre_app']}: {t['titulo']}", "contexto": t["contexto"], "actores": t["actores"], "procesos": t["procesos"],
                     "necesidades": ["Disponibilidad del servicio desde Internet", "Protección de datos personales", "Respaldo y recuperación ante fallas", "Trazabilidad de accesos y cambios"],
                     "impacto": "Sin una solución segura los usuarios pierden información, se exponen datos personales y no es posible auditar quién accedió o modificó registros."},
        "caracteristicas": caracteristicas, "requerimientos": requerimientos, "dependencias": dependencias, "limitaciones": limitaciones,
        "proveedores": proveedores, "seleccion": seleccion, "componentes": componentes, "controles": controles,
        "infra": {"vpc": f"VPC-{nn}", "cidr": f"10.{nnip}.0.0/16", "publica": f"10.{nnip}.1.0/24", "privada": f"10.{nnip}.2.0/24",
                  "web": f"web-{nn} (10.{nnip}.1.10)", "bd": f"bd-{nn} (10.{nnip}.2.10)", "motor": f"{m['nombre']} :{m['puerto']}", "appUrl": "http://<IP_PUBLICA_WEB>/"},
        "sg": sg, "bitacora": bitacora, "pruebas": pruebas, "hallazgos": [
            {"id": "HZ-01", "tipo": "Riesgo", "descripcion": "AWS CloudTrail no está disponible en AWS Academy (AccessDeniedException al abrir el servicio): no hay registro centralizado de llamadas a la API, cambios de red/SG ni accesos a la consola.",
             "req": "RNF-06", "control": "AU-2 / AU-6", "impacto": "No se pueden auditar cambios perimetrales hechos desde la consola o CloudShell.",
             "accion": "Control compensatorio en el SO: auditd (sudo, passwd, sudoers, sshd_config), auth.log/journald y revisión de sesiones (last, lastb, who, lastlog). Mejora: habilitar CloudTrail en una cuenta AWS propia."}], "cia": cia, "riesgos": riesgos, "gobierno": gobierno, "mejoras": mejoras,
        "cierre": {"conclusion": "", "aprendizajes": ""},
    }


def esquema_sql(t, motor):
    """4 tablas: usuarios_app → (padre ← hijo) y auditoria_app. Columnas de negocio según el patrón."""
    mdb = motor["clave"] == "mariadb"
    tipo = lambda tp: {"date": "DATE", "number": "DECIMAL(12,2)", "textarea": "VARCHAR(500)"}.get(tp, "VARCHAR(150)")
    nul = lambda tp: "" if tp == "textarea" else " NOT NULL"
    idc = "id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY" if mdb else "id SERIAL PRIMARY KEY"
    idg = "id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY" if mdb else "id BIGSERIAL PRIMARY KEY"
    fkt = "INT UNSIGNED" if mdb else "INTEGER"
    eng = " ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci" if mdb else ""
    ts = "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP"
    tsn = "TIMESTAMP NULL DEFAULT NULL"
    P, H, V, pat = t["padre"], t["hijo"], t.get("vocab", {}), t["patron"]
    est_p = {"inventario": ["stock INT NOT NULL DEFAULT 0", "stock_minimo INT NOT NULL DEFAULT 0", "precio DECIMAL(12,2) NOT NULL DEFAULT 0", "CONSTRAINT ck_%s_stock CHECK (stock >= 0)" % P["tabla"]],
             "prestamos": ["estado_item VARCHAR(20) NOT NULL DEFAULT 'Disponible'"],
             "membresias": ["valor DECIMAL(12,2) NOT NULL DEFAULT 0", "duracion_dias INT NOT NULL DEFAULT 30"]}.get(pat, [])
    est_h = {"inventario": ["tipo VARCHAR(40) NOT NULL", "cantidad INT NOT NULL", "monto DECIMAL(14,2) NOT NULL DEFAULT 0", "CONSTRAINT ck_%s_cant CHECK (cantidad > 0)" % H["tabla"]],
             "reservas": ["fecha DATE NOT NULL", ("bloque VARCHAR(20) NOT NULL" if V.get("modo") == "bloque" else "fecha_fin DATE NOT NULL"), "estado VARCHAR(20) NOT NULL DEFAULT 'Confirmada'"],
             "prestamos": ["fecha_prestamo DATE NOT NULL", "fecha_compromiso DATE NOT NULL", "fecha_devolucion DATE NULL", "estado VARCHAR(20) NOT NULL DEFAULT 'Activo'"],
             "ordenes": ["nivel VARCHAR(30) NOT NULL", "estado VARCHAR(40) NOT NULL", "monto DECIMAL(14,2) NULL", f"actualizado_en {tsn}", f"cerrado_en {tsn}"],
             "membresias": ["fecha_inicio DATE NOT NULL", "fecha_fin DATE NOT NULL", "estado VARCHAR(20) NOT NULL DEFAULT 'Activa'"]}[pat]
    cols_p = [f"{k} {tipo(tp)}{nul(tp)}" for k, tp, _ in P["campos"]] + est_p
    cols_h = [f"{k} {tipo(tp)}{nul(tp)}" for k, tp, _ in H["campos"]] + est_h
    j = ",\n  ".join
    idx_extra = {"reservas": f"CREATE INDEX IF NOT EXISTS idx_{H['tabla']}_agenda ON {H['tabla']} ({H['fk']}, fecha, estado);",
                 "prestamos": f"CREATE INDEX IF NOT EXISTS idx_{H['tabla']}_estado ON {H['tabla']} (estado, fecha_compromiso);",
                 "ordenes": f"CREATE INDEX IF NOT EXISTS idx_{H['tabla']}_estado ON {H['tabla']} (estado, nivel);",
                 "membresias": f"CREATE INDEX IF NOT EXISTS idx_{H['tabla']}_vigencia ON {H['tabla']} (estado, fecha_fin);",
                 "inventario": f"CREATE INDEX IF NOT EXISTS idx_{H['tabla']}_tipo ON {H['tabla']} (tipo, creado_en);"}[pat]
    return f"""-- Esquema {t['nombre_app']} ({motor['nombre']}) — patrón {pat}
-- 4 tablas relacionadas: usuarios_app → {P['tabla']} ← {H['tabla']} (y {H['tabla']} → usuarios_app), más auditoria_app.
CREATE TABLE IF NOT EXISTS usuarios_app (
  {idc},
  usuario VARCHAR(40) NOT NULL UNIQUE,
  nombre VARCHAR(100) NOT NULL,
  hash VARCHAR(255) NOT NULL,
  rol VARCHAR(20) NOT NULL,
  activo SMALLINT NOT NULL DEFAULT 1,
  intentos INT NOT NULL DEFAULT 0,
  bloqueado_hasta {tsn},
  ultimo_acceso {tsn},
  cambio_clave {tsn},
  creado_en {ts},
  CONSTRAINT ck_usuarios_rol CHECK (rol IN ('admin', 'operador', 'auditor'))
){eng};

CREATE TABLE IF NOT EXISTS {P['tabla']} (
  {idc},
  {j(cols_p)},
  activo SMALLINT NOT NULL DEFAULT 1,
  creado_en {ts}
){eng};

CREATE TABLE IF NOT EXISTS {H['tabla']} (
  {idc},
  {H['fk']} {fkt} NOT NULL,
  {j(cols_h)},
  usuario_id {fkt} NULL,
  creado_en {ts},
  CONSTRAINT fk_{H['tabla']}_{P['tabla']} FOREIGN KEY ({H['fk']}) REFERENCES {P['tabla']}(id) ON DELETE RESTRICT,
  CONSTRAINT fk_{H['tabla']}_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios_app(id) ON DELETE RESTRICT
){eng};

CREATE TABLE IF NOT EXISTS auditoria_app (
  {idg},
  fecha {ts},
  usuario VARCHAR(40) NOT NULL,
  accion VARCHAR(40) NOT NULL,
  entidad VARCHAR(40) NOT NULL,
  detalle VARCHAR(500) NOT NULL DEFAULT '',
  ip VARCHAR(45) NOT NULL DEFAULT ''
){eng};

CREATE INDEX IF NOT EXISTS idx_{H['tabla']}_{H['fk']} ON {H['tabla']} ({H['fk']});
{idx_extra}
CREATE INDEX IF NOT EXISTS idx_auditoria_fecha ON auditoria_app (fecha);
"""


def construir_diccionario(p, nn, datos, pools):
    """Diccionario adaptado a la plantilla: todos los controles y la información base, con los datos del estudiante."""
    t, m, g = p["tema"], p["motor"], p["grupos"]
    nnip = str(int(nn))
    val = {"NN": nn, "NNIP": nnip, "APP": t["nombre_app"], "MOTOR": m["nombre"], "PUERTO": m["puerto"],
           "WEB_IP": f"10.{nnip}.1.10", "BD_IP": f"10.{nnip}.2.10", "TABLA_P": t["padre"]["tabla"], "TABLA_H": t["hijo"]["tabla"],
           "U_ADMIN": f"{g['u_admin']}{nn}", "U_DEV": f"{g['u_dev']}{nn}", "U_AUDIT": f"{g['u_audit']}{nn}",
           "G_ADMIN": f"{g['admin']}_{nn}", "G_DEV": f"{g['dev']}_{nn}", "G_AUDIT": f"{g['audit']}_{nn}",
           "FIREWALL": p["firewall"], "ZONA": p["zona"][0], "ALT": p["alt"]["nombre"], "CRON": p["cron"], "RETENCION": p["retencion"],
           "TITULO": t["titulo"][0].lower() + t["titulo"][1:], "CONTEXTO": t["contexto"]}
    R = lambda x: D.rellenar(x, val)
    obligatorios = OBLIG + [c["codigo"] for c in C.CONTROLES_APP]
    relevantes = D.RELEVANTES.get(t["patron"], [])
    controles = []
    for c in D.todos_los_controles():
        fam, desc, ev, pr = D.DETALLE[c["codigo"]]
        controles.append(R({"codigo": c["codigo"], "nombre": c["nombre"], "familia": fam, "descripcion": desc, "riesgo": c["riesgo"],
                            "punto": c["punto"].replace("NN", nn), "capa": c["capa"], "req": REQMAP.get(c["codigo"], ""), "evidencia": ev,
                            "prueba": pr, "obligatorio": c["codigo"] in obligatorios, "relevante": c["codigo"] in relevantes}))
    controles.sort(key=lambda c: (not c["obligatorio"], not c["relevante"], c["codigo"]))
    fila_control = lambda c: {"codigo": c["codigo"], "nombre": c["nombre"], "riesgo": c["riesgo"], "punto": c["punto"], "capa": c["capa"],
                              "req": c["req"], "impacto": "", "estado": "Planificado"}
    rnf_extra = [
        {"id": "RNF-09", "tipo": "RNF", "categoria": "Seguridad", "descripcion": "Los relojes de web y bd están sincronizados y los registros se guardan en UTC.", "control": "AU-8"},
        {"id": "RNF-10", "tipo": "RNF", "categoria": "Seguridad", "descripcion": "Los paquetes del sistema se mantienen actualizados con parches de seguridad.", "control": "SI-2"},
        {"id": "RNF-11", "tipo": "RNF", "categoria": "Disponibilidad", "descripcion": f"Los registros y respaldos se conservan al menos {p['retencion']} días.", "control": "AU-11"},
        {"id": "RNF-12", "tipo": "RNF", "categoria": "Disponibilidad", "descripcion": "El servicio se puede reconstruir desde una AMI endurecida en menos de 1 hora.", "control": "CP-10"},
    ]
    hallazgos = datos["hallazgos"] + [dict(R(h), id=f"HZ-{i + 2:02d}") for i, h in enumerate(D.HALLAZGOS[1:])]
    bloques = {
        "hitos": datos["hitos"], "tareas": datos["tareas"], "personal": datos["personal"],
        "caracteristicas": pools.get("caracteristicas", datos["caracteristicas"]),
        "requerimientos": datos["requerimientos"] + rnf_extra,
        "dependencias": datos["dependencias"], "limitaciones": datos["limitaciones"],
        "proveedores": pools.get("proveedores", datos["proveedores"]), "componentes": datos["componentes"],
        "controles": [fila_control(c) for c in controles], "sg": datos["sg"], "bitacora": datos["bitacora"], "pruebas": datos["pruebas"],
        "hallazgos": hallazgos, "cia": datos["cia"],
        "riesgos": [dict(x, id=f"R{i + 1}") for i, x in enumerate(C.RIESGOS_RESIDUALES)],
        "gobierno": datos["gobierno"],
        "mejoras": [dict(x, id=f"M{i + 1}", evidencia="") for i, x in enumerate(C.MEJORAS)],
    }
    requisitos = [dict(q, ids=obligatorios) if q.get("ids") == "obligatorios" else q for q in D.REQUISITOS]
    return {
        "version": 1, "nn": nn, "app": t["nombre_app"], "patron": t["patron"],
        "controles": controles, "obligatorios": obligatorios, "relevantes": relevantes,
        "bloques": bloques, "claves": D.CLAVES,
        "textos": R(D.TEXTOS),
        "listas": {"problema.actores": t["actores"], "problema.procesos": t["procesos"], "problema.necesidades": datos["problema"]["necesidades"],
                   "informe.referencias": datos["informe"]["referencias"]},
        "requisitos": requisitos,
        "glosario": [{"termino": a, "definicion": b} for a, b in D.GLOSARIO],
    }


# ------------------------------------------------------------------ generación
def generar(nn, nombre, github, salida, semilla="", tema=None, motor=None, inicio=None, usados=None, forzar=False, firewall=None):
    nn = f"{int(nn):02d}"
    if not 1 <= int(nn) <= 99:
        sys.exit("NN debe estar entre 01 y 99")
    p = elegir_perfil(nn, nombre, github, semilla, tema, motor, usados, firewall)
    t, m, g, pal = p["tema"], p["motor"], p["grupos"], p["paleta"]
    inicio = inicio or dt.date.today()
    destino = (Path(salida) / f"ti3062-{nn}").resolve()
    if os.name == "nt" and not str(destino).startswith("\\\\?\\"):
        destino = Path("\\\\?\\" + str(destino))  # rutas largas en Windows
    if destino.exists():
        if not forzar:
            sys.exit(f"{destino} ya existe (usa --forzar para regenerarlo)")
        shutil.rmtree(destino)

    iniciales = "".join(w[0] for w in p["nombre_sistema"].split()[:2]).upper()
    ctx = {
        "NN": nn, "NNIP": str(int(nn)), "ESTUDIANTE": nombre, "GITHUB": github, "APP_NAME": p["nombre_sistema"], "INICIALES": iniciales,
        "FUENTE": p["fuente"][0], "FUENTE_URL": p["fuente"][1], "LAYOUT": p["layout"], "TARJETA": p["tarjeta"], "RADIO": p["radio"],
        "GRAFICO": p["grafico"], "PDF_ESTILO": p["pdf"], "RGB": ", ".join(map(str, pal["rgb"])), "PALETA": pal["nombre"],
        "PRIMARIO": pal["primario"], "ACENTO": pal["acento"], "FONDO": pal["fondo"], "SUPERFICIE": pal["superficie"], "TEXTO": pal["texto"],
        "DARK_FONDO": pal["dark_fondo"], "DARK_SUPERFICIE": pal["dark_superficie"], "DARK_TEXTO": pal["dark_texto"],
        "APP_CASO": t["nombre_app"], "VARIANTE_APP": p["variante_app"], "TABLA_PADRE": t["padre"]["tabla"], "TABLA_HIJO": t["hijo"]["tabla"],
        "ZONA": p["zona"][0], "TIPO_INSTANCIA": "t3.micro", "MOTOR": m["clave"], "MOTOR_NOMBRE": m["nombre"], "DBPORT": m["puerto"],
        "PAQUETE_BD": m["paquete"], "PHP_EXT": m["php"], "DSN": m["dsn"], "FIREWALL": p["firewall"],
        "G_ADMIN": f"{g['admin']}_{nn}", "G_DEV": f"{g['dev']}_{nn}", "G_AUDIT": f"{g['audit']}_{nn}",
        "U_ADMIN": f"{g['u_admin']}{nn}", "U_DEV": f"{g['u_dev']}{nn}", "U_AUDIT": f"{g['u_audit']}{nn}",
        "CRON": p["cron"], "RETENCION": p["retencion"], "ALT": p["alt"]["nombre"], "TEMA_TITULO": t["titulo"],
        "FECHA": dt.date.today().isoformat(),
    }

    # Copiar/renderizar plantillas
    mapa = {"sistema": ".", "app-caso": "app-caso", "instalador": "instalador"}
    for carpeta, dest in mapa.items():
        for f in (PLANT / carpeta).rglob("*"):
            if f.is_dir():
                continue
            rel = f.relative_to(PLANT / carpeta)
            out = destino / dest / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(render(f.read_text(encoding="utf-8"), ctx, str(f)), encoding="utf-8", newline="\n")
    for doc in ("README.md", "PASO-A-PASO.md"):
        (destino / doc).write_text(render((PLANT / doc).read_text(encoding="utf-8"), ctx, doc), encoding="utf-8", newline="\n")

    pools = {}
    datos = construir_datos(p, nn, nombre, github, inicio, pools)
    (destino / "data").mkdir(exist_ok=True)
    (destino / "data" / f"diccionario-{nn}.json").write_text(json.dumps(construir_diccionario(p, nn, datos, pools), ensure_ascii=False, indent=1), encoding="utf-8")
    marcar_borradores(datos)   # todo lo precargado queda como borrador hasta que el estudiante lo revise
    (destino / "data" / f"proyecto-{nn}.json").write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")

    tema_php = {"nombre_app": t["nombre_app"], "titulo": t["titulo"], "patron": t["patron"], "vocab": t.get("vocab", {}),
                "padre": {k: t["padre"][k] for k in ("tabla", "titulo", "singular")} | {"campos": [list(c) for c in t["padre"]["campos"]]},
                "hijo": {k: t["hijo"][k] for k in ("tabla", "titulo", "singular", "fk")} | {"campos": [list(c) for c in t["hijo"]["campos"]]}}
    (destino / "app-caso" / "privado" / "config_tema.php").write_text(
        "<?php\n// Estructura (no datos) de la app del caso. Generado para NN " + nn + "\n$TEMA = " + php_valor(tema_php) + ";\n", encoding="utf-8", newline="\n")
    (destino / "instalador" / "bd" / "esquema.sql").write_text(esquema_sql(t, m), encoding="utf-8", newline="\n")
    (destino / "instalador" / "llaves").mkdir(exist_ok=True)
    (destino / "instalador" / "llaves" / "LEEME.txt").write_text(
        f"Copia aquí SOLO las llaves PÚBLICAS: {ctx['U_ADMIN']}.pub, {ctx['U_DEV']}.pub, {ctx['U_AUDIT']}.pub\n"
        "Nunca subas llaves privadas al repositorio.\n", encoding="utf-8")
    (destino / ".gitignore").write_text(
        "# Nunca versionar secretos ni configuraciones locales (ver instalador/verificar-secretos.sh)\n"
        "instalador/aws/*.pem\ninstalador/aws/infra-*.env\n*.key\n*.pem\n*.ppk\nid_ed25519*\n!instalador/llaves/*.pub\n"
        ".google_authenticator\ndb.ini\n*.ini.local\n.ti3062-*\n*.b64\nevidencia-*.json\n.env\n", encoding="utf-8")
    (destino / ".gitattributes").write_text("* text=auto eol=lf\n*.png binary\n*.jpg binary\n*.pdf binary\n", encoding="utf-8")
    (destino / ".githooks").mkdir(exist_ok=True)
    gancho = destino / ".githooks" / "pre-push"
    gancho.write_text((PLANT / "githooks" / "pre-push").read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    try:
        os.chmod(gancho, 0o755)
    except OSError:
        pass
    (destino / "_headers").write_text("/*\n  X-Content-Type-Options: nosniff\n  X-Frame-Options: DENY\n  Referrer-Policy: strict-origin-when-cross-origin\n", encoding="utf-8")

    resumen = {"nn": nn, "estudiante": nombre, "tema": t["clave"], "app": t["nombre_app"], "sistema": p["nombre_sistema"], "paleta": pal["nombre"],
               "fuente": p["fuente"][0], "layout": p["layout"], "tarjeta": p["tarjeta"], "grafico": p["grafico"], "pdf": p["pdf"],
               "motor": m["clave"], "firewall": p["firewall"], "zona": p["zona"][0], "alternativo": p["alt"]["nombre"],
               "grupos": [ctx["G_ADMIN"], ctx["G_DEV"], ctx["G_AUDIT"]], "cron": p["cron"]}
    (destino / "instalador" / "perfil-variantes.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    escribir_manifiesto(destino / "instalador")
    return destino, resumen


def marcar_borradores(datos):
    """Marca como borrador (_base) cada fila y campo de texto precargado; el sistema lo quita cuando el estudiante lo edita."""
    for k, v in datos.items():
        if isinstance(v, list) and k not in ("personal",):
            for fila in v:
                if isinstance(fila, dict):
                    fila["_base"] = True
    datos["_base_obj"] = {
        "problema": [c for c in ("contexto", "actores", "procesos", "necesidades", "impacto") if datos.get("problema", {}).get(c)],
        "seleccion": [c for c in ("justificacion", "gobierno", "zonaJustificacion") if datos.get("seleccion", {}).get(c)],
        "informe": [c for c in ("proposito", "alcance", "escenario") if datos.get("informe", {}).get(c)],
    }


def escribir_manifiesto(instalador):
    """SHA-256 de cada script y del esquema generados: revisar-instalador.sh detecta cambios no esperados."""
    archivos = sorted(f for f in instalador.rglob("*") if f.is_file() and (f.suffix in (".sh", ".sql")))
    lineas = [f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.relative_to(instalador).as_posix()}" for f in archivos]
    (instalador / "MANIFIESTO.sha256").write_text("\n".join(lineas) + "\n", encoding="utf-8", newline="\n")


def main():
    ap = argparse.ArgumentParser(description="Generador del Proyecto Integrador TI3062")
    ap.add_argument("--nn"); ap.add_argument("--nombre"); ap.add_argument("--github")
    ap.add_argument("--tema"); ap.add_argument("--motor", choices=["mariadb", "postgresql"])
    ap.add_argument("--firewall", choices=["ufw", "nftables"])
    ap.add_argument("--semilla", default="", help="Cambia la combinación de variantes")
    ap.add_argument("--inicio", help="Fecha de inicio del cronograma AAAA-MM-DD (por defecto hoy)")
    ap.add_argument("--salida", default=str(BASE / "salida"))
    ap.add_argument("--lote", help="CSV con columnas nn,nombre,github[,tema][,motor]")
    ap.add_argument("--forzar", action="store_true")
    ap.add_argument("--listar-temas", action="store_true")
    a = ap.parse_args()
    if a.listar_temas:
        for t in C.TEMAS:
            print(f"{t['clave']:12} {t['nombre_app']:16} {t['titulo']}  [{t['padre']['tabla']} → {t['hijo']['tabla']}]")
        return
    inicio = dt.date.fromisoformat(a.inicio) if a.inicio else None
    filas = []
    if a.lote:
        with open(a.lote, encoding="utf-8-sig", newline="") as fh:
            filas = list(csv.DictReader(fh))
    elif a.nn and a.nombre and a.github:
        filas = [{"nn": a.nn, "nombre": a.nombre, "github": a.github, "tema": a.tema or "", "motor": a.motor or "", "firewall": a.firewall or ""}]
    else:
        ap.error("Indica --nn --nombre --github, o --lote archivo.csv")
    usados = set()
    for f in filas:
        d, res = generar(f["nn"], f["nombre"].strip(), f["github"].strip(), a.salida, a.semilla, (f.get("tema") or None), (f.get("motor") or None),
                         inicio, usados, a.forzar, (f.get("firewall") or a.firewall or None))
        usados.add(res["tema"])
        if len(usados) >= len(C.TEMAS):
            usados.clear()
        print(f"✔ {str(d).replace(chr(92) * 2 + '?' + chr(92), '')}  ·{res['app']} ({res['tema']}) · {res['sistema']} · {res['paleta']}/{res['fuente']}/{res['layout']} · {res['motor']} · {res['firewall']} · {res['zona']}")


if __name__ == "__main__":
    main()
