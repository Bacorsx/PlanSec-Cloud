<?php
/* {{APP_CASO}} — aplicación del caso · TI3062 NN {{NN}} · {{ESTUDIANTE}}
 * Solo este archivo, api.php, app.js y estilo.css están en el webroot; la lógica y la configuración viven en /var/www/ti3062. */
declare(strict_types=1);
$PRIV = getenv('TI3062_PRIV') ?: __DIR__ . '/../ti3062';
require $PRIV . '/nucleo.php';
require $PRIV . '/patrones.php';

cabeceras();
$P = $TEMA['padre']; $H = $TEMA['hijo'];
$v = (string)($_GET['v'] ?? 'panel');
$msg = ''; $err = '';
function ir(string $q): never { header('Location: ./' . $q, true, 303); exit; }
function fallo(Throwable $e): string {
    try { if (db()->inTransaction()) db()->rollBack(); } catch (Throwable) {}
    if ($e instanceof RuntimeException && !($e instanceof PDOException)) return $e->getMessage();
    error_log('[ti3062] ' . get_class($e) . ': ' . $e->getMessage());   // SI-11: el detalle queda en el log, no en pantalla
    return 'No fue posible completar la operación. Intenta nuevamente; si persiste, informa al administrador.';
}

try {
    iniciar_sesion();
} catch (Throwable $e) { $err = fallo($e); }

/* ------------------------------------------------ ingreso (sin sesión) */
if (!usuario()) {
    if (($_SERVER['REQUEST_METHOD'] ?? '') === 'POST' && ($_POST['accion'] ?? '') === 'login') {
        try { csrf_ok(); $e = ingresar((string)($_POST['usuario'] ?? ''), (string)($_POST['clave'] ?? '')); if ($e === null) ir('?v=panel'); $err = $e; }
        catch (Throwable $e) { $err = fallo($e); }
    }
    $aviso = $_SESSION['aviso'] ?? ''; unset($_SESSION['aviso']);
    ?><!doctype html>
<html lang="es" data-variante="{{VARIANTE_APP}}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ingreso · <?= h($TEMA['nombre_app']) ?></title><link rel="stylesheet" href="estilo.css"><script src="app.js" defer></script></head>
<body class="ingreso">
<main class="caja-ingreso panel">
  <div class="marca grande"><span class="logo"><?= h(mb_substr($TEMA['nombre_app'], 0, 1)) ?></span><div><strong><?= h($TEMA['nombre_app']) ?></strong><small><?= h($TEMA['titulo']) ?></small></div></div>
  <p class="aviso-legal"><b>Uso exclusivo para personal autorizado.</b> El acceso y cada acción quedan registrados con usuario, fecha e IP de origen (NIST AC-8, Ley 21.663). Al ingresar aceptas estas condiciones.</p>
  <?php if ($aviso): ?><p class="msg info"><?= h($aviso) ?></p><?php endif; ?>
  <?php if ($err): ?><p class="msg mal" role="alert"><?= h($err) ?></p><?php endif; ?>
  <form method="post" action="./" autocomplete="off">
    <?= csrf_campo() ?><input type="hidden" name="accion" value="login">
    <label><span>Usuario</span><input name="usuario" required maxlength="40" autocomplete="username" autofocus></label>
    <label><span>Contraseña</span><input name="clave" type="password" required maxlength="200" autocomplete="current-password"></label>
    <button class="primario">Ingresar</button>
  </form>
  <p class="pie-ingreso num">web-{{NN}} · <?= es_https() ? 'HTTPS' : 'HTTP' ?> · bloqueo tras <?= MAX_INTENTOS ?> intentos</p>
</main>
</body></html>
<?php
    exit;
}

