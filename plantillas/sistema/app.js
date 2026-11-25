/* Sistema de gestión, planificación y generación del informe — TI3062
 * Todo el contenido vive en el objeto `datos` (localStorage + JSON exportable).
 * El PDF se arma SOLO desde `datos`: no hay textos del informe fijos en el código. */
'use strict';
const CFG = window.CFG;
let datos = null;
let moduloActual = 'resumen';

/* ---------------- Esquema de módulos ---------------- */
const ROLES = ['Administración', 'Desarrollo', 'Auditoría'];
const EST_TAREA = ['Pendiente', 'En curso', 'Completada', 'Bloqueada'];
const EST_PRUEBA = ['Pendiente', 'Aprobada', 'Fallida'];
const EST_CONTROL = ['Planificado', 'En implementación', 'Implementado', 'No aplicado'];
const CAPAS = ['Identidad', 'Red', 'Aplicación', 'Proveedor'];
const TIPO_HALLAZGO = ['Falla', 'Desviación', 'Comportamiento esperado', 'Riesgo'];
const AREAS = ['Red / VPC', 'Security Groups', 'Instancias', 'Aplicación', 'Base de datos', 'Hardening SO', 'MFA', 'Cifrado LUKS', 'Auditoría', 'Firewall host', 'Respaldo', 'Disponibilidad'];

