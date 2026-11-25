# -*- coding: utf-8 -*-
"""Catálogo de variantes del generador TI3062.

Cada estudiante recibe una combinación distinta (según su NN, nombre y semilla):
temática del caso, tablas, paleta, tipografía, distribución, nombres de grupos,
motor de BD, firewall, proveedor alternativo, controles NIST, riesgos y mejoras.
"""

# ---------------------------------------------------------------------------
# Temáticas del caso (app que corre en web-NN). Cada una: tabla padre + tabla hija.
# Tipos de campo: text, tel, email, date, number, select:Op1|Op2, textarea
# ---------------------------------------------------------------------------
TEMAS = [
    {
        "clave": "veterinaria", "nombre_app": "VetCuidado",
        "titulo": "Clínica veterinaria comunal",
        "contexto": "Una clínica veterinaria de La Serena registra dueños y mascotas en planillas compartidas por correo, lo que provoca pérdida de fichas, datos duplicados y exposición de datos personales de los tutores.",
        "actores": ["Recepcionista", "Médico veterinario", "Tutor de la mascota", "Administrador TI"],
        "procesos": ["Registro de tutores", "Ficha de mascotas", "Agenda de atenciones", "Respaldo de fichas"],
        "padre": {"tabla": "duenos", "titulo": "Tutores", "singular": "tutor", "campos": [
            ("nombre", "text", "Nombre completo"), ("telefono", "tel", "Teléfono"), ("email", "email", "Correo")]},
        "hijo": {"tabla": "mascotas", "titulo": "Mascotas", "singular": "mascota", "fk": "dueno_id", "campos": [
            ("nombre", "text", "Nombre"), ("especie", "select:Perro|Gato|Ave|Exótico", "Especie"),
            ("fecha_nacimiento", "date", "Fecha de nacimiento"), ("observaciones", "textarea", "Observaciones")]},
    },
    {
        "clave": "biblioteca", "nombre_app": "BiblioRed",
        "titulo": "Biblioteca comunal digital",
        "contexto": "La biblioteca comunal controla su catálogo y autores en cuadernos y una planilla local sin respaldo; cuando el equipo falla se pierde el inventario y no se puede consultar desde las sedes.",
        "actores": ["Bibliotecario", "Lector", "Coordinador de sede", "Administrador TI"],
        "procesos": ["Alta de autores", "Catalogación de libros", "Consulta del catálogo", "Respaldo del catálogo"],
        "padre": {"tabla": "autores", "titulo": "Autores", "singular": "autor", "campos": [
            ("nombre", "text", "Nombre"), ("nacionalidad", "text", "Nacionalidad")]},
        "hijo": {"tabla": "libros", "titulo": "Libros", "singular": "libro", "fk": "autor_id", "campos": [
            ("titulo", "text", "Título"), ("isbn", "text", "ISBN"), ("anio", "number", "Año"),
            ("estado", "select:Disponible|Prestado|En reparación", "Estado")]},
    },
    {
        "clave": "taller", "nombre_app": "TallerPro",
        "titulo": "Taller mecánico automotriz",
        "contexto": "Un taller mecánico anota clientes y vehículos en papel; las órdenes se extravían, no hay trazabilidad de quién modificó un registro y los datos de clientes quedan expuestos en el mesón.",
        "actores": ["Jefe de taller", "Mecánico", "Cliente", "Administrador TI"],
        "procesos": ["Registro de clientes", "Ingreso de vehículos", "Seguimiento del servicio", "Respaldo de registros"],
        "padre": {"tabla": "clientes", "titulo": "Clientes", "singular": "cliente", "campos": [
            ("nombre", "text", "Nombre"), ("rut", "text", "RUT"), ("telefono", "tel", "Teléfono")]},
        "hijo": {"tabla": "vehiculos", "titulo": "Vehículos", "singular": "vehículo", "fk": "cliente_id", "campos": [
            ("patente", "text", "Patente"), ("marca", "text", "Marca"), ("modelo", "text", "Modelo"),
            ("servicio", "select:Mantención|Frenos|Motor|Diagnóstico", "Servicio")]},
    },
    {
        "clave": "canchas", "nombre_app": "ReservaYa",
        "titulo": "Reserva de canchas deportivas municipales",
        "contexto": "El municipio administra las reservas de canchas por WhatsApp; se producen dobles reservas, no hay registro histórico y la información de los vecinos circula sin control.",
        "actores": ["Encargado deportivo", "Vecino", "Coordinador municipal", "Administrador TI"],
        "procesos": ["Registro de canchas", "Reserva de horarios", "Consulta de disponibilidad", "Respaldo de reservas"],
        "padre": {"tabla": "canchas", "titulo": "Canchas", "singular": "cancha", "campos": [
            ("nombre", "text", "Nombre"), ("tipo", "select:Fútbol|Básquetbol|Tenis|Multiuso", "Tipo"),
            ("sector", "text", "Sector")]},
        "hijo": {"tabla": "reservas", "titulo": "Reservas", "singular": "reserva", "fk": "cancha_id", "campos": [
            ("vecino", "text", "Nombre del vecino"), ("fecha", "date", "Fecha"),
            ("bloque", "select:08-10|10-12|15-17|17-19|19-21", "Bloque horario")]},
    },
    {
        "clave": "ferreteria", "nombre_app": "StockFerre",
        "titulo": "Inventario de ferretería de barrio",
        "contexto": "Una ferretería lleva su inventario en una planilla en el computador de caja; hay quiebres de stock, diferencias de inventario y riesgo de pérdida total ante falla del equipo.",
        "actores": ["Dueño", "Vendedor", "Bodeguero", "Administrador TI"],
        "procesos": ["Gestión de categorías", "Registro de productos", "Control de stock", "Respaldo del inventario"],
        "padre": {"tabla": "categorias", "titulo": "Categorías", "singular": "categoría", "campos": [
            ("nombre", "text", "Nombre"), ("descripcion", "text", "Descripción")]},
        "hijo": {"tabla": "productos", "titulo": "Productos", "singular": "producto", "fk": "categoria_id", "campos": [
            ("nombre", "text", "Nombre"), ("sku", "text", "SKU"), ("stock", "number", "Stock"),
            ("precio", "number", "Precio (CLP)")]},
    },
    {
        "clave": "gimnasio", "nombre_app": "FitControl",
        "titulo": "Gestión de socios de gimnasio",
        "contexto": "Un gimnasio registra planes y socios en un cuaderno; no puede verificar vigencias, los datos personales y de salud quedan sin protección y no existe respaldo.",
        "actores": ["Recepción", "Entrenador", "Socio", "Administrador TI"],
        "procesos": ["Definición de planes", "Inscripción de socios", "Control de vigencia", "Respaldo de socios"],
        "padre": {"tabla": "planes", "titulo": "Planes", "singular": "plan", "campos": [
            ("nombre", "text", "Nombre del plan"), ("valor", "number", "Valor mensual"), ("duracion_meses", "number", "Duración (meses)")]},
        "hijo": {"tabla": "socios", "titulo": "Socios", "singular": "socio", "fk": "plan_id", "campos": [
            ("nombre", "text", "Nombre"), ("email", "email", "Correo"), ("fecha_inicio", "date", "Fecha de inicio"),
            ("estado", "select:Activo|Suspendido|Vencido", "Estado")]},
    },
    {
        "clave": "helpdesk", "nombre_app": "MesaTI",
        "titulo": "Mesa de ayuda TI para una PYME",
        "contexto": "Una PYME recibe solicitudes de soporte por correo y teléfono; los casos se pierden, no se mide el tiempo de respuesta y no hay trazabilidad por área.",
        "actores": ["Técnico de soporte", "Usuario interno", "Jefe de área", "Administrador TI"],
        "procesos": ["Registro de áreas", "Apertura de tickets", "Seguimiento de estado", "Respaldo de tickets"],
        "padre": {"tabla": "areas", "titulo": "Áreas", "singular": "área", "campos": [
            ("nombre", "text", "Nombre del área"), ("responsable", "text", "Responsable")]},
        "hijo": {"tabla": "tickets", "titulo": "Tickets", "singular": "ticket", "fk": "area_id", "campos": [
            ("asunto", "text", "Asunto"), ("prioridad", "select:Baja|Media|Alta|Crítica", "Prioridad"),
            ("estado", "select:Abierto|En curso|Cerrado", "Estado"), ("detalle", "textarea", "Detalle")]},
    },
    {
        "clave": "donaciones", "nombre_app": "RedSolidaria",
        "titulo": "Banco de alimentos de una ONG",
        "contexto": "Una ONG registra donantes y donaciones en papel; no puede rendir cuentas, se duplican registros y los datos de donantes quedan expuestos.",
        "actores": ["Coordinador de la ONG", "Voluntario", "Donante", "Administrador TI"],
        "procesos": ["Registro de donantes", "Recepción de donaciones", "Rendición de cuentas", "Respaldo de registros"],
        "padre": {"tabla": "donantes", "titulo": "Donantes", "singular": "donante", "campos": [
            ("nombre", "text", "Nombre o razón social"), ("tipo", "select:Persona|Empresa|Institución", "Tipo"),
            ("contacto", "text", "Contacto")]},
        "hijo": {"tabla": "donaciones", "titulo": "Donaciones", "singular": "donación", "fk": "donante_id", "campos": [
            ("producto", "text", "Producto"), ("cantidad", "number", "Cantidad"), ("fecha", "date", "Fecha")]},
    },
    {
        "clave": "dental", "nombre_app": "SonrisaAgenda",
        "titulo": "Agenda de clínica dental",
        "contexto": "Una clínica dental agenda pacientes en una planilla compartida; se pierden horas, hay acceso indebido a datos sensibles de salud y no existe respaldo cifrado.",
        "actores": ["Secretaria", "Odontólogo", "Paciente", "Administrador TI"],
        "procesos": ["Registro de pacientes", "Agendamiento de citas", "Confirmación de horas", "Respaldo de la agenda"],
        "padre": {"tabla": "pacientes", "titulo": "Pacientes", "singular": "paciente", "campos": [
            ("nombre", "text", "Nombre"), ("rut", "text", "RUT"), ("telefono", "tel", "Teléfono")]},
        "hijo": {"tabla": "citas", "titulo": "Citas", "singular": "cita", "fk": "paciente_id", "campos": [
            ("fecha", "date", "Fecha"), ("hora", "select:09:00|10:00|11:00|12:00|15:00|16:00|17:00", "Hora"),
            ("tratamiento", "text", "Tratamiento")]},
    },
    {
        "clave": "riego", "nombre_app": "AgroLectura",
        "titulo": "Registro de lecturas de riego agrícola",
        "contexto": "Un agricultor del valle del Elqui anota a mano la humedad de sus parcelas; los datos se pierden, no puede analizar tendencias y no tiene respaldo ante fallas.",
        "actores": ["Agricultor", "Técnico agrícola", "Asesor externo", "Administrador TI"],
        "procesos": ["Registro de parcelas", "Ingreso de lecturas", "Análisis de humedad", "Respaldo de lecturas"],
        "padre": {"tabla": "parcelas", "titulo": "Parcelas", "singular": "parcela", "campos": [
            ("nombre", "text", "Nombre"), ("cultivo", "text", "Cultivo"), ("hectareas", "number", "Hectáreas")]},
        "hijo": {"tabla": "lecturas", "titulo": "Lecturas", "singular": "lectura", "fk": "parcela_id", "campos": [
            ("fecha", "date", "Fecha"), ("humedad", "number", "Humedad (%)"), ("temperatura", "number", "Temperatura (°C)")]},
    },
    {
        "clave": "hostal", "nombre_app": "HostalCoquimbo",
        "titulo": "Reservas de hostal turístico",
        "contexto": "Un hostal de Coquimbo gestiona habitaciones y reservas en un cuaderno y redes sociales; se producen sobreventas y los datos de huéspedes no tienen protección.",
        "actores": ["Recepcionista", "Dueña del hostal", "Huésped", "Administrador TI"],
        "procesos": ["Registro de habitaciones", "Reserva de estadías", "Check-in", "Respaldo de reservas"],
        "padre": {"tabla": "habitaciones", "titulo": "Habitaciones", "singular": "habitación", "campos": [
            ("numero", "text", "Número"), ("tipo", "select:Single|Doble|Familiar", "Tipo"), ("tarifa", "number", "Tarifa (CLP)")]},
        "hijo": {"tabla": "reservas", "titulo": "Reservas", "singular": "reserva", "fk": "habitacion_id", "campos": [
            ("huesped", "text", "Huésped"), ("entrada", "date", "Entrada"), ("salida", "date", "Salida")]},
    },
    {
        "clave": "laboratorio", "nombre_app": "LabPresta",
        "titulo": "Préstamo de equipos de laboratorio",
        "contexto": "El laboratorio de redes de una sede presta equipos (routers, switches, osciloscopios) con una hoja de firma; hay equipos extraviados y no se sabe quién tiene cada uno.",
        "actores": ["Pañolero", "Docente", "Estudiante", "Administrador TI"],
        "procesos": ["Inventario de equipos", "Registro de préstamos", "Devolución", "Respaldo del inventario"],
        "padre": {"tabla": "equipos", "titulo": "Equipos", "singular": "equipo", "campos": [
            ("nombre", "text", "Nombre"), ("codigo", "text", "Código de inventario"),
            ("tipo", "select:Router|Switch|Osciloscopio|Multímetro|Otro", "Tipo")]},
        "hijo": {"tabla": "prestamos", "titulo": "Préstamos", "singular": "préstamo", "fk": "equipo_id", "campos": [
            ("solicitante", "text", "Solicitante"), ("fecha_prestamo", "date", "Fecha de préstamo"),
            ("estado", "select:Prestado|Devuelto|Atrasado", "Estado")]},
    },
]