/* ------------------------------------------------ acciones (con sesión) */
try {
    if ($v === 'salir') {
        if (!hash_equals($_SESSION['csrf'], (string)($_GET['t'] ?? ''))) throw new RuntimeException('Enlace de salida inválido.');
        auditar('logout', 'sesion'); cerrar_sesion(); $_SESSION['aviso'] = 'Sesión cerrada correctamente.'; ir('');
    }
    if (($_SERVER['REQUEST_METHOD'] ?? '') === 'POST') {
        csrf_ok();
        $a = (string)($_POST['accion'] ?? '');
        $m = '';
        if ($v === 'operar') {
            if ($a === 'registrar') { exigir('operador'); $m = p_registrar(validar($H['campos'], $_POST), $_POST); }
            else $m = p_accion($a, entero($_POST['id'] ?? '', 1, PHP_INT_MAX, 'Registro'));
        } elseif ($v === 'padre') {
            $campos = array_merge($P['campos'], p_campos_padre());
            if ($a === 'crear' || $a === 'editar') {
                exigir('operador');
                $d = validar($campos, $_POST);
                if (isset($d['stock_minimo'])) $d['stock_minimo'] = entero($d['stock_minimo'], 0, 1000000, 'Stock mínimo');
                if (isset($d['duracion_dias'])) $d['duracion_dias'] = entero($d['duracion_dias'], 1, 3650, 'Duración');
                if ($a === 'crear') {
                    $extra = ['activo' => 1, 'creado_en' => ahora_utc()] + (PATRON() === 'inventario' ? ['stock' => 0] : []) + (PATRON() === 'prestamos' ? ['estado_item' => 'Disponible'] : []);
                    $id = insertar($P['tabla'], $d + $extra);
                    auditar('crear', $P['tabla'], "#$id " . reset($d));
                    $m = ucfirst($P['singular']) . ' registrado.';
                } else {
                    $id = entero($_POST['id'] ?? '', 1, PHP_INT_MAX, 'Registro');
                    $set = implode(', ', array_map(fn($k) => "$k = ?", array_keys($d)));
                    if (!ejecutar("UPDATE {$P['tabla']} SET $set WHERE id = ?", [...array_values($d), $id])) throw new RuntimeException('No se encontró el registro.');
                    auditar('editar', $P['tabla'], "#$id " . json_encode($d, JSON_UNESCAPED_UNICODE));
                    $m = ucfirst($P['singular']) . ' actualizado.';
                }
            } elseif ($a === 'activo') {
                exigir('admin');
                $id = entero($_POST['id'] ?? '', 1, PHP_INT_MAX, 'Registro');
                ejecutar("UPDATE {$P['tabla']} SET activo = 1 - activo WHERE id = ?", [$id]);
                auditar('activar_desactivar', $P['tabla'], "#$id");
                $m = 'Estado actualizado.';
            } elseif ($a === 'mantencion' && PATRON() === 'prestamos') {
                exigir('operador');
                $id = entero($_POST['id'] ?? '', 1, PHP_INT_MAX, 'Registro');
                $n = ejecutar("UPDATE {$P['tabla']} SET estado_item = CASE WHEN estado_item = 'Disponible' THEN 'Mantención' ELSE 'Disponible' END WHERE id = ? AND estado_item <> 'Prestado'", [$id]);
                if (!$n) throw new RuntimeException('No se puede cambiar: el ítem está prestado.');
                auditar('mantencion', $P['tabla'], "#$id");
                $m = 'Estado de mantención actualizado.';
            } else throw new RuntimeException('Acción no permitida.');
        } elseif ($v === 'usuarios') {
            exigir('admin');
            if ($a === 'crear') {
                $u = mb_strtolower(trim((string)($_POST['usuario'] ?? '')));
                if (!preg_match('/^[a-z0-9._-]{3,40}$/', $u)) throw new RuntimeException('Usuario: 3 a 40 caracteres (a-z, 0-9, . _ -).');
                $rol = (string)($_POST['rol'] ?? '');
                if (!isset(ROLES[$rol])) throw new RuntimeException('Rol no válido.');
                $clave = (string)($_POST['clave'] ?? ''); validar_clave($clave, $u);
                if (valor('SELECT COUNT(*) FROM usuarios_app WHERE usuario = ?', [$u])) throw new RuntimeException('El usuario ya existe.');
                insertar('usuarios_app', ['usuario' => $u, 'nombre' => texto((string)($_POST['nombre'] ?? ''), 'Nombre', 100), 'hash' => hash_clave($clave), 'rol' => $rol, 'activo' => 1, 'intentos' => 0, 'creado_en' => ahora_utc()]);
                auditar('usuario_crear', 'usuarios_app', "$u rol $rol");
                $m = "Usuario $u creado con rol " . ROLES[$rol] . '.';
            } else {
                $id = entero($_POST['id'] ?? '', 1, PHP_INT_MAX, 'Usuario');
                $obj = fila('SELECT usuario FROM usuarios_app WHERE id = ?', [$id]) ?? throw new RuntimeException('Usuario no encontrado.');
                if ($id === $_SESSION['uid'] && $a !== 'desbloquear') throw new RuntimeException('No puedes cambiar tu propio rol o estado.');
                if ($a === 'activo') { ejecutar('UPDATE usuarios_app SET activo = 1 - activo WHERE id = ?', [$id]); $m = 'Estado del usuario actualizado.'; }
                elseif ($a === 'desbloquear') { ejecutar('UPDATE usuarios_app SET intentos = 0, bloqueado_hasta = NULL WHERE id = ?', [$id]); $m = 'Usuario desbloqueado.'; }
                elseif ($a === 'rol') {
                    $rol = (string)($_POST['rol'] ?? ''); if (!isset(ROLES[$rol])) throw new RuntimeException('Rol no válido.');
                    ejecutar('UPDATE usuarios_app SET rol = ? WHERE id = ?', [$rol, $id]); $m = 'Rol actualizado.';
                } else throw new RuntimeException('Acción no permitida.');
                auditar('usuario_' . $a, 'usuarios_app', $obj['usuario'] . ($a === 'rol' ? ' → ' . $_POST['rol'] : ''));
            }
        } elseif ($v === 'cuenta' && $a === 'clave') {
            $yo = fila('SELECT * FROM usuarios_app WHERE id = ?', [$_SESSION['uid']]);
            if (!$yo || !password_verify((string)($_POST['actual'] ?? ''), $yo['hash'])) { auditar('clave_fallida', 'usuarios_app', 'Contraseña actual incorrecta'); throw new RuntimeException('La contraseña actual no es correcta.'); }
            $n = (string)($_POST['nueva'] ?? '');
            if ($n !== (string)($_POST['repetir'] ?? '')) throw new RuntimeException('Las contraseñas nuevas no coinciden.');
            validar_clave($n, $yo['usuario']);
            ejecutar('UPDATE usuarios_app SET hash = ?, cambio_clave = ? WHERE id = ?', [hash_clave($n), ahora_utc(), $yo['id']]);
            session_regenerate_id(true);
            auditar('clave_cambiada', 'usuarios_app', $yo['usuario']);
            $m = 'Contraseña actualizada.';
        } else throw new RuntimeException('Acción no permitida.');
        $_SESSION['msg'] = $m;
        ir('?' . http_build_query(array_intersect_key($_GET, array_flip(['v', 'q', 'e', 'f', 'ff']))));
    }
    if ($v === 'exportar') {   // CSV (SI-10: celdas sin fórmulas)
        exigir('auditor');
        $std = ['inventario' => ['tipo', 'cantidad', 'monto'], 'reservas' => V('modo') === 'rango' ? ['fecha', 'fecha_fin', 'estado'] : ['fecha', 'bloque', 'estado'],
                'prestamos' => ['fecha_prestamo', 'fecha_compromiso', 'fecha_devolucion', 'estado'], 'ordenes' => ['nivel', 'estado', 'monto', 'cerrado_en'],
                'membresias' => ['fecha_inicio', 'fecha_fin', 'estado']][PATRON()];
        $cols = array_column($H['campos'], 0);
        $rows = filas("SELECT h.*, p." . ETQ() . " AS padre_txt, u.usuario AS autor FROM {$H['tabla']} h JOIN {$P['tabla']} p ON p.id = h.{$H['fk']} LEFT JOIN usuarios_app u ON u.id = h.usuario_id ORDER BY h.id DESC LIMIT 5000");
        auditar('exportar', $H['tabla'], count($rows) . ' filas');
        header('Content-Type: text/csv; charset=utf-8');
        header('Content-Disposition: attachment; filename="' . $H['tabla'] . '-' . hoy() . '.csv"');
        $o = fopen('php://output', 'w'); fwrite($o, "\xEF\xBB\xBF");
        fputcsv($o, array_merge(['id', $P['singular']], $cols, $std, ['registrado_por', 'registrado']), ';');
        foreach ($rows as $r) fputcsv($o, array_map('csv_seguro', array_merge([$r['id'], $r['padre_txt']], array_map(fn($c) => $r[$c], $cols), array_map(fn($c) => $r[$c] ?? '', $std), [$r['autor'] ?? '', local($r['creado_en'])])), ';');
        exit;
    }
} catch (Throwable $e) { $err = fallo($e); }
$msg = $_SESSION['msg'] ?? ''; unset($_SESSION['msg']);

