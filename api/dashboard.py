from datetime import date

from flask import Blueprint, jsonify, request, session
from models import Medicamento, Lote, Venta, Usuario
from auth.decorators import login_requerido
from paradigmas import funcional
from paradigmas import logica
from paradigmas import multiparadigma

dashboard_bp = Blueprint("dashboard_api", __name__, url_prefix="/api/dashboard")


@dashboard_bp.route("/resumen", methods=["GET"])
@login_requerido
def resumen():
    usuario = Usuario.query.get(session["usuario_id"])
    if session.get("rol") == "Cajero":

        sucursal_id = usuario.sucursal_id
    else:

        sucursal_id = request.args.get("sucursal_id") or None

    lotes_query = Lote.query
    ventas_query = Venta.query.filter(Venta.estado != "Anulada")
    if sucursal_id:
        lotes_query = lotes_query.filter_by(sucursal_id=sucursal_id)
        ventas_query = ventas_query.filter_by(sucursal_id=sucursal_id)

    lotes = [l.to_dict() for l in lotes_query.all()]
    ventas_validas = ventas_query.all()
    ventas = [v.to_dict() for v in ventas_validas]

    medicamentos_activos = Medicamento.query.filter_by(activo=True).all()
    if sucursal_id:


        stock_por_medicamento = {}
        for l in lotes:
            stock_por_medicamento[l["medicamento_id"]] = stock_por_medicamento.get(l["medicamento_id"], 0) + l["cantidad_actual"]
        medicamentos = []
        for m in medicamentos_activos:
            d = m.to_dict()
            d["stock_total"] = stock_por_medicamento.get(m.id, 0)
            medicamentos.append(d)
    else:
        medicamentos = [m.to_dict() for m in medicamentos_activos]

    detalles_venta = []
    for v in ventas_validas:
        detalles_venta.extend([d.to_dict() for d in v.detalles])


    reporte_funcional = funcional.pipeline_reporte_inventario(medicamentos, lotes)
    top_vendidos = funcional.top_n_productos_mas_vendidos(detalles_venta, n=5)


    alertas = logica.evaluar_alertas(medicamentos, lotes)


    estadisticas_ventas = multiparadigma.resumen_ventas(ventas)
    estadisticas_inventario = multiparadigma.resumen_inventario(lotes)




    hoy = date.today()
    ventas_hoy = [v for v in ventas_validas if v.fecha.date() == hoy]
    total_ventas_hoy = len(ventas_hoy)
    monto_vendido_hoy = round(sum(v.total for v in ventas_hoy), 2)
    ticket_promedio_hoy = round(monto_vendido_hoy / total_ventas_hoy, 2) if total_ventas_hoy else 0
    categorias = multiparadigma.top_medicamentos_por_categoria(medicamentos)
    sugeridos_reponer = multiparadigma.proyeccion_reposicion(medicamentos)
    unidades_por_dia = multiparadigma.stock_por_dia_arreglo(ventas)

    return jsonify({
        "sucursal_id": sucursal_id,
        "kpis": {
            "total_medicamentos": len(medicamentos),
            "valor_inventario": reporte_funcional["valor_total_inventario"],
            "lotes_por_vencer": len(reporte_funcional["lotes_por_vencer"]),
            "lotes_vencidos": len(reporte_funcional["lotes_vencidos"]),
            "stock_critico": len(reporte_funcional["stock_critico"]),
            "total_ventas": estadisticas_ventas["total_ventas"],
            "monto_vendido": estadisticas_ventas["monto_total"],
            "total_ventas_hoy": total_ventas_hoy,
            "monto_vendido_hoy": monto_vendido_hoy,
            "ticket_promedio_hoy": ticket_promedio_hoy,
        },
        "funcional": {
            "medicamentos_por_categoria": reporte_funcional["medicamentos_por_categoria"],
            "stock_critico": reporte_funcional["stock_critico"],
            "top_vendidos": top_vendidos,
            "alertas": reporte_funcional["alertas_funcionales"],
        },
        "logica": alertas,
        "multiparadigma": {
            "ventas": estadisticas_ventas,
            "inventario": estadisticas_inventario,
            "categorias": categorias,
            "sugeridos_reponer": sugeridos_reponer,
            "unidades_por_dia_arreglo": unidades_por_dia,
        },
    })