# ---------------------------------------------------------------------------
# Apariencia del sistema de gestión (Cloudflare Pages) y de la app del caso
# ---------------------------------------------------------------------------
PALETAS = [
    {"nombre": "Océano", "primario": "#0f5c8c", "acento": "#16a3b8", "fondo": "#f4f8fb", "superficie": "#ffffff", "texto": "#14212b", "dark_fondo": "#0b141b", "dark_superficie": "#13212c", "dark_texto": "#e3edf3", "rgb": [15, 92, 140]},
    {"nombre": "Bosque", "primario": "#2f6b3a", "acento": "#8bbf3f", "fondo": "#f5f8f2", "superficie": "#ffffff", "texto": "#1b2a1e", "dark_fondo": "#0e1510", "dark_superficie": "#18241a", "dark_texto": "#e4eee3", "rgb": [47, 107, 58]},
    {"nombre": "Ladrillo", "primario": "#a23b2a", "acento": "#e08a3c", "fondo": "#fbf6f2", "superficie": "#ffffff", "texto": "#2b1b17", "dark_fondo": "#170f0d", "dark_superficie": "#251916", "dark_texto": "#f3e6e1", "rgb": [162, 59, 42]},
    {"nombre": "Grafito", "primario": "#33404d", "acento": "#f2a541", "fondo": "#f3f4f6", "superficie": "#ffffff", "texto": "#1a1f24", "dark_fondo": "#0f1216", "dark_superficie": "#1a1f26", "dark_texto": "#e6e9ed", "rgb": [51, 64, 77]},
    {"nombre": "Uva", "primario": "#5b3a8c", "acento": "#c06bd6", "fondo": "#f7f4fb", "superficie": "#ffffff", "texto": "#221a2b", "dark_fondo": "#120e18", "dark_superficie": "#1e1828", "dark_texto": "#ece5f3", "rgb": [91, 58, 140]},
    {"nombre": "Desierto", "primario": "#8c5a1e", "acento": "#d9a441", "fondo": "#fbf8f1", "superficie": "#ffffff", "texto": "#2a2116", "dark_fondo": "#16120c", "dark_superficie": "#231d14", "dark_texto": "#f2ebdd", "rgb": [140, 90, 30]},
    {"nombre": "Marino", "primario": "#1d3557", "acento": "#e63946", "fondo": "#f1f5f9", "superficie": "#ffffff", "texto": "#14213d", "dark_fondo": "#0b1220", "dark_superficie": "#14203a", "dark_texto": "#e2e8f0", "rgb": [29, 53, 87]},
    {"nombre": "Turquesa", "primario": "#0e7c7b", "acento": "#f4a259", "fondo": "#f2f9f8", "superficie": "#ffffff", "texto": "#132625", "dark_fondo": "#0a1514", "dark_superficie": "#132321", "dark_texto": "#e0f0ee", "rgb": [14, 124, 123]},
]

