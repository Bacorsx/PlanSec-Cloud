---
tags: [nist]
---
# CM-7 · Least Functionality

**Familia:** CM · Gestión de configuración · **Capa:** Red

Habilitar solo funciones, puertos y servicios necesarios.

- **Riesgo que mitiga:** Servicios y puertos innecesarios que amplían la superficie de ataque
- **Punto de aplicación (plantilla):** Solo 80/443/22 en web y puerto BD/22 en bd; firewall de host por defecto deny
- **Evidencia sugerida:** ss -tlnp; reglas de {FIREWALL}
- **Prueba asociada:** P2

## Dónde aparece en el código

- [[diccionario]]
- [[generar]]

Ver [[Diccionario del proyecto]]
