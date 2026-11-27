---
tags: [mapa]
---
# Flujo: del generador a la defensa

1. [[generar]] lee [[catalogo]], [[temas]] y [[diccionario]] y elige la variante del estudiante ([[Variabilidad por estudiante]]).
2. Escribe el repositorio `ti3062-NN`: la [[Capa de informe]] en la raíz, la [[Capa de enfoque]] en `app-caso/`, el instalador y `data/` (proyecto + diccionario).
3. El repositorio se publica en GitHub ([[Revisión de secretos]] antes de cada push) y la capa de informe en [[Cloudflare Pages]].
4. En AWS ([[AWS Academy]]): [[revisar-instalador (sh)]] → [[01-crear-infra (sh)]] ([[VPC y subredes]], [[Security Groups]], [[IP elástica]]) → [[02-nat-temporal (sh)]].
5. bd-NN: [[00-paquetes (sh)]] → [[01-configurar-bd (sh)]] ([[TLS web→bd]], [[CA del proyecto]]) → [[02-luks-respaldos (sh)]] ([[LUKS]]) → [[03-respaldo-cron (sh)]] → [[04-probar-restauracion (sh)]].
6. web-NN: [[01-instalar-web (sh)]] ([[HTTPS]], primer administrador) → [[01-hardening (sh)]] ([[Endurecimiento del SO]], [[MFA TOTP]], [[auditd]], [[Firewall de host]]).
7. La app ([[Capa de enfoque]]) exporta el [[Paquete de evidencia]]; el sistema ([[Capa de informe]]) lo importa, se revisan los [[Borrador precargado|borradores]] y se genera el PDF ([[PDF desde los datos]]).
8. Tras cada reinicio del laboratorio: [[05-tras-reinicio (sh)]].

Ver [[Arquitectura]] · [[Instalación]] · [[Pruebas]]
