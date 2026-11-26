<?php
/* Crea un usuario de la aplicación desde la consola de web-{{NN}} (no es accesible por web).
 * Uso: printf '%s' "$CLAVE" | php crear-usuario.php <usuario> <admin|operador|auditor> "<Nombre>"
 * La contraseña se lee por la entrada estándar para que no quede en el historial ni en la lista de procesos. */
declare(strict_types=1);
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
require __DIR__ . '/nucleo.php';
[, $u, $rol, $nombre] = $argv + [null, '', '', ''];
$u = mb_strtolower(trim((string)$u));
try {
    if (!preg_match('/^[a-z0-9._-]{3,40}$/', $u)) throw new RuntimeException('Usuario: 3 a 40 caracteres (a-z, 0-9, . _ -).');
    if (!isset(ROLES[$rol])) throw new RuntimeException('Rol: admin, operador o auditor.');
    if (valor('SELECT COUNT(*) FROM usuarios_app WHERE usuario = ?', [$u])) { echo "El usuario $u ya existe: no se modifica.\n"; exit(0); }
    $clave = rtrim((string)stream_get_contents(STDIN), "\r\n");
    validar_clave($clave, $u);
    insertar('usuarios_app', ['usuario' => $u, 'nombre' => texto((string)$nombre ?: $u, 'Nombre', 100), 'hash' => hash_clave($clave), 'rol' => $rol,
        'activo' => 1, 'intentos' => 0, 'creado_en' => ahora_utc()]);
    $_SERVER['REMOTE_ADDR'] = 'consola';
    auditar('usuario_crear', 'usuarios_app', "$u rol $rol (consola)", 'root');
    echo "Usuario $u creado con rol " . ROLES[$rol] . ".\n";
} catch (Throwable $e) {
    fwrite(STDERR, 'Error: ' . ($e instanceof PDOException ? 'no se pudo conectar o escribir en la base de datos (' . $e->getCode() . ')' : $e->getMessage()) . "\n");
    exit(1);
}
