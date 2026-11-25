

let ventas = [];
const porPagina = 10;
let paginaActual = 1;

async function cargar() {
  document.getElementById("tbody").innerHTML = filaCargando(8);
  try {
    ventas = await apiRequest("/api/ventas");
  } catch (e) {
    document.getElementById("tbody").innerHTML = filaError(8);
    mostrarToast(e.message, "error");
    return;
  }
  renderTabla();
}

function renderTabla() {
  const filtro = document.getElementById("buscador").value.toLowerCase();
  const filtrados = ventas.filter(v =>
    v.numero_venta.toLowerCase().includes(filtro) ||
    v.cliente_nombre.toLowerCase().includes(filtro) ||
    (v.usuario || "").toLowerCase().includes(filtro)
  );

  const totalPaginas = Math.max(1, Math.ceil(filtrados.length / porPagina));
  if (paginaActual > totalPaginas) paginaActual = totalPaginas;
  const pagina = paginar(filtrados, paginaActual, porPagina);

  document.getElementById("tbody").innerHTML = pagina.map(v => `
    <tr class="${v.estado === 'Anulada' ? 'opacity-50' : ''}">
      <td class="font-mono text-xs">${escapeHtml(v.numero_venta)}</td>
      <td>${escapeHtml(v.cliente_nombre)}</td><td>${escapeHtml(v.usuario)}</td><td>${formatearFecha(v.fecha)}</td>
      <td><span class="badge badge-green">${escapeHtml(v.metodo_pago)}</span></td>
      <td class="font-semibold">${formatearMoneda(v.total)}</td>
      <td>${v.estado === 'Anulada' ? '<span class="badge badge-red">Anulada</span>' : '<span class="badge badge-green">Completada</span>'}</td>
      <td class="whitespace-nowrap">
        ${v.estado === 'Anulada' ? '-' : `<button data-id="${v.id}" class="btn-anular text-inka-red text-sm font-semibold hover:underline">Anular</button>`}
      </td>
    </tr>`).join("") || `<tr><td colspan="8" class="text-center text-gray-400 py-6">Sin ventas registradas</td></tr>`;

  renderPaginacion("paginacion", filtrados.length, paginaActual, porPagina, (p) => { paginaActual = p; renderTabla(); });
}

async function anular(id) {
  const venta = ventas.find(v => v.id === id);
  if (!venta) return;
  if (!(await confirmarAccion(`¿Anular la venta ${venta.numero_venta}? Se devolverá el stock a los lotes.`))) return;
  try {
    await apiRequest(`/api/ventas/${id}/anular`, { method: "POST" });
    notificarAccion("Venta anulada y stock restituido");
    cargar();
  } catch (e) {
    mostrarToast(e.message, "error");
  }
}

document.getElementById("tbody").addEventListener("click", (e) => {
  const btn = e.target.closest(".btn-anular");
  if (btn) anular(Number(btn.dataset.id));
});

cargar();