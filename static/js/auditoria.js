

let registros = [];
const porPagina = 15;
let paginaActual = 1;

const BADGE_ACCION = {
  crear: "badge-green",
  editar: "badge-gray",
  activar: "badge-green",
  desactivar: "badge-yellow",
  eliminar: "badge-red",
  anular: "badge-red",
};

async function cargar() {
  document.getElementById("tbody").innerHTML = filaCargando(5);
  try {
    registros = await apiRequest("/api/auditoria");
  } catch (e) {
    document.getElementById("tbody").innerHTML = filaError(5);
    mostrarToast(e.message, "error");
    return;
  }
  renderTabla();
}

function renderTabla() {
  const filtro = document.getElementById("buscador").value.toLowerCase();
  const filtrados = registros.filter(r =>
    r.usuario.toLowerCase().includes(filtro) ||
    r.entidad.toLowerCase().includes(filtro) ||
    (r.detalle || "").toLowerCase().includes(filtro)
  );

  const totalPaginas = Math.max(1, Math.ceil(filtrados.length / porPagina));
  if (paginaActual > totalPaginas) paginaActual = totalPaginas;
  const pagina = paginar(filtrados, paginaActual, porPagina);

  document.getElementById("tbody").innerHTML = pagina.map(r => `
    <tr>
      <td class="whitespace-nowrap text-xs text-gray-500">${formatearFecha(r.fecha)}</td>
      <td class="font-medium text-gray-700">${escapeHtml(r.usuario)}</td>
      <td><span class="badge ${BADGE_ACCION[r.accion] || 'badge-gray'}">${escapeHtml(r.accion)}</span></td>
      <td>${escapeHtml(r.entidad)}</td>
      <td class="text-gray-500 text-sm">${escapeHtml(r.detalle) || '-'}</td>
    </tr>`).join("") || `<tr><td colspan="5" class="text-center text-gray-400 py-6">Sin registros de auditoría</td></tr>`;

  renderPaginacion("paginacion", filtrados.length, paginaActual, porPagina, (p) => { paginaActual = p; renderTabla(); });
}

cargar();