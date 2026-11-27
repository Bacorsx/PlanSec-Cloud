---
tags: [codigo, pruebas]
archivo: pruebas/LEEME.md
---
# LEEME.md

# Pruebas de PlanSec-Cloud (WSL Ubuntu 24.04) Simulan AWS en una sola máquina: una interfaz `aws0` con las IP de web-NN y bd-NN y una ruta local que hace que el tráfico hacia bd salga con origen web. Requieren `root`, MariaDB, PostgreSQL, Apache + PHP 8.3, `expect`, `oathtool` y `cryptsetup`. Uso: `wsl -d Ubuntu-24.04 -u root -- bash /mnt/c/.../generador-ti3062/pruebas/90-todo.sh`. Los proyectos d

[Abrir el archivo](<file:///C:/Users/Darcu/OneDrive/Desktop/seguridad/generador-ti3062/pruebas/LEEME.md>)

## Usa

- [[pre-push]]
- [[05-tras-reinicio (sh)]]
- [[revisar-instalador (sh)]]
- [[verificar-secretos (sh)]]
- [[20-luks-respaldo (sh)]]
- [[30-hardening (sh)]]
- [[50-app (sh)]]
- [[55-matriz (sh)]]
- [[70-generador (sh)]]
- [[80-capas (sh)]]
- [[90-todo (sh)]]

## Conceptos

[[Diccionario]] · [[Firewall de host]] · [[HTTPS]] · [[LUKS]] · [[MFA TOTP]] · [[Manifiesto de scripts]] · [[Paquete de evidencia]] · [[Pruebas P1–P13]] · [[Respaldo cifrado]] · [[Revisión de secretos]] · [[Roles de la app]] · [[auditd]]

## Controles NIST

[[AC-2]] · [[AU-9]]

Capa: [[Arquitectura]] · pruebas
