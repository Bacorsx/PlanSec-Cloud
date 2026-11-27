---
tags: [nist]
---
# CM-6 · Configuration Settings

**Familia:** CM · Gestión de configuración · **Capa:** Red

Establecer parámetros de configuración seguros.

- **Riesgo que mitiga:** Parámetros inseguros por defecto
- **Punto de aplicación (plantilla):** sshd_config.d/10-ti3062.conf, php.ini (expose_php Off), ServerTokens Prod, TLS mínimo 1.2
- **Evidencia sugerida:** sshd -T; php -i | grep expose_php; curl -I
- **Prueba asociada:** P5

## Dónde aparece en el código

- [[diccionario]]
- [[generar]]

Ver [[Diccionario del proyecto]]
