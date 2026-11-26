# -*- coding: utf-8 -*-
"""Diccionario base del proyecto TI3062 (fuente única).

Contiene todos los controles NIST SP 800-53 Rev. 5 que aplican al proyecto y la información base que debe
incluirse en el informe: bancos de texto por módulo, hallazgos típicos, glosario y el contenido mínimo
exigido por la pauta y la guía U4. generar.py lo adapta a cada plantilla (NN, temática, motor, usuarios)
y lo publica como data/diccionario-NN.json; el sistema de gestión lo usa para sugerir mientras se rellena.
Marcadores disponibles en los textos: {NN} {NNIP} {APP} {MOTOR} {PUERTO} {WEB_IP} {BD_IP} {TABLA_P} {TABLA_H}
{U_ADMIN} {U_DEV} {U_AUDIT} {G_ADMIN} {G_DEV} {G_AUDIT} {FIREWALL} {ZONA} {ALT} {CRON} {RETENCION}
"""

# Controles NIST SP 800-53 Rev. 5 (pool). req_tipo indica a qué RNF se ligan.
CONTROLES = [
    {"codigo": "AC-6", "nombre": "Least Privilege", "riesgo": "Uso indebido de privilegios por usuarios no administradores", "punto": "/etc/sudoers.d/ con comandos específicos por grupo y usuario de BD sin ALL", "capa": "Identidad", "req": "seguridad"},
    {"codigo": "IA-2(1)", "nombre": "MFA para cuentas privilegiadas", "riesgo": "Robo o filtración de la llave SSH del administrador", "punto": "sshd + pam_google_authenticator (TOTP) para el grupo administrador", "capa": "Identidad", "req": "seguridad"},
    {"codigo": "SC-7", "nombre": "Boundary Protection", "riesgo": "Exposición de la base de datos y SSH a Internet", "punto": "VPC con subred privada, Security Groups y firewall de host", "capa": "Red", "req": "seguridad"},
    {"codigo": "SC-28", "nombre": "Protection of Information at Rest", "riesgo": "Lectura de respaldos si se roba el volumen o snapshot", "punto": "Volumen LUKS montado en /respaldos en bd-NN", "capa": "Proveedor", "req": "seguridad"},
    {"codigo": "AU-2", "nombre": "Event Logging", "riesgo": "Cambios no autorizados sin trazabilidad", "punto": "auditd con reglas sobre sudo, passwd, sudoers y sshd_config", "capa": "Aplicación", "req": "seguridad"},
    {"codigo": "AU-6", "nombre": "Audit Record Review", "riesgo": "Incidentes no detectados por falta de revisión", "punto": "Revisión periódica con aureport/ausearch por el grupo auditoría", "capa": "Aplicación", "req": "seguridad"},
    {"codigo": "AC-17", "nombre": "Remote Access", "riesgo": "Acceso remoto por fuerza bruta o como root", "punto": "sshd_config: sin root, sin contraseña, AllowGroups, MaxAuthTries 3", "capa": "Red", "req": "seguridad"},
    {"codigo": "AC-12", "nombre": "Session Termination", "riesgo": "Sesiones abandonadas reutilizadas por terceros", "punto": "App: sesión expira a los 15 min de inactividad y a las 8 h; SSH: ClientAliveInterval/CountMax y MaxSessions", "capa": "Identidad", "req": "seguridad"},
    {"codigo": "CP-9", "nombre": "System Backup", "riesgo": "Pérdida de datos por falla o error humano", "punto": "cron diario con dump de la BD hacia /respaldos (LUKS)", "capa": "Proveedor", "req": "disponibilidad"},
    {"codigo": "CP-10", "nombre": "System Recovery and Reconstitution", "riesgo": "Imposibilidad de recuperar el servicio tras un incidente", "punto": "Restauración probada del respaldo y snapshots de volúmenes EBS", "capa": "Proveedor", "req": "disponibilidad"},
    {"codigo": "IA-5", "nombre": "Authenticator Management", "riesgo": "Credenciales débiles o expuestas en el código", "punto": "Llaves ED25519 por usuario y credenciales de BD en /etc/ti3062/db.ini fuera del repositorio", "capa": "Aplicación", "req": "seguridad"},
    {"codigo": "CM-7", "nombre": "Least Functionality", "riesgo": "Servicios y puertos innecesarios que amplían la superficie de ataque", "punto": "Solo 80/443/22 en web y puerto BD/22 en bd; firewall de host por defecto deny", "capa": "Red", "req": "rendimiento"},
]

