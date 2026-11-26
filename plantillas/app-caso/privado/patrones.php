<?php
/* Reglas de negocio según el patrón de la temática (inventario, reservas, prestamos, ordenes, membresias).
 * Toda operación que cambia más de una tabla corre en una transacción con bloqueo de fila (FOR UPDATE). */
declare(strict_types=1);

function ultimo(array $a) { return $a[array_key_last($a)]; }
function PT(): string { global $TEMA; return $TEMA['padre']['tabla']; }
function HT(): string { global $TEMA; return $TEMA['hijo']['tabla']; }
function FK(): string { global $TEMA; return $TEMA['hijo']['fk']; }
function V(string $k, $def = null) { global $TEMA; return $TEMA['vocab'][$k] ?? $def; }
function PATRON(): string { global $TEMA; return $TEMA['patron']; }
function ETQ(): string { global $TEMA; return $TEMA['padre']['campos'][0][0]; }
function CLI(): string { global $TEMA; return $TEMA['hijo']['campos'][0][0]; }
function inicio_dia_utc(int $desplaz = 0): string {
    return (new DateTimeImmutable('today', new DateTimeZone(ZONA)))->modify("$desplaz days")->setTimezone(new DateTimeZone('UTC'))->format('Y-m-d H:i:s');
}
function tx(callable $f) {
    db()->beginTransaction();
    try { $r = $f(); db()->commit(); return $r; }
    catch (Throwable $e) { if (db()->inTransaction()) db()->rollBack(); throw $e; }
}
function bloquear_padre(int $id, string $cond = ''): array {
    $r = fila('SELECT * FROM ' . PT() . ' WHERE id = ? AND activo = 1 ' . $cond . ' FOR UPDATE', [$id]);
    if (!$r) { global $TEMA; throw new RuntimeException('El ' . $TEMA['padre']['singular'] . ' no existe, está inactivo o no cumple la condición requerida.'); }
    return $r;
}

/* ------------------------------------------------ campos estándar del patrón */
function p_campos_padre(): array {
    return match (PATRON()) {
        'inventario' => array_merge(V('precio') ? [['precio', 'number', 'Precio unitario (CLP)']] : [], [['stock_minimo', 'number', 'Stock mínimo (alerta)']]),
        'membresias' => [['valor', 'number', 'Valor (CLP)'], ['duracion_dias', 'number', 'Duración (días)']],
        default => [],
    };
}
function p_columnas_padre(): array {   // [titulo, fn(fila) => html]
    return match (PATRON()) {
        'inventario' => array_merge(
            [['Stock', fn($f) => num($f['stock']) . ((int)$f['stock'] <= (int)$f['stock_minimo'] ? ' ' . insignia('CRÍTICO', 'mal') : '')], ['Mínimo', fn($f) => num($f['stock_minimo'])]],
            V('precio') ? [['Precio', fn($f) => dinero($f['precio'])]] : []),
        'prestamos' => [['Estado', fn($f) => insignia($f['estado_item'], ['Disponible' => 'bien', 'Prestado' => 'alerta', 'Mantención' => 'info'][$f['estado_item']] ?? '')]],
        'membresias' => [['Valor', fn($f) => dinero($f['valor'])], ['Duración', fn($f) => num($f['duracion_dias']) . ' días']],
        default => [],
    };
}

/* ------------------------------------------------ formulario de la operación principal */
function p_form_hijo(): string {
    $h = '';
    switch (PATRON()) {
        case 'inventario':
            $h .= '<label><span>Tipo de movimiento</span><select name="tipo" required>';
            foreach (V('tipos') as [$t, $s]) $h .= '<option value="' . h($t) . '">' . h($t) . ($s > 0 ? ' (+)' : ' (−)') . '</option>';
            $h .= '</select></label><label><span>Cantidad (' . h(V('unidad', 'unidades')) . ')</span><input type="number" name="cantidad" min="1" max="100000" step="1" required></label>';
            break;
        case 'reservas':
            if (V('modo') === 'rango') {
                $h .= '<label><span>Entrada</span><input type="date" name="fecha" min="' . hoy() . '" value="' . hoy() . '" required></label>'
                    . '<label><span>Salida</span><input type="date" name="fecha_fin" min="' . dias(hoy(), 1) . '" value="' . dias(hoy(), 1) . '" required></label>';
            } else {
                $h .= '<label><span>Fecha</span><input type="date" name="fecha" min="' . hoy() . '" value="' . hoy() . '" required></label><label><span>Bloque</span><select name="bloque" required>';
                foreach (V('bloques') as $b) $h .= '<option>' . h($b) . '</option>';
                $h .= '</select></label>';
            }
            break;
        case 'prestamos':
            $h .= '<label><span>Devolver a más tardar</span><input type="date" name="fecha_compromiso" min="' . hoy() . '" max="' . dias(hoy(), 60) . '" value="' . dias(hoy(), (int)V('dias', 7)) . '" required></label>';
            break;
        case 'ordenes':
            $h .= '<label><span>' . h(V('nivel')) . '</span><select name="nivel" required>';
            foreach (V('niveles') as $n) $h .= '<option>' . h($n) . '</option>';
            $h .= '</select></label>';
            if (V('monto')) $h .= '<label><span>' . h(V('monto')) . ' (opcional)</span><input type="number" name="monto" min="0" step="1"></label>';
            break;
        case 'membresias':
            $h .= '<label><span>Fecha de inicio</span><input type="date" name="fecha_inicio" min="' . dias(hoy(), -30) . '" max="' . dias(hoy(), 30) . '" value="' . hoy() . '" required></label>';
            break;
    }
    return $h;
}
/* Ítems del padre que se pueden elegir al registrar */
function p_padres_elegibles(): array {
    $cond = PATRON() === 'prestamos' ? " AND estado_item = 'Disponible'" : '';
    $extra = PATRON() === 'inventario' ? ', stock' : '';
    return filas('SELECT id, ' . ETQ() . ' AS etiqueta' . $extra . ' FROM ' . PT() . ' WHERE activo = 1' . $cond . ' ORDER BY ' . ETQ());
}

