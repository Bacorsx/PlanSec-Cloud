---
tags: [codigo, instalador]
archivo: plantillas/instalador/comun/01-hardening.sh
---
# 01-hardening.sh

Endurecimiento del SO (Unidad 2): identidades, sudoers, SSH, MFA, auditd y firewall de host. Uso: sudo bash 01-hardening.sh web|bd [IP_ADMIN] - IP_ADMIN (solo web): tu IP pública para SSH. Debe coincidir con sg-web-NN. - Coloca antes las llaves públicas ED25519 en ../llaves/<usuario>.pub Mantén una segunda sesión SSH abierta mientras lo ejecutas, por si algo falla.

[Abrir el archivo](<file:///C:/Users/Darcu/OneDrive/Desktop/seguridad/generador-ti3062/plantillas/instalador/comun/01-hardening.sh>)

## Usa

- [[99-cerrar-ubuntu (sh)]]
- [[config (env)]]

## Lo usan

- [[README (md) · generador]]
- [[generar]]
- [[PASO-A-PASO (md)]]
- [[30-hardening (sh)]]
- [[80-capas (sh)]]

## Conceptos

[[Endurecimiento del SO]] · [[Firewall de host]] · [[MFA TOTP]] · [[Security Groups]] · [[auditd]]

## Controles NIST

[[AC-6]]

Capa: [[Arquitectura]] · instalador