# Controles NIST obligatorios para la aplicación web del caso (todos quedan implementados por la app y el instalador)
CONTROLES_APP = [
    {"codigo": "AC-3", "nombre": "Access Enforcement", "riesgo": "Usuarios que ejecutan acciones fuera de su rol", "punto": "App: roles admin / operador / auditor verificados en cada acción del servidor", "capa": "Aplicación", "req": "seguridad"},
    {"codigo": "AC-7", "nombre": "Unsuccessful Logon Attempts", "riesgo": "Fuerza bruta contra cuentas de la aplicación", "punto": "App: bloqueo de 15 min tras 5 intentos fallidos, registrado en auditoria_app", "capa": "Identidad", "req": "seguridad"},
    {"codigo": "AC-8", "nombre": "System Use Notification", "riesgo": "Uso no autorizado sin advertencia legal", "punto": "App: aviso de uso autorizado y registro en la pantalla de ingreso; banner SSH", "capa": "Aplicación", "req": "seguridad"},
    {"codigo": "IA-2", "nombre": "Identification and Authentication (Organizational Users)", "riesgo": "Acciones anónimas sin responsable", "punto": "App: usuarios nominativos en usuarios_app; cada registro guarda su autor", "capa": "Identidad", "req": "seguridad"},
    {"codigo": "IA-5(1)", "nombre": "Password-based Authentication", "riesgo": "Contraseñas débiles o almacenadas en claro", "punto": "App: mínimo 12 caracteres, hash bcrypt/argon2 (password_hash), cambio de clave por el usuario", "capa": "Identidad", "req": "seguridad"},
    {"codigo": "SC-8", "nombre": "Transmission Confidentiality and Integrity", "riesgo": "Intercepción de datos entre el navegador, web y la BD", "punto": "HTTPS con redirección desde HTTP + TLS 1.2/1.3 web→bd con verificación del certificado (CA propia)", "capa": "Red", "req": "seguridad"},
    {"codigo": "SC-23", "nombre": "Session Authenticity", "riesgo": "Robo o fijación de la sesión y CSRF", "punto": "App: cookie HttpOnly/Secure/SameSite=Strict, regeneración del ID al ingresar y token CSRF en cada formulario", "capa": "Aplicación", "req": "seguridad"},
    {"codigo": "SI-10", "nombre": "Information Input Validation", "riesgo": "Inyección SQL, XSS o datos inválidos", "punto": "App: consultas preparadas, listas blancas por campo, escape de salida, CSP y CSV sin fórmulas", "capa": "Aplicación", "req": "seguridad"},
    {"codigo": "SI-11", "nombre": "Error Handling", "riesgo": "Mensajes que revelan estructura interna o credenciales", "punto": "App: errores genéricos al usuario y detalle solo en el log del servidor; display_errors Off", "capa": "Aplicación", "req": "seguridad"},
    {"codigo": "AU-9", "nombre": "Protection of Audit Information", "riesgo": "Borrado o alteración del registro de actividad", "punto": "auditoria_app: el usuario de la app solo tiene INSERT/SELECT (sin UPDATE ni DELETE)", "capa": "Aplicación", "req": "seguridad"},
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
    {"accion": "Centralizar auditd, auth.log y auditoria_app en un servidor o servicio externo", "control": "AU-9(2)", "impacto": "Protege la evidencia ante un compromiso de root"},
    {"accion": "Agregar réplica de la base de datos en otra zona de disponibilidad", "control": "CP-7", "impacto": "Reduce el punto único de falla de bd-NN"},
    {"accion": "Publicar la app con un dominio y certificado de CA pública (Let's Encrypt) en lugar del autofirmado", "control": "SC-8", "impacto": "Elimina la advertencia del navegador y el riesgo de aceptar certificados falsos"},
    {"accion": "Extender MFA TOTP a los grupos de desarrollo y auditoría", "control": "IA-2(2)", "impacto": "Reduce el riesgo de suplantación con llaves robadas"},
    {"accion": "Instalar fail2ban para bloquear IPs con intentos fallidos repetidos", "control": "AC-7", "impacto": "Mitiga fuerza bruta contra SSH y la app"},
    {"accion": "Copiar respaldos cifrados a almacenamiento externo (S3 u otra región)", "control": "CP-6", "impacto": "Respaldo fuera del sitio ante pérdida de la instancia"},
    {"accion": "Escaneo periódico de vulnerabilidades con Lynis y actualizaciones automáticas", "control": "RA-5", "impacto": "Detecta configuraciones débiles y paquetes vulnerables"},
]

