# Generador TI3062 · Evaluación 4 (Proyecto Integrador Cloud)

Crea automáticamente, por estudiante, el repositorio `ti3062-NN` completo:

| Parte | Qué cumple de la pauta |
|---|---|
| `index.html` + `app.js` + `styles.css` | Sistema web de gestión (8 módulos), indicadores automáticos, localStorage, import/export JSON, **PDF generado desde los datos** (secciones 0–7) |
| `data/proyecto-NN.json` | Archivo de datos que restaura el proyecto completo (borrador precargado) |
| `app-caso/` | App PHP con formulario + listado sobre **2 tablas relacionadas**, credenciales en `/etc/ti3062/db.ini` |
| `instalador/aws/` | **AWS como receptor**: VPC-NN, subredes, IGW, rutas, SG exactos de la pauta, EC2 web/bd con IP fijas, NAT temporal, snapshots y evidencias |
| `instalador/comun/` | Paquetes, hardening (grupos, sudoers, SSH, TOTP, auditd, ufw/nftables), evidencias, cierre de la cuenta ubuntu |
| `instalador/web/`, `instalador/bd/` | Apache+PHP+TLS y copia del sistema en `/gestion`; BD con usuario de mínimo privilegio, LUKS en `/respaldos`, cron de respaldo y restauración probada |
| `PASO-A-PASO.md` | Guía personalizada con el NN, IP, nombres y comandos exactos |

## Uso

```powershell
python generar.py --listar-temas
python generar.py --nn 07 --nombre "Nombre Apellido" --github usuario
python generar.py --nn 07 --nombre "Nombre Apellido" --github usuario --tema dental --motor postgresql
python generar.py --lote alumnos.csv --salida salida
```

`alumnos.csv`: columnas `nn,nombre,github` y opcionales `tema,motor`. En lote, el generador evita repetir temáticas hasta agotar las 12.

## Variabilidad (para que no haya dos páginas iguales)

La combinación se calcula de forma determinista a partir de NN + nombre + usuario GitHub (+ `--semilla` para cambiarla):

- **Caso**: 12 temáticas, cada una con tablas, campos, actores, procesos y requerimientos propios.
- **Sistema de gestión**: 8 nombres × 8 paletas (con modo oscuro) × 8 tipografías × 3 distribuciones (menú izquierda/derecha/superior) × 4 estilos de tarjeta × 3 tipos de gráfico × 3 estilos de PDF.
- **App del caso**: paleta, tipografía y 3 distribuciones de formulario/listado.
- **Infraestructura**: MariaDB o PostgreSQL, ufw o nftables, zona us-east-1a/b/c con su justificación, 4 esquemas de nombres de grupos/usuarios, horario y retención de respaldo.
- **Contenido**: proveedor alternativo (Azure, GCP u OCI), 4–5 características, 7–8 controles NIST (6 fijos + extras), 3–4 riesgos residuales y 3–4 mejoras de un pool.

Archivo `instalador/perfil-variantes.json` resume lo que le tocó a cada uno.

## Fuentes revisadas

- Pauta Evaluación 4 y Guía U4 TI3062 (topología, SG, P1–P8, estructura del PDF, rúbrica).
- `pulentoski/repositorio-configuraciones`: VPC pública/privada en AWS, NIST/Well-Architected/CSA, Linux 07 (auditd), 08 (SSH, MFA TOTP), 09 (respaldos).
- `pulentoski/AWS` (instalación Apache/SQL; aquí se corrige `'%'` y `bind 0.0.0.0` por mínimo privilegio).
- `Bacorsx/IOT-Barrera-Firmware-php-aws-` y `Bacorsx/carrusel` (apps PHP/Node sobre AWS con BD).

> Los datos precargados son un borrador. Resultados, capturas y hallazgos deben salir de la infraestructura real de cada estudiante: la pauta rechaza evidencias ajenas y en la defensa se modifica un dato y se regenera el PDF en vivo.
