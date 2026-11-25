

let sucursales = [];
const porPagina = 10;
let paginaActual = 1;

async function cargar() {
  document.getElementById("tbody").innerHTML = `<tr><td colspan="5">${bloqueCargando()}</td></tr>`;
  try {
    sucursales = await apiRequest("/api/sucursales");
  } catch (e) {
    document.getElementById("tbody").innerHTML =
      `<tr><td colspan="5">${bloqueError("No se pudo cargar el listado de sucursales.")}</td></tr>`;
    document.getElementById("sucMostrando").innerText = "Mostrando 0 de 0 registros";
    document.getElementById("paginacion").innerHTML = "";
    return;
  }
  renderTabla();
}

function renderPaginacionSucursales(total, pagina) {
  const contenedor = document.getElementById("paginacion");
  const etiqueta = document.getElementById("sucMostrando");
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
    <button type="button" class="suc-pag-btn ${activa ? 'activa' : ''}" data-pagina="${destino}"
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
  contenedor.querySelectorAll(".suc-pag-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      paginaActual = Number(btn.dataset.pagina);
      renderTabla();
    });
  });
}

function renderTabla() {
  const filtro = document.getElementById("buscador").value.toLowerCase().trim();
  const filtrados = sucursales.filter(s =>
    s.nombre.toLowerCase().includes(filtro) || (s.direccion || "").toLowerCase().includes(filtro)
  );

  const totalPaginas = Math.max(1, Math.ceil(filtrados.length / porPagina));
  if (paginaActual > totalPaginas) paginaActual = totalPaginas;
  const pagina = paginar(filtrados, paginaActual, porPagina);

  document.getElementById("tbody").innerHTML = pagina.map(s => `
    <tr class="suc-fila">
      <td class="suc-nombre"><i class="fa-solid fa-shop"></i>${escapeHtml(s.nombre)}</td>
      <td>${escapeHtml(s.direccion) || '-'}</td>
      <td>${escapeHtml(s.telefono) || '-'}</td>
      <td><span class="suc-badge-estado ${s.activo ? 'activa' : 'inactiva'}">${s.activo ? 'Activa' : 'Inactiva'}</span></td>
      <td class="suc-acciones">
        <button type="button" data-id="${s.id}" class="btn-editar suc-btn-accion editar" aria-label="Editar ${escapeHtml(s.nombre)}" title="Editar">
          <i class="fa-solid fa-pen"></i>
        </button>
        <button type="button" data-id="${s.id}" class="btn-eliminar suc-btn-accion eliminar" aria-label="Eliminar ${escapeHtml(s.nombre)}" title="Eliminar">
          <i class="fa-solid fa-trash"></i>
        </button>
      </td>
    </tr>`).join("") || `
      <tr><td colspan="5">
        <div class="suc-vacio"><i class="fa-solid fa-shop"></i><p>No se encontraron sucursales con esos criterios</p></div>
      </td></tr>`;

  renderPaginacionSucursales(filtrados.length, paginaActual);
}






const LIMA_CENTRO = [-12.0464, -77.0428];
let mapaSucursal = null;
let marcadoresBusqueda = [];
let marcadorSeleccionado = null;

function inicializarMapa() {
  if (mapaSucursal) return;
  mapaSucursal = L.map("mapaSucursal").setView(LIMA_CENTRO, 12);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    maxZoom: 19,
  }).addTo(mapaSucursal);
  
  
  
  
  
  
  mapaSucursal.on("click", alHacerClicEnMapa);
}




function iconoInkafarma(seleccionado = false) {
  return L.divIcon({
    className: "",
    html: `<div class="marcador-inkafarma${seleccionado ? " marcador-seleccionado" : ""}"><i class="fa-solid fa-shop"></i></div>`,
    iconSize: [30, 30],
    iconAnchor: [15, 30],
    popupAnchor: [0, -28],
  });
}

function limpiarMarcadoresBusqueda() {
  marcadoresBusqueda.forEach(m => mapaSucursal.removeLayer(m));
  marcadoresBusqueda = [];
}





