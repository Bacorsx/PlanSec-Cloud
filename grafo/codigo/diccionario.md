---
tags: [codigo, generador]
archivo: diccionario.py
---
# diccionario.py

Diccionario base del proyecto TI3062 (fuente única). Contiene todos los controles NIST SP 800-53 Rev. 5 que aplican al proyecto y la información base que debe incluirse en el informe: bancos de texto por módulo, hallazgos típicos, glosario y el contenido mínimo exigido por la pauta y la guía U4. generar.py lo adapta a cada plantilla (NN, temática, motor, usuarios) y lo publica como data/diccionario-NN.json; el sistema de gestión lo usa para sugerir mientras se rellena. Marcadores disponibles en los textos: {NN} {NNIP} {APP} {MOTOR} {PUERTO} {WEB_IP} {BD_IP} {TABLA_P} {TABLA_H} {U_ADMIN} {U_DEV

[Abrir el archivo](<file:///C:/Users/Darcu/OneDrive/Desktop/seguridad/generador-ti3062/diccionario.py>)

## Usa

- [[generar]]
- [[04-probar-restauracion (sh)]]

## Lo usan

- [[README (md) · generador]]
- [[catalogo]]
- [[generar]]
- [[generar_grafo (py)]]

## Conceptos

[[AWS Academy]] · [[Auditoría de la app]] · [[Bloqueo por intentos]] · [[CSRF y CSP]] · [[Capa de informe]] · [[Diccionario]] · [[Endurecimiento del SO]] · [[Firewall de host]] · [[HTTPS]] · [[LUKS]] · [[MFA TOTP]] · [[NAT temporal]] · [[Pruebas P1–P13]] · [[Respaldo cifrado]] · [[Roles de la app]] · [[Security Groups]] · [[Sesión segura]] · [[VPC y subredes]] · [[auditd]]

## Controles NIST

[[AC-11]] · [[AC-12]] · [[AC-17]] · [[AC-2]] · [[AC-3]] · [[AC-5]] · [[AC-6]] · [[AC-7]] · [[AC-8]] · [[AU-11]] · [[AU-12]] · [[AU-2]] · [[AU-3]] · [[AU-6]] · [[AU-8]] · [[AU-9]] · [[CM-2]] · [[CM-6]] · [[CM-7]] · [[CP-10]] · [[CP-2]] · [[CP-4]] · [[CP-6]] · [[CP-7]] · [[CP-9]] · [[IA-2]] · [[IA-5]] · [[IR-4]] · [[IR-6]] · [[RA-3]] · [[RA-5]] · [[SC-12]] · [[SC-13]] · [[SC-23]] · [[SC-28]] · [[SC-5]] · [[SC-7]] · [[SC-8]] · [[SI-10]] · [[SI-11]] · [[SI-2]] · [[SI-4]]

Capa: [[Arquitectura]] · generador
