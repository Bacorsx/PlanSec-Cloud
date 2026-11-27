---
tags: [codigo, instalador]
archivo: plantillas/instalador/aws/02-nat-temporal.sh
---
# 02-nat-temporal.sh

Salida TEMPORAL a Internet para la subred privada (solo para instalar paquetes en bd-NN). Uso: bash 02-nat-temporal.sh crear | eliminar | estado El estado final evaluado debe quedar SIN salida: ejecuta "eliminar" apenas termines de instalar.

[Abrir el archivo](<file:///C:/Users/Darcu/OneDrive/Desktop/seguridad/generador-ti3062/plantillas/instalador/aws/02-nat-temporal.sh>)

## Usa

- [[config (env)]]

## Lo usan

- [[README (md) · generador]]
- [[generar]]
- [[PASO-A-PASO (md)]]
- [[01-crear-infra (sh)]]

## Conceptos

[[IP elástica]] · [[NAT temporal]] · [[VPC y subredes]]

Capa: [[Arquitectura]] · instalador