# ---------------------------------------------------------------------------
# Controles adicionales del diccionario (no se precargan; se sugieren al rellenar)
# ---------------------------------------------------------------------------
CONTROLES_EXTRA = [
    {"codigo": "AC-2", "nombre": "Account Management", "riesgo": "Cuentas sin dueño, compartidas o activas después de dejar de usarse", "punto": "Usuarios nominativos {U_ADMIN}/{U_DEV}/{U_AUDIT}; cuenta ubuntu bloqueada; usuarios de la app desactivables y revalidados en cada petición", "capa": "Identidad", "req": "seguridad"},
    {"codigo": "AC-5", "nombre": "Separation of Duties", "riesgo": "Una sola persona puede ejecutar y aprobar cambios críticos", "punto": "Grupos {G_ADMIN}, {G_DEV} y {G_AUDIT} con sudoers distintos; roles admin/operador/auditor en la app", "capa": "Identidad", "req": "seguridad"},
    {"codigo": "AC-11", "nombre": "Device Lock", "riesgo": "Sesiones abiertas en equipos desatendidos", "punto": "Expiración de la sesión de la app a los 15 min y ClientAlive en SSH", "capa": "Identidad", "req": "seguridad"},
    {"codigo": "AU-3", "nombre": "Content of Audit Records", "riesgo": "Registros sin datos suficientes para investigar", "punto": "auditoria_app guarda fecha, usuario, acción, entidad, detalle e IP; auditd con claves por evento", "capa": "Aplicación", "req": "seguridad"},
    {"codigo": "AU-8", "nombre": "Time Stamps", "riesgo": "Eventos con horas inconsistentes entre servidores", "punto": "Reloj sincronizado (systemd-timesyncd) y registros en UTC", "capa": "Proveedor", "req": "seguridad"},
    {"codigo": "AU-11", "nombre": "Audit Record Retention", "riesgo": "Pérdida de evidencia antes de una auditoría", "punto": "Rotación de auth.log/audit.log y respaldo con retención de {RETENCION} días", "capa": "Aplicación", "req": "seguridad"},
    {"codigo": "AU-12", "nombre": "Audit Record Generation", "riesgo": "Eventos críticos que no generan registro", "punto": "Reglas auditd cargadas con augenrules y auditoría de cada acción de la app", "capa": "Aplicación", "req": "seguridad"},
    {"codigo": "CM-2", "nombre": "Baseline Configuration", "riesgo": "Configuraciones distintas sin control entre ambientes", "punto": "Scripts del instalador versionados en GitHub y AMI endurecida como línea base", "capa": "Proveedor", "req": "disponibilidad"},
    {"codigo": "CM-6", "nombre": "Configuration Settings", "riesgo": "Parámetros inseguros por defecto", "punto": "sshd_config.d/10-ti3062.conf, php.ini (expose_php Off), ServerTokens Prod, TLS mínimo 1.2", "capa": "Red", "req": "seguridad"},
    {"codigo": "CP-2", "nombre": "Contingency Plan", "riesgo": "No saber cómo actuar ante una caída", "punto": "Procedimiento documentado: restaurar respaldo, relanzar desde AMI o rescatar el disco", "capa": "Proveedor", "req": "disponibilidad"},
    {"codigo": "CP-4", "nombre": "Contingency Plan Testing", "riesgo": "Planes de continuidad que no funcionan cuando se necesitan", "punto": "bd/04-probar-restauracion.sh y prueba de relanzamiento desde AMI", "capa": "Proveedor", "req": "disponibilidad"},
    {"codigo": "CP-6", "nombre": "Alternate Storage Site", "riesgo": "Perder los respaldos junto con la instancia", "punto": "Copia de respaldos cifrados fuera de bd-{NN} (snapshot o almacenamiento externo)", "capa": "Proveedor", "req": "disponibilidad"},
    {"codigo": "CP-7", "nombre": "Alternate Processing Site", "riesgo": "Sin capacidad de operar si falla la zona {ZONA}", "punto": "Mejora: réplica en otra AZ o AMI lista para relanzar en otra zona", "capa": "Proveedor", "req": "disponibilidad"},
    {"codigo": "IR-4", "nombre": "Incident Handling", "riesgo": "Incidentes atendidos sin método ni registro", "punto": "Registro del incidente como hallazgo, contención (SG, bloqueo de cuenta) y recuperación", "capa": "Aplicación", "req": "seguridad"},
    {"codigo": "IR-6", "nombre": "Incident Reporting", "riesgo": "Incumplir la obligación de reportar incidentes", "punto": "Reporte al responsable y, si aplica, a la ANCI según la Ley 21.663", "capa": "Proveedor", "req": "seguridad"},
    {"codigo": "RA-3", "nombre": "Risk Assessment", "riesgo": "Controles elegidos sin conocer las amenazas reales", "punto": "Análisis de riesgos residuales y CIA en el módulo Validación y cierre", "capa": "Proveedor", "req": "seguridad"},
    {"codigo": "RA-5", "nombre": "Vulnerability Monitoring and Scanning", "riesgo": "Vulnerabilidades conocidas sin detectar", "punto": "nmap desde el exterior (P2) y mejora con Lynis o escaneo periódico", "capa": "Red", "req": "seguridad"},
    {"codigo": "SC-5", "nombre": "Denial-of-Service Protection", "riesgo": "Saturación del servicio web", "punto": "Límites de Apache/PHP y mejora con AWS WAF o limitación de tasa", "capa": "Red", "req": "disponibilidad"},
    {"codigo": "SC-12", "nombre": "Cryptographic Key Establishment and Management", "riesgo": "Llaves privadas expuestas o sin rotación", "punto": "CA propia en bd-{NN} (/etc/ti3062/tls, 600), llaves ED25519 por usuario, frase LUKS fuera del repositorio", "capa": "Proveedor", "req": "seguridad"},
    {"codigo": "SC-13", "nombre": "Cryptographic Protection", "riesgo": "Algoritmos débiles en tránsito o en reposo", "punto": "TLS 1.2/1.3, LUKS2 (AES-XTS), hash argon2id/bcrypt para contraseñas", "capa": "Proveedor", "req": "seguridad"},
    {"codigo": "SI-2", "nombre": "Flaw Remediation", "riesgo": "Paquetes con vulnerabilidades sin parchar", "punto": "apt-get upgrade en el instalador y mejora con unattended-upgrades", "capa": "Proveedor", "req": "seguridad"},
    {"codigo": "SI-4", "nombre": "System Monitoring", "riesgo": "Ataques en curso que nadie ve", "punto": "Panel en vivo de la app, aureport/ausearch y registro del firewall ({FIREWALL})", "capa": "Red", "req": "seguridad"},
    {"codigo": "AU-9(2)", "nombre": "Store on Separate Physical Systems", "riesgo": "Un atacante con root borra los registros locales", "punto": "Mejora: enviar auditd, auth.log y auditoria_app a un servidor externo", "capa": "Aplicación", "req": "seguridad"},
    {"codigo": "IA-2(2)", "nombre": "MFA to Non-privileged Accounts", "riesgo": "Suplantación con llaves robadas de cuentas no administrativas", "punto": "Mejora: TOTP también para {G_DEV} y {G_AUDIT}", "capa": "Identidad", "req": "seguridad"},
]