FUENTES = [
    ("Inter", "Inter:wght@400;600;700"),
    ("Poppins", "Poppins:wght@400;600;700"),
    ("Nunito", "Nunito:wght@400;600;800"),
    ("IBM Plex Sans", "IBM+Plex+Sans:wght@400;600;700"),
    ("Work Sans", "Work+Sans:wght@400;600;700"),
    ("Source Sans 3", "Source+Sans+3:wght@400;600;700"),
    ("Manrope", "Manrope:wght@400;600;800"),
    ("Rubik", "Rubik:wght@400;600;700"),
]

LAYOUTS = ["lateral-izq", "lateral-der", "superior"]
ESTILOS_TARJETA = ["redondeada", "recta", "sombra", "borde"]
ESTILOS_GRAFICO = ["barras", "dona", "anillos"]
ESTILOS_PDF = ["banda", "linea", "caja"]

NOMBRES_SISTEMA = [
    "Gestor de Proyecto Cloud", "Bitácora Segura", "PlanSec Cloud", "Centro de Control del Proyecto",
    "Consola de Proyecto Integrador", "Tablero de Seguridad Cloud", "Gestión Integral TI3062", "Proyecto Seguro AWS",
]

# Nombres de grupos/usuarios funcionales (sufijo NN se agrega después)
NOMBRES_GRUPOS = [
    {"admin": "sysadmin", "dev": "desarrollo", "audit": "auditoria", "u_admin": "adm", "u_dev": "dev", "u_audit": "aud"},
    {"admin": "administracion", "dev": "devs", "audit": "auditores", "u_admin": "admin", "u_dev": "desa", "u_audit": "audit"},
    {"admin": "ops", "dev": "dev", "audit": "audit", "u_admin": "usr_admin", "u_dev": "usr_dev", "u_audit": "usr_aud"},
    {"admin": "g_admin", "dev": "g_desarrollo", "audit": "g_auditoria", "u_admin": "sysop", "u_dev": "coder", "u_audit": "revisor"},
]

