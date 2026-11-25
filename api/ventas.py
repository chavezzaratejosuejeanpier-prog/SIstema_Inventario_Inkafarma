import random
from datetime import datetime, date
from flask import Blueprint, current_app, request, jsonify, session
from extensions import db
from models import Venta, DetalleVenta, Lote, Medicamento, Usuario, Promocion
from paradigmas.funcional import calcular_totales_venta, calcular_descuento_por_volumen
from auth.decorators import login_requerido, requiere_rol
from api.auditoria import registrar_auditoria
from auth.correo import enviar_boleta_venta

ventas_bp = Blueprint("ventas_api", __name__, url_prefix="/api/ventas")


def _generar_numero_venta():
    return f"BV-{datetime.utcnow().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"


def _promocion_de_producto(medicamento_id, sucursal_id):
    """Busca la mejor promoción vigente ('porcentaje'/'monto_fijo'/'nxm')
    para un medicamento, en esta sucursal o en todas ('sucursal_id' nulo).
    Si hay varias, se queda con la que exista (no se acumulan)."""
    hoy = date.today()
    candidatas = (
        Promocion.query.filter(
            Promocion.medicamento_id == medicamento_id,
            Promocion.activo == True,
            Promocion.fecha_inicio <= hoy,
            Promocion.fecha_fin >= hoy,
            Promocion.tipo.in_(["porcentaje", "monto_fijo", "nxm"]),
        )
        .filter(db.or_(Promocion.sucursal_id == None, Promocion.sucursal_id == sucursal_id))
        .all()
    )
    if not candidatas:
        return None

    return max(candidatas, key=lambda p: _valor_referencia(p))


def _valor_referencia(promocion):
    if promocion.tipo == "porcentaje":
        return promocion.valor or 0
    if promocion.tipo == "monto_fijo":
        return promocion.valor or 0
    if promocion.tipo == "nxm" and promocion.lleva:
        return (promocion.lleva - promocion.paga) / promocion.lleva * 100
    return 0


