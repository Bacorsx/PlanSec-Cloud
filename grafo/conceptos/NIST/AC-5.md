---
tags: [nist]
---
# AC-5 · Separation of Duties

**Familia:** AC · Control de acceso · **Capa:** Identidad

Separar funciones para que ninguna persona controle un proceso crítico completo.

- **Riesgo que mitiga:** Una sola persona puede ejecutar y aprobar cambios críticos
- **Punto de aplicación (plantilla):** Grupos {G_ADMIN}, {G_DEV} y {G_AUDIT} con sudoers distintos; roles admin/operador/auditor en la app
- **Evidencia sugerida:** sudo -l -U {U_DEV}; sudo -l -U {U_AUDIT}; roles de la app
- **Prueba asociada:** P7

## Dónde aparece en el código

- [[diccionario]]
- [[generar]]

Ver [[Diccionario del proyecto]]
