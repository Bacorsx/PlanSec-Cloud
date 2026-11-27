# Paso a paso — Evaluación 4 TI3062 · NN {{NN}} · {{ESTUDIANTE}}

> Guía generada el {{FECHA}}. Todos los nombres, IP y comandos ya están adaptados a tu número de lista.
> El sistema de gestión y los scripts son la **base**: la evidencia (capturas, resultados, hallazgos) debe salir de **tu** infraestructura y es lo que se evalúa en la defensa.

## Tu perfil

| Elemento | Valor |
|---|---|
| Caso | **{{APP_CASO}}** — {{TEMA_TITULO}} (tablas `{{TABLA_PADRE}}` → `{{TABLA_HIJO}}`) |
| VPC | `VPC-{{NN}}` 10.{{NNIP}}.0.0/16 · zona `{{ZONA}}` |
| Subred pública / privada | 10.{{NNIP}}.1.0/24 / 10.{{NNIP}}.2.0/24 |
| web-{{NN}} / bd-{{NN}} | 10.{{NNIP}}.1.10 / 10.{{NNIP}}.2.10 |
| Motor BD | {{MOTOR_NOMBRE}} (puerto {{DBPORT}}), base `ti3062_{{NN}}`, usuario `app_{{NN}}` |
| Firewall de host | {{FIREWALL}} |
| Grupos | `{{G_ADMIN}}` · `{{G_DEV}}` · `{{G_AUDIT}}` |
| Usuarios | `{{U_ADMIN}}` (admin, TOTP) · `{{U_DEV}}` · `{{U_AUDIT}}` |
| Respaldo | cron `{{CRON}}` · retención {{RETENCION}} días · `/respaldos` (LUKS) |
| Proveedor alternativo | {{ALT}} |
| Sistema de gestión | {{APP_NAME}} → https://ti3062-{{NN}}.pages.dev |

```mermaid
flowchart LR
  PC[Tu PC] -- git push --> GH[GitHub ti3062-{{NN}}] -- deploy --> CF[Cloudflare Pages<br/>ti3062-{{NN}}.pages.dev]
  PC -- CloudShell / AWS CLI --> AWS
  subgraph AWS[AWS · VPC-{{NN}}]
    W[web-{{NN}}<br/>app + /gestion] -- {{DBPORT}} --> B[(bd-{{NN}}<br/>{{MOTOR_NOMBRE}} + LUKS)]
  end
  GH -- git clone --> W
```

---

## Arquitectura: una aplicación, dos capas

La pauta exige que el sistema de gestión (Cloudflare Pages) y la app del caso (web-{{NN}}) sean distintos. Por eso **{{APP_CASO}}** es un solo producto, en un solo repositorio, con dos capas separadas:

| Capa | Qué es | Dónde corre | Archivos |
|---|---|---|---|
| **Enfoque** | La aplicación del negocio ({{TEMA_TITULO}}) con usuarios, reglas, reportes y auditoría | web-{{NN}} (AWS), base en bd-{{NN}} | `app-caso/` |
| **Informe** | Gestión, planificación y generación del PDF | `ti3062-{{NN}}.pages.dev` y copia en `https://<IP_ELASTICA_WEB>/gestion/` | raíz: `index.html`, `app.js`, `styles.css`, `data/` |

Comparten nombre, colores y navegación (cada una enlaza a la otra), pero **no** comparten código, sesión ni base de datos. La evidencia pasa de la capa de enfoque a la de informe con un paquete exportado: *Exportar evidencia* en la app → *Importar evidencia de la app* en el sistema.

## Fase 0 · Repositorio y publicación (día 1)

1. Crea en GitHub el repositorio **público** `ti3062-{{NN}}` (vacío, sin README).
2. En la carpeta generada:
   ```bash
   git init -b main
   git add . && git commit -m "Estructura inicial del sistema de gestión"
   git remote add origin https://github.com/{{GITHUB}}/ti3062-{{NN}}.git
   git config core.hooksPath .githooks          # activa la revisión de secretos antes de cada push
   chmod +x .githooks/pre-push                   # en Git Bash / Linux / macOS
   bash instalador/verificar-secretos.sh         # debe terminar en «Sin secretos detectados»
   git push -u origin main
   ```
   > Si el push se bloquea, el mensaje indica el archivo: quítalo con `git rm --cached <archivo>` y agrégalo a `.gitignore`. Nunca subas `.pem`, `db.ini`, la contraseña de la app, el secreto TOTP ni capturas con QR.
