/* {{APP_CASO}} · comportamiento del cliente (archivo externo: la CSP no permite scripts en línea).
   Todo el texto que llega del servidor se pinta con textContent (nunca innerHTML) para evitar XSS. */
(function () {
  'use strict';
  var raiz = document.documentElement;

  // Modo claro/oscuro (preferencia local del navegador; no es un dato del sistema)
  try { var m = localStorage.getItem('modo'); if (m) raiz.setAttribute('data-modo', m); } catch (e) { /* sin almacenamiento */ }
  document.addEventListener('DOMContentLoaded', function () {
    var bt = document.getElementById('tema');
    if (bt) bt.addEventListener('click', function () {
      var nuevo = raiz.getAttribute('data-modo') === 'claro' ? 'oscuro' : 'claro';
      raiz.setAttribute('data-modo', nuevo);
      try { localStorage.setItem('modo', nuevo); } catch (e) { /* sin almacenamiento */ }
    });

    // Confirmación de acciones sensibles
    document.querySelectorAll('form[data-confirmar]').forEach(function (f) {
      f.addEventListener('submit', function (ev) { if (!window.confirm(f.getAttribute('data-confirmar'))) ev.preventDefault(); });
    });

    // Partes del equipo (vista "Cómo funciona"): resalta y explica la parte elegida
    document.querySelectorAll('[data-parte]').forEach(function (el) {
      el.addEventListener('click', function () { elegirParte(el.getAttribute('data-parte')); });
      el.addEventListener('keydown', function (ev) { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); elegirParte(el.getAttribute('data-parte')); } });
    });
    var cargaPc = document.getElementById('carga-pc');
    if (cargaPc) cargaPc.addEventListener('input', function () { raiz.style.setProperty('--carga', cargaPc.value); actualizarCarga(cargaPc.value); });

    if (document.getElementById('kpis')) { vivo(); setInterval(vivo, 5000); }
  });

  function elegirParte(id) {
    document.querySelectorAll('[data-parte]').forEach(function (e) { e.classList.toggle('elegida', e.getAttribute('data-parte') === id); });
    document.querySelectorAll('.ficha-parte').forEach(function (f) { f.hidden = f.id !== 'ficha-' + id; });
  }
  function actualizarCarga(v) {
    var n = parseInt(v, 10) || 0;
    var t = document.getElementById('carga-txt'); if (t) t.textContent = n + ' %';
    var rpm = document.getElementById('carga-rpm'); if (rpm) rpm.textContent = String(Math.round(600 + n * 14)) + ' RPM';
    var tmp = document.getElementById('carga-temp'); if (tmp) tmp.textContent = String(Math.round(35 + n * 0.45)) + ' °C';
    var w = document.getElementById('carga-w'); if (w) w.textContent = String(Math.round(60 + n * 3.4)) + ' W';
    raiz.setAttribute('data-carga', n >= 70 ? 'alta' : (n >= 35 ? 'media' : 'baja'));
  }

  function txt(id, v) { var e = document.getElementById(id); if (e) e.textContent = v; }
  function vivo() {
    fetch('api.php', { credentials: 'same-origin', cache: 'no-store' })
      .then(function (r) {
        if (r.status === 401) { window.location.href = './'; throw new Error('sesion'); }
        return r.json();
      })
      .then(function (d) {
        var ruta = document.getElementById('ruta');
        if (!d.canal || !d.canal.ok) { if (ruta) ruta.setAttribute('data-estado', 'mal'); txt('vivo-hora', 'sin conexión con bd'); return; }
        txt('vivo-hora', 'actualizado ' + d.hora + ' · cada 5 s');
        (d.kpis || []).forEach(function (k, i) {
          var el = document.querySelector('[data-kpi="' + i + '"]');
          if (el && el.textContent !== k.v) { el.textContent = k.v; el.classList.remove('cambio'); void el.offsetWidth; el.classList.add('cambio'); }
        });
        txt('canal-tls', d.canal.tls || 'SIN TLS');
        txt('canal-cipher', d.canal.cipher || '—');
        txt('canal-ms', d.canal.ms + ' ms');
        if (ruta) {
          ruta.setAttribute('data-estado', d.canal.tls ? 'bien' : 'alerta');
          ruta.classList.remove('pulso'); void ruta.offsetWidth; ruta.classList.add('pulso');
        }
        var feed = document.getElementById('feed');
        if (feed && d.ultimos) {
          feed.textContent = '';
          d.ultimos.forEach(function (u) {
            var li = document.createElement('li'); li.className = u.tono || '';
            var s = document.createElement('span'); s.className = 'num'; s.textContent = u.cuando;
            li.appendChild(s); li.appendChild(document.createTextNode(u.texto));
            feed.appendChild(li);
          });
        }
      })
      .catch(function () { /* se reintenta en el siguiente ciclo */ });
  }
})();