MOTORES = [
    {"clave": "mariadb", "nombre": "MariaDB", "puerto": 3306, "paquete": "mariadb-server", "php": "php-mysql", "dsn": "mysql"},
    {"clave": "postgresql", "nombre": "PostgreSQL", "puerto": 5432, "paquete": "postgresql", "php": "php-pgsql", "dsn": "pgsql"},
]

FIREWALLS = ["ufw", "nftables"]

ZONAS = [
    ("us-east-1a", "Es la zona con mayor catálogo de tipos de instancia en N. Virginia y la que AWS Academy usa por defecto; se fija en ambas subredes para que web y BD queden en la misma AZ y la latencia interna sea mínima."),
    ("us-east-1b", "Se fija explícitamente para que web-NN y bd-NN compartan AZ (sin costo de transferencia entre zonas y con menor latencia), dejando us-east-1a como zona candidata para una réplica futura."),
    ("us-east-1c", "Se elige una AZ distinta a la predeterminada para reducir la concentración con otros laboratorios del curso y se documenta us-east-1a como destino de recuperación desde snapshots."),
]

# Proveedor alternativo para el análisis multicloud
PROVEEDORES_ALT = [
    {"nombre": "Microsoft Azure", "servicio": "Azure Virtual Machines B1s + VNet con subred privada y NSG",
     "seguridad": "NSG por subred/NIC, Microsoft Entra ID con MFA, Defender for Cloud, cifrado de discos por defecto",
     "disponibilidad": "SLA 99,9% con disco Premium SSD; Availability Zones y Availability Sets",
     "fuente": "https://azure.microsoft.com/es-es/pricing/calculator/",
     "beneficios": "Integración con Entra ID y Microsoft 365; cifrado en reposo activado por defecto",
     "limitaciones": "Crédito estudiantil distinto a AWS Academy; curva de aprendizaje de la consola",
     "riesgos": "Dependencia de identidad Microsoft; costos de IP pública y discos administrados"},
    {"nombre": "Google Cloud", "servicio": "Compute Engine e2-micro + VPC con subred privada y reglas de firewall",
     "seguridad": "Firewall por etiquetas de red, IAM granular, OS Login con 2FA, cifrado en reposo por defecto",
     "disponibilidad": "SLA 99,5% instancia única; zonas múltiples por región",
     "fuente": "https://cloud.google.com/products/calculator",
     "beneficios": "Nivel gratuito e2-micro en algunas regiones; cifrado y OS Login nativos",
     "limitaciones": "e2-micro con CPU compartida; región sudamericana (São Paulo/Santiago) con precio distinto",
     "riesgos": "Cambios en el nivel gratuito; egreso de red con costo"},
    {"nombre": "Oracle Cloud (OCI)", "servicio": "VM.Standard.E2.1.Micro + VCN con subred privada y Security Lists/NSG",
     "seguridad": "Security Lists y NSG, IAM con MFA, Cloud Guard, cifrado de volúmenes por defecto",
     "disponibilidad": "Dominios de disponibilidad y de falla; región Santiago disponible",
     "fuente": "https://www.oracle.com/cl/cloud/costestimator.html",
     "beneficios": "Región en Santiago (menor latencia y datos en Chile); nivel Always Free generoso",
     "limitaciones": "Menor ecosistema y documentación en español; cuotas limitadas en Always Free",
     "riesgos": "Reclamo de capacidad Always Free; menor experiencia del equipo con la plataforma"},
]

