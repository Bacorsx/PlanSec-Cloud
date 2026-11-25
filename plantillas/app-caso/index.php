<?php
/* Aplicación del caso — TI3062 NN {{NN}} — {{APP_CASO}}
 * Las credenciales NO están en el código: se leen de /etc/ti3062/db.ini (fuera del webroot y del repositorio). */
declare(strict_types=1);
session_start();
require __DIR__ . '/config_tema.php';

function h($s): string { return htmlspecialchars((string)$s, ENT_QUOTES, 'UTF-8'); }

function db(): PDO {
    static $pdo = null;
    if ($pdo) return $pdo;
    $ini = @parse_ini_file('/etc/ti3062/db.ini');
    if (!$ini) { http_response_code(500); exit('Falta /etc/ti3062/db.ini'); }
    $dsn = $ini['driver'] === 'pgsql'
        ? "pgsql:host={$ini['host']};port={$ini['port']};dbname={$ini['dbname']}"
        : "mysql:host={$ini['host']};port={$ini['port']};dbname={$ini['dbname']};charset=utf8mb4";
    $pdo = new PDO($dsn, $ini['user'], $ini['password'], [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
    return $pdo;
}

if (empty($_SESSION['csrf'])) $_SESSION['csrf'] = bin2hex(random_bytes(16));
$vista = ($_GET['v'] ?? 'hijo') === 'padre' ? 'padre' : 'hijo';
$def = $TEMA[$vista];
$msg = ''; $err = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    try {
        if (!hash_equals($_SESSION['csrf'], $_POST['csrf'] ?? '')) throw new RuntimeException('Token inválido');
        $cols = []; $vals = [];
        foreach ($def['campos'] as [$k, $tipo, $label]) {
            $v = trim((string)($_POST[$k] ?? ''));
            if ($v === '' && $tipo !== 'textarea') throw new RuntimeException("Falta: $label");
            if ($tipo === 'number' && !is_numeric($v)) throw new RuntimeException("$label debe ser numérico");
            if (str_starts_with($tipo, 'select:') && !in_array($v, explode('|', substr($tipo, 7)), true)) throw new RuntimeException("Valor no válido en $label");
            $cols[] = $k; $vals[] = mb_substr($v, 0, 500);
        }
        if ($vista === 'hijo') {
            $fk = (int)($_POST[$def['fk']] ?? 0);
            if ($fk <= 0) throw new RuntimeException('Seleccione ' . $TEMA['padre']['singular']);
            $cols[] = $def['fk']; $vals[] = $fk;
        }
        $sql = 'INSERT INTO ' . $def['tabla'] . ' (' . implode(',', $cols) . ') VALUES (' . implode(',', array_fill(0, count($cols), '?')) . ')';
        db()->prepare($sql)->execute($vals);
        $msg = ucfirst($def['singular']) . ' registrado correctamente.';
    } catch (Throwable $e) {
        $err = $e instanceof PDOException ? 'Error de base de datos.' : $e->getMessage();
        if ($e instanceof PDOException) error_log('[ti3062] ' . $e->getMessage());
    }
}

$padres = []; $filas = []; $total = ['padre' => 0, 'hijo' => 0];
try {
    $P = $TEMA['padre']; $H = $TEMA['hijo'];
    $padres = db()->query("SELECT id, {$P['campos'][0][0]} AS etiqueta FROM {$P['tabla']} ORDER BY etiqueta")->fetchAll();
    $total['padre'] = (int)db()->query("SELECT COUNT(*) FROM {$P['tabla']}")->fetchColumn();
    $total['hijo'] = (int)db()->query("SELECT COUNT(*) FROM {$H['tabla']}")->fetchColumn();
    $filas = $vista === 'padre'
        ? db()->query("SELECT p.*, (SELECT COUNT(*) FROM {$H['tabla']} h WHERE h.{$H['fk']} = p.id) AS relacionados FROM {$P['tabla']} p ORDER BY p.id DESC LIMIT 200")->fetchAll()
        : db()->query("SELECT h.*, p.{$P['campos'][0][0]} AS padre FROM {$H['tabla']} h JOIN {$P['tabla']} p ON p.id = h.{$H['fk']} ORDER BY h.id DESC LIMIT 200")->fetchAll();
} catch (Throwable $e) { $err = $err ?: 'No hay conexión con la base de datos.'; error_log('[ti3062] ' . $e->getMessage()); }
?>
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title><?= h($TEMA['nombre_app']) ?> · <?= h($def['titulo']) ?></title>
<link rel="stylesheet" href="estilo.css">
</head>
<body class="variante-{{VARIANTE_APP}}">
<header>
  <div class="marca"><span class="logo"><?= h(mb_substr($TEMA['nombre_app'], 0, 1)) ?></span><div><strong><?= h($TEMA['nombre_app']) ?></strong><small><?= h($TEMA['titulo']) ?></small></div></div>
  <nav>
    <a href="?v=hijo" class="<?= $vista === 'hijo' ? 'activo' : '' ?>"><?= h($TEMA['hijo']['titulo']) ?> (<?= $total['hijo'] ?>)</a>
    <a href="?v=padre" class="<?= $vista === 'padre' ? 'activo' : '' ?>"><?= h($TEMA['padre']['titulo']) ?> (<?= $total['padre'] ?>)</a>
  </nav>
</header>
<main>
  <?php if ($msg): ?><p class="ok"><?= h($msg) ?></p><?php endif; ?>
  <?php if ($err): ?><p class="error"><?= h($err) ?></p><?php endif; ?>
  <section class="panel">
    <h2>Registrar <?= h($def['singular']) ?></h2>
    <form method="post" action="?v=<?= $vista ?>">
      <input type="hidden" name="csrf" value="<?= h($_SESSION['csrf']) ?>">
      <?php if ($vista === 'hijo'): ?>
        <label><?= h(ucfirst($TEMA['padre']['singular'])) ?>
          <select name="<?= h($def['fk']) ?>" required><option value="">— seleccione —</option>
            <?php foreach ($padres as $p): ?><option value="<?= (int)$p['id'] ?>"><?= h($p['etiqueta']) ?></option><?php endforeach; ?>
          </select></label>
        <?php if (!$padres): ?><p class="aviso">Primero registre un <?= h($TEMA['padre']['singular']) ?> en la pestaña <?= h($TEMA['padre']['titulo']) ?>.</p><?php endif; ?>
      <?php endif; ?>
      <?php foreach ($def['campos'] as [$k, $tipo, $label]): ?>
        <label><?= h($label) ?>
        <?php if (str_starts_with($tipo, 'select:')): ?>
          <select name="<?= h($k) ?>" required><?php foreach (explode('|', substr($tipo, 7)) as $o): ?><option><?= h($o) ?></option><?php endforeach; ?></select>
        <?php elseif ($tipo === 'textarea'): ?>
          <textarea name="<?= h($k) ?>" maxlength="500"></textarea>
        <?php else: ?>
          <input name="<?= h($k) ?>" type="<?= h($tipo) ?>" <?= $tipo === 'number' ? 'step="any"' : '' ?> maxlength="150" required>
        <?php endif; ?></label>
      <?php endforeach; ?>
      <button type="submit">Guardar</button>
    </form>
  </section>
  <section class="panel">
    <h2>Listado de <?= h(mb_strtolower($def['titulo'])) ?> <small>(desde la base de datos)</small></h2>
    <div class="tabla"><table>
      <thead><tr><th>ID</th><?php if ($vista === 'hijo'): ?><th><?= h(ucfirst($TEMA['padre']['singular'])) ?></th><?php endif; ?>
        <?php foreach ($def['campos'] as [$k, $t, $label]): ?><th><?= h($label) ?></th><?php endforeach; ?>
        <?php if ($vista === 'padre'): ?><th><?= h($TEMA['hijo']['titulo']) ?></th><?php endif; ?><th>Registrado</th></tr></thead>
      <tbody>
      <?php foreach ($filas as $f): ?><tr><td><?= (int)$f['id'] ?></td><?php if ($vista === 'hijo'): ?><td><?= h($f['padre']) ?></td><?php endif; ?>
        <?php foreach ($def['campos'] as [$k]): ?><td><?= h($f[$k]) ?></td><?php endforeach; ?>
        <?php if ($vista === 'padre'): ?><td><?= (int)$f['relacionados'] ?></td><?php endif; ?><td><?= h($f['creado_en']) ?></td></tr>
      <?php endforeach; ?>
      <?php if (!$filas): ?><tr><td colspan="20">Sin registros todavía.</td></tr><?php endif; ?>
      </tbody></table></div>
  </section>
</main>
<footer>Servidor: <?= h(gethostname()) ?> · TI3062 · NN {{NN}} · {{ESTUDIANTE}}</footer>
</body>
</html>
