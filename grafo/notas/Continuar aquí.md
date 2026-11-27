---
tags: [nota, continuar]
---
# Continuar aquí

Punto de partida para retomar PlanSec-Cloud en otra sesión. Actualizado el 2026-11-27.

## Qué es
Generador de proyectos para la **Evaluación 4 de TI3062** (pauta de Daniel Ruz, sede La Serena). Con `generar.py --nn NN --nombre … --github …` crea el repositorio `ti3062-NN` de cada estudiante: **una aplicación con dos capas** ([[Capas de la app]]), el instalador para AWS y la guía [[PASO-A-PASO (md)]].

- Carpeta local: `C:\Users\Darcu\OneDrive\Desktop\seguridad\generador-ti3062`
- GitHub: https://github.com/Bacorsx/PlanSec-Cloud (público, rama `main`)
- Documentos que mandan: pauta `E:\Descargas\Pauta_Evaluacion_4_Proyecto_Integrador_Cloud.pdf` (las copias (1) y (2) son idénticas) y guía `E:\Descargas\TI3062_U4_ES_GUÍA.docx`. Material de apoyo, no evaluado: Guía N°2 de Multicloud, manual Django/AWS y el documento Coopandes.

## Estado
- **Generador:** 15 temáticas sobre 5 patrones ([[Patrón de negocio]]), MariaDB o PostgreSQL, ufw o nftables; [[Diccionario]] con 46 controles NIST.
- **Capa de enfoque:** app PHP con roles, reglas del negocio, panel en vivo, [[TLS web→bd]], [[Auditoría de la app]] y [[Paquete de evidencia]].
- **Capa de informe:** sistema con equipo y roles, informe editable, sugerencias del diccionario, [[Borrador precargado]] e importación de evidencia.
- **Instalador:** [[revisar-instalador (sh)]], [[verificar-secretos (sh)]] + [[pre-push]], [[05-tras-reinicio (sh)]].
- **Pruebas** (WSL Ubuntu 24.04, `pruebas/`): generador 30/30, matriz de la app 8/8, LUKS 0 fallas, capas 0 fallas. Ver [[Pruebas]].
- **No probado en AWS real** ni en EC2: ver [[Pendientes]].

## Cómo retomar
1. Abrir la carpeta del proyecto y leer [[00 Inicio]] → [[Flujo]] → [[Decisiones]].
2. Regenerar este mapa tras cambiar código: `python herramientas/generar_grafo.py`.
3. Generar un proyecto de prueba: `python generar.py --nn 09 --nombre "Alumno Ejemplo" --github Bacorsx --tema datacenter --salida salida --forzar`.
4. Verificar todo: `wsl -d Ubuntu-24.04 -u root -- bash /mnt/c/Users/Darcu/OneDrive/Desktop/seguridad/generador-ti3062/pruebas/90-todo.sh` (≈15 min). Ver [[LEEME (md) · pruebas]].
5. Antes de subir: revisar `git diff`, hacer commit terminando con la línea de coautoría y `git push origin main`.

## Convenciones que se mantuvieron
- La **pauta manda**: todo cambio se contrasta con ella (topología fija, P1–P8, PDF solo desde los datos, sin secretos en evidencias).
- El estudiante debe poder rehacer todo: los scripts muestran evidencia y piden lo secreto (frase LUKS, contraseña de la app) sin guardarlo.
- Las sugerencias **nunca sobrescriben** lo escrito por el estudiante.
- Textos en español de Chile; nombres con el NN del estudiante.

## Historial de sesiones
- 2026-11-25: generador inicial, sistema de gestión, instalador y pruebas en WSL; repositorio PlanSec-Cloud.
- 2026-11-26: app multifunción por patrón, TLS web→bd, NIST de la app, equipo y roles, informe editable, diccionario.
- 2026-11-27: una app con dos capas, paquete de evidencia, borradores, LUKS tras reinicio, secretos, manifiesto y este grafo.