# Familia, descripción, evidencia sugerida y prueba asociada de cada control
DETALLE = {
    "AC-2": ("AC · Control de acceso", "Gestionar el ciclo de vida de las cuentas: creación, asignación, revisión y desactivación.", "getent passwd; passwd -S ubuntu; pantalla Usuarios de la app", "P11"),
    "AC-3": ("AC · Control de acceso", "Aplicar las autorizaciones aprobadas en cada acceso a información o funciones.", "Auditor intentando registrar → «Tu rol no permite esta acción»", "P11"),
    "AC-5": ("AC · Control de acceso", "Separar funciones para que ninguna persona controle un proceso crítico completo.", "sudo -l -U {U_DEV}; sudo -l -U {U_AUDIT}; roles de la app", "P7"),
    "AC-6": ("AC · Control de acceso", "Otorgar solo los privilegios necesarios para cada función.", "GRANTs de app_{NN}; /etc/sudoers.d/", "P3"),
    "AC-7": ("AC · Control de acceso", "Limitar los intentos de ingreso fallidos y bloquear la cuenta.", "Auditoría de la app: login_fallido y cuenta_bloqueada", "P10"),
    "AC-8": ("AC · Control de acceso", "Mostrar un aviso de uso autorizado antes de dar acceso.", "Pantalla de ingreso de la app y banner SSH (/etc/issue.net)", "P1"),
    "AC-11": ("AC · Control de acceso", "Bloquear o cerrar la sesión tras un periodo de inactividad.", "Mensaje «Tu sesión expiró» tras 15 min", "P10"),
    "AC-12": ("AC · Control de acceso", "Terminar automáticamente las sesiones por inactividad o duración.", "sshd -T | grep clientalive; expiración de la app", "P5"),
    "AC-17": ("AC · Control de acceso", "Controlar y restringir el acceso remoto.", "sshd -T filtrado; SG 22 solo desde IP admin", "P5"),
    "AU-2": ("AU · Auditoría", "Definir qué eventos se registran.", "auditctl -l; tabla auditoria_app", "P7"),
    "AU-3": ("AU · Auditoría", "Registrar qué, cuándo, dónde, origen, resultado e identidad de cada evento.", "Detalle de un evento en Auditoría de la app", "P13"),
    "AU-6": ("AU · Auditoría", "Revisar y analizar los registros de forma periódica.", "ausearch -k uso_sudo -i; aureport --summary", "P7"),
    "AU-8": ("AU · Auditoría", "Usar marcas de tiempo confiables y consistentes.", "timedatectl; fechas en auditoria_app", "P13"),
    "AU-9": ("AU · Auditoría", "Proteger la información de auditoría contra modificación o borrado.", "DELETE FROM auditoria_app → command denied", "P13"),
    "AU-9(2)": ("AU · Auditoría", "Guardar los registros en un sistema separado del que se audita.", "Propuesta de mejora", ""),
    "AU-11": ("AU · Auditoría", "Conservar los registros el tiempo requerido.", "logrotate; retención del respaldo", ""),
    "AU-12": ("AU · Auditoría", "Generar registros de los eventos definidos.", "augenrules --load; eventos en la app", "P7"),
    "CM-2": ("CM · Gestión de configuración", "Mantener una configuración base documentada y controlada.", "Repositorio ti3062-{NN} y AMI endurecida", ""),
    "CM-6": ("CM · Gestión de configuración", "Establecer parámetros de configuración seguros.", "sshd -T; php -i | grep expose_php; curl -I", "P5"),
    "CM-7": ("CM · Gestión de configuración", "Habilitar solo funciones, puertos y servicios necesarios.", "ss -tlnp; reglas de {FIREWALL}", "P2"),
    "CP-2": ("CP · Contingencia", "Contar con un plan de contingencia documentado.", "Procedimiento de recuperación en el informe", ""),
    "CP-4": ("CP · Contingencia", "Probar el plan de contingencia.", "Salida de bd/04-probar-restauracion.sh", ""),
    "CP-6": ("CP · Contingencia", "Mantener respaldos en un sitio alternativo.", "Snapshots y copia externa", ""),
    "CP-7": ("CP · Contingencia", "Contar con un sitio alternativo de procesamiento.", "Propuesta de réplica en otra AZ", ""),
    "CP-9": ("CP · Contingencia", "Respaldar la información del sistema.", "cat /etc/cron.d/ti3062-respaldo; ls -lh /respaldos", ""),
    "CP-10": ("CP · Contingencia", "Recuperar y reconstituir el sistema tras una falla.", "Restauración probada y AMI de recuperación", ""),
    "IA-2": ("IA · Identificación y autenticación", "Identificar y autenticar de forma única a cada usuario.", "Usuarios nominativos en el SO y en la app", "P1"),
    "IA-2(1)": ("IA · Identificación y autenticación", "Exigir MFA a las cuentas privilegiadas.", "Login pidiendo Verification code", "P6"),
    "IA-2(2)": ("IA · Identificación y autenticación", "Exigir MFA a las cuentas no privilegiadas.", "Propuesta de mejora", ""),
    "IA-5": ("IA · Identificación y autenticación", "Gestionar los autenticadores (llaves, contraseñas, secretos).", "Llaves ED25519; /etc/ti3062/db.ini 640", "P5"),
    "IA-5(1)": ("IA · Identificación y autenticación", "Aplicar reglas a la autenticación por contraseña.", "Contraseña corta rechazada; hash en usuarios_app", "P10"),
    "IR-4": ("IR · Respuesta a incidentes", "Manejar los incidentes: preparación, detección, contención y recuperación.", "Hallazgo documentado con su corrección", ""),
    "IR-6": ("IR · Respuesta a incidentes", "Reportar los incidentes a quien corresponda.", "Procedimiento de reporte", ""),
    "RA-3": ("RA · Evaluación de riesgos", "Evaluar los riesgos del sistema.", "Riesgos residuales y análisis CIA", ""),
    "RA-5": ("RA · Evaluación de riesgos", "Buscar vulnerabilidades de forma periódica.", "nmap -Pn -p 22,{PUERTO} {BD_IP}", "P2"),
    "SC-5": ("SC · Protección de sistemas y comunicaciones", "Proteger contra la denegación de servicio.", "Configuración de Apache/PHP", ""),
    "SC-7": ("SC · Protección de sistemas y comunicaciones", "Controlar las comunicaciones en los límites del sistema.", "Mapa de la VPC, rutas y Security Groups", "P2"),
    "SC-8": ("SC · Protección de sistemas y comunicaciones", "Proteger la confidencialidad e integridad de la información en tránsito.", "Panel en vivo con TLS; tcpdump ilegible", "P9"),
    "SC-12": ("SC · Protección de sistemas y comunicaciones", "Establecer y gestionar las llaves criptográficas.", "ls -l /etc/ti3062/tls; openssl x509 -noout -enddate", "P9"),
    "SC-13": ("SC · Protección de sistemas y comunicaciones", "Usar criptografía aprobada.", "Versión TLS y cifrado negociado; cryptsetup luksDump", "P9"),
    "SC-23": ("SC · Protección de sistemas y comunicaciones", "Proteger la autenticidad de las sesiones.", "curl -kI: Set-Cookie HttpOnly; Secure; SameSite=Strict", "P11"),
    "SC-28": ("SC · Protección de sistemas y comunicaciones", "Proteger la información en reposo.", "lsblk -f; cryptsetup status", "P8"),
    "SI-2": ("SI · Integridad del sistema", "Corregir fallas y aplicar parches.", "apt list --upgradable", ""),
    "SI-4": ("SI · Integridad del sistema", "Monitorear el sistema para detectar ataques.", "Panel en vivo; aureport -l", "P10"),
    "SI-10": ("SI · Integridad del sistema", "Validar la información de entrada.", "Texto <script> mostrado escapado", "P12"),
    "SI-11": ("SI · Integridad del sistema", "Manejar los errores sin revelar información sensible.", "Mensaje genérico ante un error", "P12"),
}

