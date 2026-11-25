

let promociones = [], medicamentos = [], sucursales = [];
const porPagina = 10;
let paginaActual = 1;

const NOMBRE_TIPO = {
  porcentaje: "% por producto",
  monto_fijo: "S/ por producto",
  nxm: "Lleva N, paga M",
  cupon: "Cupón",
};

async function cargar() {
  document.getElementById("tbody").innerHTML = filaCargando(7);
  try {
    [promociones, medicamentos, sucursales] = await Promise.all([
      apiRequest("/api/promociones"),
      apiRequest("/api/medicamentos"),
      apiRequest("/api/sucursales"),
    ]);
  } catch (e) {
    document.getElementById("tbody").innerHTML = filaError(7);
    mostrarToast(e.message, "error");
    return;
  }
  document.getElementById("f_medicamento").innerHTML = medicamentos.map(m => `<option value="${m.id}">${escapeHtml(m.nombre)}</option>`).join("");
  document.getElementById("f_sucursal").innerHTML = '<option value="">Todas las sucursales</option>' +
    sucursales.map(s => `<option value="${s.id}">${escapeHtml(s.nombre)}</option>`).join("");
  renderTabla();
}

function detalleTexto(p) {
  if (p.tipo === "porcentaje") return `${escapeHtml(p.medicamento)}: ${p.valor}% off`;
  if (p.tipo === "monto_fijo") return `${escapeHtml(p.medicamento)}: -${formatearMoneda(p.valor)}/u`;
  if (p.tipo === "nxm") return `${escapeHtml(p.medicamento)}: lleva ${p.lleva} paga ${p.paga}`;
  if (p.tipo === "cupon") return `Código "${escapeHtml(p.codigo)}": ${p.valor}% off boleta`;
  return "-";
}

function renderTabla() {
  const filtro = document.getElementById("buscador").value.toLowerCase();
  const filtrados = promociones.filter(p =>
    p.nombre.toLowerCase().includes(filtro) ||
    (p.medicamento || "").toLowerCase().includes(filtro) ||
    (p.codigo || "").toLowerCase().includes(filtro)
  );

  const totalPaginas = Math.max(1, Math.ceil(filtrados.length / porPagina));
  if (paginaActual > totalPaginas) paginaActual = totalPaginas;
  const pagina = paginar(filtrados, paginaActual, porPagina);

  document.getElementById("tbody").innerHTML = pagina.map(p => `
    <tr>
      <td class="font-medium text-gray-700"><i class="fa-solid fa-tag text-inka-green mr-1"></i>${escapeHtml(p.nombre)}</td>
      <td><span class="badge badge-yellow">${escapeHtml(NOMBRE_TIPO[p.tipo] || p.tipo)}</span></td>
      <td class="text-sm text-gray-600">${detalleTexto(p)}</td>
      <td class="text-xs text-gray-500">${formatearFecha(p.fecha_inicio)} - ${formatearFecha(p.fecha_fin)}</td>
      <td class="text-sm text-gray-600">${p.sucursal ? escapeHtml(p.sucursal) : 'Todas'}</td>
      <td>${!p.activo ? '<span class="badge badge-gray">Desactivada</span>' : (p.vigente ? '<span class="badge badge-green">Vigente</span>' : '<span class="badge badge-gray">Fuera de fecha</span>')}</td>
      <td class="whitespace-nowrap">
        <button data-id="${p.id}" class="btn-editar text-inka-green mr-2"><i class="fa-solid fa-pen"></i></button>
        <button data-id="${p.id}" class="btn-eliminar text-inka-red"><i class="fa-solid fa-trash"></i></button>
      </td>
    </tr>`).join("") || `<tr><td colspan="7" class="text-center text-gray-400 py-6">Sin promociones registradas</td></tr>`;

  renderPaginacion("paginacion", filtrados.length, paginaActual, porPagina, (p) => { paginaActual = p; renderTabla(); });
}

