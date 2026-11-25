

let compras = [], medicamentos = [], laboratorios = [], sucursales = [], itemsCompra = [];
const porPagina = 10;
let paginaActual = 1;

function fechaISO(iso) {
  const fecha = new Date(iso);
  if (isNaN(fecha.getTime())) return "";
  return `${fecha.getFullYear()}-${String(fecha.getMonth() + 1).padStart(2, "0")}-${String(fecha.getDate()).padStart(2, "0")}`;
}

function aplicarFiltros() {
  const texto = document.getElementById("buscador").value.toLowerCase().trim();
  const estado = document.getElementById("filtroEstado").value;
  const sucursal = document.getElementById("filtroSucursal").value;
  const desde = document.getElementById("fechaDesde").value;
  const hasta = document.getElementById("fechaHasta").value;

  return compras.filter(c => {
    const coincideTexto = c.numero_compra.toLowerCase().includes(texto) || (c.laboratorio || "").toLowerCase().includes(texto);
    const coincideEstado = !estado || c.estado === estado;
    const coincideSucursal = !sucursal || String(c.sucursal_id) === sucursal;
    const fecha = fechaISO(c.fecha);
    const coincideFecha = (!desde || fecha >= desde) && (!hasta || fecha <= hasta);
    return coincideTexto && coincideEstado && coincideSucursal && coincideFecha;
  });
}

function actualizarKpis(filtrados) {
  const vigentes = filtrados.filter(c => c.estado !== "Anulada");
  const monto = vigentes.reduce((suma, c) => suma + (Number(c.total) || 0), 0);
  const pendientes = filtrados.filter(c => c.estado !== "Completada" && c.estado !== "Anulada").length;
  document.getElementById("comKpiOrdenes").innerText =
    `${filtrados.length} ${filtrados.length === 1 ? "orden" : "órdenes"}`;
  document.getElementById("comKpiMonto").innerText = formatearMoneda(monto);
  document.getElementById("comKpiPendientes").innerText =
    `${pendientes} ${pendientes === 1 ? "orden" : "órdenes"}`;
}

function limpiarFiltros() {
  document.getElementById("buscador").value = "";
  document.getElementById("filtroEstado").value = "";
  document.getElementById("filtroSucursal").value = "";
  document.getElementById("fechaDesde").value = "";
  document.getElementById("fechaHasta").value = "";
  paginaActual = 1;
  renderTabla();
}

function renderPaginacionCompras(total, pagina) {
  const contenedor = document.getElementById("paginacion");
  const etiqueta = document.getElementById("comMostrando");
  if (!contenedor) return;

  const totalPaginas = Math.max(1, Math.ceil(total / porPagina));
  if (pagina > totalPaginas) pagina = totalPaginas;
  const desde = total ? (pagina - 1) * porPagina + 1 : 0;
  const hasta = Math.min(pagina * porPagina, total);

  if (etiqueta) {
    etiqueta.innerText = totalPaginas === 1
      ? `Mostrando ${total} de ${total} registros`
      : `Mostrando ${desde}-${hasta} de ${total} registros`;
  }

  const boton = (destino, contenido, deshabilitado, etiquetaAccion, activa) => `
    <button type="button" class="com-pag-btn ${activa ? 'activa' : ''}" data-pagina="${destino}"
            aria-label="${etiquetaAccion}" ${deshabilitado ? 'disabled' : ''}
            ${activa ? 'aria-current="page"' : ''}>${contenido}</button>`;

  let html = boton(1, '<i class="fa-solid fa-angles-left"></i>', pagina === 1, "Primera página", false);
  html += boton(pagina - 1, '<i class="fa-solid fa-angle-left"></i>', pagina === 1, "Página anterior", false);
  for (let i = 1; i <= totalPaginas; i++) {
    html += boton(i, String(i), i === pagina, `Página ${i}`, i === pagina);
  }
  html += boton(pagina + 1, '<i class="fa-solid fa-angle-right"></i>', pagina === totalPaginas, "Página siguiente", false);
  html += boton(totalPaginas, '<i class="fa-solid fa-angles-right"></i>', pagina === totalPaginas, "Última página", false);

  contenedor.innerHTML = html;
  contenedor.querySelectorAll(".com-pag-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      paginaActual = Number(btn.dataset.pagina);
      renderTabla();
    });
  });
}

async function cargar() {
  document.getElementById("tbody").innerHTML = `<tr><td colspan="9">${bloqueCargando()}</td></tr>`;
  try {
    [compras, medicamentos, laboratorios, sucursales] = await Promise.all([
      apiRequest("/api/compras"), apiRequest("/api/medicamentos"), apiRequest("/api/laboratorios"), apiRequest("/api/sucursales"),
    ]);
  } catch (e) {
    document.getElementById("tbody").innerHTML = `
      <tr><td colspan="9">
        <div class="com-vacio">
          <i class="fa-solid fa-triangle-exclamation"></i>
          <p>No se pudo cargar el listado de compras.</p>
          <button type="button" class="com-reintentar" onclick="cargar()">Reintentar</button>
        </div>
      </td></tr>`;
    document.getElementById("comMostrando").innerText = "Mostrando 0 de 0 registros";
    document.getElementById("paginacion").innerHTML = "";
    return;
  }
  document.getElementById("f_laboratorio").innerHTML = laboratorios.map(l => `<option value="${l.id}">${escapeHtml(l.nombre)}</option>`).join("");
  document.getElementById("f_sucursal").innerHTML = sucursales.map(s => `<option value="${s.id}">${escapeHtml(s.nombre)}</option>`).join("");
  document.getElementById("filtroSucursal").innerHTML = '<option value="">Todas las sucursales</option>' +
    sucursales.map(s => `<option value="${s.id}">${escapeHtml(s.nombre)}</option>`).join("");
  document.getElementById("item_medicamento").innerHTML = medicamentos.map(m => `<option value="${m.id}" data-precio="${m.precio_compra}">${escapeHtml(m.nombre)}</option>`).join("");
  renderTabla();
}

