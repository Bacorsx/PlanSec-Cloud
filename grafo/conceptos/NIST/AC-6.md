---
tags: [nist]
---
# AC-6 · Least Privilege

**Familia:** AC · Control de acceso · **Capa:** Identidad

Otorgar solo los privilegios necesarios para cada función.

- **Riesgo que mitiga:** Uso indebido de privilegios por usuarios no administradores
- **Punto de aplicación (plantilla):** /etc/sudoers.d/ con comandos específicos por grupo y usuario de BD sin ALL
- **Evidencia sugerida:** GRANTs de app_{NN}; /etc/sudoers.d/
- **Prueba asociada:** P3

## Dónde aparece en el código

- [[01-hardening (sh)]]
- [[PASO-A-PASO (md)]]
- [[diccionario]]
- [[generar]]
- [[generar_grafo (py)]]
- [[index (php)]]

Ver [[Diccionario del proyecto]]
