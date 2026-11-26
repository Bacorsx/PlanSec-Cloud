<?php
/* Vista "Cómo funciona": equipo de cómputo animado. Cada parte se puede elegir (clic o teclado) y explica su función.
 * La barra de carga simula el comportamiento térmico: más carga → más RPM, más temperatura y más consumo.
 * Sin estilos ni scripts en línea (CSP): la animación es CSS y la interacción está en app.js. */
declare(strict_types=1);

function ventilador(float $x, float $y, float $r, string $id = ''): string {
    $aspas = '';
    for ($i = 0; $i < 5; $i++) {
        $a = $i * 72;
        $aspas .= '<path transform="rotate(' . $a . ' ' . $x . ' ' . $y . ')" d="M' . $x . ' ' . $y . ' q' . ($r * .55) . ' ' . (-$r * .25) . ' ' . ($r * .78) . ' ' . (-$r * .72) . ' q' . (-$r * .35) . ' ' . ($r * .05) . ' ' . (-$r * .78) . ' ' . ($r * .72) . 'z"/>';
    }
    return '<circle class="forma" cx="' . $x . '" cy="' . $y . '" r="' . $r . '"/><g class="aspa">' . $aspas . '</g><circle cx="' . $x . '" cy="' . $y . '" r="' . ($r * .16) . '" fill="currentColor"/>';
}
$PARTES = [
    'cpu' => ['Procesador (CPU)', 'Ejecuta las instrucciones de los programas: busca, decodifica y ejecuta millones de operaciones por segundo en varios núcleos.',
        ['Lee datos e instrucciones desde la RAM a través del controlador de memoria.', 'Se calienta en proporción a la carga: el disipador y su ventilador evacúan ese calor.', 'Si supera su temperatura máxima reduce su frecuencia (thermal throttling) para protegerse.'], 'Clave: núcleos, frecuencia (GHz), caché y TDP (W).'],
    'cooler' => ['Disipador y ventilador de CPU', 'Transfiere el calor del procesador a las aletas de aluminio/cobre mediante pasta térmica y heatpipes; el ventilador fuerza aire a través de las aletas.',
        ['Las RPM suben con la temperatura según la curva configurada en la BIOS.', 'Sin flujo de aire suficiente el calor se acumula dentro del gabinete.'], 'Clave: capacidad de disipación (W), ruido (dBA), tamaño.'],
    'ram' => ['Memoria RAM', 'Guarda temporalmente los datos y programas en uso para que la CPU los lea rápido. Es volátil: se borra al apagar.',
        ['Funciona en canal dual (dos módulos) para duplicar el ancho de banda.', 'Más RAM evita usar el disco como memoria de intercambio, que es mucho más lento.'], 'Clave: capacidad (GB), velocidad (MT/s), latencia (CL).'],
    'gpu' => ['Tarjeta gráfica (GPU)', 'Procesa en paralelo miles de operaciones para dibujar imágenes, video 3D o cálculos de IA, y envía la imagen al monitor.',
        ['Recibe datos de la CPU por el bus PCI Express.', 'Tiene su propia memoria (VRAM) y sus propios ventiladores, que pueden detenerse en reposo.', 'Es el componente que más energía consume bajo carga.'], 'Clave: VRAM, núcleos, consumo (W), conectores de energía.'],
    'placa' => ['Placa madre', 'Interconecta todos los componentes: zócalo de CPU, ranuras de RAM, PCIe, M.2, SATA, USB y reparte la energía con sus reguladores (VRM).',
        ['El chipset administra los periféricos y el almacenamiento.', 'La BIOS/UEFI controla el arranque y las curvas de los ventiladores.'], 'Clave: zócalo compatible, chipset, formato (ATX/mATX).'],
    'psu' => ['Fuente de poder (PSU)', 'Convierte la corriente alterna del enchufe (220 V) en continua de 12 V, 5 V y 3,3 V para cada componente.',
        ['Su ventilador extrae su propio calor hacia afuera.', 'Una fuente sobredimensionada en ~30 % trabaja más fría, eficiente y silenciosa.'], 'Clave: potencia (W), certificación 80 PLUS, protecciones OVP/OCP/SCP.'],
    'ssd' => ['Almacenamiento (SSD NVMe)', 'Guarda datos de forma permanente en memoria flash. Un NVMe usa líneas PCIe y es varias veces más rápido que un disco SATA.',
        ['El sistema operativo y los programas se cargan desde aquí a la RAM.', 'Puede reducir su velocidad si se calienta; algunos incluyen disipador.'], 'Clave: capacidad, lectura/escritura (MB/s), durabilidad (TBW).'],
    'entrada' => ['Ventiladores frontales (entrada)', 'Toman aire frío del exterior y lo empujan hacia el interior del gabinete, idealmente a través de filtros de polvo.',
        ['Generan presión positiva si ingresan más aire del que sale: entra menos polvo por las rendijas.'], 'Clave: tamaño (120/140 mm), caudal (CFM), presión estática.'],
    'salida' => ['Ventilador trasero (salida)', 'Expulsa el aire caliente acumulado detrás del disipador de la CPU, completando el flujo frontal → trasero.',
        ['El aire caliente sube: la salida trasera/superior aprovecha la convección natural.'], 'Clave: alineado con el disipador para no recircular aire caliente.'],
];
?>
<div class="equipo">
<?php tarjeta_ini('Cómo funciona un equipo · toca cada parte', '<span class="nota">animación en vivo</span>'); ?>
<svg viewBox="0 0 560 470" role="img" aria-label="Diagrama animado del interior de un computador">
  <rect class="gabinete" x="10" y="10" width="540" height="450" rx="16"/>
  <rect class="calor" x="150" y="40" width="320" height="250" rx="40"/>
  <rect class="placa" x="150" y="40" width="300" height="300" rx="8"/>
  <!-- flujo de aire: frío entra por el frente (izquierda) y el caliente sale por atrás (derecha) -->
  <path class="aire" d="M40 110 C120 110 160 150 230 150"/><path class="aire" d="M40 250 C120 250 170 260 240 250"/>
  <path class="aire caliente" d="M330 120 C400 110 440 100 520 95"/><path class="aire caliente" d="M370 270 C430 250 470 200 520 170"/>
  <!-- datos y energía -->
  <path class="flujo-dato" d="M310 130 L360 130"/><path class="flujo-dato" d="M280 175 L280 238"/><path class="flujo-dato" d="M215 330 L250 175"/>
  <path class="energia" d="M200 400 L200 345"/><path class="energia" d="M320 400 L320 300"/>
  <g data-parte="placa" tabindex="0" role="button" aria-label="Placa madre"><rect class="forma" x="160" y="300" width="60" height="30" rx="4"/><text x="166" y="320">Chipset</text></g>
  <g data-parte="cpu" tabindex="0" role="button" aria-label="Procesador"><rect class="forma" x="230" y="88" width="100" height="92" rx="6"/><text x="238" y="104">CPU</text><rect class="forma" x="236" y="150" width="34" height="22" rx="3"/><text x="240" y="166">núcleos</text></g>
  <g data-parte="cooler" tabindex="0" role="button" aria-label="Disipador de CPU"><?= ventilador(298, 136, 24) ?></g>
  <g data-parte="ram" tabindex="0" role="button" aria-label="Memoria RAM"><rect class="forma" x="355" y="70" width="14" height="120" rx="3"/><rect class="forma" x="378" y="70" width="14" height="120" rx="3"/><text x="352" y="62">RAM</text><circle class="led" cx="362" cy="82" r="3"/><circle class="led" cx="385" cy="82" r="3"/></g>
  <g data-parte="gpu" tabindex="0" role="button" aria-label="Tarjeta gráfica"><rect class="forma" x="170" y="235" width="270" height="55" rx="6"/><?= ventilador(240, 262, 20) ?><?= ventilador(320, 262, 20) ?><text x="380" y="268">GPU</text></g>
  <g data-parte="ssd" tabindex="0" role="button" aria-label="SSD NVMe"><rect class="forma" x="165" y="190" width="100" height="22" rx="3"/><text x="180" y="206">SSD NVMe</text></g>
  <g data-parte="psu" tabindex="0" role="button" aria-label="Fuente de poder"><rect class="forma" x="150" y="380" width="230" height="65" rx="6"/><?= ventilador(330, 412, 22) ?><text x="165" y="417">Fuente 650 W</text></g>
  <g data-parte="entrada" tabindex="0" role="button" aria-label="Ventiladores frontales"><?= ventilador(55, 110, 32) ?><?= ventilador(55, 250, 32) ?><text x="22" y="305">Entrada</text></g>
  <g data-parte="salida" tabindex="0" role="button" aria-label="Ventilador trasero"><?= ventilador(505, 120, 30) ?><text x="476" y="170">Salida</text></g>