const MODULOS = [
  { id: 'resumen', titulo: 'Panel de resumen' },
  { id: 'planificacion', titulo: 'Gestión y planificación', bloques: [
    { tipo: 'arr', ruta: 'hitos', titulo: 'Hitos', ayuda: 'Mínimo 3 hitos.', cols: [
      { k: 'id', l: 'ID' }, { k: 'nombre', l: 'Hito' }, { k: 'fecha', l: 'Fecha objetivo', t: 'date' }, { k: 'criterio', l: 'Criterio de cierre', t: 'area' }] },
    { tipo: 'arr', ruta: 'tareas', titulo: 'Tareas', ayuda: 'Mínimo 10 tareas con rol, responsable, fechas, dependencia y estado.', cols: [
      { k: 'id', l: 'ID' }, { k: 'nombre', l: 'Tarea', t: 'area' }, { k: 'hito', l: 'Hito', t: 'ref:hitos' }, { k: 'rol', l: 'Rol', t: ROLES },
      { k: 'responsable', l: 'Responsable' }, { k: 'inicio', l: 'Inicio', t: 'date' }, { k: 'fin', l: 'Término', t: 'date' },
      { k: 'dependencia', l: 'Depende de' }, { k: 'estado', l: 'Estado', t: EST_TAREA }] },
    { tipo: 'gantt' }] },
  { id: 'problema', titulo: 'Problemática y requerimientos', bloques: [
    { tipo: 'obj', ruta: 'problema', titulo: 'Contexto', campos: [
      { k: 'titulo', l: 'Título del caso' }, { k: 'contexto', l: 'Contexto', t: 'area' },
      { k: 'actores', l: 'Actores (uno por línea)', t: 'lista' }, { k: 'procesos', l: 'Procesos afectados (uno por línea)', t: 'lista' },
      { k: 'necesidades', l: 'Necesidades críticas (una por línea)', t: 'lista' }, { k: 'impacto', l: 'Impacto en usuarios y datos', t: 'area' }] },
    { tipo: 'arr', ruta: 'caracteristicas', titulo: 'Características clave (3 a 5)', cols: [
      { k: 'id', l: 'ID' }, { k: 'descripcion', l: 'Característica', t: 'area' }, { k: 'diseno', l: 'Cómo influye en el diseño', t: 'area' }] },
    { tipo: 'arr', ruta: 'requerimientos', titulo: 'Requerimientos (≥4 RF y ≥4 RNF)', cols: [
      { k: 'id', l: 'ID' }, { k: 'tipo', l: 'Tipo', t: ['RF', 'RNF'] }, { k: 'categoria', l: 'Categoría', t: ['Funcional', 'Seguridad', 'Disponibilidad', 'Rendimiento'] },
      { k: 'descripcion', l: 'Descripción', t: 'area' }, { k: 'control', l: 'Control NIST asociado' }] },
    { tipo: 'arr', ruta: 'dependencias', titulo: 'Dependencias / componentes críticos', cols: [
      { k: 'id', l: 'ID' }, { k: 'componente', l: 'Componente' }, { k: 'descripcion', l: 'Descripción', t: 'area' }, { k: 'impacto', l: 'Impacto en la arquitectura', t: 'area' }] },
    { tipo: 'arr', ruta: 'limitaciones', titulo: 'Limitaciones técnicas y normativas', cols: [
      { k: 'id', l: 'ID' }, { k: 'tipo', l: 'Tipo', t: ['Técnica', 'Normativa', 'Entorno'] }, { k: 'descripcion', l: 'Descripción', t: 'area' }, { k: 'impacto', l: 'Impacto / compensación', t: 'area' }] }] },
  { id: 'cloud', titulo: 'Análisis cloud y multicloud', bloques: [
    { tipo: 'arr', ruta: 'proveedores', titulo: 'Comparativa de proveedores', ayuda: 'Costo mensual con fuente: calculadora oficial de cada proveedor.', cols: [
      { k: 'nombre', l: 'Proveedor' }, { k: 'servicio', l: 'Servicio equivalente', t: 'area' }, { k: 'seguridad', l: 'Seguridad', t: 'area' },
      { k: 'disponibilidad', l: 'Disponibilidad', t: 'area' }, { k: 'costo', l: 'Costo mensual (USD)' }, { k: 'fuente', l: 'Fuente del costo' },
      { k: 'beneficios', l: 'Beneficios', t: 'area' }, { k: 'limitaciones', l: 'Limitaciones', t: 'area' }, { k: 'riesgos', l: 'Riesgos', t: 'area' }] },
    { tipo: 'obj', ruta: 'seleccion', titulo: 'Selección justificada', campos: [
      { k: 'proveedor', l: 'Proveedor seleccionado' }, { k: 'justificacion', l: 'Justificación contra RF/RNF', t: 'area' },
      { k: 'gobierno', l: 'Alineación con Gobierno TI', t: 'area' }, { k: 'zona', l: 'Zona de disponibilidad' }, { k: 'zonaJustificacion', l: 'Justificación de la zona', t: 'area' }] }] },
  { id: 'nist', titulo: 'Controles NIST', bloques: [
    { tipo: 'arr', ruta: 'componentes', titulo: 'Componentes con control de acceso', cols: [
      { k: 'componente', l: 'Componente' }, { k: 'acceso', l: 'Quién accede / cómo', t: 'area' }, { k: 'control', l: 'Control aplicado', t: 'area' }, { k: 'rol', l: 'Rol protector', t: 'area' }] },
    { tipo: 'arr', ruta: 'controles', titulo: 'Controles NIST SP 800-53 Rev. 5', ayuda: 'Mínimo 3 controles con riesgo, punto de aplicación, capa y requerimiento.', cols: [
      { k: 'codigo', l: 'Código' }, { k: 'nombre', l: 'Nombre' }, { k: 'riesgo', l: 'Riesgo mitigado', t: 'area' }, { k: 'punto', l: 'Punto de aplicación', t: 'area' },
      { k: 'capa', l: 'Capa', t: CAPAS }, { k: 'req', l: 'Requerimiento' }, { k: 'impacto', l: 'Impacto esperado', t: 'area' }, { k: 'estado', l: 'Estado', t: EST_CONTROL }] }] },
  { id: 'implementacion', titulo: 'Implementación', bloques: [
    { tipo: 'obj', ruta: 'infra', titulo: 'Topología', campos: [
      { k: 'vpc', l: 'VPC' }, { k: 'cidr', l: 'CIDR VPC' }, { k: 'publica', l: 'Subred pública' }, { k: 'privada', l: 'Subred privada' },
      { k: 'web', l: 'Instancia web' }, { k: 'bd', l: 'Instancia BD' }, { k: 'motor', l: 'Motor de BD' }, { k: 'appUrl', l: 'URL de la app del caso' }] },
    { tipo: 'topologia' },
    { tipo: 'arr', ruta: 'sg', titulo: 'Security Groups y firewall de host', cols: [
      { k: 'grupo', l: 'SG' }, { k: 'puerto', l: 'Puerto' }, { k: 'origen', l: 'Origen' }, { k: 'host', l: 'Regla firewall host' }, { k: 'justificacion', l: 'Justificación', t: 'area' }] },
    { tipo: 'arr', ruta: 'bitacora', titulo: 'Bitácora de implementación', ayuda: 'Cada configuración con fecha, responsable, comando y evidencia (sin llaves privadas, secretos MFA, QR ni códigos de emergencia).', cols: [
      { k: 'fecha', l: 'Fecha', t: 'date' }, { k: 'area', l: 'Área', t: AREAS }, { k: 'configuracion', l: 'Configuración', t: 'area' }, { k: 'comando', l: 'Comando / archivo', t: 'area' },
      { k: 'responsable', l: 'Responsable' }, { k: 'ref', l: 'Tarea / control' }, { k: 'evidencia', l: 'Título evidencia' }, { k: 'descripcion', l: 'Descripción / justificación', t: 'area' }, { k: 'imagen', l: 'Captura', t: 'img' }] }] },
  { id: 'validacion', titulo: 'Validación y cierre', bloques: [
    { tipo: 'arr', ruta: 'pruebas', titulo: 'Pruebas (P1–P4 obligatorias)', cols: [
      { k: 'id', l: 'ID' }, { k: 'objetivo', l: 'Objetivo', t: 'area' }, { k: 'comando', l: 'Comando', t: 'area' }, { k: 'esperado', l: 'Esperado', t: 'area' },
      { k: 'obtenido', l: 'Obtenido', t: 'area' }, { k: 'estado', l: 'Resultado', t: EST_PRUEBA }, { k: 'control', l: 'Control NIST' }, { k: 'imagen', l: 'Captura', t: 'img' }] },
    { tipo: 'arr', ruta: 'hallazgos', titulo: 'Hallazgos', cols: [
      { k: 'id', l: 'ID' }, { k: 'tipo', l: 'Tipo', t: TIPO_HALLAZGO }, { k: 'descripcion', l: 'Descripción', t: 'area' }, { k: 'req', l: 'RF/RNF' },
      { k: 'control', l: 'Control NIST' }, { k: 'impacto', l: 'Riesgo / impacto', t: 'area' }, { k: 'accion', l: 'Corrección o mejora', t: 'area' }] },
    { tipo: 'arr', ruta: 'cia', titulo: 'Análisis CIA', cols: [
      { k: 'dimension', l: 'Dimensión', t: ['Confidencialidad', 'Integridad', 'Disponibilidad'] }, { k: 'controles', l: 'Controles que la protegen', t: 'area' },
      { k: 'verificacion', l: 'Verificación (prueba)', t: 'area' }, { k: 'impacto', l: 'Impacto operativo', t: 'area' }] },
    { tipo: 'arr', ruta: 'riesgos', titulo: 'Riesgos residuales (≥3)', cols: [
      { k: 'id', l: 'ID' }, { k: 'riesgo', l: 'Riesgo', t: 'area' }, { k: 'impacto', l: 'Impacto', t: 'area' }, { k: 'tratamiento', l: 'Tratamiento', t: 'area' }] },
    { tipo: 'arr', ruta: 'gobierno', titulo: 'Coherencia con Gobierno TI', cols: [
      { k: 'eje', l: 'Eje', t: ['Identidad', 'Acceso', 'Monitoreo', 'Continuidad', 'Respaldo'] }, { k: 'practica', l: 'Práctica aplicada', t: 'area' }, { k: 'evidencia', l: 'Evidencia', t: 'area' }] },
    { tipo: 'arr', ruta: 'mejoras', titulo: 'Acciones de mejora (≥3)', cols: [
      { k: 'id', l: 'ID' }, { k: 'accion', l: 'Acción', t: 'area' }, { k: 'control', l: 'Control NIST' }, { k: 'impacto', l: 'Impacto esperado', t: 'area' }, { k: 'evidencia', l: 'Evidencia / hallazgo origen', t: 'area' }] },
    { tipo: 'obj', ruta: 'cierre', titulo: 'Conclusiones', campos: [{ k: 'conclusion', l: 'Conclusión', t: 'area' }, { k: 'aprendizajes', l: 'Aprendizajes', t: 'area' }] }] },
  { id: 'documento', titulo: 'Documento y datos', bloques: [
    { tipo: 'obj', ruta: 'meta', titulo: 'Portada', campos: [
      { k: 'estudiante', l: 'Estudiante' }, { k: 'nn', l: 'Número de lista (NN)' }, { k: 'carrera', l: 'Carrera' }, { k: 'sede', l: 'Sede' },
      { k: 'docente', l: 'Docente' }, { k: 'urlSistema', l: 'URL del sistema' }, { k: 'urlRepo', l: 'URL del repositorio' }] },
    { tipo: 'herramientas' }] },
];

