# ti3062-{{NN}} · {{APP_NAME}}

Sistema web de gestión, planificación y generación automática del informe del **Proyecto Integrador de Seguridad en Infraestructura Cloud y Redes** (TI3062, Evaluación 4).

| | |
|---|---|
| **Autor** | {{ESTUDIANTE}} — N° de lista {{NN}} |
| **Sistema publicado** | https://ti3062-{{NN}}.pages.dev |
| **Repositorio** | https://github.com/{{GITHUB}}/ti3062-{{NN}} |
| **Caso** | {{APP_CASO}} — {{TEMA_TITULO}} |
| **App del caso (AWS)** | https://&lt;IP_ELASTICA_web-{{NN}}&gt;/ (HTTP redirige a HTTPS) |

## Descripción

El sistema reemplaza al informe tradicional. Sus módulos son: panel de resumen con indicadores calculados, gestión y planificación (hitos, tareas, cronograma), problemática y requerimientos, análisis cloud/multicloud, controles NIST SP 800-53 Rev. 5, implementación (topología, Security Groups, bitácora con evidencias), validación y cierre (pruebas, hallazgos, CIA, riesgos, Gobierno TI, mejoras) y el **botón que genera el PDF desde los datos registrados**.

La infraestructura se despliega en **AWS** (VPC-{{NN}} 10.{{NNIP}}.0.0/16) con `web-{{NN}}` en la subred pública y `bd-{{NN}}` ({{MOTOR_NOMBRE}}) en la subred privada.

## Arquitectura: una aplicación, dos capas

| Capa | Qué es | Dónde corre | Archivos |
|---|---|---|---|
| **Enfoque** | App del negocio con usuarios, reglas, reportes y auditoría | web-{{NN}} en AWS (base en bd-{{NN}}) | `app-caso/` |
| **Informe** | Gestión, planificación y PDF | https://ti3062-{{NN}}.pages.dev y `/gestion/` en web-{{NN}} | raíz y `data/` |

Las capas se enlazan entre sí y comparten identidad, pero no comparten código, sesión ni base de datos (la pauta exige que sean distintas). La evidencia medida en la app pasa al informe con **Exportar evidencia** → **Importar evidencia de la app**.

## Aplicación del caso ({{APP_CASO}})

- **Funciones del negocio** (no es solo un formulario): las define el patrón de la temática (inventario, reservas, préstamos, órdenes o membresías). Incluye reglas validadas en el servidor dentro de transacciones, disponibilidad o estados, reportes y exportación CSV.
- **Usuarios y roles**: administrador (todo), operador (registra y opera) y auditor (consulta, reportes y auditoría). Contraseñas con hash, bloqueo tras 5 intentos y sesión de 15 min.
- **Datos en vivo y cifrados**: el panel consulta cada 5 s a bd-{{NN}} por **TLS 1.2/1.3 con certificado verificado** (CA propia del proyecto) y muestra el camino del dato.
- **4 tablas relacionadas** en {{MOTOR_NOMBRE}}: `usuarios_app`, `{{TABLA_PADRE}}`, `{{TABLA_HIJO}}` y `auditoria_app` (registro que la app no puede borrar).

## Diccionario y sugerencias

`data/diccionario-{{NN}}.json` trae los controles NIST y la información base del informe adaptados a este proyecto. Mientras rellenas el sistema verás listas desplegables, autocompletado de filas, paneles **💡 Sugerencias** y botones **💡 Sugerir texto**. En el módulo **Diccionario** puedes buscar controles y revisar el contenido mínimo exigido.

## Estructura

```
index.html · app.js · styles.css   Sistema de gestión (Cloudflare Pages y copia en web-{{NN}}/gestion)
data/proyecto-{{NN}}.json          Datos del proyecto (importables para restaurar todo)
data/diccionario-{{NN}}.json       Diccionario base: controles NIST, textos sugeridos y contenido mínimo
app-caso/publico · app-caso/privado   App PHP del caso: webroot mínimo y lógica fuera del webroot
instalador/aws/                    Creación de VPC, SG, EC2, NAT temporal y snapshots (AWS CLI/CloudShell)
instalador/comun/ web/ bd/         Paquetes, hardening, MFA, auditd, firewall, BD, LUKS, respaldo
PASO-A-PASO.md                     Guía completa de la actividad
```

## Instrucciones de uso

1. Abrir https://ti3062-{{NN}}.pages.dev. Al primer ingreso carga `data/proyecto-{{NN}}.json`.
2. Los cambios se guardan automáticamente en el navegador (localStorage).
3. **Documento y datos → Exportar JSON** y reemplazar `data/proyecto-{{NN}}.json` en el repositorio para versionar los datos.
4. **Importar JSON** o **Restaurar desde el repositorio** restaura el proyecto completo.
5. **Generar PDF** construye el documento técnico (secciones 0 a 7) a partir de los datos actuales.

## Seguridad del repositorio

No contiene llaves privadas, secretos TOTP, códigos QR, códigos de emergencia ni credenciales de base de datos (estas viven en `/etc/ti3062/db.ini` en web-{{NN}}).

- `instalador/verificar-secretos.sh` revisa el repositorio; `.githooks/pre-push` lo ejecuta antes de cada push (`git config core.hooksPath .githooks`).
- `instalador/revisar-instalador.sh` verifica `MANIFIESTO.sha256`, la sintaxis y los permisos de los scripts y resume las reglas que se aplicarán. Ejecútalo antes de instalar.
- `.gitattributes` fija el fin de línea LF para que los scripts funcionen aunque se clonen en Windows.
