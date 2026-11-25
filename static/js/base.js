






function escapeHtml(valor) {
  if (valor === null || valor === undefined) return "";
  return String(valor)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function csrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.content : "";
}

async function apiRequest(url, options = {}) {
  const opts = {
    headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken() },
    ...options,
  };
  if (opts.body && typeof opts.body !== "string") {
    opts.body = JSON.stringify(opts.body);
  }
  const res = await fetch(url, opts);
  let data = null;
  try { data = await res.json(); } catch (e) { data = null; }
  if (!res.ok) {
    throw new Error((data && data.error) || `Error ${res.status}`);
  }
  return data;
}

function mostrarToast(mensaje, tipo = "exito") {
  const contenedor = document.getElementById("toast-container") || crearContenedorToast();
  const toast = document.createElement("div");
  const colores = {
    exito: "bg-inka-green",
    error: "bg-inka-red",
  };
  toast.className = `${colores[tipo] || colores.exito} text-white px-4 py-3 rounded-lg shadow-lg mb-2 text-sm font-medium animate-fade-in`;
  toast.textContent = mensaje;
  contenedor.appendChild(toast);
  setTimeout(() => toast.remove(), 3500);
}

function crearContenedorToast() {
  const div = document.createElement("div");
  div.id = "toast-container";
  div.className = "fixed top-4 right-4 z-[100]";
  document.body.appendChild(div);
  return div;
}