/* ---------------- Utilidades ---------------- */
const $ = (s, r = document) => r.querySelector(s);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const get = (ruta) => ruta.split('.').reduce((o, k) => (o == null ? o : o[k]), datos);
function asegurar(ruta, def) { if (datos[ruta] == null) datos[ruta] = def; return datos[ruta]; }
const hoy = () => new Date().toISOString().slice(0, 10);

function guardar() {
  try {
    localStorage.setItem(CFG.storageKey, JSON.stringify(datos));
    $('#estado-guardado').textContent = 'Guardado ' + new Date().toLocaleTimeString();
  } catch (e) {
    $('#estado-guardado').textContent = '⚠ Sin espacio local: exporta el JSON';
  }
}

async function cargar() {
  let local = null;
  try { local = JSON.parse(localStorage.getItem(CFG.storageKey) || 'null'); } catch (e) { local = null; }
  if (local) { datos = local; return; }
  try {
    const r = await fetch(CFG.dataFile, { cache: 'no-store' });
    datos = await r.json();
  } catch (e) {
    datos = { meta: { nn: CFG.nn } };
  }
}

/* ---------------- Indicadores (calculados desde los datos) ---------------- */
function indicadores() {
  const tareas = datos.tareas || [], pruebas = datos.pruebas || [], controles = datos.controles || [];
  const porEstado = {}; EST_TAREA.forEach((e) => (porEstado[e] = 0));
  tareas.forEach((t) => (porEstado[t.estado] = (porEstado[t.estado] || 0) + 1));
  const completadas = porEstado['Completada'] || 0;
  return {
    avance: tareas.length ? Math.round((completadas / tareas.length) * 100) : 0,
    tareas: tareas.length, porEstado,
    controlesImpl: controles.filter((c) => c.estado === 'Implementado').length, controlesTot: controles.length,
    aprobadas: pruebas.filter((p) => p.estado === 'Aprobada').length, fallidas: pruebas.filter((p) => p.estado === 'Fallida').length,
    pendientes: pruebas.filter((p) => !p.estado || p.estado === 'Pendiente').length, pruebasTot: pruebas.length,
    riesgos: (datos.riesgos || []).length, hallazgos: (datos.hallazgos || []).length,
    evidencias: (datos.bitacora || []).filter((b) => b.imagen).length, bitacora: (datos.bitacora || []).length,
    rf: (datos.requerimientos || []).filter((r) => r.tipo === 'RF').length, rnf: (datos.requerimientos || []).filter((r) => r.tipo === 'RNF').length,
  };
}

function chequeoPauta(k) {
  const c = [];
  const ok = (cond, txt) => c.push({ cond, txt });
  ok((datos.hitos || []).length >= 3, '≥3 hitos');
  ok(k.tareas >= 10, '≥10 tareas');
  ok((datos.caracteristicas || []).length >= 3 && (datos.caracteristicas || []).length <= 5, '3–5 características clave');
  ok(k.rf >= 4 && k.rnf >= 4, '≥4 RF y ≥4 RNF');
  ok((datos.proveedores || []).length >= 2, '≥2 proveedores cloud');
  ok(k.controlesTot >= 3, '≥3 controles NIST');
  ok(k.pruebasTot >= 4, '≥4 pruebas (P1–P4)');
  ok(k.riesgos >= 3, '≥3 riesgos residuales');
  ok((datos.mejoras || []).length >= 3, '≥3 acciones de mejora');
  ok(k.evidencias >= 1, 'Evidencias con captura en bitácora');
  return c;
}

/* ---------------- Gráficos SVG ---------------- */
const COLORES = { Pendiente: '#b7950b', 'En curso': 'var(--acento)', Completada: '#2e8b57', Bloqueada: '#c0392b', Aprobada: '#2e8b57', Fallida: '#c0392b' };
function svgBarras(serie) {
  const max = Math.max(1, ...serie.map((s) => s[1]));
  return `<svg viewBox="0 0 300 ${serie.length * 30}" width="100%" role="img">` + serie.map((s, i) =>
    `<text x="0" y="${i * 30 + 18}" font-size="11" fill="currentColor">${esc(s[0])}</text>
     <rect x="95" y="${i * 30 + 6}" width="${(s[1] / max) * 170}" height="16" rx="3" fill="${COLORES[s[0]] || 'var(--primario)'}"/>
     <text x="${100 + (s[1] / max) * 170}" y="${i * 30 + 18}" font-size="11" fill="currentColor">${s[1]}</text>`).join('') + '</svg>';
}
function svgDona(serie) {
  const tot = serie.reduce((a, s) => a + s[1], 0) || 1; let ang = 0; const R = 50, C = 2 * Math.PI * R;
  const arcos = serie.map((s) => { const len = (s[1] / tot) * C; const el = `<circle r="${R}" cx="70" cy="70" fill="none" stroke="${COLORES[s[0]] || 'var(--primario)'}" stroke-width="22" stroke-dasharray="${len} ${C - len}" stroke-dashoffset="${-ang}" transform="rotate(-90 70 70)"/>`; ang += len; return el; }).join('');
  const ley = serie.map((s, i) => `<rect x="150" y="${20 + i * 20}" width="10" height="10" fill="${COLORES[s[0]] || 'var(--primario)'}"/><text x="166" y="${29 + i * 20}" font-size="11" fill="currentColor">${esc(s[0])}: ${s[1]}</text>`).join('');
  return `<svg viewBox="0 0 300 140" width="100%" role="img">${arcos}${ley}</svg>`;
}
function svgAnillos(items) {
  return `<svg viewBox="0 0 ${items.length * 100} 120" width="100%" role="img">` + items.map((it, i) => {
    const R = 36, C = 2 * Math.PI * R, p = Math.max(0, Math.min(1, it[1]));
    return `<g transform="translate(${i * 100 + 50},55)"><circle r="${R}" fill="none" stroke="var(--linea)" stroke-width="9"/>
      <circle r="${R}" fill="none" stroke="var(--acento)" stroke-width="9" stroke-dasharray="${p * C} ${C}" transform="rotate(-90)"/>
      <text text-anchor="middle" y="5" font-size="14" font-weight="700" fill="currentColor">${Math.round(p * 100)}%</text>
      <text text-anchor="middle" y="58" font-size="10" fill="currentColor">${esc(it[0])}</text></g>`;
  }).join('') + '</svg>';
}

