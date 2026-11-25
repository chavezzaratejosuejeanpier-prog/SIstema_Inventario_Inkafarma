

function filaMed(m) {
  return `<div class="flex items-center justify-between border-b border-gray-50 pb-2">
    <span class="text-gray-600">${escapeHtml(m.nombre)}</span>
    <span class="badge badge-gray">Stock: ${m.stock_total} / mín. ${m.stock_minimo}</span>
  </div>`;
}
function filaLote(l) {
  return `<div class="flex items-center justify-between border-b border-gray-50 pb-2">
    <span class="text-gray-600">${escapeHtml(l.medicamento)} <span class="text-xs text-gray-400">(Lote ${escapeHtml(l.numero_lote)})</span></span>
    ${badgeVencimiento(l.dias_para_vencer)}
  </div>`;
}
function vacio(icono, texto) {
  return `<div class="text-center text-gray-400 text-sm py-4">
    <i class="fa-solid ${icono} text-lg mb-1 block"></i>${texto}
  </div>`;
}

function pintarBadgeMotor(motor) {
  const badge = document.getElementById("motorBadge");
  if (motor === "prolog") {
    badge.className = "badge badge-green";
    badge.innerHTML = '<i class="fa-solid fa-circle-check mr-1"></i> Motor: Prolog (SWI-Prolog real)';
  } else {
    badge.className = "badge badge-gray";
    badge.innerHTML = '<i class="fa-solid fa-code mr-1"></i> Motor: equivalente en Python';
  }
}

async function cargar() {
  ["vencidos", "porVencer", "stockBajo", "criticos"].forEach(id => {
    document.getElementById(id).innerHTML = bloqueCargando();
  });
  try {
    const data = await apiRequest("/api/dashboard/resumen");
    const logica = data.logica;

    pintarBadgeMotor(logica.motor);

    document.getElementById("countVencidos").innerText = logica.lotes_vencidos.length;
    document.getElementById("countPorVencer").innerText = logica.lotes_por_vencer.length;
    document.getElementById("countStockBajo").innerText = logica.medicamentos_stock_bajo.length;
    document.getElementById("countCriticos").innerText = logica.medicamentos_alerta_critica.length;

    document.getElementById("vencidos").innerHTML = logica.lotes_vencidos.length
      ? logica.lotes_vencidos.map(filaLote).join("") : vacio("fa-circle-check", "Ningún lote vencido.");
    document.getElementById("porVencer").innerHTML = logica.lotes_por_vencer.length
      ? logica.lotes_por_vencer.map(filaLote).join("") : vacio("fa-circle-check", "Nada por vencer pronto.");
    document.getElementById("stockBajo").innerHTML = logica.medicamentos_stock_bajo.length
      ? logica.medicamentos_stock_bajo.map(filaMed).join("") : vacio("fa-circle-check", "Todo el stock está en orden.");
    document.getElementById("criticos").innerHTML = logica.medicamentos_alerta_critica.length
      ? logica.medicamentos_alerta_critica.map(filaMed).join("") : vacio("fa-circle-check", "Sin alertas críticas.");
  } catch (e) {
    ["vencidos", "porVencer", "stockBajo", "criticos"].forEach(id => {
      document.getElementById(id).innerHTML = bloqueError();
    });
    mostrarToast(e.message, "error");
  }
}
cargar();