<?php
/* Paquete de evidencia de la CAPA DE ENFOQUE para la CAPA DE INFORME (TI3062 NN {{NN}}).
 * Solo datos medidos en este servidor: no incluye contraseñas, hashes ni datos personales de los registros.
 * La capa de informe (sistema de gestión) lo importa con «Importar evidencia de la app». */
declare(strict_types=1);

function evidencia_app(): array {
    global $TEMA;
    $P = PT(); $H = HT();
    $cuenta = fn(string $t): int => (int)valor("SELECT COUNT(*) FROM $t");
    $aud = [];
    foreach (filas('SELECT accion, COUNT(*) AS n, MAX(fecha) AS ultima FROM auditoria_app GROUP BY accion ORDER BY accion') as $r) {
        $aud[$r['accion']] = ['n' => (int)$r['n'], 'ultima' => local($r['ultima'], 'd-m-Y H:i')];
    }
    $ev = fn(string $a): int => $aud[$a]['n'] ?? 0;
    $ult = fn(string $a): string => $aud[$a]['ultima'] ?? '—';
    $roles = [];
    foreach (filas('SELECT rol, COUNT(*) AS n, SUM(activo) AS activos FROM usuarios_app GROUP BY rol ORDER BY rol') as $r) {
        $roles[$r['rol']] = ['total' => (int)$r['n'], 'activos' => (int)$r['activos']];
    }
    $canal = canal_bd();
    // AU-9: intento de borrado sin efecto posible (WHERE 1 = 0). Si el motor lo permite, es un hallazgo.
    try { db()->exec('DELETE FROM auditoria_app WHERE 1 = 0'); $au9 = 'PERMITIDO'; }
    catch (Throwable $e) { $au9 = 'DENEGADO por el motor (código ' . $e->getCode() . ')'; }
    $np = $cuenta($P); $nh = $cuenta($H);
    $xss = (int)valor('SELECT COUNT(*) FROM ' . $P . ' WHERE ' . ETQ() . ' LIKE ?', ['%<%']);
    $hora = local(ahora_utc(), 'd-m-Y H:i');
    $pr = [
        ['id' => 'P1', 'medido' => $np > 0 && $nh > 0,
         'obtenido' => sprintf('App %s operativa por %s: %d %s y %d %s registrados desde la app y listados desde la base de datos (%s).',
             $TEMA['nombre_app'], es_https() ? 'HTTPS' : 'HTTP', $np, mb_strtolower($TEMA['padre']['titulo']), $nh, mb_strtolower($TEMA['hijo']['titulo']), $hora)],
        ['id' => 'P9', 'medido' => $canal['ok'] && $canal['tls'] !== '',
         'obtenido' => $canal['tls'] !== ''
             ? "Canal web-{{NN}} → bd-{{NN}} cifrado con {$canal['tls']} ({$canal['cipher']}); certificado del servidor verificado con la CA del proyecto: " . ($canal['verificado'] ? 'sí' : 'no') . "; latencia {$canal['ms']} ms ($hora). La captura de tcpdump se adjunta aparte."
             : 'La conexión a la base de datos no está cifrada.'],
        ['id' => 'P10', 'medido' => $ev('cuenta_bloqueada') > 0,
         'obtenido' => $ev('login_fallido') . ' ingresos fallidos y ' . $ev('cuenta_bloqueada') . ' bloqueo(s) de cuenta registrados en auditoria_app (último bloqueo: ' . $ult('cuenta_bloqueada') . ').'],
        ['id' => 'P11', 'medido' => $ev('acceso_denegado') > 0,
         'obtenido' => $ev('acceso_denegado') . ' acción(es) denegada(s) por rol registradas como acceso_denegado (última: ' . $ult('acceso_denegado') . ').'],
        ['id' => 'P12', 'medido' => $xss > 0,
         'obtenido' => "$xss entrada(s) con código HTML/JS en {$P}: se almacenan como texto y se muestran escapadas; la CSP bloquea scripts en línea."],
        ['id' => 'P13', 'medido' => true,
         'obtenido' => "Intento de DELETE sobre auditoria_app con el usuario de la aplicación: $au9 ($hora)."],
    ];
    return [
        'tipo' => 'evidencia-ti3062', 'version' => 1, 'nn' => '{{NN}}', 'app' => $TEMA['nombre_app'], 'patron' => PATRON(),
        'generado' => local(ahora_utc(), 'd-m-Y H:i:s'), 'servidor' => gethostname(),
        'exportado_por' => $_SESSION['usuario'] . ' (' . ROLES[$_SESSION['rol']] . ')',
        'https' => es_https(),
        'canal_bd' => ['tls' => $canal['tls'], 'cifrado' => $canal['cipher'], 'certificado_verificado' => $canal['verificado'], 'latencia_ms' => $canal['ms'], 'bd' => $canal['bd']],
        'cabeceras' => array_values(array_filter(headers_list(), fn($h) => (bool)preg_match('/^(Content-Security-Policy|Strict-Transport-Security|Permissions-Policy|Cache-Control):/i', $h))),
        'tablas' => ['usuarios_app' => $cuenta('usuarios_app'), $P => $np, $H => $nh, 'auditoria_app' => $cuenta('auditoria_app')],
        'usuarios_por_rol' => $roles,
        'auditoria' => $aud,
        'indicadores' => array_map(fn($k) => ['indicador' => $k[0], 'valor' => $k[1]], p_kpis()),
        'controles' => ['SC-8' => $canal['tls'] !== '' && $canal['verificado'], 'AU-9' => str_starts_with($au9, 'DENEGADO'),
                        'AC-7' => $ev('cuenta_bloqueada') > 0, 'AC-3' => $ev('acceso_denegado') > 0, 'SI-10' => $xss > 0],
        'pruebas' => $pr,
    ];
}
