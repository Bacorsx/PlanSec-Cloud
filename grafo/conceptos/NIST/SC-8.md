---
tags: [nist]
---
# SC-8 · Transmission Confidentiality and Integrity

**Familia:** SC · Protección de sistemas y comunicaciones · **Capa:** Red

Proteger la confidencialidad e integridad de la información en tránsito.

- **Riesgo que mitiga:** Intercepción de datos entre el navegador, web y la BD
- **Punto de aplicación (plantilla):** HTTPS con redirección desde HTTP + TLS 1.2/1.3 web→bd con verificación del certificado (CA propia)
- **Evidencia sugerida:** Panel en vivo con TLS; tcpdump ilegible
- **Prueba asociada:** P9

## Dónde aparece en el código

- [[01-configurar-bd (sh)]]
- [[01-instalar-web (sh)]]
- [[50-app (sh)]]
- [[PASO-A-PASO (md)]]
- [[app (js) · informe]]
- [[diccionario]]
- [[evidencia (php)]]
- [[evidencias (sh)]]
- [[generar]]
- [[generar_grafo (py)]]
- [[index (php)]]
- [[nucleo (php)]]

Ver [[Diccionario del proyecto]]
