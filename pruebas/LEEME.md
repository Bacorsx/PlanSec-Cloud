# Pruebas de PlanSec-Cloud (WSL Ubuntu 24.04)

Simulan AWS en una sola máquina: una interfaz `aws0` con las IP de web-NN y bd-NN y una ruta local que hace que el tráfico hacia bd salga con origen web. Requieren `root`, MariaDB, PostgreSQL, Apache + PHP 8.3, `expect`, `oathtool` y `cryptsetup`.

| Script | Qué prueba |
|---|---|
| `70-generador.sh` | 15 temáticas × 2 motores: placeholders, `php -l`, `bash -n`, datos y diccionario |
| `50-app.sh <nn> <motor> <tema>` | App del caso completa: TLS web→bd, HTTPS, CSP/HSTS/cookies, roles, bloqueo, reglas del patrón, API en vivo, CSV, AU-9, XSS, AC-2 y exportar evidencia |
| `55-matriz.sh` | `50-app.sh` en 8 combinaciones (5 patrones, MariaDB y PostgreSQL) |
| `20-luks-respaldo.sh <proyecto>` | LUKS en `/respaldos`, cron, respaldo, restauración y P8 |
| `30-hardening.sh <proyecto> <web\|bd>` | Endurecimiento, SSH real, TOTP real, P5–P7 y firewall |
| `80-capas.sh <proyecto>` | `revisar-instalador.sh`, `verificar-secretos.sh` + `pre-push` y `05-tras-reinicio.sh` |
| `90-todo.sh` | Todo lo anterior en orden |

Uso: `wsl -d Ubuntu-24.04 -u root -- bash /mnt/c/.../generador-ti3062/pruebas/90-todo.sh`. Los proyectos de prueba quedan en `/root/v/ti3062-NN` y los registros en `/root/log-*.log`.

Limitaciones conocidas de WSL: `auditd` no arranca (el kernel no lo permite) y al reiniciar WSL se pierde `aws0`, por lo que las bases quedan escuchando en IP inexistentes; `50-app.sh` las reinicia con una configuración neutra antes de cada corrida.
