---
tags: [nist]
---
# IA-5 · Authenticator Management

**Familia:** IA · Identificación y autenticación · **Capa:** Aplicación

Gestionar los autenticadores (llaves, contraseñas, secretos).

- **Riesgo que mitiga:** Credenciales débiles o expuestas en el código
- **Punto de aplicación (plantilla):** Llaves ED25519 por usuario y credenciales de BD en /etc/ti3062/db.ini fuera del repositorio
- **Evidencia sugerida:** Llaves ED25519; /etc/ti3062/db.ini 640
- **Prueba asociada:** P5

## Dónde aparece en el código

- [[50-app (sh)]]
- [[diccionario]]
- [[generar]]
- [[index (php)]]
- [[nucleo (php)]]

Ver [[Diccionario del proyecto]]
