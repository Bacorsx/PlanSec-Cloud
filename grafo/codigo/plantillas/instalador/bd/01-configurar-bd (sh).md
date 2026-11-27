---
tags: [codigo, instalador]
archivo: plantillas/instalador/bd/01-configurar-bd.sh
---
# 01-configurar-bd.sh

Configura el motor de BD en bd-NN: - escucha solo en la IP privada y exige TLS (certificado de bd firmado por una CA propia del proyecto, SC-8) - base ti3062_NN con 4 tablas relacionadas (usuarios_app, maestro, operaciones, auditoria_app) - usuario exclusivo de la app solo desde la IP de web-NN, sin ALL, sin DELETE, y auditoría solo INSERT/SELECT (AU-9) Uso: sudo bash 01-configurar-bd.sh

[Abrir el archivo](<file:///C:/Users/Darcu/OneDrive/Desktop/seguridad/generador-ti3062/plantillas/instalador/bd/01-configurar-bd.sh>)

## Usa

- [[config (env)]]
- [[01-instalar-web (sh)]]

## Lo usan

- [[README (md) · generador]]
- [[generar]]
- [[PASO-A-PASO (md)]]
- [[50-app (sh)]]

## Conceptos

[[Auditoría de la app]] · [[CA del proyecto]] · [[Roles de la app]] · [[TLS web→bd]]

## Controles NIST

[[AU-9]] · [[SC-8]]

Capa: [[Arquitectura]] · instalador
