# -*- coding: utf-8 -*-
"""Catálogo de variantes del generador TI3062.

Cada estudiante recibe una combinación distinta (según su NN, nombre y semilla):
temática del caso, tablas, paleta, tipografía, distribución, nombres de grupos,
motor de BD, firewall, proveedor alternativo, controles NIST, riesgos y mejoras.
"""

# Temáticas del caso (patrones de negocio y vocabulario): ver temas.py
from temas import TEMAS, RF_PATRON  # noqa: E402,F401

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

# Controles NIST, riesgos residuales y mejoras: fuente única en diccionario.py
from diccionario import CONTROLES, CONTROLES_APP, RIESGOS_RESIDUALES, MEJORAS  # noqa: E402,F401