/* ------------------------------------------------ navegación según rol y patrón */
$nav = ['panel' => 'Panel', 'operar' => $H['titulo'], 'padre' => $P['titulo']];
if (PATRON() === 'reservas') $nav['disponibilidad'] = 'Disponibilidad';
if (V('vista_equipo')) $nav['equipo'] = 'Cómo funciona';
$nav['reportes'] = 'Reportes';
if (puede('auditor') && $_SESSION['rol'] !== 'operador') $nav['auditoria'] = 'Auditoría';
if (puede('admin')) $nav['usuarios'] = 'Usuarios';
$nav['cuenta'] = 'Mi cuenta';
if (!isset($nav[$v])) $v = 'panel';

function encabezado(string $titulo, array $nav, string $v): void {
    global $TEMA; ?><!doctype html>
<html lang="es" data-variante="{{VARIANTE_APP}}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title><?= h($titulo) ?> · <?= h($TEMA['nombre_app']) ?></title><link rel="stylesheet" href="estilo.css"><script src="app.js" defer></script></head>
<body>
<header class="barra">
  <div class="marca"><span class="logo"><?= h(mb_substr($TEMA['nombre_app'], 0, 1)) ?></span><div><strong><?= h($TEMA['nombre_app']) ?></strong><small class="etiqueta">TI3062 · NN {{NN}} · <?= h(gethostname()) ?></small></div></div>
  <div class="sesion">
    <button type="button" class="fantasma" id="tema" title="Cambiar modo claro/oscuro">◐</button>
    <span class="chip"><b><?= h($_SESSION['nombre']) ?></b> <?= insignia(ROLES[$_SESSION['rol']], 'info') ?></span>
    <a class="boton fantasma" href="?v=salir&amp;t=<?= h($_SESSION['csrf']) ?>">Salir</a>
  </div>
</header>
<div class="marco">
<nav class="menu" aria-label="Secciones">
  <?php foreach ($nav as $k => $t): ?><a href="?v=<?= h($k) ?>"<?= $k === $v ? ' aria-current="page"' : '' ?>><?= h($t) ?></a><?php endforeach; ?>
</nav>
<main>
<?php }
function pie(): void { ?>
</main></div>
<footer class="pie num">{{APP_CASO}} · web-{{NN}} → bd-{{NN}} · sesión expira tras <?= INACTIVIDAD / 60 ?> min de inactividad · uso registrado (AC-8)</footer>
</body></html>
<?php }
function tarjeta_ini(string $titulo, string $accion = '', string $clase = ''): void { echo '<section class="panel tarjeta ' . h($clase) . '"><header><h2 class="etiqueta">' . h($titulo) . '</h2>' . $accion . '</header><div class="cuerpo">'; }
function tarjeta_fin(string $pie = ''): void { echo '</div>' . ($pie ? '<footer>' . $pie . '</footer>' : '') . '</section>'; }
function form_accion(string $v, string $accion, int $id, string $texto, string $clase = 'secundario', string $confirmar = '', array $extra = []): string {
    $h = '<form method="post" action="?v=' . h($v) . '" class="en-linea"' . ($confirmar ? ' data-confirmar="' . h($confirmar) . '"' : '') . '>' . csrf_campo()
       . '<input type="hidden" name="accion" value="' . h($accion) . '"><input type="hidden" name="id" value="' . $id . '">';
    foreach ($extra as $k => $val) $h .= '<input type="hidden" name="' . h($k) . '" value="' . h($val) . '">';
    return $h . '<button class="' . h($clase) . ' chico">' . h($texto) . '</button></form>';
}