# Controles NIST SP 800-53 Rev. 5 (pool). req_tipo indica a qué RNF se ligan.
CONTROLES = [
    {"codigo": "AC-6", "nombre": "Least Privilege", "riesgo": "Uso indebido de privilegios por usuarios no administradores", "punto": "/etc/sudoers.d/ con comandos específicos por grupo y usuario de BD sin ALL", "capa": "Identidad", "req": "seguridad"},
    {"codigo": "IA-2(1)", "nombre": "MFA para cuentas privilegiadas", "riesgo": "Robo o filtración de la llave SSH del administrador", "punto": "sshd + pam_google_authenticator (TOTP) para el grupo administrador", "capa": "Identidad", "req": "seguridad"},
    {"codigo": "SC-7", "nombre": "Boundary Protection", "riesgo": "Exposición de la base de datos y SSH a Internet", "punto": "VPC con subred privada, Security Groups y firewall de host", "capa": "Red", "req": "seguridad"},
    {"codigo": "SC-28", "nombre": "Protection of Information at Rest", "riesgo": "Lectura de respaldos si se roba el volumen o snapshot", "punto": "Volumen LUKS montado en /respaldos en bd-NN", "capa": "Proveedor", "req": "seguridad"},
    {"codigo": "AU-2", "nombre": "Event Logging", "riesgo": "Cambios no autorizados sin trazabilidad", "punto": "auditd con reglas sobre sudo, passwd, sudoers y sshd_config", "capa": "Aplicación", "req": "seguridad"},
    {"codigo": "AU-6", "nombre": "Audit Record Review", "riesgo": "Incidentes no detectados por falta de revisión", "punto": "Revisión periódica con aureport/ausearch por el grupo auditoría", "capa": "Aplicación", "req": "seguridad"},
    {"codigo": "AC-17", "nombre": "Remote Access", "riesgo": "Acceso remoto por fuerza bruta o como root", "punto": "sshd_config: sin root, sin contraseña, AllowGroups, MaxAuthTries 3", "capa": "Red", "req": "seguridad"},
    {"codigo": "AC-12", "nombre": "Session Termination", "riesgo": "Sesiones abandonadas reutilizadas por terceros", "punto": "ClientAliveInterval/ClientAliveCountMax y MaxSessions en sshd", "capa": "Identidad", "req": "seguridad"},
    {"codigo": "CP-9", "nombre": "System Backup", "riesgo": "Pérdida de datos por falla o error humano", "punto": "cron diario con dump de la BD hacia /respaldos (LUKS)", "capa": "Proveedor", "req": "disponibilidad"},
    {"codigo": "CP-10", "nombre": "System Recovery and Reconstitution", "riesgo": "Imposibilidad de recuperar el servicio tras un incidente", "punto": "Restauración probada del respaldo y snapshots de volúmenes EBS", "capa": "Proveedor", "req": "disponibilidad"},
    {"codigo": "IA-5", "nombre": "Authenticator Management", "riesgo": "Credenciales débiles o expuestas en el código", "punto": "Llaves ED25519 por usuario y credenciales de BD en /etc/ti3062/db.ini fuera del repositorio", "capa": "Aplicación", "req": "seguridad"},
    {"codigo": "CM-7", "nombre": "Least Functionality", "riesgo": "Servicios y puertos innecesarios que amplían la superficie de ataque", "punto": "Solo 80/443/22 en web y puerto BD/22 en bd; firewall de host por defecto deny", "capa": "Red", "req": "rendimiento"},
]

