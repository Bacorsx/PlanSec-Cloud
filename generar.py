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
def elegir_perfil(nn, nombre, github, semilla="", tema=None, motor=None, usados=None):
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
    return {
        "rng": r, "tema": t, "motor": m,
        "paleta": r.choice(C.PALETAS), "fuente": r.choice(C.FUENTES), "layout": r.choice(C.LAYOUTS),
        "tarjeta": tarjeta, "radio": {"redondeada": "14px", "recta": "2px", "sombra": "8px", "borde": "6px"}[tarjeta],
        "grafico": r.choice(C.ESTILOS_GRAFICO), "pdf": r.choice(C.ESTILOS_PDF),
        "nombre_sistema": r.choice(C.NOMBRES_SISTEMA), "grupos": r.choice(C.NOMBRES_GRUPOS),
        "firewall": r.choice(C.FIREWALLS), "zona": r.choice(C.ZONAS), "alt": r.choice(C.PROVEEDORES_ALT),
        "variante_app": r.choice("abc"), "cron": f"{r.randint(0, 59)} {r.randint(1, 4)} * * *",
        "retencion": r.choice([7, 10, 14]),
    }


# ------------------------------------------------------------------ datos del proyecto
def construir_datos(p, nn, nombre, github, inicio):
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
        {"id": "H3", "nombre": "Validación y cierre", "fecha": d(19), "criterio": "Pruebas P1–P8, hallazgos, análisis CIA, riesgos y PDF generado"},
    ]
    resp = lambda rol: f"{nombre} ({rol})"
    tareas_base = [
        ("Levantar problemática, actores y requerimientos RF/RNF", "H1", "Auditoría", 0, 2, ""),
        ("Comparar AWS vs " + p["alt"]["nombre"] + " con calculadoras oficiales", "H1", "Administración", 1, 3, "T01"),
        ("Seleccionar controles NIST y mapear a requerimientos", "H1", "Auditoría", 3, 5, "T01"),
        ("Crear VPC-%s, subredes, IGW y tablas de rutas" % nn, "H2", "Administración", 5, 6, "T02"),
        ("Configurar sg-web-%s y sg-bd-%s con mínimo privilegio" % (nn, nn), "H2", "Administración", 6, 6, "T04"),
        ("Lanzar web-%s y bd-%s; instalar paquetes con NAT temporal y retirarla" % (nn, nn), "H2", "Administración", 6, 7, "T05"),
        (f"Desarrollar app {t['nombre_app']} ({P['tabla']}/{H['tabla']}) y desplegar en web-{nn}", "H2", "Desarrollo", 5, 9, "T06"),
        (f"Configurar {m['nombre']} y usuario app_{nn} de mínimo privilegio", "H2", "Desarrollo", 7, 8, "T06"),
        ("Endurecer SO: grupos, sudoers, SSH, TOTP y firewall de host", "H2", "Administración", 8, 11, "T06"),
        ("Configurar auditd y revisar registros", "H2", "Auditoría", 10, 11, "T09"),
        ("Volumen LUKS /respaldos, cron de respaldo y restauración probada", "H2", "Administración", 11, 12, "T08"),
        ("Snapshots de volúmenes y justificación de AZ", "H2", "Administración", 12, 13, "T11"),
        ("Ejecutar pruebas P1–P8 y registrar hallazgos", "H3", "Auditoría", 14, 16, "T12"),
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
    sel = r.sample(caract_pool, r.choice([4, 5]))
    caracteristicas = [{"id": f"C{i+1}", "descripcion": a, "diseno": b} for i, (a, b) in enumerate(sel)]

    requerimientos = [
        {"id": "RF-01", "tipo": "RF", "categoria": "Funcional", "descripcion": f"Registrar {P['singular']} mediante un formulario que inserta en la tabla {P['tabla']}.", "control": "SI-10"},
        {"id": "RF-02", "tipo": "RF", "categoria": "Funcional", "descripcion": f"Registrar {H['singular']} asociado a un {P['singular']} existente (clave foránea {H['fk']}).", "control": "SI-10"},
        {"id": "RF-03", "tipo": "RF", "categoria": "Funcional", "descripcion": f"Listar {H['titulo'].lower()} con su {P['singular']} obtenidos desde la base de datos.", "control": "AC-3"},
        {"id": "RF-04", "tipo": "RF", "categoria": "Funcional", "descripcion": f"Listar {P['titulo'].lower()} con la cantidad de {H['titulo'].lower()} asociados.", "control": "AC-3"},
        {"id": "RF-05", "tipo": "RF", "categoria": "Funcional", "descripcion": "Validar tipos y valores permitidos antes de insertar, informando errores al usuario.", "control": "SI-10"},
        {"id": "RNF-01", "tipo": "RNF", "categoria": "Seguridad", "descripcion": f"La BD no tiene IP pública y solo acepta el puerto {m['puerto']} desde sg-web-{nn}.", "control": "SC-7"},
        {"id": "RNF-02", "tipo": "RNF", "categoria": "Seguridad", "descripcion": "El acceso administrativo exige llave ED25519 y código TOTP.", "control": "IA-2(1)"},
        {"id": "RNF-03", "tipo": "RNF", "categoria": "Seguridad", "descripcion": f"La app usa el usuario app_{nn} con privilegios solo sobre ti3062_{nn} y credenciales fuera del código.", "control": "AC-6"},
        {"id": "RNF-04", "tipo": "RNF", "categoria": "Disponibilidad", "descripcion": "Respaldo diario cifrado con restauración probada (RPO 24 h, RTO < 2 h).", "control": "CP-9"},
        {"id": "RNF-05", "tipo": "RNF", "categoria": "Rendimiento", "descripcion": "El listado responde en menos de 2 s con hasta 200 registros en t3.micro.", "control": "CM-7"},
        {"id": "RNF-06", "tipo": "RNF", "categoria": "Seguridad", "descripcion": "Los cambios en cuentas, sudoers y SSH quedan registrados por auditd.", "control": "AU-2"},
    ]
    dependencias = [
        {"id": "D1", "componente": f"{m['nombre']} en bd-{nn}", "descripcion": f"Almacena {P['tabla']} y {H['tabla']}", "impacto": "Punto único de falla: requiere respaldo y snapshot"},
        {"id": "D2", "componente": f"VPC-{nn} y tablas de rutas", "descripcion": "Segmentación pública/privada", "impacto": "Define qué es alcanzable desde Internet"},
        {"id": "D3", "componente": "Security Groups y firewall de host", "descripcion": "Filtrado en dos capas", "impacto": "Deben ser coherentes o se pierde conectividad"},
        {"id": "D4", "componente": "Sesión de AWS Academy", "descripcion": "El laboratorio se detiene al expirar la sesión", "impacto": "La IP pública cambia al reiniciar: actualizar README y pruebas"},
        {"id": "D5", "componente": "GitHub + Cloudflare Pages", "descripcion": "Publican el sistema de gestión", "impacto": "Disponibilidad del informe ligada a servicios externos"},
    ]
    limitaciones = [
        {"id": "L1", "tipo": "Entorno", "descripcion": "AWS Academy no permite administrar IAM, CloudTrail ni cifrado EBS.", "impacto": "Se compensa con identidad, MFA, LUKS y auditd a nivel de SO"},
        {"id": "L2", "tipo": "Normativa", "descripcion": "Ley 21.719 (protección de datos personales) y Ley 21.663 (Marco de Ciberseguridad, ANCI).", "impacto": "Exige minimizar acceso a datos personales y registrar incidentes"},
        {"id": "L3", "tipo": "Normativa", "descripcion": "Alineación con NIST SP 800-53 Rev. 5.", "impacto": "Cada control debe justificarse con su código y evidencia"},
        {"id": "L4", "tipo": "Técnica", "descripcion": "Instancias t3.micro (2 vCPU, 1 GB RAM) en una sola AZ.", "impacto": "Sin alta disponibilidad real: se documenta como riesgo residual"},
    ]

    aws_costo = "≈ 20,30 (2×t3.micro 15,18 + EBS 1,44 + IPv4 pública 3,65) — verificar"
    alt_costo = {"Microsoft Azure": "≈ 19,50 (2×B1s + discos + IP pública) — verificar",
                 "Google Cloud": "≈ 16,00 (2×e2-micro + discos + IP externa) — verificar",
                 "Oracle Cloud (OCI)": "≈ 0 en Always Free / ≈ 12 de pago — verificar"}[p["alt"]["nombre"]]
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
        {"componente": "Endpoint web (80/443)", "acceso": "Público", "control": "Validación de entradas, CSRF, cabeceras seguras, TLS", "rol": "Protege la capa de aplicación (SI-10, SC-8)"},
        {"componente": f"Base de datos ({m['puerto']})", "acceso": f"Solo app_{nn} desde {'10.' + nnip + '.1.10'}", "control": f"sg-bd-{nn} con origen sg-web-{nn}, GRANT mínimo", "rol": "Mínimo privilegio en datos (AC-6, SC-7)"},
        {"componente": "API/consola AWS", "acceso": "Cuenta AWS Academy del estudiante", "control": "Credenciales temporales de la sesión del laboratorio", "rol": "Limitación del entorno (L1)"},
    ]
    oblig = ["SC-7", "AC-6", "IA-2(1)", "SC-28", "AU-2", "CP-9"]
    extra = r.sample([c for c in C.CONTROLES if c["codigo"] not in oblig], r.choice([1, 2]))
    reqmap = {"SC-7": "RNF-01", "IA-2(1)": "RNF-02", "AC-6": "RNF-03", "CP-9": "RNF-04", "CP-10": "RNF-04", "CM-7": "RNF-05", "AU-2": "RNF-06", "AU-6": "RNF-06", "SC-28": "RNF-04", "IA-5": "RNF-03", "AC-17": "RNF-02", "AC-12": "RNF-02"}
    controles = []
    for c in [x for x in C.CONTROLES if x["codigo"] in oblig] + extra:
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
        B("Aplicación", f"App {t['nombre_app']} desplegada con credenciales en /etc/ti3062/db.ini", "instalador/web/01-instalar-web.sh", "T07 / IA-5", "Formulario y listado funcionando"),
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
    dbcli = f"mariadb -h 10.{nnip}.2.10 -u app_{nn} -p ti3062_{nn} -e 'SELECT COUNT(*) FROM {H['tabla']}'" if m["clave"] == "mariadb" else f"psql -h 10.{nnip}.2.10 -U app_{nn} -d ti3062_{nn} -c 'SELECT COUNT(*) FROM {H['tabla']}'"
    Pz = lambda i, o, c, e, ctl: {"id": i, "objetivo": o, "comando": c, "esperado": e, "obtenido": "", "estado": "Pendiente", "control": ctl, "imagen": ""}
    pruebas = [
        Pz("P1", "Acceso a la app desde Internet (80/443)", "Navegador: http://<IP_PUBLICA_WEB>/ y https://<IP_PUBLICA_WEB>/ ; insertar un registro y verlo listado", "App operativa, inserta y lista datos", "SC-7"),
        Pz("P2", f"Escaneo de puertos a bd-{nn} desde el exterior", f"nmap -Pn -p 22,{m['puerto']} 10.{nnip}.2.10  (desde el PC) ; aws ec2 describe-instances (sin PublicIpAddress)", "Sin acceso; sin IP pública", "SC-7"),
        Pz("P3", "Conexión web → BD con el usuario de aplicación", f"En web-{nn}: {dbcli} ; repetir desde bd-{nn} con el mismo usuario (debe fallar)", f"Conexión exitosa solo desde web-{nn}", "AC-6"),
        Pz("P4", f"Salida a Internet desde bd-{nn}", "ping -c 3 8.8.8.8 ; curl -m 5 https://aws.amazon.com", "Falla", "SC-7"),
        Pz("P5", "SSH con contraseña o como root", f"ssh -o PubkeyAuthentication=no -o PreferredAuthentications=password {ud}@<IP_PUBLICA_WEB> ; ssh root@<IP_PUBLICA_WEB>", "Rechazado", "AC-17"),
        Pz("P6", "SSH administrativo sin código TOTP", f"ssh -i ~/.ssh/{ua} {ua}@<IP_PUBLICA_WEB>  (ingresar código incorrecto)", "Rechazado", "IA-2(1)"),
        Pz("P7", "Comando no autorizado en sudoers", f"Como {ud}: sudo cat /etc/shadow ; luego como {uu}: sudo ausearch -k uso_sudo -i | tail", "Denegado y registrado en auditd", "AC-6"),
        Pz("P8", "Lectura del volumen LUKS cerrado", "sudo bash instalador/bd/02-luks-respaldos.sh cerrar ; sudo strings $(cat /etc/ti3062-luks-dispositivo) | head ; sudo cryptsetup isLuks -v $(cat /etc/ti3062-luks-dispositivo)", "Datos ilegibles", "SC-28"),
    ]
    cia = [
        {"dimension": "Confidencialidad", "controles": "SC-7 (subred privada + SG), AC-6 (GRANT mínimo, sudoers), IA-2(1) (TOTP), SC-28 (LUKS)", "verificacion": "P2, P3, P6, P8", "impacto": ""},
        {"dimension": "Integridad", "controles": "AU-2 (auditd sobre archivos críticos), AC-6 (sin DROP/ALTER para la app), validación de entradas (SI-10)", "verificacion": "P7, P3", "impacto": ""},
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
        "hitos": hitos, "tareas": tareas,
        "problema": {"titulo": f"{t['nombre_app']}: {t['titulo']}", "contexto": t["contexto"], "actores": t["actores"], "procesos": t["procesos"],
                     "necesidades": ["Disponibilidad del servicio desde Internet", "Protección de datos personales", "Respaldo y recuperación ante fallas", "Trazabilidad de accesos y cambios"],
                     "impacto": "Sin una solución segura los usuarios pierden información, se exponen datos personales y no es posible auditar quién accedió o modificó registros."},
        "caracteristicas": caracteristicas, "requerimientos": requerimientos, "dependencias": dependencias, "limitaciones": limitaciones,
        "proveedores": proveedores, "seleccion": seleccion, "componentes": componentes, "controles": controles,
        "infra": {"vpc": f"VPC-{nn}", "cidr": f"10.{nnip}.0.0/16", "publica": f"10.{nnip}.1.0/24", "privada": f"10.{nnip}.2.0/24",
                  "web": f"web-{nn} (10.{nnip}.1.10)", "bd": f"bd-{nn} (10.{nnip}.2.10)", "motor": f"{m['nombre']} :{m['puerto']}", "appUrl": "http://<IP_PUBLICA_WEB>/"},
        "sg": sg, "bitacora": bitacora, "pruebas": pruebas, "hallazgos": [], "cia": cia, "riesgos": riesgos, "gobierno": gobierno, "mejoras": mejoras,
        "cierre": {"conclusion": "", "aprendizajes": ""},
    }