</svg>
<?php tarjeta_fin('Azul: aire frío que entra · rojo: aire caliente que sale · línea discontinua del color de acento: datos · amarilla: energía.'); ?>
<div>
<?php tarjeta_ini('Carga de trabajo simulada'); ?>
  <label><span>Uso del equipo: <b class="num" id="carga-txt">20 %</b></span><input type="range" id="carga-pc" min="0" max="100" value="20"></label>
  <div class="medidores"><div><span class="etiqueta">Ventiladores</span><b id="carga-rpm">880 RPM</b></div><div><span class="etiqueta">CPU</span><b id="carga-temp">44 °C</b></div><div><span class="etiqueta">Consumo</span><b id="carga-w">128 W</b></div></div>
  <p class="nota">Al subir la carga, la CPU y la GPU generan más calor; la curva de la BIOS acelera los ventiladores para mantener la temperatura bajo el límite.</p>
<?php tarjeta_fin(); ?>
<?php tarjeta_ini('Parte seleccionada'); ?>
  <p class="nota ficha-parte" id="ficha-ninguna">Toca una parte del diagrama para ver qué hace.</p>
  <?php foreach ($PARTES as $id => [$t, $d, $pts, $clave]): ?>
  <div class="ficha-parte" id="ficha-<?= h($id) ?>" hidden><h3><?= h($t) ?></h3><p><?= h($d) ?></p><ul><?php foreach ($pts as $p): ?><li><?= h($p) ?></li><?php endforeach; ?></ul><p><?= insignia($clave, 'info') ?></p></div>
  <?php endforeach; ?>
<?php tarjeta_fin(); ?>
</div>
</div>
