---
tags: [codigo, instalador]
archivo: plantillas/instalador/bd/05-tras-reinicio.sh
---
# 05-tras-reinicio.sh

Procedimiento tras reiniciar el laboratorio (AWS Academy detiene las instancias al cerrarlo). Abre el volumen LUKS (pide la frase; nunca se guarda), monta /respaldos, revisa el cron y la antigüedad del último respaldo, ejecuta uno si tiene más de 24 h y deja un resumen listo para la bitácora. Uso: sudo bash 05-tras-reinicio.sh

[Abrir el archivo](<file:///C:/Users/Darcu/OneDrive/Desktop/seguridad/generador-ti3062/plantillas/instalador/bd/05-tras-reinicio.sh>)

## Usa

- [[02-luks-respaldos (sh)]]
- [[03-respaldo-cron (sh)]]
- [[config (env)]]

## Lo usan

- [[README (md) · generador]]
- [[PASO-A-PASO (md)]]
- [[02-luks-respaldos (sh)]]
- [[80-capas (sh)]]
- [[LEEME (md) · pruebas]]

## Conceptos

[[AWS Academy]] · [[LUKS]] · [[Respaldo cifrado]]

## Controles NIST

[[CP-9]] · [[SC-28]]

Capa: [[Arquitectura]] · instalador