/* ---------------- Render ---------------- */
function renderMenu() {
  $('#menu').innerHTML = MODULOS.map((m) => `<button data-mod="${m.id}" class="${m.id === moduloActual ? 'activo' : ''}">${esc(m.titulo)}</button>`).join('');
}

function renderResumen() {
  const k = indicadores();
  const tareasSerie = Object.entries(k.porEstado);
  const pruebasSerie = [['Aprobada', k.aprobadas], ['Fallida', k.fallidas], ['Pendiente', k.pendientes]];
  let graf;
  if (CFG.grafico === 'dona') graf = `<div class="tarjeta"><h2>Tareas por estado</h2>${svgDona(tareasSerie)}</div><div class="tarjeta"><h2>Pruebas</h2>${svgDona(pruebasSerie)}</div>`;
  else if (CFG.grafico === 'anillos') graf = `<div class="tarjeta"><h2>Indicadores</h2>${svgAnillos([['Avance', k.avance / 100], ['Controles', k.controlesTot ? k.controlesImpl / k.controlesTot : 0], ['Pruebas OK', k.pruebasTot ? k.aprobadas / k.pruebasTot : 0]])}</div><div class="tarjeta"><h2>Tareas por estado</h2>${svgBarras(tareasSerie)}</div>`;
  else graf = `<div class="tarjeta"><h2>Tareas por estado</h2>${svgBarras(tareasSerie)}</div><div class="tarjeta"><h2>Pruebas</h2>${svgBarras(pruebasSerie)}</div>`;
  const chk = chequeoPauta(k);
  return `<h1>Panel de resumen</h1><p class="ayuda">Indicadores calculados automáticamente desde los datos registrados.</p>
  <div class="kpis">
    <div class="kpi"><b>${k.avance}%</b><span>Avance (${k.porEstado['Completada'] || 0}/${k.tareas} tareas)</span></div>
    <div class="kpi"><b>${k.controlesImpl}/${k.controlesTot}</b><span>Controles NIST implementados</span></div>
    <div class="kpi"><b>${k.aprobadas}/${k.pruebasTot}</b><span>Pruebas aprobadas · ${k.fallidas} fallidas</span></div>
    <div class="kpi"><b>${k.riesgos}</b><span>Riesgos residuales</span></div>
    <div class="kpi"><b>${k.hallazgos}</b><span>Hallazgos</span></div>
    <div class="kpi"><b>${k.evidencias}/${k.bitacora}</b><span>Registros de bitácora con captura</span></div>
  </div>
  <div class="graficos" style="margin-top:16px">${graf}</div>
  <div class="tarjeta"><h2>Cumplimiento mínimo de la pauta</h2><ul>${chk.map((c) => `<li>${c.cond ? '✅' : '⬜'} ${esc(c.txt)}</li>`).join('')}</ul></div>`;
}

function inputCelda(col, valor, ruta, i) {
  const attr = `data-ruta="${ruta}" data-i="${i}" data-k="${col.k}"`;
  if (Array.isArray(col.t)) return `<select ${attr}><option value=""></option>${col.t.map((o) => `<option ${o === valor ? 'selected' : ''}>${esc(o)}</option>`).join('')}</select>`;
  if (typeof col.t === 'string' && col.t.startsWith('ref:')) {
    const lista = datos[col.t.slice(4)] || [];
    return `<select ${attr}><option value=""></option>${lista.map((o) => `<option value="${esc(o.id)}" ${o.id === valor ? 'selected' : ''}>${esc(o.id + ' ' + (o.nombre || ''))}</option>`).join('')}</select>`;
  }
  if (col.t === 'area') return `<textarea ${attr}>${esc(valor)}</textarea>`;
  if (col.t === 'date') return `<input type="date" ${attr} value="${esc(valor)}">`;
  if (col.t === 'img') return `<input type="file" accept="image/*" ${attr} data-img="1">${valor ? `<img class="thumb" src="${valor}" alt="captura"><button class="btn mini peligro" data-quitar-img="1" ${attr}>Quitar</button>` : ''}`;
  return `<input ${attr} value="${esc(valor)}">`;
}