/* ------------------------------------------------ registrar operación (con reglas) */
function p_registrar(array $datos, array $post): string {
    global $TEMA; $fk = entero($post[FK()] ?? '', 1, PHP_INT_MAX, ucfirst($TEMA['padre']['singular']));
    $base = $datos + [FK() => $fk, 'usuario_id' => $_SESSION['uid'], 'creado_en' => ahora_utc()];
    switch (PATRON()) {
        case 'inventario':
            $tipos = array_column(V('tipos'), 1, 0);
            $tipo = (string)($post['tipo'] ?? '');
            if (!isset($tipos[$tipo])) throw new RuntimeException('Tipo de movimiento no permitido.');
            $cant = entero($post['cantidad'] ?? '', 1, 100000, 'Cantidad');
            return tx(function () use ($fk, $tipo, $tipos, $cant, $base) {
                $it = bloquear_padre($fk);
                $nuevo = (int)$it['stock'] + $tipos[$tipo] * $cant;
                if ($nuevo < 0) throw new RuntimeException('Stock insuficiente: hay ' . num($it['stock']) . ' ' . V('unidad') . ' de «' . etiqueta_padre($it) . '».');
                ejecutar('UPDATE ' . PT() . ' SET stock = ? WHERE id = ?', [$nuevo, $fk]);
                $id = insertar(HT(), $base + ['tipo' => $tipo, 'cantidad' => $cant, 'monto' => V('precio') ? $cant * (float)$it['precio'] : 0]);
                auditar('registrar', HT(), "#$id $tipo $cant de " . etiqueta_padre($it) . " (stock $it[stock] → $nuevo)");
                $aviso = $nuevo <= (int)$it['stock_minimo'] ? ' ⚠ Quedó en stock crítico.' : '';
                return "$tipo registrado. Stock de «" . etiqueta_padre($it) . "»: $nuevo." . $aviso;
            });
        case 'reservas':
            $f = fecha_ok((string)($post['fecha'] ?? ''), 'Fecha');
            if ($f < hoy()) throw new RuntimeException('No se puede reservar en una fecha pasada.');
            if (V('modo') === 'rango') {
                $ff = fecha_ok((string)($post['fecha_fin'] ?? ''), 'Salida');
                if ($ff <= $f) throw new RuntimeException('La salida debe ser posterior a la entrada.');
                if ($ff > dias($f, 30)) throw new RuntimeException('La estadía máxima es de 30 noches.');
                $extra = ['fecha' => $f, 'fecha_fin' => $ff];
                $cruce = 'fecha < ? AND fecha_fin > ?'; $par = [$ff, $f];
            } else {
                $b = (string)($post['bloque'] ?? '');
                if (!in_array($b, V('bloques'), true)) throw new RuntimeException('Bloque horario no válido.');
                $extra = ['fecha' => $f, 'bloque' => $b];
                $cruce = 'fecha = ? AND bloque = ?'; $par = [$f, $b];
            }
            return tx(function () use ($fk, $extra, $cruce, $par, $base) {
                $r = bloquear_padre($fk);   // serializa las reservas del mismo recurso
                $n = (int)valor('SELECT COUNT(*) FROM ' . HT() . ' WHERE ' . FK() . " = ? AND estado = 'Confirmada' AND $cruce", array_merge([$fk], $par));
                if ($n > 0) throw new RuntimeException('«' . etiqueta_padre($r) . '» ya tiene una reserva confirmada que se cruza con ese horario.');
                $id = insertar(HT(), $base + $extra + ['estado' => 'Confirmada']);
                auditar('registrar', HT(), "#$id " . etiqueta_padre($r) . ' ' . implode(' ', $extra));
                return 'Reserva confirmada para «' . etiqueta_padre($r) . '» (' . fecha($extra['fecha']) . ' ' . ($extra['bloque'] ?? 'al ' . fecha($extra['fecha_fin'])) . ').';
            });
        case 'prestamos':
            $fc = fecha_ok((string)($post['fecha_compromiso'] ?? ''), 'Fecha de devolución');
            if ($fc < hoy() || $fc > dias(hoy(), 60)) throw new RuntimeException('La devolución debe estar entre hoy y 60 días más.');
            return tx(function () use ($fk, $fc, $base) {
                $it = bloquear_padre($fk, "AND estado_item = 'Disponible'");
                $id = insertar(HT(), $base + ['fecha_prestamo' => hoy(), 'fecha_compromiso' => $fc, 'estado' => 'Activo']);
                ejecutar('UPDATE ' . PT() . " SET estado_item = 'Prestado' WHERE id = ?", [$fk]);
                auditar('registrar', HT(), "#$id préstamo de " . etiqueta_padre($it) . " hasta $fc");
                return 'Préstamo registrado: «' . etiqueta_padre($it) . '» debe devolverse el ' . fecha($fc) . '.';
            });
        case 'ordenes':
            $niv = (string)($post['nivel'] ?? '');
            if (!in_array($niv, V('niveles'), true)) throw new RuntimeException(V('nivel') . ' no válida.');
            $monto = null;
            if (V('monto') && ($post['monto'] ?? '') !== '') $monto = entero($post['monto'], 0, 999999999, V('monto'));
            $it = fila('SELECT * FROM ' . PT() . ' WHERE id = ? AND activo = 1', [$fk]) ?? throw new RuntimeException('Registro no válido.');
            $id = insertar(HT(), $base + ['nivel' => $niv, 'estado' => V('estados')[0], 'monto' => $monto, 'actualizado_en' => ahora_utc()]);
            auditar('registrar', HT(), "#$id $niv en " . etiqueta_padre($it));
            return ucfirst($GLOBALS['TEMA']['hijo']['singular']) . " #$id abierto en estado «" . V('estados')[0] . '».';
        case 'membresias':
            $fi = fecha_ok((string)($post['fecha_inicio'] ?? ''), 'Fecha de inicio');
            if ($fi < dias(hoy(), -30) || $fi > dias(hoy(), 30)) throw new RuntimeException('La fecha de inicio debe estar a ±30 días de hoy.');
            $plan = fila('SELECT * FROM ' . PT() . ' WHERE id = ? AND activo = 1', [$fk]) ?? throw new RuntimeException('Plan no válido.');
            $ff = dias($fi, (int)$plan['duracion_dias']);
            $id = insertar(HT(), $base + ['fecha_inicio' => $fi, 'fecha_fin' => $ff, 'estado' => 'Activa']);
            auditar('registrar', HT(), "#$id plan " . etiqueta_padre($plan) . " {$fi}→{$ff}");
            return 'Inscripción registrada en «' . etiqueta_padre($plan) . '», vigente hasta el ' . fecha($ff) . '.';
    }
    throw new RuntimeException('Patrón desconocido.');
}

