---
tags: [nist]
---
# AC-7 · Unsuccessful Logon Attempts

**Familia:** AC · Control de acceso · **Capa:** Identidad

Limitar los intentos de ingreso fallidos y bloquear la cuenta.

- **Riesgo que mitiga:** Fuerza bruta contra cuentas de la aplicación
- **Punto de aplicación (plantilla):** App: bloqueo de 15 min tras 5 intentos fallidos, registrado en auditoria_app
- **Evidencia sugerida:** Auditoría de la app: login_fallido y cuenta_bloqueada
- **Prueba asociada:** P10

## Dónde aparece en el código

- [[50-app (sh)]]
- [[README (md) · generador]]
- [[app (js) · informe]]
- [[diccionario]]
- [[evidencia (php)]]
- [[generar]]
- [[generar_grafo (py)]]
- [[nucleo (php)]]

Ver [[Diccionario del proyecto]]