function renderBloque(b) {
  if (b.tipo === 'arr') {
    const filas = asegurar(b.ruta, []);
    return `<div class="tarjeta"><h2>${esc(b.titulo)} <small>(${filas.length})</small></h2>${b.ayuda ? `<p class="ayuda">${esc(b.ayuda)}</p>` : ''}
      <div class="tabla-wrap"><table><thead><tr>${b.cols.map((c) => `<th>${esc(c.l)}</th>`).join('')}<th></th></tr></thead><tbody>
      ${filas.map((f, i) => `<tr>${b.cols.map((c) => `<td>${inputCelda(c, f[c.k], b.ruta, i)}</td>`).join('')}<td><button class="btn mini peligro" data-borrar="${b.ruta}" data-i="${i}" title="Eliminar fila">✕</button></td></tr>`).join('')}
      </tbody></table></div><div class="fila-botones"><button class="btn" data-agregar="${b.ruta}">+ Agregar fila</button></div></div>`;
  }
  if (b.tipo === 'obj') {
    const o = asegurar(b.ruta, {});
    return `<div class="tarjeta"><h2>${esc(b.titulo)}</h2>${b.campos.map((c) => {
      const v = c.t === 'lista' ? (o[c.k] || []).join('\n') : o[c.k];
      const attr = `data-obj="${b.ruta}" data-k="${c.k}" ${c.t === 'lista' ? 'data-lista="1"' : ''}`;
      return `<div class="campo"><label>${esc(c.l)}</label>${c.t === 'area' || c.t === 'lista' ? `<textarea ${attr}>${esc(v)}</textarea>` : `<input ${attr} value="${esc(v)}">`}</div>`;
    }).join('')}</div>`;
  }
  if (b.tipo === 'gantt') return `<div class="tarjeta"><h2>Cronograma</h2>${htmlGantt()}</div>`;
  if (b.tipo === 'topologia') return `<div class="tarjeta"><h2>Diagrama (generado desde los datos)</h2>${svgTopologia()}</div>`;
  if (b.tipo === 'herramientas') return `<div class="tarjeta"><h2>Documento técnico</h2>
      <p class="ayuda">El PDF se construye en el momento con los datos registrados. Modifica cualquier dato y vuelve a generarlo.</p>
      <div class="fila-botones"><button class="btn primario" data-accion="pdf">Generar PDF</button></div>
      <h2>Datos del proyecto</h2>
      <p class="ayuda">Los datos se guardan en este navegador. Exporta el JSON y súbelo al repositorio como <code>${esc(CFG.dataFile)}</code>.</p>
      <div class="fila-botones">
        <button class="btn" data-accion="exportar">Exportar JSON</button>
        <button class="btn" data-accion="importar">Importar JSON</button>
        <button class="btn" data-accion="repo">Restaurar desde el repositorio</button>
        <button class="btn" data-accion="tema">Cambiar tema claro/oscuro</button>
      </div></div>`;
  return '';
}

function htmlGantt() {
  const t = (datos.tareas || []).filter((x) => x.inicio && x.fin);
  if (!t.length) return '<p class="ayuda">Agrega fechas a las tareas para ver el cronograma.</p>';
  const ini = Math.min(...t.map((x) => +new Date(x.inicio))), fin = Math.max(...t.map((x) => +new Date(x.fin))) + 864e5;
  const span = fin - ini || 1;
  return `<div class="gantt">${t.map((x) => {
    const l = ((+new Date(x.inicio) - ini) / span) * 100, w = Math.max(1.5, ((+new Date(x.fin) + 864e5 - +new Date(x.inicio)) / span) * 100);
    return `<div class="g-fila"><span>${esc(x.id)} · ${esc((x.nombre || '').slice(0, 30))}</span><div class="g-pista"><div class="g-barra ${x.estado === 'Completada' ? 'hecha' : ''}" style="left:${l}%;width:${w}%" title="${esc(x.inicio)} → ${esc(x.fin)}"></div></div></div>`;
  }).join('')}</div>`;
}

function svgTopologia() {
  const f = datos.infra || {};
  return `<svg viewBox="0 0 640 260" width="100%" role="img" aria-label="Topología">
    <rect x="10" y="10" width="90" height="34" rx="6" fill="none" stroke="currentColor"/><text x="55" y="32" text-anchor="middle" font-size="12" fill="currentColor">Internet</text>
    <rect x="170" y="10" width="130" height="34" rx="6" fill="none" stroke="var(--acento)"/><text x="235" y="32" text-anchor="middle" font-size="12" fill="currentColor">Internet Gateway</text>
    <line x1="100" y1="27" x2="170" y2="27" stroke="var(--acento)"/>
    <rect x="10" y="60" width="620" height="190" rx="8" fill="none" stroke="var(--acento)" stroke-dasharray="6 4"/>
    <text x="22" y="80" font-size="12" font-weight="700" fill="currentColor">${esc(f.vpc)} ${esc(f.cidr)}</text>
    <rect x="25" y="92" width="280" height="145" rx="8" fill="none" stroke="var(--ok)"/><text x="35" y="110" font-size="11" fill="currentColor">Subred pública ${esc(f.publica)}</text>
    <rect x="335" y="92" width="280" height="145" rx="8" fill="none" stroke="var(--primario)"/><text x="345" y="110" font-size="11" fill="currentColor">Subred privada ${esc(f.privada)}</text>
    <rect x="80" y="140" width="170" height="60" rx="6" fill="none" stroke="currentColor"/><text x="165" y="165" text-anchor="middle" font-size="12" fill="currentColor">EC2 ${esc(f.web)}</text><text x="165" y="183" text-anchor="middle" font-size="10" fill="currentColor">HTTP/HTTPS · SSH</text>
    <rect x="390" y="140" width="170" height="60" rx="6" fill="none" stroke="currentColor"/><text x="475" y="165" text-anchor="middle" font-size="12" fill="currentColor">EC2 ${esc(f.bd)}</text><text x="475" y="183" text-anchor="middle" font-size="10" fill="currentColor">${esc(f.motor)} · sin IP pública</text>
    <line x1="235" y1="44" x2="165" y2="140" stroke="var(--acento)"/><line x1="250" y1="170" x2="390" y2="170" stroke="currentColor" stroke-dasharray="4 3"/>
    <text x="320" y="162" text-anchor="middle" font-size="10" fill="currentColor">solo interno</text>
    <text x="35" y="228" font-size="10" fill="currentColor">0.0.0.0/0 → IGW</text><text x="345" y="228" font-size="10" fill="currentColor">Sin ruta a Internet</text></svg>`;
}

function render() {
  renderMenu();
  $('#nombre-estudiante').textContent = (datos.meta && datos.meta.estudiante) || '';
  const m = MODULOS.find((x) => x.id === moduloActual);
  $('#contenido').innerHTML = m.id === 'resumen' ? renderResumen() : `<h1>${esc(m.titulo)}</h1>` + m.bloques.map(renderBloque).join('');
}