/* ------------------------------------------------ acciones sobre una operación */
function p_acciones(): array {   // accion => [etiqueta, rol mínimo, confirmación]
    return match (PATRON()) {
        'reservas' => ['completar' => [V('completar'), 'operador', ''], 'cancelar' => ['Cancelar', 'operador', '¿Cancelar esta reserva?']],
        'prestamos' => ['devolver' => ['Devolver', 'operador', '']],
        'ordenes' => ['avanzar' => ['Avanzar', 'operador', '']],
        'membresias' => ['renovar' => ['Renovar', 'operador', ''], 'suspender' => ['Suspender', 'operador', '¿Suspender la membresía?'], 'reactivar' => ['Reactivar', 'operador', '']],
        default => [],
    };
}
function p_acciones_fila(array $f): array {   // acciones aplicables a la fila
    return match (PATRON()) {
        'reservas' => $f['estado'] === 'Confirmada' ? ($f['fecha'] <= hoy() ? ['completar', 'cancelar'] : ['cancelar']) : [],
        'prestamos' => $f['estado'] === 'Activo' ? ['devolver'] : [],
        'ordenes' => $f['estado'] !== ultimo($GLOBALS['TEMA']['vocab']['estados']) ? ['avanzar'] : [],
        'membresias' => $f['estado'] === 'Suspendida' ? ['reactivar'] : ['renovar', 'suspender'],
        default => [],
    };
}
function p_accion(string $acc, int $id): string {
    if (!isset(p_acciones()[$acc])) throw new RuntimeException('Acción no permitida.');
    exigir(p_acciones()[$acc][1]);
    return tx(function () use ($acc, $id) {
        $f = fila('SELECT * FROM ' . HT() . ' WHERE id = ? FOR UPDATE', [$id]) ?? throw new RuntimeException('Registro no encontrado.');
        if (!in_array($acc, p_acciones_fila($f), true)) throw new RuntimeException('La acción no aplica al estado actual del registro.');
        switch ($acc) {
            case 'cancelar': ejecutar('UPDATE ' . HT() . " SET estado = 'Cancelada' WHERE id = ?", [$id]); $m = 'Reserva cancelada.'; break;
            case 'completar': ejecutar('UPDATE ' . HT() . " SET estado = 'Completada' WHERE id = ?", [$id]); $m = 'Reserva marcada como «' . V('completar') . '».'; break;
            case 'devolver':
                ejecutar('UPDATE ' . HT() . " SET estado = 'Devuelto', fecha_devolucion = ? WHERE id = ?", [hoy(), $id]);
                ejecutar('UPDATE ' . PT() . " SET estado_item = 'Disponible' WHERE id = ? AND estado_item = 'Prestado'", [$f[FK()]]);
                $m = 'Devolución registrada' . ($f['fecha_compromiso'] < hoy() ? ' con ' . (new DateTime($f['fecha_compromiso']))->diff(new DateTime(hoy()))->days . ' día(s) de atraso.' : ' a tiempo.');
                break;
            case 'avanzar':
                $est = V('estados'); $i = array_search($f['estado'], $est, true);
                $nuevo = $est[$i + 1];
                $cierre = $nuevo === ultimo($est) ? ahora_utc() : null;
                ejecutar('UPDATE ' . HT() . ' SET estado = ?, actualizado_en = ?' . ($cierre ? ', cerrado_en = ?' : '') . ' WHERE id = ?',
                    $cierre ? [$nuevo, ahora_utc(), $cierre, $id] : [$nuevo, ahora_utc(), $id]);
                $m = "Estado: {$f['estado']} → $nuevo.";
                break;
            case 'renovar':
                $plan = fila('SELECT duracion_dias FROM ' . PT() . ' WHERE id = ?', [$f[FK()]]);
                $desde = max(hoy(), $f['fecha_fin']); $hasta = dias($desde, (int)$plan['duracion_dias']);
                ejecutar('UPDATE ' . HT() . " SET fecha_fin = ?, estado = 'Activa' WHERE id = ?", [$hasta, $id]);
                $m = 'Membresía renovada hasta el ' . fecha($hasta) . '.';
                break;
            case 'suspender': ejecutar('UPDATE ' . HT() . " SET estado = 'Suspendida' WHERE id = ?", [$id]); $m = 'Membresía suspendida.'; break;
            case 'reactivar': ejecutar('UPDATE ' . HT() . " SET estado = 'Activa' WHERE id = ?", [$id]); $m = 'Membresía reactivada.'; break;
        }
        auditar($acc, HT(), "#$id " . ($f['estado'] ?? ''));
        return $m;
    });
}