# Controles que se destacan según el patrón de negocio de la temática
RELEVANTES = {
    "inventario": ["SI-10", "AU-3", "AC-5", "CP-9"],
    "reservas": ["SI-10", "AC-3", "AU-3", "SC-23"],
    "prestamos": ["AC-2", "AU-3", "SI-10", "AC-3"],
    "ordenes": ["IR-4", "CP-2", "CP-4", "CP-10", "SI-4"],
    "membresias": ["IA-5(1)", "AC-2", "SC-28", "AU-11"],
}

# Hallazgos típicos del proyecto (se sugieren en Validación y cierre)
HALLAZGOS = [
    {"tipo": "Riesgo", "descripcion": "AWS CloudTrail no está disponible en AWS Academy (AccessDeniedException).", "req": "RNF-06", "control": "AU-2 / AU-6", "impacto": "No se pueden auditar cambios hechos desde la consola o CloudShell.", "accion": "Control compensatorio en el SO (auditd, auth.log, auditoria_app) y CloudTrail en una cuenta propia como mejora."},
    {"tipo": "Desviación", "descripcion": "El certificado HTTPS de web-{NN} es autofirmado: el navegador muestra una advertencia.", "req": "RNF-07", "control": "SC-8", "impacto": "Un usuario podría acostumbrarse a aceptar certificados falsos.", "accion": "Dominio propio y certificado de CA pública (Let's Encrypt)."},
    {"tipo": "Riesgo", "descripcion": "El volumen LUKS de bd-{NN} se debe abrir a mano tras cada reinicio del laboratorio.", "req": "RNF-04", "control": "CP-9", "impacto": "Si nadie lo abre, el respaldo diario falla y queda registrado como error.", "accion": "Procedimiento de inicio documentado y alerta si /respaldos no está montado."},
    {"tipo": "Riesgo", "descripcion": "web-{NN} y bd-{NN} están en una sola zona de disponibilidad ({ZONA}).", "req": "RNF-04", "control": "CP-7", "impacto": "Una falla de la zona detiene todo el servicio.", "accion": "AMI de recuperación y réplica en otra AZ como mejora."},
    {"tipo": "Comportamiento esperado", "descripcion": "La conexión a la base de datos sin TLS es rechazada por el servidor.", "req": "RNF-07", "control": "SC-8", "impacto": "Confirma que no existe un canal en texto plano web→bd.", "accion": "Mantener el TLS obligatorio en {MOTOR}."},
    {"tipo": "Comportamiento esperado", "descripcion": "La cuenta de la app se bloquea tras 5 intentos fallidos y el evento queda registrado.", "req": "RNF-08", "control": "AC-7", "impacto": "Mitiga ataques de fuerza bruta.", "accion": "Revisar periódicamente los bloqueos en Auditoría."},
    {"tipo": "Falla", "descripcion": "Una regla de firewall o Security Group no coincide con la otra capa (inconsistencia SG / {FIREWALL}).", "req": "RNF-01", "control": "SC-7", "impacto": "Puede dejar un servicio sin acceso o abrir un puerto de más.", "accion": "Alinear ambas capas y volver a ejecutar las pruebas P2 y P3."},
    {"tipo": "Riesgo", "descripcion": "Los registros de auditoría se guardan solo en las mismas instancias.", "req": "RNF-06", "control": "AU-9(2)", "impacto": "Un atacante con root podría borrar la evidencia.", "accion": "Enviar los registros a un servidor externo."},
]