/* ---------------- Eventos ---------------- */
function comprimirImagen(file) {
  return new Promise((res, rej) => {
    const fr = new FileReader();
    fr.onload = () => {
      const img = new Image();
      img.onload = () => {
        const max = 1280, s = Math.min(1, max / Math.max(img.width, img.height));
        const c = document.createElement('canvas'); c.width = img.width * s; c.height = img.height * s;
        c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
        res(c.toDataURL('image/jpeg', 0.72));
      };
      img.onerror = rej; img.src = fr.result;
    };
    fr.onerror = rej; fr.readAsDataURL(file);
  });
}

document.addEventListener('change', async (e) => {
  const el = e.target;
  if (el.id === 'input-importar') return importarArchivo(el.files[0]);
  if (el.dataset.img && el.files[0]) {
    datos[el.dataset.ruta][+el.dataset.i][el.dataset.k] = await comprimirImagen(el.files[0]);
    guardar(); render(); return;
  }
});
document.addEventListener('input', (e) => {
  const el = e.target;
  if (el.dataset.obj) {
    const o = asegurar(el.dataset.obj, {});
    o[el.dataset.k] = el.dataset.lista ? el.value.split('\n').map((s) => s.trim()).filter(Boolean) : el.value;
    guardar(); return;
  }
  if (el.dataset.ruta && !el.dataset.img) { datos[el.dataset.ruta][+el.dataset.i][el.dataset.k] = el.value; guardar(); }
});
document.addEventListener('click', (e) => {
  const el = e.target.closest('button'); if (!el) return;
  if (el.dataset.mod) { moduloActual = el.dataset.mod; render(); $('#contenido').focus(); return; }
  if (el.dataset.agregar) { asegurar(el.dataset.agregar, []).push({}); guardar(); render(); return; }
  if (el.dataset.borrar) { if (confirm('¿Eliminar esta fila?')) { datos[el.dataset.borrar].splice(+el.dataset.i, 1); guardar(); render(); } return; }
  if (el.dataset.quitarImg) { datos[el.dataset.ruta][+el.dataset.i][el.dataset.k] = ''; guardar(); render(); return; }
  const acc = el.dataset.accion;
  if (acc === 'pdf') generarPDF();
  if (acc === 'exportar') exportar();
  if (acc === 'importar') $('#input-importar').click();
  if (acc === 'repo') restaurarRepo();
  if (acc === 'tema') { const r = document.documentElement; r.dataset.theme = r.dataset.theme === 'dark' ? 'light' : 'dark'; }
});

function exportar() {
  const blob = new Blob([JSON.stringify(datos, null, 2)], { type: 'application/json' });
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `proyecto-${CFG.nn}.json`; a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}
function importarArchivo(file) {
  if (!file) return;
  const fr = new FileReader();
  fr.onload = () => { try { datos = JSON.parse(fr.result); guardar(); render(); alert('Proyecto restaurado.'); } catch (err) { alert('JSON inválido: ' + err.message); } };
  fr.readAsText(file);
}
async function restaurarRepo() {
  if (!confirm('Se reemplazarán los datos locales por ' + CFG.dataFile + '. ¿Continuar?')) return;
  try { const r = await fetch(CFG.dataFile, { cache: 'no-store' }); datos = await r.json(); guardar(); render(); alert('Proyecto restaurado desde el repositorio.'); }
  catch (err) { alert('No se pudo leer ' + CFG.dataFile); }
}

/* ---------------- PDF (solo desde `datos`) ---------------- */
function txt(s) { // jsPDF con fuentes estándar solo admite Latin-1
  return String(s ?? '').replace(/[→⇒]/g, '->').replace(/[←]/g, '<-').replace(/≥/g, '>=').replace(/≤/g, '<=').replace(/[–—]/g, '-')
    .replace(/[“”]/g, '"').replace(/[‘’]/g, "'").replace(/[•·]/g, '-').replace(/…/g, '...').replace(/[^\x00-\xFF]/g, '');
}