function limpiarDireccion(displayName) {
  const partes = displayName.split(",").map(p => p.trim());
  if (partes.length > 1 && partes[0].toLowerCase().includes("inkafarma")) {
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

async function buscarEnNominatim(query) {
  try {
    const resp = await fetch(
      `https://nominatim.openstreetmap.org/search?format=json&limit=15&countrycodes=pe&q=${encodeURIComponent(query)}`
    );
    return await resp.json();
  } catch (e) {
    return [];
  }
}

function agregarMarcadorBusqueda(r) {
  const lat = parseFloat(r.lat), lon = parseFloat(r.lon);
  const nombreCorto = r.display_name.split(",")[0];

  const contenido = document.createElement("div");
  contenido.className = "text-xs";
  const titulo = document.createElement("b");
  titulo.textContent = nombreCorto;
  const direccion = document.createElement("p");
  direccion.className = "text-gray-500 my-1";
  direccion.textContent = r.display_name;
  const boton = document.createElement("button");
  boton.type = "button";
  boton.textContent = "Usar esta ubicación";
  boton.className = "btn-inka px-2 py-1 text-xs";
  boton.onclick = () => elegirUbicacion(lat, lon, r.display_name);
  contenido.append(titulo, direccion, boton);

  const marcador = L.marker([lat, lon], { icon: iconoInkafarma() }).addTo(mapaSucursal).bindPopup(contenido);
  marcadoresBusqueda.push(marcador);
}

async function buscarInkafarmaEnMapa() {
  inicializarMapa();
  const texto = document.getElementById("f_buscar_mapa").value.trim();
  if (!texto) {
    mostrarToast("Escribe una ciudad o zona para buscar", "error");
    return;
  }

  limpiarMarcadoresBusqueda();
  const encontrados = await buscarEnNominatim(`Inkafarma ${texto}`);
  if (encontrados.length) {
    encontrados.forEach(agregarMarcadorBusqueda);
    mapaSucursal.fitBounds(marcadoresBusqueda.map(m => m.getLatLng()), { padding: [30, 30] });
    return;
  }

  
  
  
  
  
  const zona = await buscarEnNominatim(texto);
  if (zona.length) {
    mapaSucursal.setView([parseFloat(zona[0].lat), parseFloat(zona[0].lon)], 16);
    mostrarToast(
      "No se encontró un Inkafarma con ese nombre en OpenStreetMap para esta zona. Acércate en el mapa y haz clic exactamente sobre el local para ubicarlo manualmente.",
      "error"
    );
  } else {
    mostrarToast("No se encontró esa ubicación. Intenta con otra ciudad o distrito.", "error");
  }
}

function elegirUbicacion(lat, lon, direccion) {
  fijarUbicacionSeleccionada(lat, lon, limpiarDireccion(direccion));
  mostrarToast("Ubicación asignada a la sucursal", "exito");
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
    mostrarToast("Ubicación asignada a la sucursal", "exito");
  } catch (err) {
    mostrarToast("Ubicación asignada (no se pudo autocompletar la dirección, escríbela manualmente)", "exito");
  }
}

function fijarUbicacionSeleccionada(lat, lon, direccion) {
  document.getElementById("f_latitud").value = lat;
  document.getElementById("f_longitud").value = lon;
  
  
  
  
  if (direccion) document.getElementById("f_direccion").value = direccion;
  if (marcadorSeleccionado) mapaSucursal.removeLayer(marcadorSeleccionado);
  marcadorSeleccionado = L.marker([lat, lon], { icon: iconoInkafarma(true) }).addTo(mapaSucursal).bindPopup("Ubicación seleccionada").openPopup();
  mapaSucursal.setView([lat, lon], 16);
  actualizarBadgeUbicacion(true);
}

function abrirModal(s = null) {
  document.getElementById("form").reset();
  document.getElementById("modalTitulo").innerText = s ? "Editar sucursal" : "Nueva sucursal";
  document.getElementById("f_id").value = s ? s.id : "";
  document.getElementById("f_nombre").value = s ? s.nombre : "";
  document.getElementById("f_direccion").value = s ? (s.direccion || "") : "";
  document.getElementById("f_telefono").value = s ? (s.telefono || "") : "";
  document.getElementById("f_buscar_mapa").value = "";
  document.getElementById("f_latitud").value = s && s.latitud != null ? s.latitud : "";
  document.getElementById("f_longitud").value = s && s.longitud != null ? s.longitud : "";
  actualizarBadgeUbicacion(!!(s && s.latitud != null && s.longitud != null));
  document.getElementById("modal").classList.remove("hidden");

  requestAnimationFrame(() => {
    inicializarMapa();
    mapaSucursal.invalidateSize();
    limpiarMarcadoresBusqueda();
    if (marcadorSeleccionado) { mapaSucursal.removeLayer(marcadorSeleccionado); marcadorSeleccionado = null; }
    if (s && s.latitud != null && s.longitud != null) {
      marcadorSeleccionado = L.marker([s.latitud, s.longitud], { icon: iconoInkafarma(true) }).addTo(mapaSucursal).bindPopup(s.nombre);
      mapaSucursal.setView([s.latitud, s.longitud], 16);
    } else {
      mapaSucursal.setView(LIMA_CENTRO, 12);
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
    direccion: document.getElementById("f_direccion").value,
    telefono: document.getElementById("f_telefono").value,
    latitud: lat ? parseFloat(lat) : null,
    longitud: lon ? parseFloat(lon) : null,
  };
  try {
    if (id) await apiRequest(`/api/sucursales/${id}`, { method: "PUT", body: payload });
    else await apiRequest("/api/sucursales", { method: "POST", body: payload });
    notificarAccion("Sucursal guardada correctamente");
    cerrarModal(); cargar();
  } catch (e) { mostrarToast(e.message, "error"); }
}

async function eliminar(id) {
  if (!(await confirmarAccion("¿Desactivar esta sucursal?"))) return;
  try {
    await apiRequest(`/api/sucursales/${id}`, { method: "DELETE" });
    notificarAccion("Sucursal desactivada");
    cargar();
  } catch (e) { mostrarToast(e.message, "error"); }
}

document.getElementById("tbody").addEventListener("click", (e) => {
  const btnEditar = e.target.closest(".btn-editar");
  if (btnEditar) return abrirModal(sucursales.find(s => s.id === Number(btnEditar.dataset.id)));
  const btnEliminar = e.target.closest(".btn-eliminar");
  if (btnEliminar) eliminar(Number(btnEliminar.dataset.id));
});

document.getElementById("f_buscar_mapa").addEventListener("keydown", (e) => {
  if (e.key === "Enter") { e.preventDefault(); buscarInkafarmaEnMapa(); }
});

cargar();