# Glosario de términos del informe
GLOSARIO = [
    ("VPC", "Red virtual aislada dentro de AWS donde se crean las subredes del proyecto."),
    ("Security Group", "Firewall con estado de AWS que se aplica a cada instancia."),
    ("Subred privada", "Subred sin ruta hacia Internet; aloja la base de datos."),
    ("NAT temporal", "Salida a Internet usada solo para instalar paquetes en bd y eliminada después."),
    ("MFA / TOTP", "Segundo factor de autenticación con códigos temporales de 6 dígitos."),
    ("LUKS", "Cifrado de disco de Linux usado para el volumen de respaldos."),
    ("TLS", "Protocolo que cifra la comunicación entre navegador, web y base de datos."),
    ("CA", "Autoridad certificadora; en el proyecto, una CA propia firma el certificado de bd."),
    ("auditd", "Servicio de auditoría del kernel de Linux."),
    ("RPO / RTO", "Pérdida de datos máxima aceptable / tiempo máximo para recuperar el servicio."),
    ("MTTR", "Tiempo medio de recuperación de un incidente."),
    ("CIA", "Confidencialidad, integridad y disponibilidad de la información."),
    ("NIST SP 800-53", "Catálogo de controles de seguridad y privacidad del NIST (Rev. 5)."),
    ("Gobierno TI", "Marco que alinea la tecnología con los objetivos de la organización: identidad, acceso, monitoreo, continuidad y respaldo."),
    ("AMI", "Imagen de una instancia EC2 usada para recuperarla o replicarla."),
]

