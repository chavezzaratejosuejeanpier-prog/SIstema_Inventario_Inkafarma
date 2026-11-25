

let lotes = [], medicamentos = [], sucursales = [];
const porPagina = 10;
let paginaActual = 1;


function clasificarLote(l) {
  const dias = Number(l.dias_para_vencer);
  if (dias < 0) return { clave: "vencidos", texto: "Vencido", icono: "fa-triangle-exclamation" };
  if (dias <= 30) {
    return {
      clave: "proximos",
      texto: dias === 0 ? "Vence hoy" : `Vence en ${dias} días`,
      icono: "fa-clock",
    };
  }
  return { clave: "vigentes", texto: "Vigente", icono: "fa-circle-check" };
}

function actualizarKpis() {
  const conteo = { vigentes: 0, proximos: 0, vencidos: 0 };
  lotes.forEach(l => { conteo[clasificarLote(l).clave] += 1; });
  const ids = { vigentes: "kpiVigentes", proximos: "kpiPorVencer", vencidos: "kVencidos" };
  Object.keys(ids).forEach(clave => {
    const elemento = document.getElementById(ids[clave]);
    elemento.innerText = conteo[clave];
    elemento.classList.remove("cargando");
  });
}

function renderPaginacionLotes(total, pagina) {
  const contenedor = document.getElementById("paginacion");
  const etiqueta = document.getElementById("lotMostrando");
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
    <button type="button" class="lot-pag-btn ${activa ? 'activa' : ''}" data-pagina="${destino}"
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
  contenedor.querySelectorAll(".lot-pag-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      paginaActual = Number(btn.dataset.pagina);
      renderTabla();
    });
  });
}

async function cargar() {
  document.getElementById("tbody").innerHTML = `<tr><td colspan="9">${bloqueCargando()}</td></tr>`;
  try {
    [lotes, medicamentos, sucursales] = await Promise.all([
      apiRequest("/api/lotes"), apiRequest("/api/medicamentos"), apiRequest("/api/sucursales"),
    ]);
  } catch (e) {
    ["kpiVigentes", "kpiPorVencer", "kVencidos"].forEach(id => {
      document.getElementById(id).innerText = "—";
      document.getElementById(id).classList.remove("cargando");
    });
    document.getElementById("tbody").innerHTML = `
      <tr><td colspan="9">
        <div class="lot-vacio">
          <i class="fa-solid fa-triangle-exclamation"></i>
          <p>No se pudo cargar el inventario de lotes.</p>
          <button type="button" class="lot-reintentar" onclick="cargar()">Reintentar</button>
        </div>
      </td></tr>`;
    document.getElementById("lotMostrando").innerText = "Mostrando 0 de 0 registros";
    document.getElementById("paginacion").innerHTML = "";
    return;
  }
  document.getElementById("f_medicamento").innerHTML = medicamentos.map(m => `<option value="${m.id}">${escapeHtml(m.nombre)} (${escapeHtml(m.codigo)})</option>`).join("");
  document.getElementById("f_sucursal").innerHTML = sucursales.map(s => `<option value="${s.id}">${escapeHtml(s.nombre)}</option>`).join("");
  document.getElementById("filtroSucursal").innerHTML = '<option value="">Todas las sucursales</option>' +
    sucursales.map(s => `<option value="${s.id}">${escapeHtml(s.nombre)}</option>`).join("");
  actualizarKpis();
  renderTabla();
}