RIESGOS_RESIDUALES = [
    {"riesgo": "Instancia única de base de datos en una sola AZ", "impacto": "Alto: una falla de la AZ deja el servicio sin datos hasta restaurar desde snapshot", "tratamiento": "Aceptado temporalmente; mejora propuesta: réplica en otra AZ"},
    {"riesgo": "El volumen LUKS requiere desbloqueo manual tras reinicio", "impacto": "Medio: los respaldos programados fallan si nadie abre el volumen después de un reinicio", "tratamiento": "Procedimiento documentado y alerta si /respaldos no está montado"},
    {"riesgo": "Logs de auditoría almacenados solo localmente", "impacto": "Medio: un atacante con root podría borrar la evidencia", "tratamiento": "Mejora propuesta: envío a servidor central (rsyslog/CloudWatch)"},
    {"riesgo": "Sin TLS con certificado de una CA pública en la app del caso", "impacto": "Medio: advertencias de certificado y posible intercepción si se usa HTTP", "tratamiento": "Mejora propuesta: dominio propio + Let's Encrypt"},
    {"riesgo": "Sin IAM ni CloudTrail en AWS Academy", "impacto": "Medio: no hay auditoría de acciones en la consola de AWS", "tratamiento": "Compensado con auditd a nivel de SO; limitación del entorno"},
    {"riesgo": "Las llaves privadas residen en el equipo personal del estudiante", "impacto": "Alto: robo del equipo compromete el acceso (mitigado por TOTP solo en admin)", "tratamiento": "Frase de paso en las llaves y MFA para todos los grupos como mejora"},
]

