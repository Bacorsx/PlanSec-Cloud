---
tags: [nist]
---
# CP-9 · System Backup

**Familia:** CP · Contingencia · **Capa:** Proveedor

Respaldar la información del sistema.

- **Riesgo que mitiga:** Pérdida de datos por falla o error humano
- **Punto de aplicación (plantilla):** cron diario con dump de la BD hacia /respaldos (LUKS)
- **Evidencia sugerida:** cat /etc/cron.d/ti3062-respaldo; ls -lh /respaldos
- **Prueba asociada:** —

## Dónde aparece en el código

- [[05-tras-reinicio (sh)]]
- [[diccionario]]
- [[generar]]

Ver [[Diccionario del proyecto]]