/* ------------------------------------------------ estado mostrado y columnas */
function p_estado(array $f): array {   // [texto, tono]
    switch (PATRON()) {
        case 'inventario': $s = array_column(V('tipos'), 1, 0)[$f['tipo']] ?? 1; return [$f['tipo'], $s > 0 ? 'bien' : 'alerta'];
        case 'reservas': return [$f['estado'] === 'Completada' ? V('completar') : $f['estado'], ['Confirmada' => 'info', 'Completada' => 'bien', 'Cancelada' => 'mal'][$f['estado']] ?? ''];
        case 'prestamos':
            if ($f['estado'] === 'Activo' && $f['fecha_compromiso'] < hoy()) return ['Atrasado', 'mal'];
            return [$f['estado'], $f['estado'] === 'Activo' ? 'alerta' : 'bien'];
        case 'ordenes':
            $est = V('estados'); $fin = ultimo($est);
            return [$f['estado'], $f['estado'] === $fin ? 'bien' : ($f['estado'] === $est[0] ? 'mal' : 'alerta')];
        case 'membresias':
            if ($f['estado'] === 'Suspendida') return ['Suspendida', 'mal'];
            if ($f['fecha_fin'] < hoy()) return ['Vencida', 'mal'];
            return [$f['fecha_fin'] <= dias(hoy(), 7) ? 'Por vencer' : 'Vigente', $f['fecha_fin'] <= dias(hoy(), 7) ? 'alerta' : 'bien'];
    }
    return ['', ''];
}
function p_columnas_hijo(): array {
    return match (PATRON()) {
        'inventario' => array_merge([['Cantidad', fn($f) => num($f['cantidad'])]], V('precio') ? [['Monto', fn($f) => dinero($f['monto'])]] : []),
        'reservas' => V('modo') === 'rango'
            ? [['Entrada', fn($f) => fecha($f['fecha'])], ['Salida', fn($f) => fecha($f['fecha_fin'])]]
            : [['Fecha', fn($f) => fecha($f['fecha'])], ['Bloque', fn($f) => h($f['bloque'])]],
        'prestamos' => [['Préstamo', fn($f) => fecha($f['fecha_prestamo'])], ['Compromiso', fn($f) => fecha($f['fecha_compromiso'])], ['Devuelto', fn($f) => fecha($f['fecha_devolucion'])]],
        'ordenes' => array_merge([[V('nivel'), fn($f) => insignia($f['nivel'], $f['nivel'] === ultimo($GLOBALS['TEMA']['vocab']['niveles']) ? 'mal' : '')]],
            V('monto') ? [['Monto', fn($f) => $f['monto'] === null ? '—' : dinero($f['monto'])]] : [],
            [['Cierre', fn($f) => local($f['cerrado_en'])]]),
        'membresias' => [['Inicio', fn($f) => fecha($f['fecha_inicio'])], ['Término', fn($f) => fecha($f['fecha_fin'])]],
        default => [],
    };
}
function p_estados_filtro(): array {
    return match (PATRON()) {
        'reservas' => ['Confirmada', 'Completada', 'Cancelada'],
        'prestamos' => ['Activo', 'Devuelto'],
        'ordenes' => V('estados'),
        'membresias' => ['Activa', 'Suspendida'],
        'inventario' => array_column(V('tipos'), 0),
        default => [],
    };
}
function p_col_estado(): string { return PATRON() === 'inventario' ? 'tipo' : 'estado'; }
function p_vivo(array $f): string {   // texto corto para el panel en vivo
    [$e] = p_estado($f);
    $q = match (PATRON()) {
        'inventario' => num($f['cantidad']) . ' ' . V('unidad'),
        'reservas' => fecha($f['fecha']) . ' ' . ($f['bloque'] ?? '→ ' . fecha($f['fecha_fin'] ?? '')),
        'prestamos' => 'hasta ' . fecha($f['fecha_compromiso']),
        'ordenes' => $f['nivel'],
        'membresias' => 'hasta ' . fecha($f['fecha_fin']),
        default => '',
    };
    return "$e · " . $f['padre_txt'] . ' · ' . $f[CLI()] . " · $q";
}

