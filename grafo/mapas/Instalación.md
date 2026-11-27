---
tags: [mapa]
---
# Orden de instalación

| Paso | Dónde | Script |
|---|---|---|
| 0 | PC / CloudShell | [[revisar-instalador (sh)]] |
| 1 | CloudShell | [[01-crear-infra (sh)]] y [[02-nat-temporal (sh)]] crear |
| 2 | bd-NN | [[00-paquetes (sh)]] bd → NAT eliminar → [[01-configurar-bd (sh)]] |
| 3 | web-NN | [[00-paquetes (sh)]] web → [[01-instalar-web (sh)]] |
| 4 | ambas | [[01-hardening (sh)]] → TOTP → [[99-cerrar-ubuntu (sh)]] |
| 5 | bd-NN | [[02-luks-respaldos (sh)]] → [[03-respaldo-cron (sh)]] → [[04-probar-restauracion (sh)]] |
| 6 | CloudShell | [[03-snapshots-y-evidencias (sh)]] (snapshots + AMI) |
| Siempre | bd-NN | [[05-tras-reinicio (sh)]] tras reiniciar el laboratorio |
| Evidencias | ambas | [[evidencias (sh)]] |