def _descuento_de_linea(promocion, cantidad, precio_unitario):
    subtotal_linea = cantidad * precio_unitario
    if promocion.tipo == "porcentaje":
        return round(subtotal_linea * (promocion.valor / 100), 2)
    if promocion.tipo == "monto_fijo":
        return round(min(promocion.valor * cantidad, subtotal_linea), 2)
    if promocion.tipo == "nxm":
        unidades_gratis = (cantidad // promocion.lleva) * (promocion.lleva - promocion.paga)
        return round(min(unidades_gratis * precio_unitario, subtotal_linea), 2)
    return 0.0


def _buscar_cupon(codigo, sucursal_id):
    hoy = date.today()
    return (
        Promocion.query.filter(
            db.func.upper(Promocion.codigo) == codigo.strip().upper(),
            Promocion.tipo == "cupon",
            Promocion.activo == True,
            Promocion.fecha_inicio <= hoy,
            Promocion.fecha_fin >= hoy,
        )
        .filter(db.or_(Promocion.sucursal_id == None, Promocion.sucursal_id == sucursal_id))
        .first()
    )


@ventas_bp.route("", methods=["GET"])
@login_requerido
def listar():
    query = Venta.query
    if request.args.get("propio") == "1":
        query = query.filter_by(usuario_id=session["usuario_id"])
    if request.args.get("sucursal_id"):
        query = query.filter_by(sucursal_id=request.args.get("sucursal_id"))
    ventas = query.order_by(Venta.fecha.desc()).all()
    return jsonify([v.to_dict() for v in ventas])


@ventas_bp.route("", methods=["POST"])
@requiere_rol("Administrador", "Cajero")
def crear():
    """Registra una venta. Descuenta stock automáticamente usando el
    criterio FEFO (First Expired, First Out) DENTRO de la sucursal del
    usuario que vende, y aplica en orden: promociones por producto,
    cupón (si se envía uno) y el descuento automático por volumen."""
    usuario = Usuario.query.get(session["usuario_id"])
    data = request.get_json()
    items = data.get("items", [])
    if not items:
        return jsonify({"error": "Debe incluir al menos un ítem"}), 400

    metodo_pago = data.get("metodo_pago", "Efectivo")
    referencia_pago = (data.get("referencia_pago") or "").strip()
    if metodo_pago in ("Tarjeta", "Yape/Plin") and not referencia_pago:
        campo = "los últimos 4 dígitos de la tarjeta" if metodo_pago == "Tarjeta" else "el N° de operación"
        return jsonify({"error": f"Debes ingresar {campo} para pagos con {metodo_pago}"}), 400

    if session.get("rol") == "Cajero":
        sucursal_id = usuario.sucursal_id
    else:
        sucursal_id = data.get("sucursal_id") or usuario.sucursal_id
    if not sucursal_id:
        return jsonify({"error": "Tu usuario no tiene una sucursal asignada. Contacta al administrador."}), 400

    detalles_calculo = []
    descuento_productos_total = 0.0
    for item in items:
        medicamento = Medicamento.query.get(item["medicamento_id"])
        if not medicamento:
            return jsonify({"error": f"Medicamento {item['medicamento_id']} no encontrado"}), 404
        cantidad_solicitada = int(item["cantidad"])

        lotes_disponibles = (
            Lote.query.filter_by(medicamento_id=medicamento.id, sucursal_id=sucursal_id)
            .filter(Lote.cantidad_actual > 0)
            .order_by(Lote.fecha_vencimiento.asc())
            .all()
        )
        lotes_disponibles = [l for l in lotes_disponibles if l.dias_para_vencer >= 0]

        stock_disponible = sum(l.cantidad_actual for l in lotes_disponibles)
        if stock_disponible < cantidad_solicitada:
            return jsonify({
                "error": f"Stock insuficiente para {medicamento.nombre} en tu sucursal. Disponible: {stock_disponible}"
            }), 400

        if medicamento.requiere_receta and not (item.get("numero_receta") or "").strip():
            return jsonify({
                "error": f"{medicamento.nombre} requiere número de receta médica para poder venderse"
            }), 400

        promocion = _promocion_de_producto(medicamento.id, sucursal_id)
        descuento_linea = _descuento_de_linea(promocion, cantidad_solicitada, medicamento.precio_venta) if promocion else 0.0
        descuento_productos_total += descuento_linea

        detalles_calculo.append({
            "medicamento": medicamento,
            "cantidad": cantidad_solicitada,
            "precio_unitario": medicamento.precio_venta,
            "numero_receta": (item.get("numero_receta") or "").strip() or None,
            "lotes_a_descontar": lotes_disponibles,
            "promocion": promocion,
            "descuento_linea": descuento_linea,
        })


    totales = calcular_totales_venta([
        {"cantidad": d["cantidad"], "precio_unitario": d["precio_unitario"]} for d in detalles_calculo
    ])
    subtotal = totales["subtotal"]

    cupon_promocion = None
    descuento_cupon = 0.0
    codigo_cupon = (data.get("cupon") or "").strip()
    if codigo_cupon:
        cupon_promocion = _buscar_cupon(codigo_cupon, sucursal_id)
        if not cupon_promocion:
            return jsonify({"error": "El cupón ingresado no existe o ya no está vigente"}), 400
        base_cupon = max(subtotal - descuento_productos_total, 0)
        descuento_cupon = round(base_cupon * (cupon_promocion.valor / 100), 2)



    base_volumen = max(subtotal - descuento_productos_total - descuento_cupon, 0)
    descuento_volumen = calcular_descuento_por_volumen(base_volumen)

    descuento_total = round(descuento_productos_total + descuento_cupon + descuento_volumen, 2)
    subtotal_con_descuento = round(subtotal - descuento_total, 2)
    igv = round(subtotal_con_descuento * 0.18, 2)
    total_final = round(subtotal_con_descuento + igv, 2)

    venta = Venta(
        numero_venta=_generar_numero_venta(),
        usuario_id=session["usuario_id"],
        sucursal_id=sucursal_id,
        cliente_nombre=data.get("cliente_nombre", "Cliente Varios"),
        cliente_dni=data.get("cliente_dni"),
        cliente_email=(data.get("cliente_email") or "").strip() or None,
        metodo_pago=metodo_pago,
        referencia_pago=referencia_pago or None,
        descuento=descuento_total,
        cupon_codigo=cupon_promocion.codigo if cupon_promocion else None,
        total=total_final,
    )
    db.session.add(venta)
    db.session.flush()

    for d in detalles_calculo:
        cantidad_restante = d["cantidad"]
        lote_referencia = None
        for lote in d["lotes_a_descontar"]:
            if cantidad_restante <= 0:
                break
            descontar = min(lote.cantidad_actual, cantidad_restante)
            lote.cantidad_actual -= descontar
            cantidad_restante -= descontar
            lote_referencia = lote_referencia or lote

        detalle = DetalleVenta(
            venta_id=venta.id,
            medicamento_id=d["medicamento"].id,
            lote_id=lote_referencia.id if lote_referencia else None,
            promocion_id=d["promocion"].id if d["promocion"] else None,
            cantidad=d["cantidad"],
            precio_unitario=d["precio_unitario"],
            subtotal=round(d["cantidad"] * d["precio_unitario"], 2),
            descuento=d["descuento_linea"],
            numero_receta=d["numero_receta"],
        )
        db.session.add(detalle)

    db.session.commit()
    registrar_auditoria("crear", "Venta", venta.id, f"{venta.numero_venta} - S/ {venta.total:.2f}")

    boleta_enviada = False
    if venta.cliente_email:
        try:
            enviar_boleta_venta(venta)
            boleta_enviada = True
        except Exception:


            current_app.logger.exception(
                "No se pudo enviar la boleta de la venta %s a %s", venta.numero_venta, venta.cliente_email
            )

    respuesta = venta.to_dict()
    respuesta["boleta_enviada"] = boleta_enviada
    return jsonify(respuesta), 201


@ventas_bp.route("/<int:id>/anular", methods=["POST"])
@requiere_rol("Administrador")
def anular(id):
    """Anula una venta ya registrada y devuelve el stock descontado a los
    lotes de los que salió (según el lote_id guardado en cada detalle)."""
    venta = Venta.query.get_or_404(id)
    if venta.estado == "Anulada":
        return jsonify({"error": "Esta venta ya está anulada"}), 400

    for detalle in venta.detalles:
        if detalle.lote_id:
            lote = Lote.query.get(detalle.lote_id)
            if lote:
                lote.cantidad_actual += detalle.cantidad

    venta.estado = "Anulada"
    db.session.commit()
    registrar_auditoria("anular", "Venta", venta.id, f"{venta.numero_venta} - S/ {venta.total:.2f}")
    return jsonify(venta.to_dict())