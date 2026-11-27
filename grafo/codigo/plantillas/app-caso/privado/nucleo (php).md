---
tags: [codigo, enfoque]
archivo: plantillas/app-caso/privado/nucleo.php
---
# nucleo.php

Núcleo de la aplicación del caso — TI3062 NN {{NN}} Vive FUERA del webroot (/var/www/ti3062). Contiene conexión a la BD con TLS verificado, sesión segura, autenticación con bloqueo por intentos, control de acceso por rol, CSRF, validación y auditoría. Las credenciales NO están en el código: se leen de /etc/ti3062/db.ini (640 root:www-data).

[Abrir el archivo](<file:///C:/Users/Darcu/OneDrive/Desktop/seguridad/generador-ti3062/plantillas/app-caso/privado/nucleo.php>)

## Lo usan

- [[README (md) · generador]]
- [[crear-usuario (php)]]
- [[api (php)]]
- [[index (php)]]
- [[evidencias (sh)]]
- [[01-instalar-web (sh)]]
- [[50-app (sh)]]

## Conceptos

[[Auditoría de la app]] · [[Bloqueo por intentos]] · [[CSRF y CSP]] · [[HTTPS]] · [[Roles de la app]] · [[Sesión segura]] · [[TLS web→bd]]

## Controles NIST

[[AC-12]] · [[AC-2]] · [[AC-7]] · [[AU-2]] · [[AU-3]] · [[AU-9]] · [[IA-2]] · [[IA-5]] · [[SC-23]] · [[SC-8]] · [[SI-10]] · [[SI-11]]

Capa: [[Arquitectura]] · enfoque