# Contenido mínimo del informe (pauta Evaluación 4 + guía U4). tipo: min | ids | campo | evidencia
REQUISITOS = [
    {"txt": "≥3 hitos", "modulo": "planificacion", "tipo": "min", "ruta": "hitos", "min": 3},
    {"txt": "≥10 tareas con responsable, fechas, dependencia y estado", "modulo": "planificacion", "tipo": "min", "ruta": "tareas", "min": 10},
    {"txt": "Integrantes del equipo con cargo y rol", "modulo": "equipo", "tipo": "min", "ruta": "personal", "min": 1},
    {"txt": "Contexto, actores, procesos y necesidades del caso", "modulo": "problema", "tipo": "campo", "ruta": "problema", "campos": ["contexto", "actores", "procesos", "necesidades"]},
    {"txt": "3 a 5 características clave", "modulo": "problema", "tipo": "min", "ruta": "caracteristicas", "min": 3, "max": 5},
    {"txt": "≥4 requerimientos funcionales (RF-XX)", "modulo": "problema", "tipo": "min", "ruta": "requerimientos", "min": 4, "filtro": {"tipo": "RF"}},
    {"txt": "≥4 requerimientos no funcionales (RNF-XX)", "modulo": "problema", "tipo": "min", "ruta": "requerimientos", "min": 4, "filtro": {"tipo": "RNF"}},
    {"txt": "Dependencias y limitaciones registradas", "modulo": "problema", "tipo": "min", "ruta": "limitaciones", "min": 1},
    {"txt": "≥2 proveedores cloud (AWS y otro) con costo y fuente", "modulo": "cloud", "tipo": "min", "ruta": "proveedores", "min": 2},
    {"txt": "Selección justificada y zona de disponibilidad", "modulo": "cloud", "tipo": "campo", "ruta": "seleccion", "campos": ["justificacion", "zona", "zonaJustificacion"]},
    {"txt": "≥3 controles NIST con riesgo, punto, capa y requerimiento", "modulo": "nist", "tipo": "min", "ruta": "controles", "min": 3},
    {"txt": "Controles obligatorios del proyecto presentes", "modulo": "nist", "tipo": "ids", "ruta": "controles", "clave": "codigo", "ids": "obligatorios"},
    {"txt": "Bitácora con evidencias (captura)", "modulo": "implementacion", "tipo": "evidencia", "ruta": "bitacora", "min": 1},
    {"txt": "Pruebas P1 a P4 obligatorias", "modulo": "validacion", "tipo": "ids", "ruta": "pruebas", "clave": "id", "ids": ["P1", "P2", "P3", "P4"]},
    {"txt": "Hallazgos vinculados a RF/RNF y control NIST", "modulo": "validacion", "tipo": "min", "ruta": "hallazgos", "min": 1},
    {"txt": "Análisis CIA de las tres dimensiones", "modulo": "validacion", "tipo": "ids", "ruta": "cia", "clave": "dimension", "ids": ["Confidencialidad", "Integridad", "Disponibilidad"]},
    {"txt": "≥3 riesgos residuales con impacto", "modulo": "validacion", "tipo": "min", "ruta": "riesgos", "min": 3},
    {"txt": "Coherencia con Gobierno TI (identidad, acceso, monitoreo, continuidad y respaldo)", "modulo": "validacion", "tipo": "ids", "ruta": "gobierno", "clave": "eje", "ids": ["Identidad", "Acceso", "Monitoreo", "Continuidad", "Respaldo"]},
    {"txt": "≥3 acciones de mejora con control NIST", "modulo": "validacion", "tipo": "min", "ruta": "mejoras", "min": 3},
    {"txt": "Conclusiones del equipo", "modulo": "validacion", "tipo": "campo", "ruta": "cierre", "campos": ["conclusion"]},
    {"txt": "Portada e introducción (propósito, alcance y escenario)", "modulo": "informe", "tipo": "campo", "ruta": "informe", "campos": ["titulo", "proposito", "alcance", "escenario"]},
]

