<?php
/* Núcleo de la aplicación del caso — TI3062 NN {{NN}}
 * Vive FUERA del webroot (/var/www/ti3062). Contiene conexión a la BD con TLS verificado, sesión segura,
 * autenticación con bloqueo por intentos, control de acceso por rol, CSRF, validación y auditoría.
 * Las credenciales NO están en el código: se leen de /etc/ti3062/db.ini (640 root:www-data). */
declare(strict_types=1);
require __DIR__ . '/config_tema.php';

const INACTIVIDAD = 900;      // AC-12: 15 min sin actividad
const MAX_SESION = 28800;     // AC-12: 8 h como máximo
const MAX_INTENTOS = 5;       // AC-7
const BLOQUEO_MIN = 15;       // AC-7
const MIN_CLAVE = 12;         // IA-5(1)
const ROLES = ['admin' => 'Administrador', 'operador' => 'Operador', 'auditor' => 'Auditor'];
const NIVEL = ['auditor' => 1, 'operador' => 2, 'admin' => 3];
const ZONA = 'America/Santiago';

date_default_timezone_set('UTC');
ini_set('display_errors', '0');   // SI-11
error_reporting(E_ALL);

function h($s): string { return htmlspecialchars((string)$s, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8'); }
function hoy(): string { return (new DateTimeImmutable('now', new DateTimeZone(ZONA)))->format('Y-m-d'); }
function ahora_utc(): string { return gmdate('Y-m-d H:i:s'); }
function dias(string $fecha, int $n): string { return (new DateTimeImmutable($fecha))->modify(($n >= 0 ? '+' : '') . $n . ' days')->format('Y-m-d'); }
function local(?string $ts, string $fmt = 'd-m-Y H:i'): string {
    if (!$ts) return '—';
    try { return (new DateTimeImmutable($ts, new DateTimeZone('UTC')))->setTimezone(new DateTimeZone(ZONA))->format($fmt); }
    catch (Throwable) { return (string)$ts; }
}
function fecha(?string $f): string { return $f ? implode('-', array_reverse(explode('-', substr($f, 0, 10)))) : '—'; }
function dinero($v): string { return '$' . number_format((float)$v, 0, ',', '.'); }
function num($v): string { return number_format((float)$v, 0, ',', '.'); }
function es_https(): bool { return ($_SERVER['HTTPS'] ?? '') === 'on' || (string)($_SERVER['SERVER_PORT'] ?? '') === '443'; }

/* ---------------------------------------------------------------- cabeceras HTTP */
function cabeceras(): void {
    header("Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'; object-src 'none'");
    header('Permissions-Policy: camera=(), microphone=(), geolocation=()');
    header('Cache-Control: no-store');
    if (es_https()) header('Strict-Transport-Security: max-age=31536000');
}

/* ---------------------------------------------------------------- base de datos (TLS verificado) */
function ini(): array {
    static $i = null;
    if ($i === null) {
        $i = @parse_ini_file(getenv('TI3062_DBINI') ?: '/etc/ti3062/db.ini');
        if (!$i) throw new RuntimeException('No se encontró la configuración de la base de datos.');
    }
    return $i;
}
function es_pg(): bool { return ini()['driver'] === 'pgsql'; }
function db(): PDO {
    static $pdo = null;
    if ($pdo) return $pdo;
    $i = ini(); $ca = $i['ssl_ca'] ?? '';
    $op = [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC, PDO::ATTR_EMULATE_PREPARES => false];
    if ($i['driver'] === 'pgsql') {
        // SC-8: verify-full = cifra y comprueba que el certificado del servidor sea de nuestra CA y de la IP de bd
        $dsn = "pgsql:host={$i['host']};port={$i['port']};dbname={$i['dbname']}" . ($ca ? ";sslmode=verify-full;sslrootcert=$ca" : '');
        $pdo = new PDO($dsn, $i['user'], $i['password'], $op);
        $pdo->exec("SET TIME ZONE 'UTC'");
    } else {
        if ($ca) { $op[PDO::MYSQL_ATTR_SSL_CA] = $ca; $op[PDO::MYSQL_ATTR_SSL_VERIFY_SERVER_CERT] = true; }
        $pdo = new PDO("mysql:host={$i['host']};port={$i['port']};dbname={$i['dbname']};charset=utf8mb4", $i['user'], $i['password'], $op);
        $pdo->exec("SET time_zone = '+00:00'");
    }
    return $pdo;
}
/* Estado del canal web→bd: versión TLS y cifrado negociado en ESTA conexión */
function canal_bd(): array {
    $t0 = microtime(true);
    try {
        if (es_pg()) {
            $r = db()->query('SELECT ssl, version, cipher FROM pg_stat_ssl WHERE pid = pg_backend_pid()')->fetch() ?: [];
            $tls = !empty($r['ssl']) ? (string)$r['version'] : ''; $cipher = (string)($r['cipher'] ?? '');
        } else {
            $r = db()->query("SHOW SESSION STATUS WHERE Variable_name IN ('Ssl_version','Ssl_cipher')")->fetchAll(PDO::FETCH_KEY_PAIR);
            $tls = (string)($r['Ssl_version'] ?? ''); $cipher = (string)($r['Ssl_cipher'] ?? '');
        }
        return ['ok' => true, 'tls' => $tls, 'cipher' => $cipher, 'verificado' => !empty(ini()['ssl_ca']),
                'ms' => round((microtime(true) - $t0) * 1000, 1), 'bd' => ini()['host'] . ':' . ini()['port'], 'web' => gethostname()];
    } catch (Throwable $e) {
        error_log('[ti3062] canal: ' . $e->getMessage());
        return ['ok' => false, 'tls' => '', 'cipher' => '', 'verificado' => false, 'ms' => 0, 'bd' => ini()['host'] ?? '?', 'web' => gethostname()];
    }
}
function insertar(string $tabla, array $d): int {
    $sql = "INSERT INTO $tabla (" . implode(', ', array_keys($d)) . ') VALUES (' . implode(', ', array_fill(0, count($d), '?')) . ')';
    if (es_pg()) { $st = db()->prepare($sql . ' RETURNING id'); $st->execute(array_values($d)); return (int)$st->fetchColumn(); }
    db()->prepare($sql)->execute(array_values($d));
    return (int)db()->lastInsertId();
}
function fila(string $sql, array $p = []): ?array { $st = db()->prepare($sql); $st->execute($p); $r = $st->fetch(); return $r ?: null; }
function filas(string $sql, array $p = []): array { $st = db()->prepare($sql); $st->execute($p); return $st->fetchAll(); }
function valor(string $sql, array $p = []) { $st = db()->prepare($sql); $st->execute($p); return $st->fetchColumn(); }
function ejecutar(string $sql, array $p = []): int { $st = db()->prepare($sql); $st->execute($p); return $st->rowCount(); }

/* ---------------------------------------------------------------- auditoría (AU-2, AU-3, AU-9) */
function auditar(string $accion, string $entidad, string $detalle = '', ?string $usuario = null): void {
    try {
        insertar('auditoria_app', ['fecha' => ahora_utc(), 'usuario' => mb_substr($usuario ?? ($_SESSION['usuario'] ?? '-'), 0, 40),
            'accion' => $accion, 'entidad' => $entidad, 'detalle' => mb_substr($detalle, 0, 500), 'ip' => $_SERVER['REMOTE_ADDR'] ?? 'cli']);
    } catch (Throwable $e) { error_log('[ti3062] auditoria: ' . $e->getMessage()); }
}

/* ---------------------------------------------------------------- sesión (AC-12, SC-23) */
function iniciar_sesion(bool $actividad = true): void {
    session_name('ti3062_sid');
    session_set_cookie_params(['lifetime' => 0, 'path' => '/', 'secure' => es_https(), 'httponly' => true, 'samesite' => 'Strict']);
    ini_set('session.use_strict_mode', '1');
    ini_set('session.use_only_cookies', '1');
    session_start();
    if (!empty($_SESSION['uid'])) {
        $t = time();
        if ($t - ($_SESSION['ultimo'] ?? 0) > INACTIVIDAD || $t - ($_SESSION['inicio'] ?? 0) > MAX_SESION) {
            auditar('sesion_expirada', 'sesion', 'Inactividad o duración máxima');
            cerrar_sesion();
            $_SESSION['aviso'] = 'Tu sesión expiró. Ingresa nuevamente.';
        } elseif ($actividad) {
            $_SESSION['ultimo'] = $t;
        }
    }
    if (empty($_SESSION['csrf'])) $_SESSION['csrf'] = bin2hex(random_bytes(32));
}
function cerrar_sesion(): void { $_SESSION = []; session_regenerate_id(true); $_SESSION['csrf'] = bin2hex(random_bytes(32)); }
function usuario(): ?array { return empty($_SESSION['uid']) ? null : $_SESSION; }
function puede(string $rol_min): bool { return isset($_SESSION['rol']) && NIVEL[$_SESSION['rol']] >= NIVEL[$rol_min]; }
function exigir(string $rol_min): void {
    if (!puede($rol_min)) {
        auditar('acceso_denegado', 'rol', 'Requiere ' . $rol_min . ' (' . ($_SERVER['REQUEST_URI'] ?? '') . ')');
        throw new RuntimeException('Tu rol no permite esta acción.');
    }
}
function csrf_ok(): void {
    if (!hash_equals($_SESSION['csrf'] ?? '', (string)($_POST['csrf'] ?? ''))) {
        auditar('csrf_invalido', 'sesion', $_SERVER['REQUEST_URI'] ?? '');
        throw new RuntimeException('La sesión del formulario no es válida. Recarga la página.');
    }
}
function csrf_campo(): string { return '<input type="hidden" name="csrf" value="' . h($_SESSION['csrf']) . '">'; }

/* ---------------------------------------------------------------- autenticación (IA-2, IA-5(1), AC-7) */
function validar_clave(string $clave, string $usuario): void {
    if (mb_strlen($clave) < MIN_CLAVE) throw new RuntimeException('La contraseña debe tener al menos ' . MIN_CLAVE . ' caracteres.');
    if (stripos($clave, $usuario) !== false) throw new RuntimeException('La contraseña no puede contener el nombre de usuario.');
    if (!preg_match('/[A-Za-z]/', $clave) || !preg_match('/[0-9]/', $clave)) throw new RuntimeException('La contraseña debe combinar letras y números.');
}
function hash_clave(string $c): string { return password_hash($c, defined('PASSWORD_ARGON2ID') ? PASSWORD_ARGON2ID : PASSWORD_DEFAULT); }
function ingresar(string $u, string $clave): ?string {
    $u = mb_strtolower(trim($u));
    $r = preg_match('/^[a-z0-9._-]{3,40}$/', $u) ? fila('SELECT * FROM usuarios_app WHERE usuario = ?', [$u]) : null;
    if ($r && $r['bloqueado_hasta'] && $r['bloqueado_hasta'] > ahora_utc()) {
        auditar('login_bloqueado', 'usuario', 'Intento durante bloqueo', $u);
        return 'Cuenta bloqueada temporalmente por intentos fallidos. Intenta más tarde o contacta al administrador.';
    }
    if (!$r || !(int)$r['activo'] || !password_verify($clave, $r['hash'])) {
        if (!$r) password_verify($clave, hash_clave('usuario-inexistente')); // tiempo similar exista o no el usuario
        if ($r) {
            $n = (int)$r['intentos'] + 1;
            $hasta = $n >= MAX_INTENTOS ? gmdate('Y-m-d H:i:s', time() + BLOQUEO_MIN * 60) : null;
            ejecutar('UPDATE usuarios_app SET intentos = ?, bloqueado_hasta = ? WHERE id = ?', [$hasta ? 0 : $n, $hasta, $r['id']]);
            if ($hasta) auditar('cuenta_bloqueada', 'usuario', MAX_INTENTOS . ' intentos fallidos', $u);
        }
        auditar('login_fallido', 'usuario', 'Credenciales incorrectas', $u ?: '-');
        return 'Usuario o contraseña incorrectos.';
    }
    ejecutar('UPDATE usuarios_app SET intentos = 0, bloqueado_hasta = NULL, ultimo_acceso = ? WHERE id = ?', [ahora_utc(), $r['id']]);
    if (password_needs_rehash($r['hash'], defined('PASSWORD_ARGON2ID') ? PASSWORD_ARGON2ID : PASSWORD_DEFAULT)) {
        ejecutar('UPDATE usuarios_app SET hash = ? WHERE id = ?', [hash_clave($clave), $r['id']]);
    }
    session_regenerate_id(true);   // SC-23: evita fijación de sesión
    $_SESSION = ['uid' => (int)$r['id'], 'usuario' => $r['usuario'], 'nombre' => $r['nombre'], 'rol' => $r['rol'],
                 'inicio' => time(), 'ultimo' => time(), 'csrf' => bin2hex(random_bytes(32))];
    auditar('login_ok', 'usuario', 'Rol ' . $r['rol']);
    return null;
}

/* ---------------------------------------------------------------- validación de entradas (SI-10) */
function opciones(string $tipo): array { return str_starts_with($tipo, 'select:') ? explode('|', substr($tipo, 7)) : []; }
function validar(array $campos, array $src): array {
    $out = [];
    foreach ($campos as [$k, $tipo, $label]) {
        $v = trim(preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/u', '', (string)($src[$k] ?? '')));
        if ($v === '') {
            if ($tipo === 'textarea') { $out[$k] = ''; continue; }
            throw new RuntimeException("Falta: $label.");
        }
        switch (true) {
            case $tipo === 'number':
                if (!is_numeric($v) || (float)$v < 0 || (float)$v > 999999999) throw new RuntimeException("$label debe ser un número entre 0 y 999.999.999.");
                $v = (string)(float)$v; break;
            case $tipo === 'email':
                if (!filter_var($v, FILTER_VALIDATE_EMAIL)) throw new RuntimeException("$label no es un correo válido."); break;
            case $tipo === 'tel':
                if (!preg_match('/^\+?[0-9 ()-]{6,20}$/', $v)) throw new RuntimeException("$label no es un teléfono válido."); break;
            case $tipo === 'date':
                $d = DateTimeImmutable::createFromFormat('!Y-m-d', $v);
                if (!$d || $d->format('Y-m-d') !== $v) throw new RuntimeException("$label no es una fecha válida."); break;
            case str_starts_with($tipo, 'select:'):
                if (!in_array($v, opciones($tipo), true)) throw new RuntimeException("Valor no permitido en $label."); break;
            default:
                if (mb_strlen($v) > ($tipo === 'textarea' ? 500 : 150)) throw new RuntimeException("$label es demasiado largo.");
        }
        $out[$k] = $v;
    }
    return $out;
}
function entero($v, int $min, int $max, string $label): int {
    if (filter_var($v, FILTER_VALIDATE_INT) === false || (int)$v < $min || (int)$v > $max) throw new RuntimeException("$label debe ser un entero entre $min y $max.");
    return (int)$v;
}
function fecha_ok(string $v, string $label): string {
    $d = DateTimeImmutable::createFromFormat('!Y-m-d', $v);
    if (!$d || $d->format('Y-m-d') !== $v) throw new RuntimeException("$label no es una fecha válida.");
    return $v;
}
function texto(string $v, string $label, int $max = 150): string {
    $v = trim($v);
    if ($v === '' || mb_strlen($v) > $max) throw new RuntimeException("$label es obligatorio (máx. $max caracteres).");
    return $v;
}

/* ---------------------------------------------------------------- utilidades de interfaz */
function etiqueta_padre(array $f): string { global $TEMA; return (string)$f[$TEMA['padre']['campos'][0][0]]; }
function control(array $c, $valor = ''): string {
    [$k, $tipo, $label] = $c;
    $req = $tipo === 'textarea' ? '' : ' required';
    $html = '<label><span>' . h($label) . '</span>';
    if ($ops = opciones($tipo)) {
        $html .= '<select name="' . h($k) . '"' . $req . '>';
        foreach ($ops as $o) $html .= '<option' . ($o === (string)$valor ? ' selected' : '') . '>' . h($o) . '</option>';
        $html .= '</select>';
    } elseif ($tipo === 'textarea') {
        $html .= '<textarea name="' . h($k) . '" maxlength="500" rows="3">' . h($valor) . '</textarea>';
    } else {
        $extra = $tipo === 'number' ? ' step="any" min="0"' : ' maxlength="150"';
        $html .= '<input name="' . h($k) . '" type="' . h($tipo) . '" value="' . h($valor) . '"' . $extra . $req . '>';
    }
    return $html . '</label>';
}
/* Estado SIEMPRE con color + ícono + texto (accesible: nunca solo color) */
function insignia(string $texto, string $tono = ''): string {
    $ico = ['bien' => '✓', 'alerta' => '▲', 'mal' => '✕', 'info' => '●'][$tono] ?? '';
    return '<span class="pill ' . h($tono) . '">' . ($ico ? '<i aria-hidden="true">' . $ico . '</i>' : '') . h($texto) . '</span>';
}
function barra(float $v, float $max): string { return '<progress max="' . h(max($max, 1)) . '" value="' . h($v) . '"></progress>'; }
function csv_seguro($v): string { $v = (string)$v; return preg_match('/^[=+\-@\t\r]/', $v) ? "'" . $v : $v; }  // SI-10: sin fórmulas en CSV
