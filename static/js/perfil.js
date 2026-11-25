

async function cargarPerfil() {
  try {
    const u = await apiRequest("/api/usuarios/me");
    document.getElementById("infoEmail").innerText = u.email;
    document.getElementById("perfilEmail").innerText = u.email;
    document.getElementById("perfilMiembroDesde").innerText = u.fecha_registro
      ? "Miembro desde " + formatearFecha(u.fecha_registro)
      : "";
  } catch (e) {
    document.getElementById("perfilEmail").innerText = "";
    mostrarToast(e.message, "error");
  }
}

function alternarVisibilidad(idInput, boton) {
  const input = document.getElementById(idInput);
  const icono = boton.querySelector("i");
  const mostrar = input.type === "password";
  input.type = mostrar ? "text" : "password";
  icono.className = mostrar ? "fa-solid fa-eye-slash" : "fa-solid fa-eye";
}

function marcarError(idWrap, idMensaje, mensaje) {
  document.getElementById(idWrap).classList.add("campo-error");
  const el = document.getElementById(idMensaje);
  el.innerText = mensaje;
  el.classList.add("visible");
}

function limpiarError(idWrap, idMensaje) {
  document.getElementById(idWrap).classList.remove("campo-error");
  const el = document.getElementById(idMensaje);
  el.innerText = "";
  el.classList.remove("visible");
}

function marcarRequisito(id, cumplido) {
  const el = document.getElementById(id);
  el.classList.toggle("cumplido", cumplido);
  el.querySelector("i").className = cumplido ? "fa-solid fa-circle-check" : "fa-solid fa-circle";
}

function validarFormulario() {
  const actual = document.getElementById("f_actual").value;
  const nueva = document.getElementById("f_nueva").value;
  const confirmar = document.getElementById("f_confirmar").value;

  const longitudOk = nueva.length >= 6;
  const distintaOk = nueva.length > 0 && nueva !== actual;
  const coincideOk = confirmar.length > 0 && confirmar === nueva;

  marcarRequisito("reqLongitud", longitudOk);
  marcarRequisito("reqDistinta", nueva.length === 0 || distintaOk);
  marcarRequisito("reqCoincide", coincideOk);

  if (confirmar.length > 0 && confirmar !== nueva) {
    marcarError("wrapConfirmar", "errorConfirmar", "No coincide con la nueva contraseña");
  } else {
    limpiarError("wrapConfirmar", "errorConfirmar");
  }

  const formValido = actual.length > 0 && longitudOk && distintaOk && coincideOk;
  document.getElementById("btnGuardar").disabled = !formValido;
  return formValido;
}

document.getElementById("f_actual").addEventListener("input", () => {
  limpiarError("wrapActual", "errorActual");
  validarFormulario();
});
document.getElementById("f_nueva").addEventListener("input", () => {
  limpiarError("wrapNueva", "errorNueva");
  validarFormulario();
});
document.getElementById("f_confirmar").addEventListener("input", validarFormulario);

async function cambiarPassword(e) {
  e.preventDefault();
  if (!validarFormulario()) return;

  const password_actual = document.getElementById("f_actual").value;
  const password_nueva = document.getElementById("f_nueva").value;

  const btn = document.getElementById("btnGuardar");
  btn.disabled = true;

  try {
    await apiRequest("/api/usuarios/me/password", {
      method: "PUT",
      body: { password_actual, password_nueva },
    });
    notificarAccion("Contraseña actualizada correctamente");
    document.getElementById("form").reset();
    ["reqLongitud", "reqDistinta", "reqCoincide"].forEach(id => marcarRequisito(id, false));
    limpiarError("wrapActual", "errorActual");
    limpiarError("wrapConfirmar", "errorConfirmar");
  } catch (e) {
    if (e.message.toLowerCase().includes("actual")) {
      marcarError("wrapActual", "errorActual", e.message);
    } else {
      marcarError("wrapNueva", "errorNueva", e.message);
    }
    mostrarToast(e.message, "error");
    btn.disabled = false;
  }
}

cargarPerfil();