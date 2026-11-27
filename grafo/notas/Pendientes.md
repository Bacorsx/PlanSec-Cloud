---
tags: [nota, pendientes]
---
# Pendientes

Actualizado el 2026-11-27. Ver [[Continuar aquí]].

## Por validar en AWS real (AWS Academy)
- [ ] Recorrido completo de [[PASO-A-PASO (md)]] en un Learner Lab: [[01-crear-infra (sh)]], NAT, bd, web, hardening, LUKS, snapshots y AMI.
- [ ] [[auditd]] y la prueba P7 en EC2: en WSL el kernel no permite iniciar auditd.
- [ ] [[01-hardening (sh)]] en el rol **web** con **nftables**: la prueba se interrumpió; solo se validó bd con ufw.
- [ ] [[IP elástica]] y [[03-snapshots-y-evidencias (sh)]] modo `ami` contra la API real.
- [ ] Cloudflare Pages con un repositorio generado real (que `/data/proyecto-NN.json` y `diccionario-NN.json` se publiquen).

## Por revisar
- [ ] Ver en pantalla el menú «Capa de informe» de la app ([[index (php)]]); las pruebas automáticas cubren la exportación, no el aspecto.
- [ ] Rendimiento del sistema con muchas capturas en el JSON (localStorage tiene un límite de unos 5 MB).
- [ ] Ubuntu 26.04 (sudo-rs) no está soportado: la guía pide elegir 24.04.

## Ideas posibles (no pedidas)
- Detección automática del límite de localStorage con aviso para exportar.
- Más temáticas por patrón.
- Exportar el informe también a .docx si el docente lo pidiera (hoy la pauta exige PDF generado por el sistema).

## Entorno local de esta sesión (temporal)
- Muestras servidas en WSL/localhost: sistema NN 09 (puerto 8709), copia de prueba NN 07 (8710) y app ContinuaDC (8088). Se apagan al cerrar la sesión o reiniciar WSL.
