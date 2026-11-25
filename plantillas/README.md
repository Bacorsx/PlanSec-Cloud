# ti3062-{{NN}} · {{APP_NAME}}

Sistema web de gestión, planificación y generación automática del informe del **Proyecto Integrador de Seguridad en Infraestructura Cloud y Redes** (TI3062, Evaluación 4).

| | |
|---|---|
| **Autor** | {{ESTUDIANTE}} — N° de lista {{NN}} |
| **Sistema publicado** | https://ti3062-{{NN}}.pages.dev |
| **Repositorio** | https://github.com/{{GITHUB}}/ti3062-{{NN}} |
| **Caso** | {{APP_CASO}} — {{TEMA_TITULO}} |
| **App del caso (AWS)** | http://&lt;IP_PUBLICA_web-{{NN}}&gt;/ (IP elástica fija) |

## Descripción

El sistema reemplaza al informe tradicional. Sus módulos son: panel de resumen con indicadores calculados, gestión y planificación (hitos, tareas, cronograma), problemática y requerimientos, análisis cloud/multicloud, controles NIST SP 800-53 Rev. 5, implementación (topología, Security Groups, bitácora con evidencias), validación y cierre (pruebas, hallazgos, CIA, riesgos, Gobierno TI, mejoras) y el **botón que genera el PDF desde los datos registrados**.

La infraestructura se despliega en **AWS** (VPC-{{NN}} 10.{{NNIP}}.0.0/16) con `web-{{NN}}` en la subred pública y `bd-{{NN}}` ({{MOTOR_NOMBRE}}) en la subred privada.

## Estructura

```
index.html · app.js · styles.css   Sistema de gestión (Cloudflare Pages y copia en web-{{NN}}/gestion)
data/proyecto-{{NN}}.json          Datos del proyecto (importables para restaurar todo)
app-caso/                          Aplicación PHP del caso ({{TABLA_PADRE}} → {{TABLA_HIJO}})
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
