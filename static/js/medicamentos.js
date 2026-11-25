

let medicamentos = [], laboratorios = [];
const puedeEditar = document.body.dataset.usuarioRol === "Administrador";
const porPagina = 10;
let paginaActual = 1;

function esStockBajo(m) {
  return Number(m.stock_total) <= Number(m.stock_minimo);
}

function limpiarMenus() {
  document.querySelectorAll(".med-menu").forEach(menu => menu.classList.add("hidden"));
  document.querySelectorAll(".med-menu-btn").forEach(btn => btn.setAttribute("aria-expanded", "false"));
}

function alternarMenu(btn) {
  const menu = document.getElementById("med-menu-" + btn.dataset.id);
  if (!menu) return;
  const estabaAbierto = !menu.classList.contains("hidden");
  limpiarMenus();
  if (!estabaAbierto) {
    menu.classList.remove("hidden");
    btn.setAttribute("aria-expanded", "true");
    const primerItem = menu.querySelector("button");
    if (primerItem) primerItem.focus();
  }
}

function renderPaginacionMedicamentos(total, pagina) {
  const contenedor = document.getElementById("paginacion");
  const etiqueta = document.getElementById("medMostrando");
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
    <button type="button" class="med-pag-btn ${activa ? 'activa' : ''}" data-pagina="${destino}"
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
  contenedor.querySelectorAll(".med-pag-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      paginaActual = Number(btn.dataset.pagina);
      renderTabla();
    });
  });
}

function aplicarFiltros() {
  const texto = document.getElementById("buscador").value.toLowerCase().trim();
  const categoria = document.getElementById("filtroCategoria").value;
  const laboratorio = document.getElementById("filtroLaboratorio").value;
  const estado = document.getElementById("filtroEstado").value;

  return medicamentos.filter(m => {
    const coincideTexto = !texto || m.nombre.toLowerCase().includes(texto) || m.codigo.toLowerCase().includes(texto);
    const coincideCategoria = !categoria || m.categoria === categoria;
    const coincideLaboratorio = !laboratorio || String(m.laboratorio_id) === laboratorio;
    let coincideEstado = true;
    if (estado === "Disponible") coincideEstado = !esStockBajo(m);
    else if (estado === "Stock bajo") coincideEstado = esStockBajo(m);
    else if (estado === "Activo") coincideEstado = !!m.activo;
    else if (estado === "Inactivo") coincideEstado = !m.activo;
    return coincideTexto && coincideCategoria && coincideLaboratorio && coincideEstado;
  });
}

function limpiarFiltros() {
  document.getElementById("buscador").value = "";
  document.getElementById("filtroCategoria").value = "";
  document.getElementById("filtroLaboratorio").value = "";
  document.getElementById("filtroEstado").value = "";
  paginaActual = 1;
  renderTabla();
}

function renderTabla() {
  const colspan = puedeEditar ? 8 : 7;
  const filtrados = aplicarFiltros();
  const totalPaginas = Math.max(1, Math.ceil(filtrados.length / porPagina));
  if (paginaActual > totalPaginas) paginaActual = totalPaginas;
  const pagina = paginar(filtrados, paginaActual, porPagina);

  document.getElementById("tbody").innerHTML = pagina.map(m => {
    const bajo = esStockBajo(m);
    const receta = m.requiere_receta ? '<span class="med-badge-receta">Receta</span>' : '';
    const acciones = puedeEditar ? `
      <td>
        <div class="med-acciones-celda">
          <button type="button" class="med-menu-btn" data-id="${m.id}" aria-haspopup="true" aria-expanded="false"
                  aria-label="Acciones para ${escapeHtml(m.nombre)}" aria-controls="med-menu-${m.id}">
            <i class="fa-solid fa-ellipsis-vertical"></i>
          </button>
          <div class="med-menu hidden" id="med-menu-${m.id}" role="menu">
            <button type="button" class="med-menu-item med-menu-item-editar" data-id="${m.id}" role="menuitem">
              <i class="fa-solid fa-pen"></i> Editar
            </button>
            ${m.activo ? `<button type="button" class="med-menu-item peligro med-menu-item-desactivar" data-id="${m.id}" role="menuitem">
              <i class="fa-solid fa-trash"></i> Desactivar
            </button>` : ''}
          </div>
        </div>
      </td>` : '';

    return `<tr>
      <td class="med-codigo">${escapeHtml(m.codigo)}</td>
      <td><span class="med-nombre">${escapeHtml(m.nombre)}</span>${receta}</td>
      <td>${escapeHtml(m.laboratorio) || '-'}</td>
      <td>${escapeHtml(m.categoria) || '-'}</td>
      <td class="med-precio">${formatearMoneda(m.precio_venta)}</td>
      <td><span class="med-badge-stock ${bajo ? 'bajo' : 'ok'}">${m.stock_total}</span></td>
      <td>
        <div class="med-estado">
          <span class="med-badge-estado ${bajo ? 'stock-bajo' : 'disponible'}">
            <i class="fa-solid ${bajo ? 'fa-triangle-exclamation' : 'fa-circle-check'}"></i>
            ${bajo ? 'Stock bajo' : 'Disponible'}
          </span>
          <span class="med-estado-admin">${m.activo ? 'Activo' : 'Inactivo'}</span>
        </div>
      </td>
      ${acciones}
    </tr>`;
  }).join("") || `<tr><td colspan="${colspan}" class="med-vacio">Sin resultados para los filtros seleccionados.</td></tr>`;

  renderPaginacionMedicamentos(filtrados.length, paginaActual);
}

