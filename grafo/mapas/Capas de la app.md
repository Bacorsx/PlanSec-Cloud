---
tags: [mapa]
---
# Una aplicación, dos capas

La pauta exige que el sistema de gestión (Cloudflare Pages) y la app del caso (web-NN) sean **distintos**. Por eso es un solo producto y un solo repositorio con dos capas:

| | [[Capa de enfoque]] | [[Capa de informe]] |
|---|---|---|
| Qué es | App del negocio ([[Patrón de negocio]]) | Gestión, planificación y PDF |
| Dónde | web-NN + bd-NN (AWS) | ti3062-NN.pages.dev y /gestion |
| Código | `plantillas/app-caso/` | `plantillas/sistema/` |
| Datos | BD con 4 tablas, [[Auditoría de la app]] | `data/proyecto-NN.json`, [[Diccionario]] |
| Seguridad | [[Roles de la app]], [[Sesión segura]], [[CSRF y CSP]], [[TLS web→bd]] | [[Borrador precargado]], [[Revisión de secretos]] |

Se comunican solo con el [[Paquete de evidencia]] (sin compartir código, sesión ni base de datos).