function alCambiarTipo() {
  const tipo = document.getElementById("f_tipo").value;
  document.querySelectorAll(".campo-producto").forEach(el => el.classList.toggle("hidden", tipo === "cupon"));
  document.querySelectorAll(".campo-valor").forEach(el => el.classList.toggle("hidden", tipo === "nxm"));
  document.querySelectorAll(".campo-nxm").forEach(el => el.classList.toggle("hidden", tipo !== "nxm"));
  document.querySelectorAll(".campo-cupon").forEach(el => el.classList.toggle("hidden", tipo !== "cupon"));

  const etiquetas = {
    porcentaje: "Porcentaje de descuento (%)",
    monto_fijo: "Descuento por unidad (S/)",
    cupon: "Porcentaje de descuento del cupón (%)",
  };
  document.getElementById("labelValor").innerText = etiquetas[tipo] || "Valor";
  document.getElementById("f_medicamento").required = tipo !== "cupon";
  document.getElementById("f_codigo").required = tipo === "cupon";
}

function abrirModal(p = null) {
  document.getElementById("form").reset();
  document.getElementById("modalTitulo").innerText = p ? "Editar promoción" : "Nueva promoción";
  document.getElementById("f_id").value = p ? p.id : "";
  document.getElementById("f_nombre").value = p ? p.nombre : "";
  document.getElementById("f_tipo").value = p ? p.tipo : "porcentaje";
  document.getElementById("f_medicamento").value = p ? p.medicamento_id : "";
  document.getElementById("f_valor").value = p && p.valor != null ? p.valor : "";
  document.getElementById("f_lleva").value = p && p.lleva != null ? p.lleva : "";
  document.getElementById("f_paga").value = p && p.paga != null ? p.paga : "";
  document.getElementById("f_codigo").value = p ? (p.codigo || "") : "";
  document.getElementById("f_fecha_inicio").value = p ? p.fecha_inicio : "";
  document.getElementById("f_fecha_fin").value = p ? p.fecha_fin : "";
  document.getElementById("f_sucursal").value = p && p.sucursal_id ? p.sucursal_id : "";
  alCambiarTipo();
  document.getElementById("modal").classList.remove("hidden");
}
function cerrarModal() { document.getElementById("modal").classList.add("hidden"); }

async function guardar(e) {
  e.preventDefault();
  const id = document.getElementById("f_id").value;
  const payload = {
    nombre: document.getElementById("f_nombre").value,
    tipo: document.getElementById("f_tipo").value,
    medicamento_id: document.getElementById("f_medicamento").value ? parseInt(document.getElementById("f_medicamento").value) : null,
    valor: document.getElementById("f_valor").value ? parseFloat(document.getElementById("f_valor").value) : null,
    lleva: document.getElementById("f_lleva").value ? parseInt(document.getElementById("f_lleva").value) : null,
    paga: document.getElementById("f_paga").value ? parseInt(document.getElementById("f_paga").value) : null,
    codigo: document.getElementById("f_codigo").value,
    fecha_inicio: document.getElementById("f_fecha_inicio").value,
    fecha_fin: document.getElementById("f_fecha_fin").value,
    sucursal_id: document.getElementById("f_sucursal").value ? parseInt(document.getElementById("f_sucursal").value) : null,
  };
  try {
    if (id) await apiRequest(`/api/promociones/${id}`, { method: "PUT", body: payload });
    else await apiRequest("/api/promociones", { method: "POST", body: payload });
    notificarAccion("Promoción guardada correctamente");
    cerrarModal(); cargar();
  } catch (e) { mostrarToast(e.message, "error"); }
}

async function eliminar(id) {
  if (!(await confirmarAccion("¿Desactivar esta promoción?"))) return;
  try {
    await apiRequest(`/api/promociones/${id}`, { method: "DELETE" });
    notificarAccion("Promoción desactivada");
    cargar();
  } catch (e) { mostrarToast(e.message, "error"); }
}

document.getElementById("tbody").addEventListener("click", (e) => {
  const btnEditar = e.target.closest(".btn-editar");
  if (btnEditar) return abrirModal(promociones.find(p => p.id === Number(btnEditar.dataset.id)));
  const btnEliminar = e.target.closest(".btn-eliminar");
  if (btnEliminar) eliminar(Number(btnEliminar.dataset.id));
});

cargar();