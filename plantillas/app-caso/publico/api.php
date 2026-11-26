<?php
/* API en vivo (JSON) — la consulta app.js cada 5 s. Exige sesión y NO renueva el tiempo de inactividad (AC-12). */
declare(strict_types=1);
$PRIV = getenv('TI3062_PRIV') ?: __DIR__ . '/../ti3062';
require $PRIV . '/nucleo.php';
require $PRIV . '/patrones.php';
cabeceras();
header('Content-Type: application/json; charset=utf-8');
try { iniciar_sesion(false); } catch (Throwable $e) { http_response_code(503); echo '{"error":"servicio"}'; exit; }
if (!usuario()) { http_response_code(401); echo '{"error":"sesion"}'; exit; }
try {
    $P = $TEMA['padre']; $H = $TEMA['hijo'];
    $ult = filas("SELECT h.*, p." . ETQ() . " AS padre_txt FROM {$H['tabla']} h JOIN {$P['tabla']} p ON p.id = h.{$H['fk']} ORDER BY h.id DESC LIMIT 8");
    echo json_encode([
        'hora' => local(ahora_utc(), 'H:i:s'),
        'kpis' => array_map(fn($k) => ['v' => $k[1], 't' => $k[2]], p_kpis()),
        'ultimos' => array_map(fn($f) => ['cuando' => local($f['creado_en'], 'd-m H:i'), 'texto' => p_vivo($f), 'tono' => p_estado($f)[1]], $ult),
        'canal' => canal_bd(),
        'https' => es_https(),
    ], JSON_UNESCAPED_UNICODE);
} catch (Throwable $e) {
    error_log('[ti3062] api: ' . $e->getMessage());
    http_response_code(503);
    echo json_encode(['error' => 'bd', 'canal' => ['ok' => false]]);
}
