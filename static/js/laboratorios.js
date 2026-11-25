

let laboratorios = [];
const porPagina = 10;
let paginaActual = 1;

async function cargar() {
  document.getElementById("tbody").innerHTML = `<tr><td colspan="7">${bloqueCargando()}</td></tr>`;
  try {
    laboratorios = await apiRequest("/api/laboratorios");
  } catch (e) {
    document.getElementById("tbody").innerHTML =
      `<tr><td colspan="7">${bloqueError("No se pudo cargar el listado de laboratorios.")}</td></tr>`;
    document.getElementById("labMostrando").innerText = "Mostrando 0 de 0 registros";
    document.getElementById("paginacion").innerHTML = "";
    return;
  }
  renderTabla();
}

function renderPaginacionLaboratorios(total, pagina) {
  const contenedor = document.getElementById("paginacion");
  const etiqueta = document.getElementById("labMostrando");
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
    <button type="button" class="lab-pag-btn ${activa ? 'activa' : ''}" data-pagina="${destino}"
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
  contenedor.querySelectorAll(".lab-pag-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      paginaActual = Number(btn.dataset.pagina);
      renderTabla();
    });
  });
}

function renderTabla() {
  const filtro = document.getElementById("buscador").value.toLowerCase().trim();
  const filtrados = laboratorios.filter(l =>
    l.nombre.toLowerCase().includes(filtro) ||
    (l.ruc || "").toLowerCase().includes(filtro) ||
    (l.email || "").toLowerCase().includes(filtro)
  );

  const totalPaginas = Math.max(1, Math.ceil(filtrados.length / porPagina));
  if (paginaActual > totalPaginas) paginaActual = totalPaginas;
  const pagina = paginar(filtrados, paginaActual, porPagina);

  const vacio = laboratorios.length === 0
    ? "Aún no hay laboratorios registrados"
    : "No se encontraron laboratorios con esos criterios";

  document.getElementById("tbody").innerHTML = pagina.map(l => {
    const correo = l.email || '-';
    return `
    <tr class="lab-fila">
      <td class="lab-nombre"><i class="fa-solid fa-industry"></i>${escapeHtml(l.nombre)}</td>
      <td>${escapeHtml(l.ruc) || '-'}</td>
      <td>${escapeHtml(l.telefono) || '-'}</td>
      <td class="lab-email" title="${escapeHtml(correo)}">${escapeHtml(correo)}</td>
      <td>${escapeHtml(l.direccion) || '-'}</td>
      <td><span class="lab-badge-estado ${l.activo ? 'activo' : 'inactivo'}"><i class="lab-punto"></i>${l.activo ? 'Activo' : 'Inactivo'}</span></td>
      <td class="lab-acciones">
        <button type="button" data-id="${l.id}" class="btn-editar lab-btn-accion editar" title="Editar laboratorio" aria-label="Editar laboratorio">
          <i class="fa-solid fa-pen"></i>
        </button>
        <button type="button" data-id="${l.id}" class="btn-eliminar lab-btn-accion eliminar" title="Eliminar laboratorio" aria-label="Eliminar laboratorio">
          <i class="fa-solid fa-trash"></i>
        </button>
      </td>
    </tr>`;
  }).join("") || `
    <tr><td colspan="7">
      <div class="lab-vacio"><i class="fa-solid fa-flask"></i><p>${vacio}</p></div>
    </td></tr>`;

  renderPaginacionLaboratorios(filtrados.length, paginaActual);
}







const LIMA_CENTRO = [-12.0464, -77.0428];
let mapaLaboratorio = null;
let marcadorSeleccionado = null;

function inicializarMapa() {
  if (mapaLaboratorio) return;
  mapaLaboratorio = L.map("mapaLaboratorio").setView(LIMA_CENTRO, 12);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    maxZoom: 19,
  }).addTo(mapaLaboratorio);
  mapaLaboratorio.on("click", alHacerClicEnMapa);
}

function iconoLaboratorio() {
  return L.divIcon({
    className: "",
    html: '<div class="marcador-laboratorio"><i class="fa-solid fa-industry"></i></div>',
    iconSize: [30, 30],
    iconAnchor: [15, 30],
    popupAnchor: [0, -28],
  });
}





function limpiarDireccion(displayName) {
  const nombre = (document.getElementById("f_nombre").value || "").trim().toLowerCase();
  const partes = displayName.split(",").map(p => p.trim());
  if (nombre && partes.length > 1 && partes[0].toLowerCase().includes(nombre)) {
    return partes.slice(1).join(", ");
  }
  return displayName;
}