/* ------------------------------------------------ indicadores (panel) */
function p_kpis(): array {   // [etiqueta, valor, tono]
    $P = PT(); $H = HT(); $hoy = hoy(); $d0 = inicio_dia_utc(); $k = [];
    switch (PATRON()) {
        case 'inventario':
            $k[] = ['Ítems activos', num(valor("SELECT COUNT(*) FROM $P WHERE activo = 1")), ''];
            $crit = (int)valor("SELECT COUNT(*) FROM $P WHERE activo = 1 AND stock <= stock_minimo");
            $k[] = ['Stock crítico', num($crit), $crit ? 'mal' : 'bien'];
            $k[] = ['Movimientos hoy', num(valor("SELECT COUNT(*) FROM $H WHERE creado_en >= ?", [$d0])), ''];
            if (V('precio')) {
                $k[] = ['Valor del inventario', dinero(valor("SELECT COALESCE(SUM(stock * precio), 0) FROM $P WHERE activo = 1")), ''];
                if (V('venta')) $k[] = [V('venta') . ' hoy', dinero(valor("SELECT COALESCE(SUM(monto), 0) FROM $H WHERE tipo = ? AND creado_en >= ?", [V('venta'), $d0])), 'bien'];
            } else {
                $k[] = ['Unidades en stock', num(valor("SELECT COALESCE(SUM(stock), 0) FROM $P WHERE activo = 1")), ''];
            }
            break;
        case 'reservas':
            $hoyN = V('modo') === 'rango'
                ? valor("SELECT COUNT(*) FROM $H WHERE estado <> 'Cancelada' AND fecha <= ? AND fecha_fin > ?", [$hoy, $hoy])
                : valor("SELECT COUNT(*) FROM $H WHERE estado <> 'Cancelada' AND fecha = ?", [$hoy]);
            $k[] = [V('modo') === 'rango' ? 'Ocupadas hoy' : 'Reservas hoy', num($hoyN), 'info'];
            $k[] = ['Próximos 7 días', num(valor("SELECT COUNT(*) FROM $H WHERE estado = 'Confirmada' AND fecha > ? AND fecha <= ?", [$hoy, dias($hoy, 7)])), ''];
            $k[] = [$GLOBALS['TEMA']['padre']['titulo'] . ' activos', num(valor("SELECT COUNT(*) FROM $P WHERE activo = 1")), ''];
            $tot = (int)valor("SELECT COUNT(*) FROM $H WHERE creado_en >= ?", [inicio_dia_utc(-30)]);
            $can = (int)valor("SELECT COUNT(*) FROM $H WHERE estado = 'Cancelada' AND creado_en >= ?", [inicio_dia_utc(-30)]);
            $k[] = ['Cancelación 30 días', $tot ? round(100 * $can / $tot) . ' %' : '0 %', $tot && $can / $tot > .2 ? 'alerta' : 'bien'];
            break;
        case 'prestamos':
            $k[] = ['Préstamos activos', num(valor("SELECT COUNT(*) FROM $H WHERE estado = 'Activo'")), 'alerta'];
            $atr = (int)valor("SELECT COUNT(*) FROM $H WHERE estado = 'Activo' AND fecha_compromiso < ?", [$hoy]);
            $k[] = ['Atrasados', num($atr), $atr ? 'mal' : 'bien'];
            $k[] = ['Disponibles', num(valor("SELECT COUNT(*) FROM $P WHERE activo = 1 AND estado_item = 'Disponible'")), 'bien'];
            $k[] = ['En mantención', num(valor("SELECT COUNT(*) FROM $P WHERE activo = 1 AND estado_item = 'Mantención'")), 'info'];
            break;
        case 'ordenes':
            $est = V('estados'); $fin = ultimo($est); $niv = V('niveles');
            $k[] = ['Abiertos', num(valor("SELECT COUNT(*) FROM $H WHERE estado <> ?", [$fin])), 'alerta'];
            $cr = (int)valor("SELECT COUNT(*) FROM $H WHERE estado <> ? AND nivel = ?", [$fin, ultimo($niv)]);
            $k[] = [ultimo($niv) . ' abiertos', num($cr), $cr ? 'mal' : 'bien'];
            $k[] = ['Cerrados 7 días', num(valor("SELECT COUNT(*) FROM $H WHERE estado = ? AND cerrado_en >= ?", [$fin, inicio_dia_utc(-7)])), 'bien'];
            $k[] = [V('rto') ? 'MTTR 30 días' : 'Tiempo medio de cierre', dur_txt(p_mttr()), ''];
            if (V('monto')) $k[] = ['Facturado 30 días', dinero(valor("SELECT COALESCE(SUM(monto), 0) FROM $H WHERE estado = ? AND cerrado_en >= ?", [$fin, inicio_dia_utc(-30)])), 'bien'];
            if (V('rto')) { $fx = p_fuera_rto(); $k[] = ['Fuera de RTO', num($fx), $fx ? 'mal' : 'bien']; }
            break;
        case 'membresias':
            $k[] = ['Vigentes', num(valor("SELECT COUNT(*) FROM $H WHERE estado = 'Activa' AND fecha_fin >= ?", [$hoy])), 'bien'];
            $pv = (int)valor("SELECT COUNT(*) FROM $H WHERE estado = 'Activa' AND fecha_fin >= ? AND fecha_fin <= ?", [$hoy, dias($hoy, 7)]);
            $k[] = ['Por vencer (7 días)', num($pv), $pv ? 'alerta' : 'bien'];
            $k[] = ['Vencidas', num(valor("SELECT COUNT(*) FROM $H WHERE estado = 'Activa' AND fecha_fin < ?", [$hoy])), 'mal'];
            $ing = valor("SELECT COALESCE(SUM(p.valor * 30.0 / p.duracion_dias), 0) FROM $H h JOIN $P p ON p.id = h." . FK() . " WHERE h.estado = 'Activa' AND h.fecha_fin >= ? AND p.duracion_dias > 0", [$hoy]);
            $k[] = ['Ingreso mensual estimado', dinero($ing), ''];
            break;
    }
    return $k;
}
function p_mttr(): ?float {
    $fin = ultimo($GLOBALS['TEMA']['vocab']['estados']);
    $r = filas('SELECT creado_en, cerrado_en FROM ' . HT() . ' WHERE estado = ? AND cerrado_en >= ?', [$fin, inicio_dia_utc(-30)]);
    if (!$r) return null;
    $s = array_sum(array_map(fn($x) => strtotime($x['cerrado_en'] . ' UTC') - strtotime($x['creado_en'] . ' UTC'), $r));
    return $s / count($r) / 3600;
}
function dur_txt(?float $h): string {
    if ($h === null) return '—';
    return $h < 1 ? max(1, (int)round($h * 60)) . ' min' : number_format($h, 1, ',', '.') . ' h';
}
function p_fuera_rto(): int {   // incidentes cuya duración supera el RTO del activo
    $col = V('rto'); $n = 0;
    foreach (filas('SELECT h.creado_en, h.cerrado_en, p.' . $col . ' AS rto FROM ' . HT() . ' h JOIN ' . PT() . ' p ON p.id = h.' . FK() . ' WHERE h.creado_en >= ?', [inicio_dia_utc(-30)]) as $x) {
        $dur = (strtotime(($x['cerrado_en'] ?: gmdate('Y-m-d H:i:s')) . ' UTC') - strtotime($x['creado_en'] . ' UTC')) / 3600;
        if ($dur > (float)$x['rto']) $n++;
    }
    return $n;
}