function renderTabla() {
  const filtro = document.getElementById("buscador").value.toLowerCase().trim();
  const sucursalFiltro = document.getElementById("filtroSucursal").value;
  const vencimientoFiltro = document.getElementById("filtroVencimiento").value;
  const filtrados = lotes.filter(l => {
    const coincideTexto = l.medicamento.toLowerCase().includes(filtro) || l.numero_lote.toLowerCase().includes(filtro);
    const coincideSucursal = !sucursalFiltro || l.sucursal_id === parseInt(sucursalFiltro);
    const coincideVencimiento = !vencimientoFiltro || vencimientoFiltro === clasificarLote(l).clave;
    return coincideTexto && coincideSucursal && coincideVencimiento;
  });

  const totalPaginas = Math.max(1, Math.ceil(filtrados.length / porPagina));
  if (paginaActual > totalPaginas) paginaActual = totalPaginas;
  const pagina = paginar(filtrados, paginaActual, porPagina);

  const vacio = lotes.length === 0
    ? "Aún no hay lotes registrados"
    : "No se encontraron lotes con esos criterios";

  document.getElementById("tbody").innerHTML = pagina.map(l => {
    const estado = clasificarLote(l);
    const filaClase = estado.clave === "vencidos" ? "fila-vencida" : (estado.clave === "proximos" ? "fila-por-vencer" : "");
    return `
    <tr class="lot-fila ${filaClase}">
      <td class="lot-medicamento">${escapeHtml(l.medicamento)}</td>
      <td class="lot-codigo">${escapeHtml(l.numero_lote)}</td>
      <td>${escapeHtml(l.sucursal) || '-'}</td>
      <td class="lot-fecha">${formatearFecha(l.fecha_vencimiento)}</td>
      <td><span class="lot-badge ${estado.clave}"><i class="fa-solid ${estado.icono}"></i>${estado.texto}</span></td>
      <td class="lot-cantidad">${l.cantidad_inicial}</td>
      <td class="lot-cantidad">${l.cantidad_actual}</td>
      <td class="lot-precio">${formatearMoneda(l.precio_compra_unitario)}</td>
      <td class="lot-acciones">
        <button type="button" data-id="${l.id}" class="btn-editar lot-btn-accion editar" title="Editar lote" aria-label="Editar lote"><i class="fa-solid fa-pen"></i></button>
        <button type="button" data-id="${l.id}" class="btn-eliminar lot-btn-accion eliminar" title="Eliminar lote" aria-label="Eliminar lote"><i class="fa-solid fa-trash"></i></button>
      </td>
    </tr>`;
  }).join("") || `
    <tr><td colspan="9">
      <div class="lot-vacio"><i class="fa-solid fa-boxes-stacked"></i><p>${vacio}</p></div>
    </td></tr>`;

  renderPaginacionLotes(filtrados.length, paginaActual);
}

function abrirModal(l = null) {
  document.getElementById("form").reset();
  document.getElementById("modalTitulo").innerText = l ? "Editar lote" : "Nuevo lote";
  document.getElementById("f_id").value = l ? l.id : "";
  document.getElementById("f_medicamento").value = l ? l.medicamento_id : "";
  document.getElementById("f_medicamento").disabled = !!l;
  document.getElementById("f_sucursal").value = l ? l.sucursal_id : (sucursales[0] ? sucursales[0].id : "");
  document.getElementById("f_sucursal").disabled = !!l;
  document.getElementById("f_numero").value = l ? l.numero_lote : "";
  document.getElementById("f_vencimiento").value = l ? l.fecha_vencimiento : "";
  document.getElementById("labelCantidad").innerText = l ? "Cantidad actual" : "Cantidad inicial";
  document.getElementById("f_cantidad").value = l ? l.cantidad_actual : "";
  document.getElementById("f_precio").value = l ? l.precio_compra_unitario : "";
  document.getElementById("modal").classList.remove("hidden");
}
function cerrarModal() { document.getElementById("modal").classList.add("hidden"); }

async function guardar(e) {
  e.preventDefault();
  const id = document.getElementById("f_id").value;
  const cantidad = parseInt(document.getElementById("f_cantidad").value);
  try {
    if (id) {
      await apiRequest(`/api/lotes/${id}`, { method: "PUT", body: {
        numero_lote: document.getElementById("f_numero").value,
        fecha_vencimiento: document.getElementById("f_vencimiento").value,
        cantidad_actual: cantidad,
        precio_compra_unitario: parseFloat(document.getElementById("f_precio").value),
      }});
      notificarAccion("Lote actualizado correctamente");
    } else {
      await apiRequest("/api/lotes", { method: "POST", body: {
        medicamento_id: parseInt(document.getElementById("f_medicamento").value),
        sucursal_id: parseInt(document.getElementById("f_sucursal").value),
        numero_lote: document.getElementById("f_numero").value,
        fecha_vencimiento: document.getElementById("f_vencimiento").value,
        cantidad_inicial: cantidad,
        precio_compra_unitario: parseFloat(document.getElementById("f_precio").value),
      }});
      notificarAccion("Lote registrado correctamente");
    }
    cerrarModal(); cargar();
  } catch (e) { mostrarToast(e.message, "error"); }
}

async function eliminar(id) {
  if (!(await confirmarAccion("¿Eliminar este lote?"))) return;
  try {
    await apiRequest(`/api/lotes/${id}`, { method: "DELETE" });
    notificarAccion("Lote eliminado"); cargar();
  } catch (e) { mostrarToast(e.message, "error"); }
}

document.getElementById("tbody").addEventListener("click", (e) => {
  const btnEditar = e.target.closest(".btn-editar");
  if (btnEditar) return abrirModal(lotes.find(l => l.id === Number(btnEditar.dataset.id)));
  const btnEliminar = e.target.closest(".btn-eliminar");
  if (btnEliminar) eliminar(Number(btnEliminar.dataset.id));
});

cargar();