# Textos base de los campos de texto (sistema → «Sugerir texto»). Se rellenan con los marcadores de la plantilla.
TEXTOS = {
    "problema.impacto": ["Sin una solución segura, los usuarios de {APP} pierden información, se exponen datos personales protegidos por la Ley 21.719 y no es posible auditar quién accedió o modificó registros."],
    "seleccion.justificacion": ["AWS cumple los RF con EC2 y {MOTOR} y permite implementar los RNF de seguridad (subred privada, Security Groups por referencia y TLS web→bd), disponibilidad (snapshots, AMI y respaldo cifrado) y rendimiento (t3.micro). {ALT} ofrece capacidades equivalentes, pero el curso dispone de AWS Academy y la topología exigida está definida sobre AWS."],
    "seleccion.gobierno": ["La selección se alinea con los ejes de Gobierno TI: identidad (usuarios nominativos por rol en el SO y en la app), acceso (mínimo privilegio, MFA y roles), monitoreo (auditd y auditoría de la app), continuidad (AMI y restauración probada) y respaldo (cron diario cifrado con retención de {RETENCION} días)."],
    "seleccion.zonaJustificacion": ["Se fija {ZONA} en ambas subredes para que web-{NN} y bd-{NN} compartan zona: menor latencia y sin costo de transferencia entre zonas. La falta de redundancia entre zonas se declara como riesgo residual y se propone una réplica como mejora (CP-7)."],
    "informe.proposito": ["Diseñar, implementar y validar en AWS una solución cloud segura para {TITULO}, que mejore la disponibilidad de acceso aplicando controles NIST SP 800-53 Rev. 5 en las capas de identidad, red, aplicación y proveedor."],
    "informe.alcance": ["Incluye la VPC-{NN} con subred pública y privada, las instancias web-{NN} y bd-{NN}, la aplicación {APP} con usuarios por rol y conexión cifrada a {MOTOR}, el endurecimiento del sistema operativo (MFA, sudoers, auditd, {FIREWALL}), el cifrado y respaldo de la base de datos, y la validación con las pruebas P1 a P13. No incluye alta disponibilidad multi-AZ, que se propone como mejora."],
    "informe.escenario": ["{CONTEXTO}"],
    "informe.intro1": ["El proyecto se organiza en tres hitos (análisis, implementación y validación) con tareas asignadas por rol: administración, desarrollo y auditoría."],
    "informe.intro2": ["Esta sección describe el problema del caso {APP}, sus características clave y los requerimientos que guían el diseño."],
    "informe.intro3": ["Se comparan AWS y {ALT} con criterios técnicos, de seguridad, disponibilidad y costo, y se justifica la selección."],
    "informe.intro4": ["Se identifican los componentes que requieren control de acceso y los controles NIST SP 800-53 Rev. 5 que protegen cada capa."],
    "informe.intro5": ["Se documenta la implementación en AWS: topología, Security Groups, endurecimiento del SO, cifrado, respaldo y evidencias."],
    "informe.intro6": ["Se ejecutan las pruebas P1 a P13 y se contrastan los resultados con los requerimientos y los controles NIST."],
    "informe.intro7": ["Se evalúa el nivel de seguridad alcanzado (CIA), los riesgos residuales, la coherencia con Gobierno TI y las mejoras propuestas."],
    "cierre.conclusion": ["La solución implementada en AWS protege la confidencialidad (subred privada, TLS web→bd, LUKS y MFA), la integridad (validación de entradas, transacciones y auditoría inmutable) y la disponibilidad (respaldo diario cifrado, restauración probada y AMI de recuperación) de {APP}. Las pruebas P1 a P13 confirman el funcionamiento de los controles; los riesgos residuales se concentran en la zona única y en las limitaciones de AWS Academy."],
    "cierre.aprendizajes": ["Aplicar controles en varias capas (red, SO y aplicación) compensa las limitaciones del proveedor; documentar cada configuración con su evidencia facilita la auditoría y la defensa."],
}

# Bloques del sistema que reciben sugerencias y su clave de comparación
CLAVES = {
    "hitos": "id", "tareas": "nombre", "personal": "cargo", "caracteristicas": "descripcion", "requerimientos": "id",
    "dependencias": "componente", "limitaciones": "descripcion", "proveedores": "nombre", "componentes": "componente",
    "controles": "codigo", "sg": "justificacion", "bitacora": "configuracion", "pruebas": "id", "hallazgos": "descripcion",
    "cia": "dimension", "riesgos": "riesgo", "gobierno": "eje", "mejoras": "accion",
}


import re as _re


def rellenar(obj, valores):
    """Reemplaza los marcadores {CLAVE} en textos, listas y diccionarios (deja intactos los desconocidos)."""
    if isinstance(obj, str):
        return _re.sub(r"\{([A-Z_]+)\}", lambda m: str(valores.get(m.group(1), m.group(0))), obj)
    if isinstance(obj, list):
        return [rellenar(x, valores) for x in obj]
    if isinstance(obj, tuple):
        return tuple(rellenar(x, valores) for x in obj)
    if isinstance(obj, dict):
        return {k: rellenar(v, valores) for k, v in obj.items()}
    return obj


def todos_los_controles():
    return CONTROLES + CONTROLES_APP + CONTROLES_EXTRA
