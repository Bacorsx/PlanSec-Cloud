---
tags: [codigo, instalador]
archivo: plantillas/instalador/comun/99-cerrar-ubuntu.sh
---
# 99-cerrar-ubuntu.sh

Deja la instancia con un máximo de 3 usuarios interactivos: bloquea la cuenta inicial "ubuntu". Ejecutar SOLO después de comprobar que el administrador entra con llave + TOTP y puede usar sudo. Uso: sudo bash 99-cerrar-ubuntu.sh

[Abrir el archivo](<file:///C:/Users/Darcu/OneDrive/Desktop/seguridad/generador-ti3062/plantillas/instalador/comun/99-cerrar-ubuntu.sh>)

## Usa

- [[config (env)]]

## Lo usan

- [[README (md) · generador]]
- [[PASO-A-PASO (md)]]
- [[01-hardening (sh)]]
- [[30-hardening (sh)]]

## Conceptos

[[Endurecimiento del SO]] · [[MFA TOTP]]

Capa: [[Arquitectura]] · instalador
