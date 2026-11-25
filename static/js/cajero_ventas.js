

let medicamentos = [], itemsVenta = [];
const sucursalId = document.body.dataset.sucursalId;

async function cargar() {
  medicamentos = await apiRequest(`/api/medicamentos?activos=1&sucursal_id=${sucursalId}`);
  document.getElementById("item_medicamento").innerHTML = medicamentos.map(m =>
    `<option value="${m.id}" data-precio="${m.precio_venta}" data-stock="${m.stock_total}" data-receta="${m.requiere_receta ? '1' : '0'}">${escapeHtml(m.nombre)} (stock: ${m.stock_total}) - ${formatearMoneda(m.precio_venta)}</option>`).join("");
  renderResultados();
  if (medicamentos.length) seleccionarMedicamento(medicamentos[0].id);
  else renderProductoSeleccionado();
}

function renderResultados() {
  const contenedor = document.getElementById("resultadosMedicamentos");
  if (!contenedor) return;
  const texto = document.getElementById("buscadorMedicamento").value.toLowerCase().trim();
  const lista = medicamentos
    .filter(m => m.nombre.toLowerCase().includes(texto) || m.codigo.toLowerCase().includes(texto))
    .slice(0, 8);

  contenedor.innerHTML = lista.length
    ? lista.map(m => `
        <button type="button" class="ven-resultado" data-id="${m.id}">
          <span class="ven-resultado-icono"><i class="fa-solid fa-capsules"></i></span>
          <span class="ven-resultado-info">
            <strong>${escapeHtml(m.nombre)}</strong>
            <small>${escapeHtml(m.codigo)} · ${escapeHtml(m.laboratorio || '-')}</small>
          </span>
          <span class="ven-resultado-precio">${formatearMoneda(m.precio_venta)}</span>
        </button>`).join("")
    : `<p class="ven-vacio">No se encontraron medicamentos.</p>`;
}

function seleccionarMedicamento(id) {
  document.getElementById("item_medicamento").value = String(id);
  renderProductoSeleccionado();
  alCambiarMedicamento();
}

function renderProductoSeleccionado() {
  const caja = document.getElementById("productoSeleccionado");
  if (!caja) return;
  const sel = document.getElementById("item_medicamento");
  const opt = sel.options[sel.selectedIndex];
  if (!opt) { caja.classList.add("hidden"); caja.innerHTML = ""; return; }

  const m = medicamentos.find(x => x.id === Number(sel.value));
  const bajo = m && Number(m.stock_total) <= Number(m.stock_minimo);
  caja.classList.remove("hidden");
  caja.innerHTML = `
    <div class="ven-producto-cab">
      <span class="ven-producto-icono"><i class="fa-solid fa-capsules"></i></span>
      <div class="ven-producto-info">
        <h4>${escapeHtml(m ? m.nombre : opt.text)}</h4>
        <p>${escapeHtml(m ? m.codigo : '')} · ${escapeHtml(m ? (m.laboratorio || '-') : '')}</p>
      </div>
      <span class="ven-producto-precio">${formatearMoneda(opt.dataset.precio)}</span>
    </div>
    <div class="ven-producto-acciones">
      <div>
        <label for="item_cantidad">Cantidad</label>
        <input id="item_cantidad" type="number" min="1" placeholder="1">
        ${bajo ? `<span class="ven-stock-bajo">Stock: ${m.stock_total}</span>` : ''}
      </div>
      <button type="button" onclick="agregarItem()" class="ven-btn-agregar">
        <i class="fa-solid fa-plus"></i> Agregar
      </button>
    </div>
    <div id="campoReceta" class="hidden ven-receta">
      <i class="fa-solid fa-file-medical"></i>
      <input id="item_receta" placeholder="N° de receta médica (obligatorio para este producto)">
    </div>`;
}

function alCambiarMedicamento() {
  const sel = document.getElementById("item_medicamento");
  const opt = sel.options[sel.selectedIndex];
  const requiereReceta = !!opt && opt.dataset.receta === "1";
  const campoReceta = document.getElementById("campoReceta");
  if (campoReceta) campoReceta.classList.toggle("hidden", !requiereReceta);
  if (!requiereReceta) {
    const receta = document.getElementById("item_receta");
    if (receta) receta.value = "";
  }
}

