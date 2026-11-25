import random
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from extensions import db
from models import Compra, DetalleCompra, Lote, Medicamento
from auth.decorators import login_requerido, requiere_rol
from api.auditoria import registrar_auditoria

compras_bp = Blueprint("compras_api", __name__, url_prefix="/api/compras")


def _generar_numero_compra():
    return f"OC-{datetime.utcnow().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"


@compras_bp.route("", methods=["GET"])
@login_requerido
def listar():
    query = Compra.query
    if request.args.get("sucursal_id"):
        query = query.filter_by(sucursal_id=request.args.get("sucursal_id"))
    compras = query.order_by(Compra.fecha.desc()).all()
    return jsonify([c.to_dict() for c in compras])


@compras_bp.route("", methods=["POST"])
@requiere_rol("Administrador")
def crear():
    """Registra una compra a un laboratorio. Cada ítem genera un nuevo
    lote (o incrementa uno existente) para reflejar el ingreso de stock."""
    data = request.get_json()
    items = data.get("items", [])
    if not data.get("laboratorio_id") or not data.get("sucursal_id") or not items:
        return jsonify({"error": "Laboratorio, sucursal y al menos un ítem son obligatorios"}), 400

    compra = Compra(
        numero_compra=_generar_numero_compra(),
        laboratorio_id=data["laboratorio_id"],
        usuario_id=session["usuario_id"],
        sucursal_id=data["sucursal_id"],
        total=0,
    )
    db.session.add(compra)
    db.session.flush()

    total = 0.0
    for item in items:
        medicamento = Medicamento.query.get(item["medicamento_id"])
        if not medicamento:
            continue
        cantidad = int(item["cantidad"])
        precio_unitario = float(item["precio_unitario"])
        subtotal = round(cantidad * precio_unitario, 2)
        total += subtotal

        lote = Lote(
            medicamento_id=medicamento.id,
            sucursal_id=compra.sucursal_id,
            numero_lote=item.get("numero_lote", f"L-{random.randint(10000, 99999)}"),
            fecha_vencimiento=datetime.strptime(item["fecha_vencimiento"], "%Y-%m-%d").date(),
            cantidad_inicial=cantidad,
            cantidad_actual=cantidad,
            precio_compra_unitario=precio_unitario,
        )
        db.session.add(lote)
        db.session.flush()

        detalle = DetalleCompra(
            compra_id=compra.id,
            medicamento_id=medicamento.id,
            lote_id=lote.id,
            cantidad=cantidad,
            precio_unitario=precio_unitario,
            subtotal=subtotal,
        )
        db.session.add(detalle)

    compra.total = round(total, 2)
    db.session.commit()
    registrar_auditoria("crear", "Compra", compra.id, f"{compra.numero_compra} - S/ {compra.total:.2f}")
    return jsonify(compra.to_dict()), 201


@compras_bp.route("/<int:id>/anular", methods=["POST"])
@requiere_rol("Administrador")
def anular(id):
    """Anula una compra ya registrada y revierte el stock que había
    ingresado a cada lote. Si de algún lote ya se vendieron unidades
    (cantidad_actual < lo que esa compra ingresó), no se puede anular:
    habría que dejar el stock en negativo."""
    compra = Compra.query.get_or_404(id)
    if compra.estado == "Anulada":
        return jsonify({"error": "Esta compra ya está anulada"}), 400

    for detalle in compra.detalles:
        if detalle.lote_id:
            lote = Lote.query.get(detalle.lote_id)
            if lote and lote.cantidad_actual < detalle.cantidad:
                return jsonify({
                    "error": f"No se puede anular: ya se vendieron unidades del lote {lote.numero_lote}."
                }), 400

    for detalle in compra.detalles:
        if detalle.lote_id:
            lote = Lote.query.get(detalle.lote_id)
            if lote:
                lote.cantidad_actual -= detalle.cantidad

    compra.estado = "Anulada"
    db.session.commit()
    registrar_auditoria("anular", "Compra", compra.id, f"{compra.numero_compra} - S/ {compra.total:.2f}")
    return jsonify(compra.to_dict())