function generarPDF() {
  if (!window.jspdf) { alert('No se pudo cargar jsPDF (revisa la conexión).'); return; }
  const { jsPDF } = window.jspdf;
  const doc = new jsPDF({ unit: 'mm', format: 'a4' });
  const W = 210, M = 16, RGB = CFG.rgb; let y = M; let fig = 0;
  const meta = datos.meta || {};
  const salto = (h) => { if (y + h > 280) { doc.addPage(); y = M + 6; } };
  const titulo = (t) => {
    salto(16); doc.setFont('helvetica', 'bold'); doc.setFontSize(14);
    if (CFG.pdfEstilo === 'banda') { doc.setFillColor(...RGB); doc.rect(M, y - 6, W - 2 * M, 9, 'F'); doc.setTextColor(255); doc.text(txt(t), M + 3, y); doc.setTextColor(20); y += 9; }
    else if (CFG.pdfEstilo === 'caja') { doc.setDrawColor(...RGB); doc.setLineWidth(0.6); doc.rect(M, y - 6, W - 2 * M, 9); doc.setTextColor(...RGB); doc.text(txt(t), M + 3, y); doc.setTextColor(20); y += 9; }
    else { doc.setTextColor(...RGB); doc.text(txt(t), M, y); doc.setDrawColor(...RGB); doc.setLineWidth(0.5); doc.line(M, y + 2, W - M, y + 2); doc.setTextColor(20); y += 8; }
  };
  const sub = (t) => { salto(10); doc.setFont('helvetica', 'bold'); doc.setFontSize(11); doc.text(txt(t), M, y); y += 6; };
  const parrafo = (t) => {
    if (!t) return; doc.setFont('helvetica', 'normal'); doc.setFontSize(10);
    const l = doc.splitTextToSize(txt(t), W - 2 * M); l.forEach((ln) => { salto(5); doc.text(ln, M, y); y += 4.6; }); y += 2;
  };
  const lista = (arr) => (arr || []).forEach((it) => parrafo('- ' + it));
  const tabla = (head, filas) => {
    if (!filas.length) { parrafo('(sin registros)'); return; }
    doc.autoTable({ startY: y, head: [head.map(txt)], body: filas.map((f) => f.map(txt)), margin: { left: M, right: M }, styles: { fontSize: 8, cellPadding: 1.5, overflow: 'linebreak' }, headStyles: { fillColor: RGB }, theme: 'grid' });
    y = doc.lastAutoTable.finalY + 6;
  };
  const tablaDe = (ruta) => {
    const b = MODULOS.flatMap((m) => m.bloques || []).find((x) => x.ruta === ruta);
    const cols = b.cols.filter((c) => c.t !== 'img');
    tabla(cols.map((c) => c.l), (datos[ruta] || []).map((f) => cols.map((c) => f[c.k] || '')));
  };
  const imagenes = (ruta, tituloF, refF) => (datos[ruta] || []).filter((f) => f.imagen).forEach((f) => {
    const p = doc.getImageProperties(f.imagen); const sc = Math.min((W - 2 * M - 30) / p.width, 110 / p.height);
    const iw = p.width * sc, h = p.height * sc;
    salto(h + 14); fig++;
    doc.addImage(f.imagen, 'JPEG', (W - iw) / 2, y, iw, h); y += h + 4;
    doc.setFont('helvetica', 'italic'); doc.setFontSize(9);
    doc.splitTextToSize(txt(`Figura ${fig}: ${tituloF(f)} — ${refF(f)}`), W - 2 * M).forEach((ln) => { doc.text(ln, M, y); y += 4; }); y += 3;
  });

  // 0. Portada
  doc.setFillColor(...RGB); doc.rect(0, 0, W, 70, 'F');
  doc.setTextColor(255); doc.setFont('helvetica', 'bold'); doc.setFontSize(20);
  doc.text(doc.splitTextToSize(txt('Proyecto Integrador de Seguridad en Infraestructura Cloud y Redes'), W - 2 * M), M, 30);
  doc.setFontSize(12); doc.text(txt('TI3062 · Gestión de Seguridad de la Información'), M, 55);
  doc.setTextColor(20); y = 90; doc.setFontSize(16); doc.text(txt((datos.problema && datos.problema.titulo) || ''), M, y); y += 14;
  doc.setFontSize(11); doc.setFont('helvetica', 'normal');
  [['Estudiante', meta.estudiante], ['Número de lista', meta.nn], ['Carrera', meta.carrera], ['Sede', meta.sede], ['Docente', meta.docente],
   ['Fecha de generación', new Date().toLocaleString('es-CL')], ['URL del sistema', meta.urlSistema], ['URL del repositorio', meta.urlRepo],
   ['URL de la aplicación', (datos.infra || {}).appUrl]].forEach(([k, v]) => { doc.setFont('helvetica', 'bold'); doc.text(txt(k + ':'), M, y); doc.setFont('helvetica', 'normal'); doc.text(txt(v || '-'), M + 50, y); y += 8; });
  const k = indicadores();
  y += 6; parrafo(`Estado al generar: avance ${k.avance}% · ${k.controlesImpl}/${k.controlesTot} controles implementados · ${k.aprobadas}/${k.pruebasTot} pruebas aprobadas · ${k.riesgos} riesgos residuales.`);

  // 1. Planificación
  doc.addPage(); y = M + 6;
  titulo('1. Planificación y gestión');
  parrafo(`Avance global: ${k.avance}% (${k.porEstado['Completada'] || 0} de ${k.tareas} tareas completadas). Estados: ` + Object.entries(k.porEstado).map((e) => `${e[0]} ${e[1]}`).join(', ') + '.');
  sub('Hitos'); tablaDe('hitos');
  ROLES.forEach((r) => { sub('Tareas del rol ' + r); const cols = ['id', 'nombre', 'hito', 'responsable', 'inicio', 'fin', 'dependencia', 'estado'];
    tabla(['ID', 'Tarea', 'Hito', 'Responsable', 'Inicio', 'Término', 'Depende de', 'Estado'], (datos.tareas || []).filter((t) => t.rol === r).map((t) => cols.map((c) => t[c] || ''))); });
  sub('Cronograma');
  const tg = (datos.tareas || []).filter((x) => x.inicio && x.fin);
  if (tg.length) {
    const ini = Math.min(...tg.map((x) => +new Date(x.inicio))), fin = Math.max(...tg.map((x) => +new Date(x.fin))) + 864e5, span = fin - ini, ancho = W - 2 * M - 55;
    doc.setFontSize(7);
    tg.forEach((x) => { salto(6); doc.text(txt(`${x.id} ${(x.nombre || '').slice(0, 32)}`), M, y + 3);
      const l = ((+new Date(x.inicio) - ini) / span) * ancho, w = Math.max(1, ((+new Date(x.fin) + 864e5 - +new Date(x.inicio)) / span) * ancho);
      doc.setFillColor(230); doc.rect(M + 55, y, ancho, 4, 'F'); x.estado === 'Completada' ? doc.setFillColor(46, 139, 87) : doc.setFillColor(...RGB); doc.rect(M + 55 + l, y, w, 4, 'F'); y += 5.5; });
    y += 2; doc.text(txt(`${new Date(ini).toISOString().slice(0, 10)}  ...  ${new Date(fin - 864e5).toISOString().slice(0, 10)}`), M + 55, y); y += 6;
  }

  // 2. Problemática
  titulo('2. Problemática, requerimientos, dependencias y limitaciones');
  const p = datos.problema || {};
  sub('Contexto'); parrafo(p.contexto);
  sub('Actores'); lista(p.actores); sub('Procesos afectados'); lista(p.procesos); sub('Necesidades críticas'); lista(p.necesidades);
  sub('Impacto'); parrafo(p.impacto);
  sub('Características clave'); tablaDe('caracteristicas');
  sub('Requerimientos funcionales y no funcionales'); tablaDe('requerimientos');
  sub('Dependencias'); tablaDe('dependencias');
  sub('Limitaciones'); tablaDe('limitaciones');

  // 3. Cloud
  titulo('3. Alternativas cloud y selección');
  const prov = datos.proveedores || [];
  const crit = [['Servicio equivalente', 'servicio'], ['Seguridad', 'seguridad'], ['Disponibilidad', 'disponibilidad'], ['Costo mensual (USD)', 'costo'], ['Fuente', 'fuente'], ['Beneficios', 'beneficios'], ['Limitaciones', 'limitaciones'], ['Riesgos', 'riesgos']];
  tabla(['Criterio', ...prov.map((x) => x.nombre || '')], crit.map(([l, c]) => [l, ...prov.map((x) => x[c] || '')]));
  const s = datos.seleccion || {};
  sub('Selección: ' + (s.proveedor || '')); parrafo(s.justificacion); sub('Alineación con Gobierno TI'); parrafo(s.gobierno);
  sub('Zona de disponibilidad: ' + (s.zona || '')); parrafo(s.zonaJustificacion);

  // 4. NIST
  titulo('4. Controles NIST SP 800-53 Rev. 5');
  sub('Componentes con control de acceso'); tablaDe('componentes');
  sub('Controles seleccionados y justificación'); tablaDe('controles');
  sub('Integración por capas');
  CAPAS.forEach((c) => { const cs = (datos.controles || []).filter((x) => x.capa === c); parrafo(`${c}: ` + (cs.length ? cs.map((x) => `${x.codigo} (${x.punto})`).join('; ') : 'sin controles asignados')); });

  // 5. Implementación
  titulo('5. Implementación');
  const f = datos.infra || {};
  sub('Topología');
  tabla(['Componente', 'Valor'], [['VPC', `${f.vpc || ''} ${f.cidr || ''}`], ['Subred pública', f.publica], ['Subred privada', f.privada], ['Instancia web', f.web], ['Instancia BD', f.bd], ['Motor', f.motor], ['App del caso', f.appUrl]].map((r) => r.map((v) => v || '')));
  salto(70); const x0 = M, y0 = y; doc.setDrawColor(...RGB); doc.setLineDashPattern([2, 1.5], 0); doc.rect(x0, y0, W - 2 * M, 60); doc.setLineDashPattern([], 0);
  doc.setFontSize(9); doc.text(txt(`${f.vpc || ''} ${f.cidr || ''}`), x0 + 3, y0 + 6);
  doc.setDrawColor(46, 139, 87); doc.rect(x0 + 5, y0 + 10, 80, 45); doc.text(txt('Pública ' + (f.publica || '')), x0 + 8, y0 + 16);
  doc.setDrawColor(...RGB); doc.rect(x0 + 93, y0 + 10, 80, 45); doc.text(txt('Privada ' + (f.privada || '')), x0 + 96, y0 + 16);
  doc.setDrawColor(60); doc.rect(x0 + 20, y0 + 25, 50, 18); doc.text(txt('EC2 ' + (f.web || '')), x0 + 24, y0 + 33); doc.text('HTTP/HTTPS - SSH', x0 + 24, y0 + 39);
  doc.rect(x0 + 108, y0 + 25, 50, 18); doc.text(txt('EC2 ' + (f.bd || '')), x0 + 112, y0 + 33); doc.text(txt((f.motor || '') + ' - sin IP publica'), x0 + 112, y0 + 39);
  doc.setLineDashPattern([1, 1], 0); doc.line(x0 + 70, y0 + 34, x0 + 108, y0 + 34); doc.setLineDashPattern([], 0);
  doc.text('0.0.0.0/0 -> IGW', x0 + 8, y0 + 52); doc.text('Sin ruta a Internet', x0 + 96, y0 + 52); y = y0 + 66;
  sub('Security Groups y firewall de host'); tablaDe('sg');
  sub('Bitácora de implementación (endurecimiento, disponibilidad y evidencias)');
  AREAS.forEach((a) => { const reg = (datos.bitacora || []).filter((b) => b.area === a); if (!reg.length) return; sub('· ' + a);
    tabla(['Fecha', 'Configuración', 'Comando / archivo', 'Responsable', 'Ref.', 'Justificación'], reg.map((b) => [b.fecha, b.configuracion, b.comando, b.responsable, b.ref, b.descripcion].map((v) => v || ''))); });
  sub('Evidencias'); imagenes('bitacora', (b) => b.evidencia || b.configuracion || 'Evidencia', (b) => `${b.descripcion || ''} (ref. ${b.ref || '-'})`);

  // 6. Validación
  titulo('6. Validación');
  sub('Pruebas ejecutadas'); tablaDe('pruebas');
  sub('Verificación de controles');
  tabla(['Control', 'Estado', 'Pruebas asociadas'], (datos.controles || []).map((c) => [c.codigo + ' ' + (c.nombre || ''), c.estado || '', (datos.pruebas || []).filter((t) => (t.control || '').includes(c.codigo)).map((t) => `${t.id}: ${t.estado || 'Pendiente'}`).join(', ') || '-']));
  sub('Hallazgos y contraste con requerimientos / NIST'); tablaDe('hallazgos');
  sub('Capturas de las pruebas'); imagenes('pruebas', (t) => `${t.id} ${t.objetivo || ''}`, (t) => `resultado ${t.estado || 'Pendiente'} (control ${t.control || '-'})`);

  // 7. Evaluación final
  titulo('7. Evaluación final');
  sub('Análisis CIA'); tablaDe('cia');
  sub('Riesgos residuales'); tablaDe('riesgos');
  sub('Coherencia con Gobierno TI'); tablaDe('gobierno');
  sub('Acciones de mejora'); tablaDe('mejoras');
  const c = datos.cierre || {}; sub('Conclusiones'); parrafo(c.conclusion); if (c.aprendizajes) { sub('Aprendizajes'); parrafo(c.aprendizajes); }

  const n = doc.getNumberOfPages();
  for (let i = 2; i <= n; i++) { doc.setPage(i); doc.setFontSize(8); doc.setTextColor(120); doc.text(txt(`TI3062 · ${meta.estudiante || ''} · NN ${meta.nn || ''} · ${CFG.appName}`), M, 290); doc.text(`${i}/${n}`, W - M, 290, { align: 'right' }); }
  doc.save(`TI3062_Proyecto_NN${meta.nn || CFG.nn}_${hoy()}.pdf`);
}

/* ---------------- Inicio ---------------- */
cargar().then(render);