function alCambiarMetodoPago() {
  const metodo = document.getElementById("f_metodo").value;
  document.getElementById("campoTarjeta").classList.toggle("hidden", metodo !== "Tarjeta");
  document.getElementById("campoYapePlin").classList.toggle("hidden", metodo !== "Yape/Plin");
  if (metodo !== "Tarjeta") {
    document.getElementById("f_tarjeta_digitos").value = "";
    document.getElementById("f_tarjeta_titular").value = "";
  }
  if (metodo !== "Yape/Plin") document.getElementById("f_operacion").value = "";
}

function abrirModal() {
  itemsVenta = [];
  document.getElementById("f_cliente").value = "";
  document.getElementById("f_cliente_email").value = "";
  document.getElementById("f_cupon").value = "";
  document.getElementById("f_metodo").value = "Efectivo";
  document.getElementById("buscadorMedicamento").value = "";
  renderResultados();
  renderItems();
  alCambiarMetodoPago();
  renderProductoSeleccionado();
  alCambiarMedicamento();
  document.getElementById("buscadorMedicamento").focus();
}
function cerrarModal() { abrirModal(); }

function agregarItem() {
  const sel = document.getElementById("item_medicamento");
  const opt = sel.options[sel.selectedIndex];
  if (!opt) { mostrarToast("No hay productos disponibles", "error"); return; }

  const medicamento_id = parseInt(sel.value);
  const cantidad = parseInt(document.getElementById("item_cantidad").value);
  const precio_unitario = parseFloat(opt.dataset.precio);
  const stockDisponible = parseInt(opt.dataset.stock);
  const requiereReceta = opt.dataset.receta === "1";
  const numeroReceta = document.getElementById("item_receta").value.trim();
  const producto = medicamentos.find(m => m.id === medicamento_id);

  if (!cantidad || cantidad <= 0) { mostrarToast("Ingresa una cantidad válida", "error"); return; }
  if (cantidad > stockDisponible) { mostrarToast("Cantidad supera el stock disponible", "error"); return; }
  if (requiereReceta && !numeroReceta) {
    mostrarToast("Este medicamento requiere el N° de receta médica", "error");
    return;
  }

  const existente = itemsVenta.find(it => it.medicamento_id === medicamento_id);
  if (existente) {
    if (existente.cantidad + cantidad > stockDisponible) { mostrarToast("Cantidad supera el stock disponible", "error"); return; }
    existente.cantidad += cantidad;
    existente.stock = stockDisponible;
    if (numeroReceta) existente.numero_receta = numeroReceta;
  } else {
    itemsVenta.push({
      medicamento_id, nombre: opt.text.replace(/\s*\(stock:.*/, ""), cantidad, precio_unitario,
      codigo: producto ? producto.codigo : "",
      stock: stockDisponible,
      numero_receta: requiereReceta ? numeroReceta : null,
    });
  }
  document.getElementById("item_cantidad").value = "";
  document.getElementById("item_receta").value = "";
  renderItems();
}

function renderItems() {
  const hayItems = itemsVenta.length > 0;
  document.getElementById("tituloItems").innerText = `Productos seleccionados (${itemsVenta.length})`;
  document.getElementById("items_tbody").innerHTML = itemsVenta.map((it, i) => `
    <tr class="ven-item-fila">
      <td>
        <div class="ven-item-nombre">${escapeHtml(it.nombre)} ${it.numero_receta ? `<span class="badge badge-yellow" title="N° receta: ${escapeHtml(it.numero_receta)}">Receta ${escapeHtml(it.numero_receta)}</span>` : ''}</div>
        <div class="ven-item-codigo">${escapeHtml(it.codigo)}</div>
      </td>
      <td>
        <div class="ven-cant-control">
          <button type="button" onclick="cambiarCantidad(${i}, -1)" aria-label="Disminuir cantidad">−</button>
          <span>${it.cantidad}</span>
          <button type="button" onclick="cambiarCantidad(${i}, 1)" aria-label="Aumentar cantidad">+</button>
        </div>
      </td>
      <td class="ven-item-precio">${formatearMoneda(it.precio_unitario)}</td>
      <td class="ven-item-subtotal">${formatearMoneda(it.cantidad * it.precio_unitario)}</td>
      <td><button type="button" onclick="quitarItem(${i})" class="ven-btn-quitar" aria-label="Quitar producto"><i class="fa-solid fa-trash"></i></button></td>
    </tr>`).join("");
  document.getElementById("items_vacio").classList.toggle("hidden", hayItems);

  const subtotal = itemsVenta.reduce((a, it) => a + it.cantidad * it.precio_unitario, 0);
  const descuento = calcularDescuentoEstimado(subtotal);
  const subtotalConDescuento = subtotal - descuento;
  const igv = subtotalConDescuento * 0.18;

  document.getElementById("subtotalVenta").innerText = formatearMoneda(subtotal);
  document.getElementById("filaDescuentoVenta").style.display = descuento > 0 ? "flex" : "none";
  document.getElementById("descuentoVenta").innerText = "- " + formatearMoneda(descuento);
  document.getElementById("igvVenta").innerText = formatearMoneda(igv);
  document.getElementById("totalVenta").innerText = formatearMoneda(subtotalConDescuento + igv);
}




function calcularDescuentoEstimado(subtotal) {
  const tramos = [[500, 0.10], [200, 0.05], [0, 0]];
  for (const [minimo, porcentaje] of tramos) {
    if (subtotal >= minimo) return Math.round(subtotal * porcentaje * 100) / 100;
  }
  return 0;
}

function cambiarCantidad(i, delta) {
  const item = itemsVenta[i];
  if (!item) return;
  const nueva = item.cantidad + delta;
  if (nueva < 1) return;
  if (nueva > (item.stock || Infinity)) { mostrarToast("Cantidad supera el stock disponible", "error"); return; }
  item.cantidad = nueva;
  renderItems();
}

function quitarItem(i) { itemsVenta.splice(i, 1); renderItems(); }

async function guardarVenta() {
  if (!itemsVenta.length) { mostrarToast("Agrega al menos un producto", "error"); return; }

  const metodo = document.getElementById("f_metodo").value;
  let referencia_pago = "";
  if (metodo === "Tarjeta") {
    const digitos = document.getElementById("f_tarjeta_digitos").value.trim();
    const titular = document.getElementById("f_tarjeta_titular").value.trim();
    if (!/^\d{4}$/.test(digitos) || !titular) {
      mostrarToast("Ingresa los últimos 4 dígitos y el titular de la tarjeta", "error");
      return;
    }
    referencia_pago = `${digitos} · ${titular}`;
  } else if (metodo === "Yape/Plin") {
    const operacion = document.getElementById("f_operacion").value.trim();
    if (!operacion) { mostrarToast("Ingresa el N° de operación", "error"); return; }
    referencia_pago = operacion;
  }

  const payload = {
    cliente_nombre: document.getElementById("f_cliente").value || "Cliente Varios",
    cliente_email: document.getElementById("f_cliente_email").value.trim(),
    cupon: document.getElementById("f_cupon").value.trim(),
    metodo_pago: metodo,
    referencia_pago,
    items: itemsVenta.map(it => ({ medicamento_id: it.medicamento_id, cantidad: it.cantidad, numero_receta: it.numero_receta })),
  };
  try {
    const venta = await apiRequest("/api/ventas", { method: "POST", body: payload });
    cerrarModal();
    notificarAccion(`Venta ${venta.numero_venta} registrada correctamente`);
    if (payload.cliente_email) {
      mostrarToast(
        venta.boleta_enviada ? `Boleta enviada a ${payload.cliente_email}` : "No se pudo enviar la boleta por correo",
        venta.boleta_enviada ? "exito" : "error"
      );
    }
    mostrarBoleta(venta);
    cargar();
  } catch (e) { mostrarToast(e.message, "error"); }
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
  document.getElementById("boletaFilaReferencia").classList.toggle("hidden", !venta.referencia_pago);
  document.getElementById("boletaReferencia").innerText = venta.referencia_pago || "";
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

document.getElementById("resultadosMedicamentos").addEventListener("click", (e) => {
  const boton = e.target.closest(".ven-resultado");
  if (boton) seleccionarMedicamento(Number(boton.dataset.id));
});

cargar();