/* ------------------------------------------------ disponibilidad (reservas) */
function p_disponibilidad(string $f, ?string $ff): string {
    $rec = filas('SELECT id, ' . ETQ() . ' AS etiqueta FROM ' . PT() . ' WHERE activo = 1 ORDER BY ' . ETQ());
    if (!$rec) return '<p class="vacio">Registra primero un recurso.</p>';
    if (V('modo') === 'rango') {
        $ocu = filas('SELECT ' . FK() . ' AS r, ' . CLI() . ' AS c, fecha, fecha_fin FROM ' . HT() . " WHERE estado = 'Confirmada' AND fecha < ? AND fecha_fin > ?", [$ff, $f]);
        $m = []; foreach ($ocu as $o) $m[$o['r']] = $o;
        $h = '<div class="tabla"><table><thead><tr><th>' . h($GLOBALS['TEMA']['padre']['singular']) . '</th><th>Estado del ' . fecha($f) . ' al ' . fecha($ff) . '</th></tr></thead><tbody>';
        foreach ($rec as $r) $h .= '<tr><td>' . h($r['etiqueta']) . '</td><td>' . (isset($m[$r['id']]) ? insignia('Ocupada: ' . $m[$r['id']]['c'] . ' (' . fecha($m[$r['id']]['fecha']) . '–' . fecha($m[$r['id']]['fecha_fin']) . ')', 'mal') : insignia('Disponible', 'bien')) . '</td></tr>';
        return $h . '</tbody></table></div>';
    }
    $ocu = filas('SELECT ' . FK() . ' AS r, bloque, ' . CLI() . ' AS c FROM ' . HT() . " WHERE estado <> 'Cancelada' AND fecha = ?", [$f]);
    $m = []; foreach ($ocu as $o) $m[$o['r']][$o['bloque']] = $o['c'];
    $h = '<div class="tabla"><table class="grilla"><thead><tr><th></th>';
    foreach (V('bloques') as $b) $h .= '<th>' . h($b) . '</th>';
    $h .= '</tr></thead><tbody>';
    foreach ($rec as $r) {
        $h .= '<tr><th>' . h($r['etiqueta']) . '</th>';
        foreach (V('bloques') as $b) $h .= isset($m[$r['id']][$b]) ? '<td class="ocupado">' . h($m[$r['id']][$b]) . '</td>' : '<td class="libre">libre</td>';
        $h .= '</tr>';
    }
    return $h . '</tbody></table></div>';
}