function formatearMoneda(valor) {
  return "S/ " + Number(valor || 0).toLocaleString("es-PE", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatearFecha(fechaISO) {
  if (!fechaISO) return "-";
  const f = new Date(fechaISO);
  return f.toLocaleDateString("es-PE", { year: "numeric", month: "short", day: "numeric" });
}

function badgeVencimiento(dias) {
  if (dias < 0) return `<span class="badge badge-red">Vencido</span>`;
  if (dias <= 30) return `<span class="badge badge-yellow">Vence en ${dias} días</span>`;
  return `<span class="badge badge-green">Vigente</span>`;
}


function filaCargando(colspan) {
  return `<tr><td colspan="${colspan}" class="text-center text-gray-400 py-10">
    <i class="fa-solid fa-circle-notch fa-spin mr-2"></i>Cargando...
  </td></tr>`;
}

function filaError(colspan, mensaje = "No se pudo cargar la información. Intenta de nuevo.") {
  return `<tr><td colspan="${colspan}" class="text-center text-inka-red py-10">
    <i class="fa-solid fa-triangle-exclamation mr-2"></i>${mensaje}
  </td></tr>`;
}


function bloqueCargando() {
  return `<div class="text-center text-gray-400 text-sm py-6">
    <i class="fa-solid fa-circle-notch fa-spin mr-2"></i>Cargando...
  </div>`;
}

function bloqueError(mensaje = "No se pudo cargar la información. Intenta de nuevo.") {
  return `<div class="text-center text-inka-red text-sm py-6">
    <i class="fa-solid fa-triangle-exclamation mr-2"></i>${mensaje}
  </div>`;
}


function paginar(array, pagina, porPagina) {
  const inicio = (pagina - 1) * porPagina;
  return array.slice(inicio, inicio + porPagina);
}



function renderPaginacion(contenedorId, totalItems, paginaActual, porPagina, callback) {
  const contenedor = document.getElementById(contenedorId);
  if (!contenedor) return;
  const totalPaginas = Math.max(1, Math.ceil(totalItems / porPagina));

  if (totalPaginas <= 1) { contenedor.innerHTML = ""; return; }

  contenedor.innerHTML = `
    <div class="flex items-center justify-between mt-4 text-sm text-gray-500">
      <span>Página ${paginaActual} de ${totalPaginas} · ${totalItems} registro(s)</span>
      <div class="flex gap-1">
        <button data-pagina="${paginaActual - 1}" ${paginaActual === 1 ? "disabled" : ""} class="btn-paginacion px-3 py-1 border border-gray-200 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-50">
          <i class="fa-solid fa-chevron-left"></i>
        </button>
        <button data-pagina="${paginaActual + 1}" ${paginaActual === totalPaginas ? "disabled" : ""} class="btn-paginacion px-3 py-1 border border-gray-200 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-50">
          <i class="fa-solid fa-chevron-right"></i>
        </button>
      </div>
    </div>`;

  contenedor.querySelectorAll(".btn-paginacion").forEach(btn => {
    btn.addEventListener("click", () => callback(Number(btn.dataset.pagina)));
  });
}



function confirmarAccion(mensaje) {
  const modal = document.getElementById("modal-confirmacion");
  const btnAceptar = document.getElementById("confirmacionAceptar");
  const btnCancelar = document.getElementById("confirmacionCancelar");

  document.getElementById("confirmacionMensaje").innerText = mensaje;
  modal.classList.remove("hidden");

  return new Promise((resolve) => {
    const limpiar = () => {
      modal.classList.add("hidden");
      btnAceptar.removeEventListener("click", onAceptar);
      btnCancelar.removeEventListener("click", onCancelar);
    };
    const onAceptar = () => { limpiar(); resolve(true); };
    const onCancelar = () => { limpiar(); resolve(false); };
    btnAceptar.addEventListener("click", onAceptar);
    btnCancelar.addEventListener("click", onCancelar);
  });
}






const SONIDO_NOTIFICACION = new Audio("/static/audio/notification-sound.mp3");

function reproducirSonidoNotificacion() {
  SONIDO_NOTIFICACION.currentTime = 0;
  SONIDO_NOTIFICACION.play().catch(() => {});
}

function _claveNotificaciones() {
  const rol = document.body.dataset.usuarioRol || "invitado";
  return `inkafarma_notificaciones_${rol}`;
}

function _leerNotificaciones() {
  try {
    return JSON.parse(localStorage.getItem(_claveNotificaciones())) || [];
  } catch (e) {
    return [];
  }
}

function _guardarNotificaciones(lista) {
  localStorage.setItem(_claveNotificaciones(), JSON.stringify(lista.slice(0, 30)));
}

function renderNotificaciones() {
  const badge = document.getElementById("badgeNotificaciones");
  const contenedor = document.getElementById("listaNotificaciones");
  if (!badge || !contenedor) return;

  const lista = _leerNotificaciones();
  const noLeidas = lista.filter(n => !n.leida).length;
  badge.classList.toggle("hidden", noLeidas === 0);
  badge.innerText = noLeidas > 9 ? "9+" : noLeidas;

  contenedor.innerHTML = lista.length
    ? lista.map(n => `
        <div class="px-4 py-3 text-sm ${n.leida ? "" : "notif-no-leida"}">
          <p class="text-gray-700"><i class="fa-solid ${n.tipo === "error" ? "fa-circle-exclamation text-inka-red" : "fa-circle-check text-inka-green"} mr-1.5"></i>${n.mensaje}</p>
          <p class="text-[11px] text-gray-400 mt-0.5 ml-5">${n.fecha}</p>
        </div>`).join("")
    : `<div class="px-4 py-8 text-center text-gray-400 text-sm">Sin notificaciones</div>`;
}




function notificarAccion(mensaje, tipo = "exito") {
  mostrarToast(mensaje, tipo);
  reproducirSonidoNotificacion();

  const lista = _leerNotificaciones();
  lista.unshift({
    mensaje,
    tipo,
    fecha: new Date().toLocaleString("es-PE", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" }),
    leida: false,
  });
  _guardarNotificaciones(lista);
  renderNotificaciones();
}

function limpiarNotificaciones() {
  _guardarNotificaciones([]);
  renderNotificaciones();
}

function marcarNotificacionesLeidas() {
  const lista = _leerNotificaciones().map(n => ({ ...n, leida: true }));
  _guardarNotificaciones(lista);
  renderNotificaciones();
}

document.addEventListener("DOMContentLoaded", () => {
  renderNotificaciones();

  const btnCampana = document.getElementById("btnCampana");
  const panel = document.getElementById("panelNotificaciones");
  const btnLimpiar = document.getElementById("btnLimpiarNotificaciones");
  if (!btnCampana || !panel) return;

  btnCampana.addEventListener("click", (e) => {
    e.stopPropagation();
    panel.classList.toggle("hidden");
    if (!panel.classList.contains("hidden")) marcarNotificacionesLeidas();
  });
  document.addEventListener("click", (e) => {
    if (!panel.contains(e.target) && e.target !== btnCampana) panel.classList.add("hidden");
  });
  if (btnLimpiar) {
    btnLimpiar.addEventListener("click", (e) => {
      e.stopPropagation();
      limpiarNotificaciones();
    });
  }
});


async function cargarIndicadorVentasHoy() {
  const elemento = document.getElementById("ventasHoy");
  if (!elemento) return;
  try {
    const data = await apiRequest("/api/dashboard/resumen");
    elemento.innerText = data.kpis.total_ventas_hoy;
  } catch (e) {
    elemento.innerText = "0";
  }
}

document.addEventListener("DOMContentLoaded", cargarIndicadorVentasHoy);


document.addEventListener("DOMContentLoaded", () => {
  const btnMenu = document.getElementById("btnMenuMovil");
  const sidebar = document.getElementById("sidebarPrincipal");
  const overlay = document.getElementById("sidebarOverlay");
  if (!btnMenu || !sidebar || !overlay) return;

  const cerrar = () => {
    sidebar.classList.remove("abierta");
    overlay.classList.add("hidden");
  };

  btnMenu.addEventListener("click", () => {
    sidebar.classList.add("abierta");
    overlay.classList.remove("hidden");
  });
  overlay.addEventListener("click", cerrar);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") cerrar();
  });
});





function saludoYFecha() {
  const ahora = new Date();
  const hora = ahora.getHours();
  const saludo = hora < 12 ? "Buenos días" : hora < 19 ? "Buenas tardes" : "Buenas noches";
  const elementoSaludo = document.getElementById("saludoHora");
  const elementoFecha = document.getElementById("fechaHoy");
  if (elementoSaludo) elementoSaludo.innerText = saludo;
  if (elementoFecha) {
    elementoFecha.innerText = ahora.toLocaleDateString("es-PE", {
      weekday: "long", day: "numeric", month: "long", year: "numeric",
    });
  }
}

function tarjetaKpiPremium(icono, tono, etiqueta, valor, detalle) {
  return `
    <div class="kpi-card">
      <div class="kpi-top">
        <span class="kpi-icon ${tono}"><i class="fa-solid ${icono}"></i></span>
        <span class="kpi-detalle">${escapeHtml(detalle || "")}</span>
      </div>
      <p class="kpi-label">${escapeHtml(etiqueta)}</p>
      <p class="kpi-valor">${escapeHtml(valor)}</p>
    </div>`;
}

function estadoVacioPremium(mensaje) {
  return `<div class="empty-state"><i class="fa-regular fa-folder-open"></i><p>${escapeHtml(mensaje)}</p></div>`;
}


function serieVentas7Dias(ventasPorDia, arregloUnidades) {
  const dias = (arregloUnidades || []).map(d => d.dia);
  const montosPorDia = {};
  (ventasPorDia || []).forEach(v => {
    const partes = String(v.dia || "").split("-");
    if (partes.length === 3) montosPorDia[partes[2] + "/" + partes[1]] = Number(v.monto) || 0;
  });
  if (!dias.length) {
    return (ventasPorDia || []).map(v => ({ dia: String(v.dia).slice(5), monto: Number(v.monto) || 0 }));
  }
  return dias.map(dia => ({ dia, monto: montosPorDia[dia] || 0 }));
}

function renderTopVendidosPremium(id, topVendidos) {
  const contenedor = document.getElementById(id);
  if (!contenedor) return;
  const lista = topVendidos || [];
  if (!lista.length) {
    contenedor.innerHTML = estadoVacioPremium("Aún no hay ventas registradas.");
    return;
  }
  const total = lista.reduce((suma, p) => suma + (Number(p.cantidad_vendida) || 0), 0);
  contenedor.innerHTML = `
    <table class="tabla-premium">
      <thead><tr><th>#</th><th>Medicamento</th><th>Unidades</th><th>Participación</th></tr></thead>
      <tbody>${lista.map((p, i) => {
        const unidades = Number(p.cantidad_vendida) || 0;
        const porcentaje = total ? Math.round((unidades / total) * 100) : 0;
        return `<tr>
          <td><span class="pos-circulo">${i + 1}</span></td>
          <td class="med-nombre">${escapeHtml(p.medicamento)}</td>
          <td class="med-unidades">${unidades}</td>
          <td><div class="participacion"><div class="barra-participacion"><span style="width:${porcentaje}%"></span></div><small>${porcentaje}%</small></div></td>
        </tr>`;
      }).join("")}</tbody>
    </table>`;
}

function renderAlertasPremium(id, alertas) {
  const contenedor = document.getElementById(id);
  if (!contenedor) return;
  const lista = alertas || [];
  if (!lista.length) {
    contenedor.innerHTML = estadoVacioPremium("No hay alertas críticas por el momento.");
    return;
  }
  contenedor.innerHTML = lista.map(m => `
    <div class="alerta-row">
      <span class="alerta-icon"><i class="fa-solid fa-triangle-exclamation"></i></span>
      <div class="alerta-body">
        <p class="alerta-nombre">${escapeHtml(m.nombre)}</p>
        <p class="alerta-meta">Stock actual: ${m.stock_total} und. | Mínimo: ${m.stock_minimo} und.</p>
      </div>
      <span class="badge-stock-bajo">Stock bajo</span>
    </div>`).join("");
}

let chartVentas, chartCategorias;
const COLORES_CATEGORIAS = ["#008F32", "#00A83B", "#86EFAC", "#FDE68A", "#0B1731", "#DCFCE7"];

function dibujarGraficoVentasPremium(serie) {
  const lienzo = document.getElementById("chartVentas");
  if (!lienzo || typeof Chart === "undefined") return;
  if (chartVentas) chartVentas.destroy();

  const ctx = lienzo.getContext("2d");
  const degradado = ctx.createLinearGradient(0, 0, 0, 250);
  degradado.addColorStop(0, "rgba(0,168,59,0.28)");
  degradado.addColorStop(1, "rgba(0,168,59,0.01)");

  chartVentas = new Chart(ctx, {
    type: "line",
    data: {
      labels: serie.map(v => v.dia),
      datasets: [{
        label: "Ventas (S/)",
        data: serie.map(v => v.monto),
        borderColor: "#00A83B",
        backgroundColor: degradado,
        borderWidth: 3,
        fill: true,
        tension: 0.35,
        pointRadius: 4,
        pointHoverRadius: 6,
        pointBackgroundColor: "#FFFFFF",
        pointBorderColor: "#00A83B",
        pointBorderWidth: 2,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { intersect: false, mode: "index" },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#0B1731",
          padding: 10,
          displayColors: false,
          callbacks: { label: (item) => " " + formatearMoneda(item.parsed.y) },
        },
      },
      scales: {
        x: { grid: { display: false }, border: { display: false }, ticks: { color: "#94A3B8", font: { size: 11 } } },
        y: {
          beginAtZero: true,
          grid: { color: "#EEF2F6" },
          border: { display: false },
          ticks: { color: "#94A3B8", font: { size: 11 }, precision: 0, callback: (valor) => "S/ " + valor },
        },
      },
    },
  });
}

function dibujarGraficoCategoriasPremium(categorias) {
  const lienzo = document.getElementById("chartCategorias");
  if (!lienzo || typeof Chart === "undefined") return;
  if (chartCategorias) chartCategorias.destroy();

  const total = categorias.reduce((suma, c) => suma + (Number(c.cantidad) || 0), 0);
  chartCategorias = new Chart(lienzo, {
    type: "doughnut",
    data: {
      labels: categorias.map(c => c.categoria),
      datasets: [{
        data: categorias.map(c => c.cantidad),
        backgroundColor: COLORES_CATEGORIAS,
        borderWidth: 0,
        hoverOffset: 6,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "68%",
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#0B1731",
          padding: 10,
          callbacks: {
            label: (item) => {
              const porcentaje = total ? Math.round((Number(item.parsed) / total) * 100) : 0;
              return ` ${item.label}: ${item.parsed} (${porcentaje}%)`;
            },
          },
        },
      },
    },
  });

  const leyenda = document.getElementById("leyendaCategorias");
  if (leyenda) {
    leyenda.innerHTML = categorias.map((c, i) => {
      const porcentaje = total ? Math.round((Number(c.cantidad) / total) * 100) : 0;
      return `<span><i style="background:${COLORES_CATEGORIAS[i % COLORES_CATEGORIAS.length]}"></i>${escapeHtml(c.categoria)} · ${porcentaje}%</span>`;
    }).join("");
  }
}