MEJORAS = [
    {"accion": "Centralizar logs de auditd y auth.log en un servidor o servicio externo", "control": "AU-9", "impacto": "Protege la evidencia ante un compromiso de root"},
    {"accion": "Agregar réplica de la base de datos en otra zona de disponibilidad", "control": "CP-7", "impacto": "Reduce el punto único de falla de bd-NN"},
    {"accion": "Publicar la app con certificado TLS válido (Let's Encrypt) y redirección HTTP→HTTPS", "control": "SC-8", "impacto": "Confidencialidad e integridad en tránsito"},
    {"accion": "Extender MFA TOTP a los grupos de desarrollo y auditoría", "control": "IA-2(2)", "impacto": "Reduce el riesgo de suplantación con llaves robadas"},
    {"accion": "Instalar fail2ban para bloquear IPs con intentos fallidos repetidos", "control": "AC-7", "impacto": "Mitiga fuerza bruta contra SSH y la app"},
    {"accion": "Copiar respaldos cifrados a almacenamiento externo (S3 u otra región)", "control": "CP-6", "impacto": "Respaldo fuera del sitio ante pérdida de la instancia"},
    {"accion": "Escaneo periódico de vulnerabilidades con Lynis y actualizaciones automáticas", "control": "RA-5", "impacto": "Detecta configuraciones débiles y paquetes vulnerables"},
]
