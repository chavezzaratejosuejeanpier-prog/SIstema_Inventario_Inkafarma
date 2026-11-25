

async function cargarSucursalesFiltro() {
  const select = document.getElementById("filtroSucursal");
  if (!select) return;
  try {
    const sucursales = await apiRequest("/api/sucursales");
    select.innerHTML = '<option value="">Todas las sucursales</option>' +
      sucursales.map(s => `<option value="${s.id}">${escapeHtml(s.nombre)}</option>`).join("");
  } catch (e) {  }
}

async function cargarDashboard() {
  document.getElementById("kpis").innerHTML = `<div class="col-span-4">${bloqueCargando()}</div>`;
  ["topVendidos", "alertasCriticas", "alertasFuncionales"].forEach(id => {
    document.getElementById(id).innerHTML = bloqueCargando();
  });

  try {
    const select = document.getElementById("filtroSucursal");
    const sucursalId = select ? select.value : "";
    const query = sucursalId ? `?sucursal_id=${sucursalId}` : "";
    const data = await apiRequest(`/api/dashboard/resumen${query}`);
    const k = data.kpis;
    const arreglo = data.multiparadigma.unidades_por_dia_arreglo || [];
    const unidadesHoy = arreglo.length ? (arreglo[arreglo.length - 1].unidades_vendidas || 0) : 0;
    const totalUnidades7d = arreglo.reduce((suma, d) => suma + (Number(d.unidades_vendidas) || 0), 0);

    document.getElementById("kpis").innerHTML = [
      tarjetaKpiPremium("fa-cart-shopping", "verde", "Ventas del día", formatearMoneda(k.monto_vendido_hoy), `${k.total_ventas_hoy} ventas hoy`),
      tarjetaKpiPremium("fa-box", "verde", "Productos vendidos", unidadesHoy, `${totalUnidades7d} unid. en 7 días`),
      tarjetaKpiPremium("fa-triangle-exclamation", "naranja", "Stock bajo", k.stock_critico, `${k.lotes_vencidos} lotes vencidos`),
      tarjetaKpiPremium("fa-calendar-day", "rojo", "Lotes por vencer", k.lotes_por_vencer, "Próximos 30 días"),
    ].join("");

    const serie = serieVentas7Dias(data.multiparadigma.ventas.ventas_por_dia, arreglo);
    dibujarGraficoVentasPremium(serie);

    const contenedorUnidades = document.getElementById("arregloUnidades");
    if (serie.every(v => v.monto === 0)) {
      contenedorUnidades.innerHTML = estadoVacioPremium("Aún no hay ventas en los últimos 7 días.");
    } else {
      contenedorUnidades.innerHTML = arreglo.map(d => `
        <div class="unidad-dia">
          <p class="unidad-dia-label">${escapeHtml(d.dia)}</p>
          <p class="unidad-dia-valor">${d.unidades_vendidas}</p>
        </div>`).join("");
    }

    dibujarGraficoCategoriasPremium(data.multiparadigma.categorias || []);
    renderTopVendidosPremium("topVendidos", data.funcional.top_vendidos);
    renderAlertasPremium("alertasCriticas", data.logica.medicamentos_alerta_critica);

    const motor = document.getElementById("motorLogico");
    if (motor) motor.innerText = "Motor de reglas activo: " + data.logica.motor;

    const alertasFuncionales = data.funcional.alertas || [];
    const BADGE_NIVEL = {
      VENCIDO: "badge-red", STOCK_BAJO: "badge-yellow", POR_VENCER: "badge-yellow",
    };
    document.getElementById("alertasFuncionales").innerHTML = alertasFuncionales.length
      ? alertasFuncionales.map(a => `
          <div class="alerta-row">
            <span class="alerta-icon"><i class="fa-solid fa-circle-info"></i></span>
            <div class="alerta-body">
              <p class="alerta-nombre">${escapeHtml(a.medicamento)}</p>
              <p class="alerta-meta">Alerta generada por el pipeline funcional</p>
            </div>
            <span class="badge ${BADGE_NIVEL[a.nivel] || 'badge-gray'}">${escapeHtml(String(a.nivel).replace('_', ' '))}</span>
          </div>`).join("")
      : estadoVacioPremium("Sin alertas por el momento.");

  } catch (e) {
    document.getElementById("kpis").innerHTML = `<div class="col-span-4">${bloqueError()}</div>`;
    ["topVendidos", "alertasCriticas", "alertasFuncionales"].forEach(id => {
      document.getElementById(id).innerHTML = bloqueError();
    });
    mostrarToast(e.message, "error");
  }
}

saludoYFecha();
cargarSucursalesFiltro();
cargarDashboard();
