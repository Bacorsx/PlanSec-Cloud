---
tags: [nist]
---
# AU-2 · Event Logging

**Familia:** AU · Auditoría · **Capa:** Aplicación

Definir qué eventos se registran.

- **Riesgo que mitiga:** Cambios no autorizados sin trazabilidad
- **Punto de aplicación (plantilla):** auditd con reglas sobre sudo, passwd, sudoers y sshd_config
- **Evidencia sugerida:** auditctl -l; tabla auditoria_app
- **Prueba asociada:** P7

## Dónde aparece en el código

- [[diccionario]]
- [[generar]]
- [[nucleo (php)]]
- [[temas]]

Ver [[Diccionario del proyecto]]