function actualizarBadgeUbicacion(tieneUbicacion) {
  const badge = document.getElementById("badgeUbicacion");
  if (tieneUbicacion) {
    badge.className = "badge badge-green";
    badge.innerHTML = '<i class="fa-solid fa-circle-check mr-1"></i>Ubicado';
  } else {
    badge.className = "badge badge-gray";
    badge.innerHTML = '<i class="fa-solid fa-circle-question mr-1"></i>Sin ubicar';
  }
}

async function alHacerClicEnMapa(e) {
  const { lat, lng } = e.latlng;
  fijarUbicacionSeleccionada(lat, lng, null);

  try {
    const resp = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=18`
    );
    const resultado = await resp.json();
    if (resultado && resultado.display_name) {
      document.getElementById("f_direccion").value = limpiarDireccion(resultado.display_name);
    }
    mostrarToast("Ubicación asignada al laboratorio", "exito");
  } catch (err) {
    mostrarToast("Ubicación asignada (no se pudo autocompletar la dirección, escríbela manualmente)", "exito");
  }
}

function fijarUbicacionSeleccionada(lat, lon) {
  document.getElementById("f_latitud").value = lat;
  document.getElementById("f_longitud").value = lon;
  if (marcadorSeleccionado) mapaLaboratorio.removeLayer(marcadorSeleccionado);
  marcadorSeleccionado = L.marker([lat, lon], { icon: iconoLaboratorio() }).addTo(mapaLaboratorio).bindPopup("Ubicación seleccionada").openPopup();
  mapaLaboratorio.setView([lat, lon], 16);
  actualizarBadgeUbicacion(true);
}

function abrirModal(l = null) {
  document.getElementById("form").reset();
  document.getElementById("modalTitulo").innerText = l ? "Editar laboratorio" : "Nuevo laboratorio";
  document.getElementById("f_id").value = l ? l.id : "";
  document.getElementById("f_nombre").value = l ? l.nombre : "";
  document.getElementById("f_ruc").value = l ? (l.ruc || "") : "";
  document.getElementById("f_telefono").value = l ? (l.telefono || "") : "";
  document.getElementById("f_email").value = l ? (l.email || "") : "";
  document.getElementById("f_direccion").value = l ? (l.direccion || "") : "";
  document.getElementById("f_latitud").value = l && l.latitud != null ? l.latitud : "";
  document.getElementById("f_longitud").value = l && l.longitud != null ? l.longitud : "";
  actualizarBadgeUbicacion(!!(l && l.latitud != null && l.longitud != null));
  document.getElementById("modal").classList.remove("hidden");

  requestAnimationFrame(() => {
    inicializarMapa();
    mapaLaboratorio.invalidateSize();
    if (marcadorSeleccionado) { mapaLaboratorio.removeLayer(marcadorSeleccionado); marcadorSeleccionado = null; }
    if (l && l.latitud != null && l.longitud != null) {
      marcadorSeleccionado = L.marker([l.latitud, l.longitud], { icon: iconoLaboratorio() }).addTo(mapaLaboratorio).bindPopup(l.nombre);
      mapaLaboratorio.setView([l.latitud, l.longitud], 16);
    } else {
      mapaLaboratorio.setView(LIMA_CENTRO, 12);
    }
  });
}
function cerrarModal() { document.getElementById("modal").classList.add("hidden"); }

async function guardar(e) {
  e.preventDefault();
  const id = document.getElementById("f_id").value;
  const lat = document.getElementById("f_latitud").value;
  const lon = document.getElementById("f_longitud").value;
  const payload = {
    nombre: document.getElementById("f_nombre").value,
    ruc: document.getElementById("f_ruc").value,
    telefono: document.getElementById("f_telefono").value,
    email: document.getElementById("f_email").value,
    direccion: document.getElementById("f_direccion").value,
    latitud: lat ? parseFloat(lat) : null,
    longitud: lon ? parseFloat(lon) : null,
  };
  try {
    if (id) await apiRequest(`/api/laboratorios/${id}`, { method: "PUT", body: payload });
    else await apiRequest("/api/laboratorios", { method: "POST", body: payload });
    notificarAccion("Laboratorio guardado correctamente");
    cerrarModal(); cargar();
  } catch (e) { mostrarToast(e.message, "error"); }
}

async function eliminar(id) {
  if (!(await confirmarAccion("¿Desactivar este laboratorio?"))) return;
  try {
    await apiRequest(`/api/laboratorios/${id}`, { method: "DELETE" });
    notificarAccion("Laboratorio desactivado"); cargar();
  } catch (e) { mostrarToast(e.message, "error"); }
}

document.getElementById("tbody").addEventListener("click", (e) => {
  const btnEditar = e.target.closest(".btn-editar");
  if (btnEditar) return abrirModal(laboratorios.find(l => l.id === Number(btnEditar.dataset.id)));
  const btnEliminar = e.target.closest(".btn-eliminar");
  if (btnEliminar) eliminar(Number(btnEliminar.dataset.id));
});

cargar();