3. **Cloudflare Pages**: Workers & Pages → *Create* → *Pages* → *Connect to Git* → `ti3062-{{NN}}`.
   - Project name: `ti3062-{{NN}}` (así queda `ti3062-{{NN}}.pages.dev`)
   - Framework preset: *None* · Build command: *(vacío)* · Build output directory: `/`
4. Abre la URL y verifica que carga el panel con tus datos.

> 📌 **Commits**: la pauta pide ≥15 commits en ≥3 días distintos. Haz un commit real al terminar cada fase (al final hay un plan sugerido). No reescribas fechas.

## Fase 1 · Análisis y diseño en el sistema (H1 · criterios 4.1.1–4.1.3)

En el sistema, revisa y **reescribe con tus palabras** lo que viene precargado:

- **Diccionario**: mientras rellenas, usa las listas desplegables, los paneles **💡 Sugerencias** bajo cada tabla y **💡 Sugerir texto** en los campos largos. Reescribe con tus palabras lo que agregues. El panel de resumen marca qué falta del contenido mínimo y te lleva al módulo.
- **Equipo y roles**: registra a cada integrante con su cargo y rol (Administración, Desarrollo, Auditoría). En *Gestión y planificación* elige el **responsable** de cada tarea desde esa lista.
- **Contenido del informe**: edita el título, la introducción (propósito, alcance, escenario), el título y párrafo de cada sección, el pie de página y las referencias. Todo lo que sale en el PDF se puede cambiar ahí o en los otros módulos.
- **Problemática**: contexto, actores, procesos, necesidades, impacto. Ajusta el caso si tu docente te asignó otro.
- **Características clave** (3–5) con cómo influyen en el diseño.
- **Requerimientos**: ≥4 RF y ≥4 RNF (seguridad, disponibilidad y rendimiento), cada uno con control NIST.
- **Análisis cloud**: entra a https://calculator.aws/ y a la calculadora de {{ALT}}, arma la misma configuración (2 VM pequeñas, disco, IP pública), **reemplaza los costos estimados** por los tuyos y pega el enlace de la estimación como fuente.
- **Controles NIST**: revisa riesgo, punto de aplicación, capa y requerimiento; completa “impacto esperado”.
- Exporta el JSON → reemplaza `data/proyecto-{{NN}}.json` → commit `Análisis del problema y requerimientos`.

## Fase 2 · Infraestructura en AWS (receptor del despliegue)

1. Inicia el laboratorio de **AWS Academy** y abre la consola (región **us-east-1**) → **CloudShell**.
   > Alternativa: AWS CLI en tu PC copiando las credenciales de *AWS Details* en `~/.aws/credentials`.