async function cargar() {
  const colspan = puedeEditar ? 8 : 7;
  document.getElementById("tbody").innerHTML = filaCargando(colspan);
  try {
    [medicamentos, laboratorios] = await Promise.all([
      apiRequest("/api/medicamentos"),
      apiRequest("/api/laboratorios"),
    ]);
  } catch (e) {
    document.getElementById("tbody").innerHTML = filaError(colspan);
    mostrarToast(e.message, "error");
    return;
  }

  document.getElementById("f_laboratorio").innerHTML = laboratorios.map(l => `<option value="${l.id}">${escapeHtml(l.nombre)}</option>`).join("");
  document.getElementById("filtroLaboratorio").innerHTML = '<option value="">Todos los laboratorios</option>' +
    laboratorios.map(l => `<option value="${l.id}">${escapeHtml(l.nombre)}</option>`).join("");

  const categorias = [...new Set(medicamentos.map(m => m.categoria).filter(Boolean))].sort();
  document.getElementById("filtroCategoria").innerHTML = '<option value="">Todas las categorías</option>' +
    categorias.map(c => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`).join("");

  document.getElementById("contadorMedicamentos").innerText =
    `${medicamentos.length} ${medicamentos.length === 1 ? 'medicamento' : 'medicamentos'}`;

  renderTabla();
}

function abrirModal(m = null) {
  document.getElementById("form").reset();
  document.getElementById("modalTitulo").innerText = m ? "Editar medicamento" : "Nuevo medicamento";
  document.getElementById("f_id").value = m ? m.id : "";
  document.getElementById("f_codigo").value = m ? m.codigo : "";
  document.getElementById("f_codigo").disabled = !!m;
  document.getElementById("f_nombre").value = m ? m.nombre : "";
  document.getElementById("f_laboratorio").value = m ? m.laboratorio_id : "";
  document.getElementById("f_categoria").value = m ? (m.categoria || "") : "";
  document.getElementById("f_presentacion").value = m ? (m.presentacion || "") : "";
  document.getElementById("f_precio_compra").value = m ? m.precio_compra : "";
  document.getElementById("f_precio_venta").value = m ? m.precio_venta : "";
  document.getElementById("f_stock_minimo").value = m ? m.stock_minimo : 10;
  document.getElementById("f_receta").checked = m ? m.requiere_receta : false;
  document.getElementById("modal").classList.remove("hidden");
}
function cerrarModal() { document.getElementById("modal").classList.add("hidden"); }

async function guardar(e) {
  e.preventDefault();
  const id = document.getElementById("f_id").value;
  const payload = {
    codigo: document.getElementById("f_codigo").value,
    nombre: document.getElementById("f_nombre").value,
    laboratorio_id: parseInt(document.getElementById("f_laboratorio").value),
    categoria: document.getElementById("f_categoria").value,
    presentacion: document.getElementById("f_presentacion").value,
    precio_compra: parseFloat(document.getElementById("f_precio_compra").value),
    precio_venta: parseFloat(document.getElementById("f_precio_venta").value),
    stock_minimo: parseInt(document.getElementById("f_stock_minimo").value),
    requiere_receta: document.getElementById("f_receta").checked,
  };
  try {
    if (id) await apiRequest(`/api/medicamentos/${id}`, { method: "PUT", body: payload });
    else await apiRequest("/api/medicamentos", { method: "POST", body: payload });
    notificarAccion("Medicamento guardado correctamente");
    cerrarModal();
    cargar();
  } catch (e) { mostrarToast(e.message, "error"); }
}

async function eliminar(id) {
  if (!(await confirmarAccion("¿Desactivar este medicamento?"))) return;
  try {
    await apiRequest(`/api/medicamentos/${id}`, { method: "DELETE" });
    notificarAccion("Medicamento desactivado");
    cargar();
  } catch (e) { mostrarToast(e.message, "error"); }
}

document.getElementById("tbody").addEventListener("click", (e) => {
  const btnMenu = e.target.closest(".med-menu-btn");
  if (btnMenu) { alternarMenu(btnMenu); return; }

  const btnEditar = e.target.closest(".med-menu-item-editar");
  if (btnEditar) {
    limpiarMenus();
    abrirModal(medicamentos.find(m => m.id === Number(btnEditar.dataset.id)));
    return;
  }

  const btnDesactivar = e.target.closest(".med-menu-item-desactivar");
  if (btnDesactivar) {
    limpiarMenus();
    eliminar(Number(btnDesactivar.dataset.id));
  }
});

document.addEventListener("click", (e) => {
  if (!e.target.closest(".med-acciones-celda")) limpiarMenus();
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") limpiarMenus();
});

cargar();