/* ------------------------------------------------ reportes */
function tabla_html(array $cab, array $rows): string {
    if (!$rows) return '<p class="vacio">Sin datos todavía.</p>';
    $h = '<div class="tabla"><table><thead><tr>';
    foreach ($cab as $c) $h .= '<th>' . h($c) . '</th>';
    $h .= '</tr></thead><tbody>';
    foreach ($rows as $r) { $h .= '<tr>'; foreach ($r as $c) $h .= '<td>' . $c . '</td>'; $h .= '</tr>'; }
    return $h . '</tbody></table></div>';
}
function ranking(array $rows, string $et, string $val, string $suf = ''): string {
    if (!$rows) return '<p class="vacio">Sin datos todavía.</p>';
    $max = max(array_map(fn($r) => (float)$r[$val], $rows));
    $h = '<ul class="ranking">';
    foreach ($rows as $r) $h .= '<li><span>' . h($r[$et]) . '</span>' . barra((float)$r[$val], $max) . '<b>' . num($r[$val]) . h($suf) . '</b></li>';
    return $h . '</ul>';
}
function p_reportes(): array {   // [titulo => html]
    global $TEMA; $P = PT(); $H = HT(); $FK = FK(); $E = ETQ(); $hoy = hoy(); $r = [];
    switch (PATRON()) {
        case 'inventario':
            $neg = array_keys(array_filter(array_column(V('tipos'), 1, 0), fn($s) => $s < 0));
            $in = implode(',', array_fill(0, count($neg), '?'));
            $r['Stock crítico (reponer)'] = tabla_html([$TEMA['padre']['singular'], 'Stock', 'Mínimo', 'Faltante'], array_map(fn($x) => [h($x['e']), num($x['stock']), num($x['stock_minimo']), insignia(num(max(0, $x['stock_minimo'] - $x['stock'] + 1)), 'mal')],
                filas("SELECT $E AS e, stock, stock_minimo FROM $P WHERE activo = 1 AND stock <= stock_minimo ORDER BY stock")));
            $r['Mayor salida (30 días)'] = ranking(filas("SELECT p.$E AS e, SUM(h.cantidad) AS n FROM $H h JOIN $P p ON p.id = h.$FK WHERE h.tipo IN ($in) AND h.creado_en >= ? GROUP BY p.$E ORDER BY n DESC LIMIT 5", array_merge($neg, [inicio_dia_utc(-30)])), 'e', 'n', ' ' . V('unidad'));
            $dias = filas("SELECT CAST(creado_en AS DATE) AS d, SUM(CASE WHEN tipo IN ($in) THEN cantidad ELSE 0 END) AS salidas, SUM(CASE WHEN tipo IN ($in) THEN 0 ELSE cantidad END) AS entradas FROM $H WHERE creado_en >= ? GROUP BY CAST(creado_en AS DATE) ORDER BY d", array_merge($neg, $neg, [inicio_dia_utc(-6)]));
            $r['Movimientos últimos 7 días'] = tabla_html(['Día', 'Entradas', 'Salidas'], array_map(fn($x) => [fecha((string)$x['d']), num($x['entradas']), num($x['salidas'])], $dias));
            if (V('precio')) $r['Valorización por ítem'] = ranking(filas("SELECT $E AS e, stock * precio AS v FROM $P WHERE activo = 1 AND stock > 0 ORDER BY v DESC LIMIT 8"), 'e', 'v');
            break;
        case 'reservas':
            $r['Ocupación por ' . $TEMA['padre']['singular'] . ' (±30 días)'] = ranking(filas("SELECT p.$E AS e, COUNT(*) AS n FROM $H h JOIN $P p ON p.id = h.$FK WHERE h.estado <> 'Cancelada' AND h.fecha >= ? AND h.fecha <= ? GROUP BY p.$E ORDER BY n DESC", [dias($hoy, -30), dias($hoy, 30)]), 'e', 'n', ' reservas');
            $ag = V('modo') === 'rango'
                ? filas("SELECT h.*, p.$E AS padre_txt FROM $H h JOIN $P p ON p.id = h.$FK WHERE h.estado = 'Confirmada' AND h.fecha <= ? AND h.fecha_fin > ? ORDER BY p.$E", [$hoy, $hoy])
                : filas("SELECT h.*, p.$E AS padre_txt FROM $H h JOIN $P p ON p.id = h.$FK WHERE h.estado = 'Confirmada' AND h.fecha = ? ORDER BY h.bloque", [$hoy]);
            $r['Agenda de hoy'] = tabla_html([$TEMA['padre']['singular'], 'Cliente', V('modo') === 'rango' ? 'Salida' : 'Bloque'], array_map(fn($x) => [h($x['padre_txt']), h($x[CLI()]), h(V('modo') === 'rango' ? fecha($x['fecha_fin']) : $x['bloque'])], $ag));
            $r['Reservas por estado (30 días)'] = ranking(filas("SELECT estado AS e, COUNT(*) AS n FROM $H WHERE creado_en >= ? GROUP BY estado", [inicio_dia_utc(-30)]), 'e', 'n');
            break;
        case 'prestamos':
            $r['Préstamos atrasados'] = tabla_html([$TEMA['padre']['singular'], 'Solicitante', 'Compromiso', 'Días de atraso'], array_map(fn($x) => [h($x['padre_txt']), h($x[CLI()]), fecha($x['fecha_compromiso']), insignia((string)(new DateTime($x['fecha_compromiso']))->diff(new DateTime($hoy))->days, 'mal')],
                filas("SELECT h.*, p.$E AS padre_txt FROM $H h JOIN $P p ON p.id = h.$FK WHERE h.estado = 'Activo' AND h.fecha_compromiso < ? ORDER BY h.fecha_compromiso", [$hoy])));
            $r['Más prestados'] = ranking(filas("SELECT p.$E AS e, COUNT(*) AS n FROM $H h JOIN $P p ON p.id = h.$FK GROUP BY p.$E ORDER BY n DESC LIMIT 5"), 'e', 'n', ' préstamos');
            $r['Préstamos por solicitante'] = ranking(filas('SELECT ' . CLI() . " AS e, COUNT(*) AS n FROM $H GROUP BY " . CLI() . ' ORDER BY n DESC LIMIT 5'), 'e', 'n');
            $dev = filas("SELECT fecha_compromiso, fecha_devolucion FROM $H WHERE estado = 'Devuelto'");
            $ok = count(array_filter($dev, fn($x) => $x['fecha_devolucion'] <= $x['fecha_compromiso']));
            $r['Devoluciones a tiempo'] = $dev ? '<p class="cifra">' . round(100 * $ok / count($dev)) . ' %</p><p class="nota">' . $ok . ' de ' . count($dev) . ' devoluciones</p>' : '<p class="vacio">Sin devoluciones todavía.</p>';
            break;
        case 'ordenes':
            $r['Por estado'] = ranking(filas("SELECT estado AS e, COUNT(*) AS n FROM $H GROUP BY estado ORDER BY n DESC"), 'e', 'n');
            $r['Abiertos por ' . mb_strtolower(V('nivel'))] = ranking(filas("SELECT nivel AS e, COUNT(*) AS n FROM $H WHERE estado <> ? GROUP BY nivel ORDER BY n DESC", [ultimo($GLOBALS['TEMA']['vocab']['estados'])]), 'e', 'n');
            $r['Con más casos (30 días)'] = ranking(filas("SELECT p.$E AS e, COUNT(*) AS n FROM $H h JOIN $P p ON p.id = h.$FK WHERE h.creado_en >= ? GROUP BY p.$E ORDER BY n DESC LIMIT 5", [inicio_dia_utc(-30)]), 'e', 'n');
            if (V('rto')) {
                $rows = [];
                foreach (filas("SELECT id, $E AS e, " . V('rto') . " AS rto FROM $P WHERE activo = 1 ORDER BY $E") as $a) {
                    $inc = filas("SELECT creado_en, cerrado_en FROM $H WHERE $FK = ? AND creado_en >= ?", [$a['id'], inicio_dia_utc(-30)]);
                    $caida = 0; $peor = 0;
                    foreach ($inc as $x) { $d = (strtotime(($x['cerrado_en'] ?: gmdate('Y-m-d H:i:s')) . ' UTC') - strtotime($x['creado_en'] . ' UTC')) / 3600; $caida += $d; $peor = max($peor, $d); }
                    $disp = max(0, 100 - 100 * $caida / 720);
                    $rows[] = [h($a['e']), num(count($inc)), round($peor, 1) . ' h / ' . num($a['rto']) . ' h', insignia(number_format($disp, 2, ',', '.') . ' %', $disp >= 99.5 ? 'bien' : ($disp >= 98 ? 'alerta' : 'mal')),
                               $peor > (float)$a['rto'] ? insignia('Excede RTO', 'mal') : insignia('Cumple', 'bien')];
                }
                $r['Continuidad por activo (30 días)'] = tabla_html(['Activo', 'Incidentes', 'Peor recuperación / RTO', 'Disponibilidad', 'RTO'], $rows);
            }
            $mt = p_mttr();
            $r['Tiempo medio de cierre (30 días)'] = $mt === null ? '<p class="vacio">Sin casos cerrados todavía.</p>' : '<p class="cifra">' . dur_txt($mt) . '</p>';
            break;
        case 'membresias':
            $r['Por vencer (7 días)'] = tabla_html(['Socio', 'Plan', 'Término'], array_map(fn($x) => [h($x[CLI()]), h($x['padre_txt']), insignia(fecha($x['fecha_fin']), 'alerta')],
                filas("SELECT h.*, p.$E AS padre_txt FROM $H h JOIN $P p ON p.id = h.$FK WHERE h.estado = 'Activa' AND h.fecha_fin >= ? AND h.fecha_fin <= ? ORDER BY h.fecha_fin", [$hoy, dias($hoy, 7)])));
            $r['Vencidas (contactar)'] = tabla_html(['Socio', 'Plan', 'Venció'], array_map(fn($x) => [h($x[CLI()]), h($x['padre_txt']), insignia(fecha($x['fecha_fin']), 'mal')],
                filas("SELECT h.*, p.$E AS padre_txt FROM $H h JOIN $P p ON p.id = h.$FK WHERE h.estado = 'Activa' AND h.fecha_fin < ? ORDER BY h.fecha_fin DESC LIMIT 20", [$hoy])));
            $r['Vigentes por plan'] = ranking(filas("SELECT p.$E AS e, COUNT(*) AS n FROM $H h JOIN $P p ON p.id = h.$FK WHERE h.estado = 'Activa' AND h.fecha_fin >= ? GROUP BY p.$E ORDER BY n DESC", [$hoy]), 'e', 'n');
            break;
    }
    return $r;
}
