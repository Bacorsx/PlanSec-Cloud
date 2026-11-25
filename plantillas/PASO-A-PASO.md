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

## Fase 0 · Repositorio y publicación (día 1)

1. Crea en GitHub el repositorio **público** `ti3062-{{NN}}` (vacío, sin README).
2. En la carpeta generada:
   ```bash
   git init -b main
   git add . && git commit -m "Estructura inicial del sistema de gestión"
   git remote add origin https://github.com/{{GITHUB}}/ti3062-{{NN}}.git
   git push -u origin main
   ```
3. **Cloudflare Pages**: Workers & Pages → *Create* → *Pages* → *Connect to Git* → `ti3062-{{NN}}`.
   - Project name: `ti3062-{{NN}}` (así queda `ti3062-{{NN}}.pages.dev`)
   - Framework preset: *None* · Build command: *(vacío)* · Build output directory: `/`
4. Abre la URL y verifica que carga el panel con tus datos.

> 📌 **Commits**: la pauta pide ≥15 commits en ≥3 días distintos. Haz un commit real al terminar cada fase (al final hay un plan sugerido). No reescribas fechas.

## Fase 1 · Análisis y diseño en el sistema (H1 · criterios 4.1.1–4.1.3)

En el sistema, revisa y **reescribe con tus palabras** lo que viene precargado:

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
   git clone https://github.com/{{GITHUB}}/ti3062-{{NN}}.git && cd ti3062-{{NN}}/instalador/aws
   bash 01-crear-infra.sh <TU_IP_PUBLICA>
   bash 02-nat-temporal.sh crear        # salida temporal para instalar paquetes en bd-{{NN}}
   ```
4. Descarga `llave-ti3062-{{NN}}.pem` (CloudShell → *Actions* → *Download file*, ruta `ti3062-{{NN}}/instalador/aws/llave-ti3062-{{NN}}.pem`) y guárdala en `~/.ssh/` de tu PC. **No la subas a GitHub.**
5. Captura la consola: mapa de recursos de la VPC, subredes, tablas de rutas, SG e instancias → bitácora.

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
sudo bash comun/00-paquetes.sh bd          # mientras existe la NAT temporal
```
Luego, en **CloudShell**: `bash 02-nat-temporal.sh eliminar` → captura la tabla de rutas sin `0.0.0.0/0`.

```bash
sudo bash bd/01-configurar-bd.sh            # motor en 10.{{NNIP}}.2.10, base, tablas y app_{{NN}}
sudo cat /root/.ti3062-clave-app            # la necesitarás en web (no la captures)
```

## Fase 5 · Aplicación del caso en web-{{NN}}

```bash
ssh web-{{NN}}
git clone https://github.com/{{GITHUB}}/ti3062-{{NN}}.git && cd ti3062-{{NN}}/instalador
sudo bash comun/00-paquetes.sh web
sudo bash web/01-instalar-web.sh            # pide la clave de app_{{NN}}; prueba P3 al final
```
Abre `http://<IP_PUBLICA_WEB>/`: registra un {{TABLA_PADRE}} y luego un {{TABLA_HIJO}} asociado → **P1**.
También queda una copia del sistema de gestión en `http://<IP_PUBLICA_WEB>/gestion/`.

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

Evidencias rápidas: `sudo bash comun/evidencias.sh identidad|sudo|ssh|mfa|auditd|firewall`.

## Fase 7 · Cifrado, respaldo y disponibilidad (bd-{{NN}})

```bash
sudo bash bd/02-luks-respaldos.sh           # LUKS2 sobre el disco extra de 2 GB → /respaldos
sudo bash bd/03-respaldo-cron.sh            # cron {{CRON}} + primer respaldo
sudo bash bd/04-probar-restauracion.sh      # restauración probada (captura obligatoria)
```
En CloudShell: `bash 03-snapshots-y-evidencias.sh` (snapshots de ambas instancias + tablas de evidencia).
Justifica la zona `{{ZONA}}` en *Análisis cloud → Selección*.

## Fase 8 · Validación (H3 · criterio 4.1.5)

Los comandos de **P1–P8** ya están en el módulo *Validación*. Para cada prueba: ejecútala, escribe el **resultado obtenido**, marca Aprobada/Fallida y sube la captura (hostname visible).

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

Registra **hallazgos** (falla, desviación, comportamiento esperado o riesgo) vinculados a RF/RNF y control NIST. Una prueba fallida bien documentada con su corrección no resta.

## Fase 9 · Evaluación final y PDF (criterio 4.1.6)

1. Completa CIA (impacto operativo), riesgos residuales (≥3, con impacto), Gobierno TI y mejoras (≥3, con control NIST y hallazgo de origen).
2. Cambia el estado de tareas y controles a *Completada/Implementado* según corresponda: el panel recalcula el avance.
3. **Generar PDF** → revisa portada y secciones 0–7.
4. Exporta el JSON → `data/proyecto-{{NN}}.json` → commit y push. Cloudflare redepliega solo.

## Antes de la defensa

- [ ] Iniciar el laboratorio AWS ≥ 30 min antes; instancias **running**.
- [ ] La IP pública de web cambia al reiniciar: actualiza `~/.ssh/config`, el README y *Implementación → URL de la app*.
- [ ] Si cambió **tu** IP: en CloudShell `aws ec2 authorize-security-group-ingress --group-id <sg-web> --protocol tcp --port 22 --cidr <NUEVA_IP>/32` (y elimina la anterior); en web vuelve a ejecutar `sudo bash comun/01-hardening.sh web <NUEVA_IP>` (reescribe la regla SSH de {{FIREWALL}}). Hazlo **antes** de perder la sesión.
- [ ] Tras reiniciar bd: `sudo bash bd/02-luks-respaldos.sh abrir` (o el respaldo nocturno falla — riesgo residual documentado).
- [ ] Practica: modificar un dato en el sistema y regenerar el PDF; ejecutar cualquier P1–P8 en vivo.
- [ ] Verifica que ninguna captura muestre llaves privadas, secreto/QR TOTP o códigos de emergencia.

## Plan sugerido de commits (≥15 en ≥3 días)

| Día | Commits |
|---|---|
| 1 | Estructura inicial · README con URL · Datos de portada · Problemática y actores · Requerimientos RF/RNF |
| 2 | Comparativa cloud con costos reales · Controles NIST · Llaves públicas · Bitácora red y SG · App del caso desplegada |
| 3 | Hardening y MFA · LUKS y respaldo · Restauración probada · Pruebas P1–P4 |
| 4 | Pruebas P5–P8 y hallazgos · CIA, riesgos y mejoras · PDF final y README actualizado |