encabezado($nav[$v], $nav, $v);
if ($msg): ?><p class="msg bien" role="status"><?= h($msg) ?></p><?php endif;
if ($err): ?><p class="msg mal" role="alert"><?= h($err) ?></p><?php endif;

try {
switch ($v) {
/* ================================================= PANEL */
case 'panel':
    $k = p_kpis(); $c = canal_bd(); ?>
    <h1><?= h($TEMA['titulo']) ?></h1>
    <div class="metricas" id="kpis">
      <?php foreach ($k as $i => [$l, $val, $t]): ?><div class="panel metrica <?= h($t) ?>"><span class="etiqueta"><?= h($l) ?></span><b class="num" data-kpi="<?= $i ?>"><?= h($val) ?></b></div><?php endforeach; ?>
    </div>
    <?php tarjeta_ini('Camino del dato · en vivo', '<span class="nota num" id="vivo-hora">actualiza cada 5 s</span>', 'camino'); ?>
      <div class="ruta" id="ruta" data-estado="<?= $c['ok'] && $c['tls'] ? 'bien' : ($c['ok'] ? 'alerta' : 'mal') ?>">
        <div class="nodo bien"><span class="etiqueta">Cliente</span><b>Navegador</b><small><?= es_https() ? 'HTTPS (TLS)' : 'HTTP → usar HTTPS' ?></small></div>
        <div class="enlace <?= es_https() ? 'cifrado' : 'plano' ?>"><span><?= es_https() ? 'HTTPS 443' : 'HTTP 80' ?></span><i></i></div>
        <div class="nodo bien"><span class="etiqueta">Subred pública</span><b>web-{{NN}}</b><small>Apache + PHP · sesión <?= h(ROLES[$_SESSION['rol']]) ?></small></div>
        <div class="enlace <?= $c['tls'] ? 'cifrado' : 'plano' ?>" id="enlace-bd"><span id="canal-tls"><?= $c['tls'] ? h($c['tls']) : 'SIN TLS' ?></span><i></i></div>
        <div class="nodo <?= $c['ok'] ? 'bien' : 'mal' ?>" id="nodo-bd"><span class="etiqueta">Subred privada</span><b>bd-{{NN}}</b><small class="num" id="canal-bd"><?= h($c['bd']) ?> · {{MOTOR_NOMBRE}}</small></div>
      </div>
      <dl class="datos-canal num">
        <div><dt>Cifrado</dt><dd id="canal-cipher"><?= h($c['cipher'] ?: '—') ?></dd></div>
        <div><dt>Certificado de bd</dt><dd id="canal-ver"><?= $c['verificado'] ? insignia('Verificado con CA del proyecto', 'bien') : insignia('No verificado', 'mal') ?></dd></div>
        <div><dt>Latencia consulta</dt><dd id="canal-ms"><?= h($c['ms']) ?> ms</dd></div>
      </dl>
    <?php tarjeta_fin('Cada 5 s el navegador pide datos a web-{{NN}}, que los consulta en bd-{{NN}} por un canal TLS verificado (NIST SC-8). Estado: verde cifrado y verificado · amarillo sin cifrar · rojo sin conexión.'); ?>
    <div class="dos">
    <?php tarjeta_ini('Últimas operaciones', '<a class="boton fantasma chico" href="?v=operar">Ver todas</a>'); ?>
      <ul class="feed" id="feed">
        <?php foreach (filas("SELECT h.*, p." . ETQ() . " AS padre_txt FROM {$H['tabla']} h JOIN {$P['tabla']} p ON p.id = h.{$H['fk']} ORDER BY h.id DESC LIMIT 8") as $f): [, $t] = p_estado($f); ?>
          <li class="<?= h($t) ?>"><span class="num"><?= h(local($f['creado_en'], 'd-m H:i')) ?></span><?= h(p_vivo($f)) ?></li>
        <?php endforeach; ?>
      </ul>
    <?php tarjeta_fin();
    if ($_SESSION['rol'] !== 'operador') {
        tarjeta_ini('Actividad de seguridad reciente', '<a class="boton fantasma chico" href="?v=auditoria">Auditoría</a>');
        echo tabla_html(['Fecha', 'Usuario', 'Acción'], array_map(fn($a) => ['<span class="num">' . h(local($a['fecha'], 'd-m H:i')) . '</span>', h($a['usuario']), insignia($a['accion'], str_contains($a['accion'], 'fallido') || str_contains($a['accion'], 'bloque') || str_contains($a['accion'], 'denegado') ? 'mal' : '')],
            filas('SELECT fecha, usuario, accion FROM auditoria_app ORDER BY id DESC LIMIT 6')));
        tarjeta_fin();
    } ?>
    </div>
    <?php break;

/* ================================================= OPERACIÓN PRINCIPAL */
case 'operar':
    $q = trim((string)($_GET['q'] ?? '')); $e = (string)($_GET['e'] ?? '');
    echo '<div class="dos ancho-izq">';
    if (puede('operador')) {
        $padres = p_padres_elegibles();
        tarjeta_ini('Registrar ' . $H['singular']); ?>
        <form method="post" action="?v=operar" class="formulario">
          <?= csrf_campo() ?><input type="hidden" name="accion" value="registrar">
          <label><span><?= h(ucfirst($P['singular'])) ?></span><select name="<?= h($H['fk']) ?>" required><option value="">— seleccione —</option>
            <?php foreach ($padres as $p): ?><option value="<?= (int)$p['id'] ?>"><?= h($p['etiqueta']) ?><?= isset($p['stock']) ? ' · stock ' . num($p['stock']) : '' ?></option><?php endforeach; ?>
          </select></label>
          <?php if (!$padres): ?><p class="msg info">No hay <?= h(mb_strtolower($P['titulo'])) ?> disponibles. Regístralos en <a href="?v=padre"><?= h($P['titulo']) ?></a>.</p><?php endif; ?>
          <?= p_form_hijo() ?>
          <?php foreach ($H['campos'] as $c) echo control($c); ?>
          <button class="primario">Guardar</button>
        </form>
        <?php tarjeta_fin('Las reglas del negocio se validan en el servidor dentro de una transacción.');
    } else {
        tarjeta_ini('Solo lectura'); echo '<p class="nota">Tu rol (' . h(ROLES[$_SESSION['rol']]) . ') puede consultar y exportar, pero no registrar.</p>'; tarjeta_fin();
    }
    $where = []; $par = [];
    if ($q !== '') { $where[] = '(h.' . CLI() . ' LIKE ? OR p.' . ETQ() . ' LIKE ?)'; $par[] = "%$q%"; $par[] = "%$q%"; }
    if ($e !== '' && in_array($e, p_estados_filtro(), true)) { $where[] = 'h.' . p_col_estado() . ' = ?'; $par[] = $e; }
    $rows = filas("SELECT h.*, p." . ETQ() . " AS padre_txt, u.usuario AS autor FROM {$H['tabla']} h JOIN {$P['tabla']} p ON p.id = h.{$H['fk']} LEFT JOIN usuarios_app u ON u.id = h.usuario_id"
        . ($where ? ' WHERE ' . implode(' AND ', $where) : '') . ' ORDER BY h.id DESC LIMIT 100', $par);
    $acc = p_acciones();
    tarjeta_ini($H['titulo'] . ' · ' . count($rows) . ' registros', '<a class="boton fantasma chico" href="?v=exportar">Exportar CSV</a>'); ?>
      <form method="get" class="filtros"><input type="hidden" name="v" value="operar">
        <input name="q" value="<?= h($q) ?>" placeholder="Buscar <?= h(mb_strtolower($H['campos'][0][2])) ?> o <?= h($P['singular']) ?>" maxlength="60">
        <select name="e"><option value="">Todos</option><?php foreach (p_estados_filtro() as $o): ?><option<?= $o === $e ? ' selected' : '' ?>><?= h($o) ?></option><?php endforeach; ?></select>
        <button class="secundario chico">Filtrar</button></form>
      <?php
      $cab = array_merge(['#', ucfirst($P['singular']), 'Estado'], array_column(p_columnas_hijo(), 0), array_column($H['campos'], 2), ['Registró', 'Fecha', '']);
      echo tabla_html($cab, array_map(function ($f) use ($H, $acc) {
          [$et, $tn] = p_estado($f);
          $celdas = ['<span class="num">' . (int)$f['id'] . '</span>', h($f['padre_txt']), insignia($et, $tn)];
          foreach (p_columnas_hijo() as [, $fn]) $celdas[] = $fn($f);
          foreach ($H['campos'] as [$k]) $celdas[] = h(mb_strimwidth((string)$f[$k], 0, 60, '…'));
          $celdas[] = h($f['autor'] ?? '—'); $celdas[] = '<span class="num">' . h(local($f['creado_en'], 'd-m-y H:i')) . '</span>';
          $b = '';
          if (puede('operador')) foreach (p_acciones_fila($f) as $a) $b .= form_accion('operar', $a, (int)$f['id'], $acc[$a][0], $a === 'cancelar' || $a === 'suspender' ? 'peligro' : 'secundario', $acc[$a][2]);
          $celdas[] = '<div class="acciones">' . $b . '</div>';
          return $celdas;
      }, $rows));
    tarjeta_fin();
    echo '</div>';
    break;

/* ================================================= MAESTRO (tabla padre) */
case 'padre':
    $campos = array_merge($P['campos'], p_campos_padre());
    $ed = isset($_GET['editar']) && puede('operador') ? fila("SELECT * FROM {$P['tabla']} WHERE id = ?", [entero($_GET['editar'], 1, PHP_INT_MAX, 'Registro')]) : null;
    $q = trim((string)($_GET['q'] ?? ''));
    echo '<div class="dos ancho-izq">';
    if (puede('operador')) {
        tarjeta_ini($ed ? 'Editar ' . $P['singular'] . ' #' . $ed['id'] : 'Nuevo ' . $P['singular'], $ed ? '<a class="boton fantasma chico" href="?v=padre">Cancelar</a>' : ''); ?>
        <form method="post" action="?v=padre" class="formulario">
          <?= csrf_campo() ?><input type="hidden" name="accion" value="<?= $ed ? 'editar' : 'crear' ?>"><?php if ($ed): ?><input type="hidden" name="id" value="<?= (int)$ed['id'] ?>"><?php endif; ?>
          <?php foreach ($campos as $c) echo control($c, $ed[$c[0]] ?? ''); ?>
          <button class="primario"><?= $ed ? 'Guardar cambios' : 'Registrar' ?></button>
        </form>
        <?php tarjeta_fin(PATRON() === 'inventario' ? 'El stock no se edita a mano: cambia solo con movimientos registrados (trazabilidad).' : '');
    }
    $rows = filas("SELECT p.*, (SELECT COUNT(*) FROM {$H['tabla']} h WHERE h.{$H['fk']} = p.id) AS relacionados FROM {$P['tabla']} p"
        . ($q !== '' ? ' WHERE p.' . ETQ() . ' LIKE ?' : '') . ' ORDER BY p.activo DESC, p.' . ETQ() . ' LIMIT 200', $q !== '' ? ["%$q%"] : []);
    tarjeta_ini($P['titulo'] . ' · ' . count($rows)); ?>
      <form method="get" class="filtros"><input type="hidden" name="v" value="padre"><input name="q" value="<?= h($q) ?>" placeholder="Buscar" maxlength="60"><button class="secundario chico">Buscar</button></form>
      <?php
      $cab = array_merge(['#'], array_column($P['campos'], 2), array_column(p_columnas_padre(), 0), [$H['titulo'], 'Estado', '']);
      echo tabla_html($cab, array_map(function ($f) use ($P) {
          $c = ['<span class="num">' . (int)$f['id'] . '</span>'];
          foreach ($P['campos'] as [$k, $t]) $c[] = $t === 'number' ? num($f[$k]) : h($f[$k]);
          foreach (p_columnas_padre() as [, $fn]) $c[] = $fn($f);
          $c[] = '<span class="num">' . num($f['relacionados']) . '</span>';
          $c[] = (int)$f['activo'] ? insignia('Activo', 'bien') : insignia('Inactivo', 'mal');
          $b = '';
          if (puede('operador')) $b .= '<a class="boton secundario chico" href="?v=padre&amp;editar=' . (int)$f['id'] . '">Editar</a>';
          if (puede('operador') && PATRON() === 'prestamos' && $f['estado_item'] !== 'Prestado') $b .= form_accion('padre', 'mantencion', (int)$f['id'], $f['estado_item'] === 'Mantención' ? 'Habilitar' : 'Mantención');
          if (puede('admin')) $b .= form_accion('padre', 'activo', (int)$f['id'], (int)$f['activo'] ? 'Desactivar' : 'Activar', (int)$f['activo'] ? 'peligro' : 'secundario', (int)$f['activo'] ? '¿Desactivar? Se conserva su historial.' : '');
          $c[] = '<div class="acciones">' . $b . '</div>';
          return $c;
      }, $rows));
    tarjeta_fin('No se borran registros: se desactivan para conservar la trazabilidad (el usuario de la app no tiene permiso DELETE).');
    echo '</div>';
    break;

/* ================================================= DISPONIBILIDAD (reservas) */
case 'disponibilidad':
    $f = (string)($_GET['f'] ?? hoy()); $ff = (string)($_GET['ff'] ?? dias(hoy(), 1));
    $f = fecha_ok($f, 'Fecha'); if (V('modo') === 'rango') { $ff = fecha_ok($ff, 'Hasta'); if ($ff <= $f) $ff = dias($f, 1); }
    tarjeta_ini('Disponibilidad de ' . mb_strtolower($P['titulo'])); ?>
      <form method="get" class="filtros"><input type="hidden" name="v" value="disponibilidad">
        <label class="en-linea"><span>Fecha</span><input type="date" name="f" value="<?= h($f) ?>"></label>
        <?php if (V('modo') === 'rango'): ?><label class="en-linea"><span>Hasta</span><input type="date" name="ff" value="<?= h($ff) ?>"></label><?php endif; ?>
        <button class="secundario chico">Consultar</button></form>
      <?= p_disponibilidad($f, V('modo') === 'rango' ? $ff : null) ?>
    <?php tarjeta_fin('Calculado en vivo desde bd-{{NN}}: una celda ocupada no puede volver a reservarse (regla validada en el servidor).');
    break;

/* ================================================= CÓMO FUNCIONA (equipos de cómputo) */
case 'equipo':
    require $PRIV . '/vista_equipo.php';
    break;

/* ================================================= REPORTES */
case 'reportes':
    echo '<div class="mosaico">';
    foreach (p_reportes() as $t => $html) { tarjeta_ini($t); echo $html; tarjeta_fin(); }
    echo '</div>';
    break;

/* ================================================= AUDITORÍA */
case 'auditoria':
    exigir('auditor');
    $u = trim((string)($_GET['q'] ?? '')); $e = trim((string)($_GET['e'] ?? ''));
    $where = []; $par = [];
    if ($u !== '') { $where[] = 'usuario = ?'; $par[] = $u; }
    if ($e !== '') { $where[] = 'accion = ?'; $par[] = $e; }
    $rows = filas('SELECT * FROM auditoria_app' . ($where ? ' WHERE ' . implode(' AND ', $where) : '') . ' ORDER BY id DESC LIMIT 200', $par);
    $acciones = array_column(filas('SELECT DISTINCT accion FROM auditoria_app ORDER BY accion'), 'accion');
    tarjeta_ini('Registro de auditoría de la aplicación · ' . count($rows) . ' eventos'); ?>
      <form method="get" class="filtros"><input type="hidden" name="v" value="auditoria">
        <input name="q" value="<?= h($u) ?>" placeholder="Usuario" maxlength="40">
        <select name="e"><option value="">Todas las acciones</option><?php foreach ($acciones as $o): ?><option<?= $o === $e ? ' selected' : '' ?>><?= h($o) ?></option><?php endforeach; ?></select>
        <button class="secundario chico">Filtrar</button></form>
      <?= tabla_html(['#', 'Fecha', 'Usuario', 'Acción', 'Entidad', 'Detalle', 'IP'], array_map(fn($a) => ['<span class="num">' . (int)$a['id'] . '</span>', '<span class="num">' . h(local($a['fecha'], 'd-m-Y H:i:s')) . '</span>', h($a['usuario']),
          insignia($a['accion'], preg_match('/fallid|bloque|denegad|csrf/', $a['accion']) ? 'mal' : (str_starts_with($a['accion'], 'login_ok') ? 'bien' : '')), h($a['entidad']), h($a['detalle']), '<span class="num">' . h($a['ip']) . '</span>'], $rows)) ?>
    <?php tarjeta_fin('Registro inmutable para la app: el usuario de base de datos solo puede insertar y leer en auditoria_app (NIST AU-9).');
    break;

/* ================================================= USUARIOS */
case 'usuarios':
    exigir('admin');
    echo '<div class="dos ancho-izq">';
    tarjeta_ini('Nuevo usuario'); ?>
      <form method="post" action="?v=usuarios" class="formulario" autocomplete="off">
        <?= csrf_campo() ?><input type="hidden" name="accion" value="crear">
        <label><span>Usuario</span><input name="usuario" required pattern="[a-z0-9._\-]{3,40}" maxlength="40"></label>
        <label><span>Nombre</span><input name="nombre" required maxlength="100"></label>
        <label><span>Rol</span><select name="rol"><?php foreach (ROLES as $k => $t): ?><option value="<?= h($k) ?>"><?= h($t) ?></option><?php endforeach; ?></select></label>
        <label><span>Contraseña inicial (mín. <?= MIN_CLAVE ?>, letras y números)</span><input name="clave" type="password" required minlength="<?= MIN_CLAVE ?>" autocomplete="new-password"></label>
        <button class="primario">Crear usuario</button>
      </form>
    <?php tarjeta_fin('Administrador: todo · Operador: registra y opera · Auditor: consulta, reportes y auditoría (mínimo privilegio, AC-6).');
    tarjeta_ini('Usuarios de la aplicación');
    echo tabla_html(['Usuario', 'Nombre', 'Rol', 'Estado', 'Último acceso', ''], array_map(function ($u) {
        $bloq = $u['bloqueado_hasta'] && $u['bloqueado_hasta'] > ahora_utc();
        $sel = '<form method="post" action="?v=usuarios" class="en-linea">' . csrf_campo() . '<input type="hidden" name="accion" value="rol"><input type="hidden" name="id" value="' . (int)$u['id'] . '"><select name="rol">';
        foreach (ROLES as $k => $t) $sel .= '<option value="' . h($k) . '"' . ($k === $u['rol'] ? ' selected' : '') . '>' . h($t) . '</option>';
        $sel .= '</select><button class="secundario chico">Cambiar</button></form>';
        $propio = (int)$u['id'] === $_SESSION['uid'];
        return [h($u['usuario']), h($u['nombre']), $propio ? insignia(ROLES[$u['rol']], 'info') : $sel,
            $bloq ? insignia('Bloqueado', 'mal') : ((int)$u['activo'] ? insignia('Activo', 'bien') : insignia('Inactivo', 'mal')),
            '<span class="num">' . h(local($u['ultimo_acceso'])) . '</span>',
            '<div class="acciones">' . ($bloq || $u['intentos'] ? form_accion('usuarios', 'desbloquear', (int)$u['id'], 'Desbloquear') : '')
            . ($propio ? '' : form_accion('usuarios', 'activo', (int)$u['id'], (int)$u['activo'] ? 'Desactivar' : 'Activar', (int)$u['activo'] ? 'peligro' : 'secundario')) . '</div>'];
    }, filas('SELECT * FROM usuarios_app ORDER BY usuario')));
    tarjeta_fin();
    echo '</div>';
    break;

/* ================================================= MI CUENTA */
case 'cuenta':
    $yo = fila('SELECT usuario, nombre, rol, ultimo_acceso, cambio_clave FROM usuarios_app WHERE id = ?', [$_SESSION['uid']]);
    echo '<div class="dos">';
    tarjeta_ini('Mi cuenta'); ?>
      <dl class="datos-canal"><div><dt>Usuario</dt><dd><?= h($yo['usuario']) ?></dd></div><div><dt>Rol</dt><dd><?= insignia(ROLES[$yo['rol']], 'info') ?></dd></div>
      <div><dt>Último ingreso</dt><dd class="num"><?= h(local($yo['ultimo_acceso'])) ?></dd></div><div><dt>Último cambio de clave</dt><dd class="num"><?= h(local($yo['cambio_clave'])) ?></dd></div></dl>
    <?php tarjeta_fin();
    tarjeta_ini('Cambiar contraseña'); ?>
      <form method="post" action="?v=cuenta" class="formulario" autocomplete="off">
        <?= csrf_campo() ?><input type="hidden" name="accion" value="clave">
        <label><span>Contraseña actual</span><input name="actual" type="password" required autocomplete="current-password"></label>
        <label><span>Nueva (mín. <?= MIN_CLAVE ?>, letras y números)</span><input name="nueva" type="password" required minlength="<?= MIN_CLAVE ?>" autocomplete="new-password"></label>
        <label><span>Repetir nueva</span><input name="repetir" type="password" required minlength="<?= MIN_CLAVE ?>" autocomplete="new-password"></label>
        <button class="primario">Actualizar</button>
      </form>
    <?php tarjeta_fin('La contraseña se guarda solo como hash (password_hash), nunca en texto plano (IA-5(1)).');
    echo '</div>';
    break;
}
} catch (Throwable $e) { echo '<p class="msg mal" role="alert">' . h(fallo($e)) . '</p>'; }
pie();
