---
tags: [nist]
---
# AU-9 · Protection of Audit Information

**Familia:** AU · Auditoría · **Capa:** Aplicación

Proteger la información de auditoría contra modificación o borrado.

- **Riesgo que mitiga:** Borrado o alteración del registro de actividad
- **Punto de aplicación (plantilla):** auditoria_app: el usuario de la app solo tiene INSERT/SELECT (sin UPDATE ni DELETE)
- **Evidencia sugerida:** DELETE FROM auditoria_app → command denied
- **Prueba asociada:** P13

## Dónde aparece en el código

- [[01-configurar-bd (sh)]]
- [[50-app (sh)]]
- [[LEEME (md) · pruebas]]
- [[app (js) · informe]]
- [[diccionario]]
- [[evidencia (php)]]
- [[generar]]
- [[generar_grafo (py)]]
- [[index (php)]]
- [[nucleo (php)]]

Ver [[Diccionario del proyecto]]