2. Averigua tu IP pública (https://checkip.amazonaws.com) **desde tu PC**, no desde CloudShell.
3. En CloudShell:
   ```bash
   git clone https://github.com/{{GITHUB}}/ti3062-{{NN}}.git && cd ti3062-{{NN}}
   bash instalador/revisar-instalador.sh        # integridad (manifiesto), sintaxis, permisos y reglas que se aplicarán
   cd instalador/aws
   bash 01-crear-infra.sh <TU_IP_PUBLICA>
   bash 02-nat-temporal.sh crear        # salida temporal para instalar paquetes en bd-{{NN}}
   ```
4. Descarga `llave-ti3062-{{NN}}.pem` (CloudShell → *Actions* → *Download file*, ruta `ti3062-{{NN}}/instalador/aws/llave-ti3062-{{NN}}.pem`) y guárdala en `~/.ssh/` de tu PC. **No la subas a GitHub.**
5. Captura la consola: mapa de recursos de la VPC, subredes, tablas de rutas, SG e instancias → bitácora.
6. Abre **CloudTrail** en la consola y captura el `AccessDeniedException`: es la evidencia del hallazgo precargado **HZ-01** (sin auditoría centralizada → control compensatorio en el SO).

> ⚠ Si lanzas las instancias desde la consola, elige **Ubuntu Server 24.04 LTS** en la lista de AMI. El ícono *Ubuntu* de Inicio rápido puede traer 26.04, que usa `sudo-rs` (no acepta las directivas de registro de sudo de los scripts). `01-crear-infra.sh` ya fija 24.04.

> Si prefieres la consola web, sigue la guía de pulentoski *Cloud/AWS/VPC con subred pública y subred privada en AWS* con tus valores NN. El resultado debe ser idéntico al de la tabla de tu perfil.

## Fase 3 · Acceso SSH desde tu PC

1. Crea las llaves ED25519 de tus 3 usuarios (PowerShell o bash):
   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/{{U_ADMIN}} -C "{{U_ADMIN}}"
   ssh-keygen -t ed25519 -f ~/.ssh/{{U_DEV}}   -C "{{U_DEV}}"
   ssh-keygen -t ed25519 -f ~/.ssh/{{U_AUDIT}} -C "{{U_AUDIT}}"
   ```
   Copia **solo** los `.pub` a `instalador/llaves/` y haz commit (`Llaves públicas de usuarios`).
2. Agrega a `~/.ssh/config` (reemplaza la IP pública de web-{{NN}} que mostró el script):
   ```
   Host web-{{NN}}
       HostName <IP_PUBLICA_WEB>
       User ubuntu
       IdentityFile ~/.ssh/llave-ti3062-{{NN}}.pem
   Host bd-{{NN}}
       HostName 10.{{NNIP}}.2.10
       User ubuntu
       IdentityFile ~/.ssh/llave-ti3062-{{NN}}.pem
       ProxyJump web-{{NN}}
   ```
3. Prueba: `ssh web-{{NN}}` y `ssh bd-{{NN}}` (bd se alcanza a través de web, que actúa de bastión).

## Fase 4 · Base de datos en bd-{{NN}}

```bash
# Desde tu PC: copiar el repositorio a bd (no tiene Internet)
scp -r ti3062-{{NN}} bd-{{NN}}:~
ssh bd-{{NN}}
cd ~/ti3062-{{NN}}/instalador
bash revisar-instalador.sh                  # antes de instalar en esta instancia
sudo bash comun/00-paquetes.sh bd          # mientras existe la NAT temporal
```
Luego, en **CloudShell**: `bash 02-nat-temporal.sh eliminar` → captura la tabla de rutas sin `0.0.0.0/0`.

```bash
sudo bash bd/01-configurar-bd.sh            # CA del proyecto + TLS obligatorio, 4 tablas, app_{{NN}} sin DELETE
sudo cat /root/.ti3062-clave-app            # contraseña de la app: SECRETA (no la captures)
sudo cat /root/.ti3062-ca-bd.b64            # certificado de la CA en una línea: público (sí puedes capturarlo)
```
📸 Captura la salida de *Evidencia*: GRANTs sin ALL ni DELETE, `auditoria_app` solo INSERT/SELECT y TLS activo (`require_secure_transport` / `ssl = on`).

## Fase 5 · Aplicación del caso en web-{{NN}}

```bash
ssh web-{{NN}}
git clone https://github.com/{{GITHUB}}/ti3062-{{NN}}.git && cd ti3062-{{NN}}/instalador
bash revisar-instalador.sh
sudo bash comun/00-paquetes.sh web
sudo bash web/01-instalar-web.sh            # pide la línea de la CA, la clave de app_{{NN}} y crea el administrador de la app
```
El script prueba la conexión y debe mostrar `Conexión OK … TLSv1.3 … certificado verificado: sí` (P3 / P9).

1. Abre `http://<IP_ELASTICA_WEB>/` → redirige a **HTTPS** (acepta el certificado autofirmado; es un riesgo residual documentado).
2. Ingresa con el administrador. Lee el aviso de uso autorizado (AC-8).
3. **Usuarios** → crea un **operador** y un **auditor** (mínimo privilegio en la app: AC-3/AC-6).
4. Registra {{TABLA_PADRE}} y luego operaciones de {{TABLA_HIJO}}: prueba las reglas del negocio (la app rechaza lo que no corresponde) → **P1**.
5. **Panel**: el *camino del dato en vivo* muestra Navegador → web-{{NN}} → bd-{{NN}} con la versión TLS, el cifrado y la latencia, actualizados cada 5 s. 📸 Captúralo: es la evidencia de SC-8.
6. **Reportes** y **Auditoría** (como auditor): exporta el CSV y revisa los eventos registrados.

También queda una copia del sistema de gestión en `https://<IP_ELASTICA_WEB>/gestion/`.

## Fase 6 · Endurecimiento del SO (ambas instancias)

> Mantén **dos** sesiones abiertas: si algo falla, corriges desde la otra.

```bash
# web-{{NN}}
cd ~/ti3062-{{NN}}/instalador && git pull
sudo bash comun/01-hardening.sh web <TU_IP_PUBLICA>
# bd-{{NN}}  (los .pub ya viajaron con el scp de la Fase 4)
sudo bash comun/01-hardening.sh bd
```
El script pide la contraseña de sudo de cada usuario y aplica: grupos y usuarios, `/srv/areas` (2770/2750), sudoers por rol, `sshd_config.d/10-ti3062.conf`, PAM TOTP, auditd y {{FIREWALL}}.

**MFA del administrador** (en cada instancia):
```bash
ssh -i ~/.ssh/{{U_ADMIN}} {{U_ADMIN}}@<IP_PUBLICA_WEB>
google-authenticator -t -d -f -r 3 -R 30 -w 3   # escanea con tu app; NO captures QR, secreto ni códigos
```
Cierra y vuelve a entrar: debe pedir `Verification code`. Repite en bd (`ssh -J ... {{U_ADMIN}}@10.{{NNIP}}.2.10`).

Actualiza `~/.ssh/config` para usar `{{U_ADMIN}}` con `IdentityFile ~/.ssh/{{U_ADMIN}}`. Los scripts quedaron en `/home/ubuntu`; cópialos al área de administración (como ubuntu) y, ya probado el acceso del admin, bloquea la cuenta inicial (deja máximo 3 usuarios):
```bash
sudo cp -r /home/ubuntu/ti3062-{{NN}} /srv/areas/administracion/      # como ubuntu
sudo bash /srv/areas/administracion/ti3062-{{NN}}/instalador/comun/99-cerrar-ubuntu.sh   # como {{U_ADMIN}}
```

Evidencias rápidas: `sudo bash comun/evidencias.sh identidad|sudo|ssh|mfa|auditd|sesiones|firewall` (`sesiones`: accesos con IP de origen, intentos fallidos, conectados y último acceso por usuario).

> **Si quedas fuera** (TOTP perdido o SSH mal configurado): AWS Academy no permite consola serial, así que se rescata el disco. Detén la instancia → *Volumes* → desconecta su disco raíz → lanza una Ubuntu temporal **en la misma zona** con la llave `.pem` → **ya encendida**, adjunta el disco → en ella: `sudo mount /dev/nvme1n1p1 /mnt` (revisa el nombre con `lsblk`), `sudo mv /mnt/etc/ssh/sshd_config.d/10-ti3062.conf{,.bak}` y `sudo cp /mnt/etc/pam.d/sshd.bak-ti3062 /mnt/etc/pam.d/sshd`, `sudo umount /mnt` → desconecta, vuelve a adjuntarlo a tu instancia como `/dev/sda1` → enciende, entra como `{{U_ADMIN}}` solo con llave y vuelve a ejecutar `01-hardening.sh`. Termina la instancia temporal. Documenta el incidente como hallazgo.

## Fase 7 · Cifrado, respaldo y disponibilidad (bd-{{NN}})

```bash
sudo bash bd/02-luks-respaldos.sh           # LUKS2 sobre el disco extra de 2 GB → /respaldos
sudo bash bd/03-respaldo-cron.sh            # cron {{CRON}} + primer respaldo
sudo bash bd/04-probar-restauracion.sh      # restauración probada (captura obligatoria)
```
En CloudShell: `bash 03-snapshots-y-evidencias.sh` (snapshots de ambas instancias, una AMI de cada una ya endurecida para recuperarla en minutos, y tablas de evidencia).
Justifica la zona `{{ZONA}}` en *Análisis cloud → Selección*.

## Fase 8 · Validación (H3 · criterio 4.1.5)

Los comandos de **P1–P13** ya están en el módulo *Validación* (P1–P8 de la pauta + P9–P13 de la aplicación web). Para cada prueba: ejecútala, escribe el **resultado obtenido**, marca Aprobada/Fallida y sube la captura (hostname visible).

| ID | Dónde | Clave |
|---|---|---|
| P1 | Navegador | insertar y listar |
| P2 | Tu PC / Kali | `nmap -Pn -p 22,{{DBPORT}} 10.{{NNIP}}.2.10` + instancia sin IP pública |
| P3 | web-{{NN}} y bd-{{NN}} | conecta solo desde web |
| P4 | bd-{{NN}} | `ping 8.8.8.8` y `curl` fallan |
| P5 | Tu PC | contraseña / root rechazados |
| P6 | Tu PC | admin con código incorrecto rechazado |
| P7 | web o bd | `{{U_DEV}}` ejecuta `sudo cat /etc/shadow` → denegado; `{{U_AUDIT}}` lo ve con `ausearch` |
| P8 | bd-{{NN}} | `bd/02-luks-respaldos.sh cerrar` → `strings` ilegible; luego `abrir` |
| P9 | bd-{{NN}} + web-{{NN}} | `tcpdump` en bd mientras registras algo: no se lee el texto; conexión sin TLS rechazada |
| P10 | App | 5 claves erróneas → cuenta bloqueada 15 min; se ve en *Auditoría* |
| P11 | App | como **auditor** intenta registrar → «Tu rol no permite esta acción» (`acceso_denegado`) |
| P12 | App | registra `<script>alert(1)</script>` y `' OR '1'='1` → se muestra como texto |
| P13 | web-{{NN}} | `DELETE FROM auditoria_app` con app_{{NN}} → *command denied* |

**Evidencia real de la app → informe:** en la app entra como administrador o auditor → **Exportar evidencia** (descarga `evidencia-{{NN}}-….json`, sin contraseñas ni datos personales). En el sistema: *Validación y cierre* → **Importar evidencia de la app**. Completa *Obtenido* de P1 y P9–P13 (solo si está vacío) y agrega el registro a la bitácora. Las capturas igual se adjuntan a mano.

**Borradores:** todo lo que viene precargado aparece atenuado con la etiqueta «borrador». Edítalo o márcalo «✓ Revisado» solo si coincide con tu evidencia real (salidas de auditd, tcpdump, nmap, respaldos). El panel de resumen cuenta lo que falta revisar y el PDF te avisa si quedan borradores o pruebas «Aprobada» sin resultado y captura.

Registra **hallazgos** (falla, desviación, comportamiento esperado o riesgo) vinculados a RF/RNF y control NIST. Una prueba fallida bien documentada con su corrección no resta.

## Fase 9 · Evaluación final y PDF (criterio 4.1.6)

1. Completa CIA (impacto operativo), riesgos residuales (≥3, con impacto), Gobierno TI y mejoras (≥3, con control NIST y hallazgo de origen).
2. Cambia el estado de tareas y controles a *Completada/Implementado* según corresponda: el panel recalcula el avance.
3. **Generar PDF** → revisa portada y secciones 0–7.
4. Exporta el JSON → `data/proyecto-{{NN}}.json` → `bash instalador/verificar-secretos.sh` → commit y push. Cloudflare redepliega solo.

## Antes de la defensa

- [ ] Iniciar el laboratorio AWS ≥ 30 min antes; instancias **running**.
- [ ] web-{{NN}} usa IP elástica: no cambia al reiniciar el laboratorio (si la liberaste, actualiza `~/.ssh/config`, el README y *Implementación → URL de la app*).
- [ ] Si cambió **tu** IP: en CloudShell `aws ec2 authorize-security-group-ingress --group-id <sg-web> --protocol tcp --port 22 --cidr <NUEVA_IP>/32` (y elimina la anterior); en web vuelve a ejecutar `sudo bash comun/01-hardening.sh web <NUEVA_IP>` (reescribe la regla SSH de {{FIREWALL}}). Hazlo **antes** de perder la sesión.
- [ ] Tras reiniciar el laboratorio, en bd-{{NN}}: `sudo bash bd/05-tras-reinicio.sh` (abre LUKS con tu frase, monta `/respaldos`, revisa el cron y ejecuta un respaldo si el último tiene más de 24 h). Al entrar por SSH verás un aviso si el volumen sigue cerrado. Copia el resumen que imprime a la bitácora (Área *Respaldo*).
- [ ] Practica: modificar un dato en el sistema y regenerar el PDF; ejecutar cualquier prueba P1–P13 en vivo; mostrar el panel en vivo de la app (canal TLS web → bd).
- [ ] Verifica que ninguna captura muestre llaves privadas, secreto/QR TOTP o códigos de emergencia.

## Plan sugerido de commits (≥15 en ≥3 días)

| Día | Commits |
|---|---|
| 1 | Estructura inicial · README con URL · Datos de portada · Problemática y actores · Requerimientos RF/RNF |
| 2 | Comparativa cloud con costos reales · Controles NIST · Llaves públicas · Bitácora red y SG · App del caso desplegada |
| 3 | Hardening y MFA · LUKS y respaldo · Restauración probada · Pruebas P1–P4 |
| 4 | Pruebas P5–P8 y hallazgos · CIA, riesgos y mejoras · PDF final y README actualizado |