def esquema_sql(t, motor):
    def tipo(tp):
        if tp == "date": return "DATE"
        if tp == "number": return "DECIMAL(12,2)"
        if tp == "textarea": return "VARCHAR(500)"
        return "VARCHAR(150)"
    P, H = t["padre"], t["hijo"]
    if motor["clave"] == "mariadb":
        idc, eng = "id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY", " ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
        fkt = "INT UNSIGNED"
    else:
        idc, eng, fkt = "id SERIAL PRIMARY KEY", "", "INTEGER"
    nul = lambda tp: "" if tp == "textarea" else " NOT NULL"
    cols_p = ",\n  ".join(f"{k} {tipo(tp)}{nul(tp)}" for k, tp, _ in P["campos"])
    cols_h = ",\n  ".join(f"{k} {tipo(tp)}{nul(tp)}" for k, tp, _ in H["campos"])
    return f"""-- Esquema {t['nombre_app']} ({motor['nombre']}) — 2 tablas relacionadas
CREATE TABLE IF NOT EXISTS {P['tabla']} (
  {idc},
  {cols_p},
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
){eng};

CREATE TABLE IF NOT EXISTS {H['tabla']} (
  {idc},
  {H['fk']} {fkt} NOT NULL,
  {cols_h},
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_{H['tabla']}_{P['tabla']} FOREIGN KEY ({H['fk']}) REFERENCES {P['tabla']}(id) ON DELETE RESTRICT
){eng};

CREATE INDEX IF NOT EXISTS idx_{H['tabla']}_{H['fk']} ON {H['tabla']} ({H['fk']});
"""


