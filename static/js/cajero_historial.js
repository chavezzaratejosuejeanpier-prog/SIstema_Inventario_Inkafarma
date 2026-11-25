

let ventas = [];
const porPagina = 10;
let paginaActual = 1;

function fechaLocal(iso) {
  const fecha = new Date(iso);
  if (isNaN(fecha.getTime())) return null;
  return new Date(fecha.getFullYear(), fecha.getMonth(), fecha.getDate());
}

function aplicarPeriodo() {
  const periodo = document.getElementById("filtroPeriodo").value;
  const hoy = new Date();
  hoy.setHours(0, 0, 0, 0);

  if (periodo === "hoy") {
    return ventas.filter(v => {
      const f = fechaLocal(v.fecha);
      return f && f.getTime() === hoy.getTime();
    });
  }
  if (periodo === "mes") {
    return ventas.filter(v => {
      const f = fechaLocal(v.fecha);
      return f && f.getFullYear() === hoy.getFullYear() && f.getMonth() === hoy.getMonth();
    });
  }

  const dias = Number(periodo);
  const limite = new Date(hoy);
  limite.setDate(limite.getDate() - (dias - 1));
  return ventas.filter(v => {
    const f = fechaLocal(v.fecha);
    return f && f >= limite;
  });
}

function aplicarFiltros() {
  const texto = document.getElementById("buscador").value.toLowerCase().trim();
  return aplicarPeriodo().filter(v =>
    v.numero_venta.toLowerCase().includes(texto) ||
    (v.cliente_nombre || "").toLowerCase().includes(texto)
  );
}

function actualizarIndicadores(porPeriodo) {
  const total = porPeriodo.reduce((suma, v) => suma + (Number(v.total) || 0), 0);
  document.getElementById("totalVendidoPeriodo").innerText = formatearMoneda(total);
  document.getElementById("boletasPeriodo").innerText = porPeriodo.length;
}

function renderPaginacionHistorial(total, pagina) {
  const contenedor = document.getElementById("paginacion");
  const etiqueta = document.getElementById("hisMostrando");
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
    <button type="button" class="his-pag-btn ${activa ? 'activa' : ''}" data-pagina="${destino}"
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
  contenedor.querySelectorAll(".his-pag-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      paginaActual = Number(btn.dataset.pagina);
      renderTabla();
    });
  });
}

function estadoVacioHistorial(mensaje) {
  return `<div class="his-vacio"><i class="fa-solid fa-receipt"></i><p>${mensaje}</p></div>`;
}

function renderTabla() {
  const porPeriodo = aplicarPeriodo();
  actualizarIndicadores(porPeriodo);

  const filtrados = aplicarFiltros();
  const totalPaginas = Math.max(1, Math.ceil(filtrados.length / porPagina));
  if (paginaActual > totalPaginas) paginaActual = totalPaginas;
  const pagina = paginar(filtrados, paginaActual, porPagina);

  const tbody = document.getElementById("tbody");
  if (!filtrados.length) {
    const texto = document.getElementById("buscador").value.trim();
    const mensaje = texto
      ? "No se encontraron boletas con esos criterios"
      : "No hay ventas registradas en este período";
    tbody.innerHTML = `<tr><td colspan="6">${estadoVacioHistorial(mensaje)}</td></tr>`;
  } else {
    tbody.innerHTML = pagina.map(v => `
      <tr class="his-fila">
        <td class="his-boleta">${escapeHtml(v.numero_venta)}</td>
        <td>${escapeHtml(v.cliente_nombre)}</td>
        <td>${formatearFecha(v.fecha)}</td>
        <td><span class="his-badge-pago">${escapeHtml(v.metodo_pago)}</span></td>
        <td class="his-total">${formatearMoneda(v.total)}</td>
        <td>
          <button type="button" data-id="${v.id}" class="his-btn-boleta">
            <i class="fa-solid fa-receipt"></i> Ver boleta
          </button>
        </td>
      </tr>`).join("");
  }

  renderPaginacionHistorial(filtrados.length, paginaActual);
}

async function cargar() {
  document.getElementById("tbody").innerHTML = `<tr><td colspan="6">${bloqueCargando()}</td></tr>`;
  try {
    ventas = await apiRequest("/api/ventas?propio=1");
  } catch (e) {
    document.getElementById("tbody").innerHTML = `<tr><td colspan="6">${bloqueError("No se pudo cargar el historial de ventas.")}</td></tr>`;
    document.getElementById("totalVendidoPeriodo").innerText = "S/ 0.00";
    document.getElementById("boletasPeriodo").innerText = "0";
    document.getElementById("hisMostrando").innerText = "Mostrando 0 de 0 registros";
    document.getElementById("paginacion").innerHTML = "";
    return;
  }
  renderTabla();
}

function mostrarBoleta(venta) {
  const subtotal = venta.detalles.reduce((a, d) => a + d.subtotal, 0);
  const descuento = venta.descuento || 0;
  const igv = venta.total - (subtotal - descuento);

  document.getElementById("boletaNumero").innerText = "N° " + venta.numero_venta;
  document.getElementById("boletaCliente").innerText = venta.cliente_nombre;
  document.getElementById("boletaFecha").innerText = formatearFecha(venta.fecha);
  document.getElementById("boletaVendedor").innerText = venta.usuario;
  document.getElementById("boletaMetodo").innerText = venta.metodo_pago;
  document.getElementById("boletaItems").innerHTML = venta.detalles.map(d => `
    <tr>
      <td class="py-0.5">${escapeHtml(d.medicamento)}${d.promocion ? `<br><span class="text-[10px] text-inka-green"><i class="fa-solid fa-tag"></i> ${escapeHtml(d.promocion)}</span>` : ''}</td>
      <td>${d.cantidad}</td><td class="text-right">${formatearMoneda(d.subtotal)}</td>
    </tr>`).join("");
  document.getElementById("boletaSubtotal").innerText = formatearMoneda(subtotal);
  document.getElementById("boletaFilaDescuento").style.display = descuento > 0 ? "flex" : "none";
  document.getElementById("boletaDescuento").innerText = "- " + formatearMoneda(descuento);
  document.getElementById("boletaIgv").innerText = formatearMoneda(igv);
  document.getElementById("boletaTotal").innerText = formatearMoneda(venta.total);
  document.getElementById("boletaFilaCupon").classList.toggle("hidden", !venta.cupon_codigo);
  document.getElementById("boletaCupon").innerText = venta.cupon_codigo || "";

  document.getElementById("modalBoleta").classList.remove("hidden");
}
function cerrarBoleta() { document.getElementById("modalBoleta").classList.add("hidden"); }

document.getElementById("tbody").addEventListener("click", (e) => {
  const btn = e.target.closest(".his-btn-boleta");
  if (!btn) return;
  const venta = ventas.find(v => v.id === Number(btn.dataset.id));
  if (venta) mostrarBoleta(venta);
});

cargar();
