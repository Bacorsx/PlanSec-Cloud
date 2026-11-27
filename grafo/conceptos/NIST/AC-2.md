---
tags: [nist]
---
# AC-2 · Account Management

**Familia:** AC · Control de acceso · **Capa:** Identidad

Gestionar el ciclo de vida de las cuentas: creación, asignación, revisión y desactivación.

- **Riesgo que mitiga:** Cuentas sin dueño, compartidas o activas después de dejar de usarse
- **Punto de aplicación (plantilla):** Usuarios nominativos {U_ADMIN}/{U_DEV}/{U_AUDIT}; cuenta ubuntu bloqueada; usuarios de la app desactivables y revalidados en cada petición
- **Evidencia sugerida:** getent passwd; passwd -S ubuntu; pantalla Usuarios de la app
- **Prueba asociada:** P11

## Dónde aparece en el código

- [[50-app (sh)]]
- [[LEEME (md) · pruebas]]
- [[diccionario]]
- [[generar]]
- [[nucleo (php)]]

Ver [[Diccionario del proyecto]]
