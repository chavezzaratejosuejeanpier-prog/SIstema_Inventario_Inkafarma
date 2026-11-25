



async function cargarDashboard() {
  saludoYFecha();
  document.getElementById("kpis").innerHTML = `<div class="col-span-4">${bloqueCargando()}</div>`;
  ["topVendidos", "alertasCriticas"].forEach(id => {
    document.getElementById(id).innerHTML = bloqueCargando();
  });

  try {
    const data = await apiRequest("/api/dashboard/resumen");
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

  } catch (e) {
    document.getElementById("kpis").innerHTML = `<div class="col-span-4">${bloqueError()}</div>`;
    ["topVendidos", "alertasCriticas"].forEach(id => {
      document.getElementById(id).innerHTML = bloqueError();
    });
    mostrarToast(e.message, "error");
  }
}

cargarDashboard();
