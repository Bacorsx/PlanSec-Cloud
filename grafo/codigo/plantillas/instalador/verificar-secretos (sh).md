---
tags: [codigo, instalador]
archivo: plantillas/instalador/verificar-secretos.sh
---
# verificar-secretos.sh

Revisa el repositorio ti3062-{{NN}} antes de cada push: bloquea llaves privadas, secretos TOTP, credenciales de BD y otros archivos sensibles. Lo ejecuta .githooks/pre-push y se puede correr a mano. Uso (desde la raíz del repositorio): bash instalador/verificar-secretos.sh

[Abrir el archivo](<file:///C:/Users/Darcu/OneDrive/Desktop/seguridad/generador-ti3062/plantillas/instalador/verificar-secretos.sh>)

## Usa

- [[pre-push]]
- [[config (env)]]

## Lo usan

- [[README (md) · generador]]
- [[generar]]
- [[generar_grafo (py)]]
- [[PASO-A-PASO (md)]]
- [[README (md) · estudiante]]
- [[pre-push]]
- [[80-capas (sh)]]
- [[LEEME (md) · pruebas]]

## Conceptos

[[CA del proyecto]] · [[MFA TOTP]] · [[Patrón de negocio]] · [[Revisión de secretos]]

Capa: [[Arquitectura]] · instalador