# ------------------------------------------------------------------ generación
def generar(nn, nombre, github, salida, semilla="", tema=None, motor=None, inicio=None, usados=None, forzar=False):
    nn = f"{int(nn):02d}"
    if not 1 <= int(nn) <= 99:
        sys.exit("NN debe estar entre 01 y 99")
    p = elegir_perfil(nn, nombre, github, semilla, tema, motor, usados)
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

    datos = construir_datos(p, nn, nombre, github, inicio)
    (destino / "data").mkdir(exist_ok=True)
    (destino / "data" / f"proyecto-{nn}.json").write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")

    tema_php = {"nombre_app": t["nombre_app"], "titulo": t["titulo"],
                "padre": {k: t["padre"][k] for k in ("tabla", "titulo", "singular")} | {"campos": [list(c) for c in t["padre"]["campos"]]},
                "hijo": {k: t["hijo"][k] for k in ("tabla", "titulo", "singular", "fk")} | {"campos": [list(c) for c in t["hijo"]["campos"]]}}
    (destino / "app-caso" / "config_tema.php").write_text(
        "<?php\n// Estructura (no datos) de la app del caso. Generado para NN " + nn + "\n$TEMA = " + php_valor(tema_php) + ";\n", encoding="utf-8", newline="\n")
    (destino / "instalador" / "bd" / "esquema.sql").write_text(esquema_sql(t, m), encoding="utf-8", newline="\n")
    (destino / "instalador" / "llaves").mkdir(exist_ok=True)
    (destino / "instalador" / "llaves" / "LEEME.txt").write_text(
        f"Copia aquí SOLO las llaves PÚBLICAS: {ctx['U_ADMIN']}.pub, {ctx['U_DEV']}.pub, {ctx['U_AUDIT']}.pub\n"
        "Nunca subas llaves privadas al repositorio.\n", encoding="utf-8")
    (destino / ".gitignore").write_text("instalador/aws/*.pem\ninstalador/aws/infra-*.env\n*.key\n*.pem\n.google_authenticator\n", encoding="utf-8")
    (destino / "_headers").write_text("/*\n  X-Content-Type-Options: nosniff\n  X-Frame-Options: DENY\n  Referrer-Policy: strict-origin-when-cross-origin\n", encoding="utf-8")

    resumen = {"nn": nn, "estudiante": nombre, "tema": t["clave"], "app": t["nombre_app"], "sistema": p["nombre_sistema"], "paleta": pal["nombre"],
               "fuente": p["fuente"][0], "layout": p["layout"], "tarjeta": p["tarjeta"], "grafico": p["grafico"], "pdf": p["pdf"],
               "motor": m["clave"], "firewall": p["firewall"], "zona": p["zona"][0], "alternativo": p["alt"]["nombre"],
               "grupos": [ctx["G_ADMIN"], ctx["G_DEV"], ctx["G_AUDIT"]], "cron": p["cron"]}
    (destino / "instalador" / "perfil-variantes.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    return destino, resumen


def main():
    ap = argparse.ArgumentParser(description="Generador del Proyecto Integrador TI3062")
    ap.add_argument("--nn"); ap.add_argument("--nombre"); ap.add_argument("--github")
    ap.add_argument("--tema"); ap.add_argument("--motor", choices=["mariadb", "postgresql"])
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
        filas = [{"nn": a.nn, "nombre": a.nombre, "github": a.github, "tema": a.tema or "", "motor": a.motor or ""}]
    else:
        ap.error("Indica --nn --nombre --github, o --lote archivo.csv")
    usados = set()
    for f in filas:
        d, res = generar(f["nn"], f["nombre"].strip(), f["github"].strip(), a.salida, a.semilla, (f.get("tema") or None), (f.get("motor") or None),
                         inicio, usados, a.forzar)
        usados.add(res["tema"])
        if len(usados) >= len(C.TEMAS):
            usados.clear()
        print(f"✔ {str(d).replace(chr(92) * 2 + '?' + chr(92), '')}  ·{res['app']} ({res['tema']}) · {res['sistema']} · {res['paleta']}/{res['fuente']}/{res['layout']} · {res['motor']} · {res['firewall']} · {res['zona']}")


if __name__ == "__main__":
    main()
