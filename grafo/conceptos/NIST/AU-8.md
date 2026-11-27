---
tags: [nist]
---
# AU-8 · Time Stamps

**Familia:** AU · Auditoría · **Capa:** Proveedor

Usar marcas de tiempo confiables y consistentes.

- **Riesgo que mitiga:** Eventos con horas inconsistentes entre servidores
- **Punto de aplicación (plantilla):** Reloj sincronizado (systemd-timesyncd) y registros en UTC
- **Evidencia sugerida:** timedatectl; fechas en auditoria_app
- **Prueba asociada:** P13

## Dónde aparece en el código

- [[diccionario]]
- [[generar]]

Ver [[Diccionario del proyecto]]
