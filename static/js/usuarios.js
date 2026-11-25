

let usuarios = [], roles = [], sucursales = [];
const porPagina = 10;
let paginaActual = 1;
const usuarioIdActual = Number(document.body.dataset.usuarioId);

async function cargar() {
  document.getElementById("tbody").innerHTML = filaCargando(6);
  try {
    [usuarios, roles, sucursales] = await Promise.all([
      apiRequest("/api/usuarios"), apiRequest("/api/usuarios/roles"), apiRequest("/api/sucursales"),
    ]);
  } catch (e) {
    document.getElementById("tbody").innerHTML = filaError(6);
    mostrarToast(e.message, "error");
    return;
  }
  document.getElementById("f_rol").innerHTML = roles.map(r => `<option value="${r.id}">${escapeHtml(r.nombre)}</option>`).join("");
  document.getElementById("f_sucursal").innerHTML = '<option value="">Sin asignar (ve todas las sucursales)</option>' +
    sucursales.map(s => `<option value="${s.id}">${escapeHtml(s.nombre)}</option>`).join("");
  renderTabla();
}

function alCambiarRol() {
  const opt = document.getElementById("f_rol").selectedOptions[0];
  const esCajero = opt && opt.textContent.trim() === "Cajero";
  document.getElementById("f_sucursal").required = !!esCajero;
}

function renderTabla() {
  const filtro = document.getElementById("buscador").value.toLowerCase();
  const filtrados = usuarios.filter(u => u.nombre.toLowerCase().includes(filtro) || u.email.toLowerCase().includes(filtro));

  const totalPaginas = Math.max(1, Math.ceil(filtrados.length / porPagina));
  if (paginaActual > totalPaginas) paginaActual = totalPaginas;
  const pagina = paginar(filtrados, paginaActual, porPagina);

  document.getElementById("tbody").innerHTML = pagina.map(u => {
    const esUno_mismo = u.id === usuarioIdActual;
    const tituloToggle = u.activo ? "Desactivar usuario" : "Activar usuario";
    const iconoToggle = u.activo ? "fa-toggle-on" : "fa-toggle-off";
    const inicial = (u.nombre || "?").trim().charAt(0).toUpperCase();
    return `
    <tr>
      <td class="font-medium text-gray-700">
        <div class="flex items-center gap-2.5">
          <div class="w-8 h-8 rounded-full bg-inka-green-light flex items-center justify-center text-inka-green font-bold text-xs shrink-0">${escapeHtml(inicial)}</div>
          ${escapeHtml(u.nombre)}
        </div>
      </td>
      <td>${escapeHtml(u.email)}</td>
      <td><span class="badge ${u.rol === 'Administrador' ? 'badge-rol-administrador' : 'badge-rol-cajero'}">${escapeHtml(u.rol)}</span></td>
      <td class="text-sm text-gray-600">${u.sucursal ? escapeHtml(u.sucursal) : '<span class="text-gray-400">Todas</span>'}</td>
      <td>${u.activo ? '<span class="badge badge-green">Activo</span>' : '<span class="badge badge-gray">Inactivo</span>'}</td>
      <td class="whitespace-nowrap">
        <button data-id="${u.id}" class="btn-editar text-inka-green mr-2" title="Editar"><i class="fa-solid fa-pen"></i></button>
        <button data-id="${u.id}" class="btn-toggle mr-2 ${u.activo ? 'text-inka-yellow' : 'text-gray-400'}"
          title="${tituloToggle}" ${esUno_mismo ? "disabled" : ""}><i class="fa-solid ${iconoToggle}"></i></button>
        <button data-id="${u.id}" class="btn-eliminar text-inka-red" title="Eliminar" ${esUno_mismo ? "disabled" : ""}><i class="fa-solid fa-trash"></i></button>
      </td>
    </tr>`;
  }).join("") || `<tr><td colspan="6" class="text-center text-gray-400 py-6">Sin usuarios</td></tr>`;

  renderPaginacion("paginacion", filtrados.length, paginaActual, porPagina, (p) => { paginaActual = p; renderTabla(); });
}

function abrirModal(u = null) {
  document.getElementById("form").reset();
  document.getElementById("modalTitulo").innerText = u ? "Editar usuario" : "Nuevo usuario";
  document.getElementById("f_id").value = u ? u.id : "";
  document.getElementById("f_nombre").value = u ? u.nombre : "";
  document.getElementById("f_email").value = u ? u.email : "";
  document.getElementById("f_email").disabled = !!u;
  document.getElementById("f_rol").value = u ? u.rol_id : "";
  document.getElementById("f_sucursal").value = u && u.sucursal_id ? u.sucursal_id : "";
  document.getElementById("f_password").required = !u;
  document.getElementById("labelPassword").innerText = u ? "Nueva contraseña (dejar vacío para no cambiar)" : "Contraseña";
  alCambiarRol();
  document.getElementById("modal").classList.remove("hidden");
}

function cerrarModal() { 
  document.getElementById("modal").classList.add("hidden"); 
}

async function guardar(e) {
  e.preventDefault();
  const id = document.getElementById("f_id").value;
  const payload = {
    nombre: document.getElementById("f_nombre").value,
    email: document.getElementById("f_email").value,
    rol_id: parseInt(document.getElementById("f_rol").value),
    sucursal_id: document.getElementById("f_sucursal").value ? parseInt(document.getElementById("f_sucursal").value) : null,
    password: document.getElementById("f_password").value,
  };
  try {
    if (id) {
      await apiRequest(`/api/usuarios/${id}`, { method: "PUT", body: payload });
      notificarAccion("Usuario modificado correctamente");
    } else {
      await apiRequest("/api/usuarios", { method: "POST", body: payload });
      notificarAccion("Usuario creado correctamente");
    }
    cerrarModal(); 
    cargar();
  } catch (e) { 
    mostrarToast(e.message, "error"); 
  }
}

async function toggleActivo(usuario) {
  const accion = usuario.activo ? "desactivar" : "activar";
  if (!(await confirmarAccion(`¿Seguro que quieres ${accion} a ${usuario.nombre}?`))) return;
  try {
    await apiRequest(`/api/usuarios/${usuario.id}`, { method: "PUT", body: { activo: !usuario.activo } });
    notificarAccion(`Usuario ${usuario.activo ? "desactivado" : "activado"} correctamente`);
    cargar();
  } catch (e) {
    mostrarToast(e.message, "error");
  }
}

async function eliminar(id) {
  if (!(await confirmarAccion("¿Eliminar este usuario permanentemente? Esta acción no se puede deshacer."))) return;
  try {
    await apiRequest(`/api/usuarios/${id}`, { method: "DELETE" });
    notificarAccion("Usuario eliminado correctamente");
    cargar();
  } catch (e) {
    mostrarToast(e.message, "error");
  }
}

document.getElementById("tbody").addEventListener("click", (e) => {
  const btnEditar = e.target.closest(".btn-editar");
  if (btnEditar) return abrirModal(usuarios.find(u => u.id === Number(btnEditar.dataset.id)));
  const btnToggle = e.target.closest(".btn-toggle");
  if (btnToggle && !btnToggle.disabled) return toggleActivo(usuarios.find(u => u.id === Number(btnToggle.dataset.id)));
  const btnEliminar = e.target.closest(".btn-eliminar");
  if (btnEliminar && !btnEliminar.disabled) eliminar(Number(btnEliminar.dataset.id));
});

cargar();