function renderTabla() {
  const filtrados = aplicarFiltros();
  actualizarKpis(filtrados);

  const totalPaginas = Math.max(1, Math.ceil(filtrados.length / porPagina));
  if (paginaActual > totalPaginas) paginaActual = totalPaginas;
  const pagina = paginar(filtrados, paginaActual, porPagina);

  document.getElementById("tbody").innerHTML = pagina.map(c => `
    <tr class="com-fila ${c.estado === 'Anulada' ? 'anulada' : ''}">
      <td class="com-orden">${escapeHtml(c.numero_compra)}</td>
      <td class="com-laboratorio">${escapeHtml(c.laboratorio)}</td>
      <td>${escapeHtml(c.sucursal) || '-'}</td>
      <td>${escapeHtml(c.usuario)}</td>
      <td class="com-fecha">${formatearFecha(c.fecha)}</td>
      <td class="com-total">${formatearMoneda(c.total)}</td>
      <td>${c.detalles.length} ${c.detalles.length === 1 ? 'ítem' : 'ítems'}</td>
      <td><span class="com-badge ${c.estado === 'Anulada' ? 'anulada' : 'completada'}">${escapeHtml(c.estado)}</span></td>
      <td class="com-acciones">
        ${c.estado === 'Anulada' ? '<span class="com-sin-accion">-</span>' : `<button type="button" data-id="${c.id}" class="btn-anular com-btn-anular" title="Anular compra" aria-label="Anular compra ${escapeHtml(c.numero_compra)}">Anular</button>`}
      </td>
    </tr>`).join("") || `
    <tr><td colspan="9">
      <div class="com-vacio">
        <i class="fa-solid fa-cart-shopping"></i>
        <p class="com-vacio-principal">${compras.length === 0 ? 'Sin compras registradas' : 'No se encontraron compras con esos criterios'}</p>
        ${compras.length === 0 ? '<p class="com-vacio-secundario">Cuando registres una nueva compra, aparecerá aquí el historial de órdenes.</p>' : ''}
      </div>
    </td></tr>`;

  renderPaginacionCompras(filtrados.length, paginaActual);
}

async function anular(id) {
  const compra = compras.find(c => c.id === id);
  if (!compra) return;
  if (!(await confirmarAccion(`¿Anular la compra ${compra.numero_compra}? Se revertirá el stock que ingresó.`))) return;
  try {
    await apiRequest(`/api/compras/${id}/anular`, { method: "POST" });
    notificarAccion("Compra anulada y stock revertido");
    cargar();
  } catch (e) {
    mostrarToast(e.message, "error");
  }
}

document.getElementById("tbody").addEventListener("click", (e) => {
  const btn = e.target.closest(".btn-anular");
  if (btn) anular(Number(btn.dataset.id));
});

function abrirModal() {
  itemsCompra = [];
  renderItems();
  document.getElementById("modal").classList.remove("hidden");
}
function cerrarModal() { document.getElementById("modal").classList.add("hidden"); }

function agregarItem() {
  const sel = document.getElementById("item_medicamento");
  const medicamento_id = parseInt(sel.value);
  const nombre = sel.options[sel.selectedIndex].text;
  const numero_lote = document.getElementById("item_lote").value || `L-${Date.now()}`;
  const fecha_vencimiento = document.getElementById("item_vencimiento").value;
  const cantidad = parseInt(document.getElementById("item_cantidad").value);
  const precio_unitario = parseFloat(document.getElementById("item_precio").value);

  if (!fecha_vencimiento || !cantidad || !precio_unitario) {
    mostrarToast("Completa fecha de vencimiento, cantidad y precio", "error"); return;
  }
  itemsCompra.push({ medicamento_id, nombre, numero_lote, fecha_vencimiento, cantidad, precio_unitario });
  renderItems();
}

function renderItems() {
  document.getElementById("items_tbody").innerHTML = itemsCompra.map((it, i) => `
    <tr class="border-b border-gray-50">
      <td class="py-1">${escapeHtml(it.nombre)}</td><td>${escapeHtml(it.numero_lote)}</td><td>${escapeHtml(it.fecha_vencimiento)}</td>
      <td>${it.cantidad} x ${formatearMoneda(it.precio_unitario)}</td>
      <td class="text-right"><button onclick="quitarItem(${i})" class="text-inka-red"><i class="fa-solid fa-xmark"></i></button></td>
    </tr>`).join("");
  const total = itemsCompra.reduce((a, it) => a + it.cantidad * it.precio_unitario, 0);
  document.getElementById("totalCompra").innerText = formatearMoneda(total);
}
function quitarItem(i) { itemsCompra.splice(i, 1); renderItems(); }

async function guardarCompra() {
  if (!itemsCompra.length) { mostrarToast("Agrega al menos un ítem", "error"); return; }
  const payload = {
    laboratorio_id: parseInt(document.getElementById("f_laboratorio").value),
    sucursal_id: parseInt(document.getElementById("f_sucursal").value),
    items: itemsCompra,
  };
  try {
    await apiRequest("/api/compras", { method: "POST", body: payload });
    notificarAccion("Compra registrada e inventario actualizado");
    cerrarModal(); cargar();
  } catch (e) { mostrarToast(e.message, "error"); }
}
cargar();
