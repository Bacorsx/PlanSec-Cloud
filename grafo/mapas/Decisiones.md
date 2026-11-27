---
tags: [mapa]
---
# Decisiones y por qué

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
- **Controles en el SO**: AWS Academy no permite IAM ni CloudTrail (hallazgo HZ-01).
