---
tags: [codigo, generador]
archivo: generar.py
---
# generar.py

Generador automático del Proyecto Integrador TI3062 (Evaluación 4). Crea, para cada estudiante, un repositorio ti3062-NN listo para GitHub + Cloudflare Pages + AWS: - Sistema web de gestión/planificación que genera el PDF desde los datos (raíz del repo) - data/proyecto-NN.json precargado (borrador a completar con evidencia real) - app-caso/: aplicación PHP con 2 tablas relacionadas para web-NN - instalador/: scripts para AWS (VPC, SG, EC2, NAT temporal, snapshots) y para las instancias - PASO-A-PASO.md personalizado con el NN, nombres y comandos exactos Cada combinación (temática, colores, tip

[Abrir el archivo](<file:///C:/Users/Darcu/OneDrive/Desktop/seguridad/generador-ti3062/generar.py>)

## Usa

- [[README (md) · generador]]
- [[catalogo]]
- [[diccionario]]
- [[PASO-A-PASO (md)]]
- [[crear-usuario (php)]]
- [[pre-push]]
- [[01-crear-infra (sh)]]
- [[02-nat-temporal (sh)]]
- [[03-snapshots-y-evidencias (sh)]]
- [[01-configurar-bd (sh)]]
- [[02-luks-respaldos (sh)]]
- [[03-respaldo-cron (sh)]]
- [[04-probar-restauracion (sh)]]
- [[01-hardening (sh)]]
- [[evidencias (sh)]]
- [[revisar-instalador (sh)]]
- [[verificar-secretos (sh)]]
- [[01-instalar-web (sh)]]

## Lo usan

- [[LEEME (md) · generador]]
- [[README (md) · generador]]
- [[diccionario]]
- [[generar_grafo (py)]]
- [[50-app (sh)]]
- [[70-generador (sh)]]
- [[run (sh)]]

## Conceptos

[[AWS Academy]] · [[Auditoría de la app]] · [[Bloqueo por intentos]] · [[Borrador precargado]] · [[CA del proyecto]] · [[CSRF y CSP]] · [[Capa de enfoque]] · [[Capa de informe]] · [[Cloudflare Pages]] · [[Diccionario]] · [[Endurecimiento del SO]] · [[Firewall de host]] · [[HTTPS]] · [[IP elástica]] · [[LUKS]] · [[MFA TOTP]] · [[Manifiesto de scripts]] · [[NAT temporal]] · [[Patrón de negocio]] · [[Pruebas P1–P13]] · [[Respaldo cifrado]] · [[Revisión de secretos]] · [[Roles de la app]] · [[Security Groups]] · [[Sesión segura]] · [[TLS web→bd]] · [[VPC y subredes]] · [[Variabilidad por estudiante]] · [[auditd]]

## Controles NIST

[[AC-11]] · [[AC-12]] · [[AC-17]] · [[AC-2]] · [[AC-3]] · [[AC-5]] · [[AC-6]] · [[AC-7]] · [[AC-8]] · [[AU-11]] · [[AU-12]] · [[AU-2]] · [[AU-3]] · [[AU-6]] · [[AU-8]] · [[AU-9]] · [[CM-2]] · [[CM-6]] · [[CM-7]] · [[CP-10]] · [[CP-2]] · [[CP-4]] · [[CP-6]] · [[CP-7]] · [[CP-9]] · [[IA-2]] · [[IA-5]] · [[IR-4]] · [[IR-6]] · [[RA-3]] · [[RA-5]] · [[SC-12]] · [[SC-13]] · [[SC-23]] · [[SC-28]] · [[SC-5]] · [[SC-7]] · [[SC-8]] · [[SI-10]] · [[SI-11]] · [[SI-2]] · [[SI-4]]

Capa: [[Arquitectura]] · generador
