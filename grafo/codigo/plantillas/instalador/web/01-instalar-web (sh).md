---
tags: [codigo, instalador]
archivo: plantillas/instalador/web/01-instalar-web.sh
---
# 01-instalar-web.sh

Despliega en web-NN la aplicación del caso y una copia del sistema de gestión en /gestion. - Webroot (/var/www/html): solo index.php, api.php, app.js y estilo.css - Lógica y configuración fuera del webroot (/var/www/ti3062); credenciales en /etc/ti3062/db.ini (640 root:www-data) - Conexión a bd-NN por TLS verificando el certificado con la CA del proyecto (SC-8); HTTPS con redirección desde HTTP - Crea el primer usuario administrador de la aplicación Uso: sudo bash 01-instalar-web.sh

[Abrir el archivo](<file:///C:/Users/Darcu/OneDrive/Desktop/seguridad/generador-ti3062/plantillas/instalador/web/01-instalar-web.sh>)

## Usa

- [[crear-usuario (php)]]
- [[nucleo (php)]]
- [[api (php)]]
- [[estilo (css)]]
- [[index (php)]]
- [[config (env)]]
- [[index (html)]]
- [[styles (css)]]

## Lo usan

- [[README (md) · generador]]
- [[generar]]
- [[PASO-A-PASO (md)]]
- [[01-configurar-bd (sh)]]
- [[50-app (sh)]]

## Conceptos

[[CA del proyecto]] · [[Capa de enfoque]] · [[Capa de informe]] · [[Diccionario]] · [[HTTPS]] · [[IP elástica]] · [[Pruebas P1–P13]] · [[TLS web→bd]]

## Controles NIST

[[SC-8]]

Capa: [[Arquitectura]] · instalador
