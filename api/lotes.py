from datetime import datetime
from flask import Blueprint, request, jsonify
from extensions import db
from models import Lote, Medicamento
from auth.decorators import login_requerido, requiere_rol
from api.auditoria import registrar_auditoria

lotes_bp = Blueprint("lotes_api", __name__, url_prefix="/api/lotes")


@lotes_bp.route("", methods=["GET"])
@login_requerido
def listar():
    medicamento_id = request.args.get("medicamento_id")
    sucursal_id = request.args.get("sucursal_id")
    query = Lote.query
    if medicamento_id:
        query = query.filter_by(medicamento_id=medicamento_id)
    if sucursal_id:
        query = query.filter_by(sucursal_id=sucursal_id)
    lotes = query.order_by(Lote.fecha_vencimiento).all()
    return jsonify([l.to_dict() for l in lotes])


@lotes_bp.route("", methods=["POST"])
@requiere_rol("Administrador")
def crear():
    data = request.get_json()
    requeridos = ["medicamento_id", "sucursal_id", "numero_lote", "fecha_vencimiento", "cantidad_inicial"]
    if not all(data.get(c) for c in requeridos):
        return jsonify({"error": "Faltan campos obligatorios del lote (incluida la sucursal)"}), 400

    medicamento = Medicamento.query.get(data["medicamento_id"])
    if not medicamento:
        return jsonify({"error": "Medicamento no encontrado"}), 404

    cantidad = int(data["cantidad_inicial"])
    lote = Lote(
        medicamento_id=data["medicamento_id"],
        sucursal_id=data["sucursal_id"],
        numero_lote=data["numero_lote"],
        fecha_fabricacion=datetime.strptime(data["fecha_fabricacion"], "%Y-%m-%d").date()
        if data.get("fecha_fabricacion") else None,
        fecha_vencimiento=datetime.strptime(data["fecha_vencimiento"], "%Y-%m-%d").date(),
        cantidad_inicial=cantidad,
        cantidad_actual=cantidad,
        precio_compra_unitario=float(data.get("precio_compra_unitario", medicamento.precio_compra)),
    )
    db.session.add(lote)
    db.session.commit()
    registrar_auditoria("crear", "Lote", lote.id, f"{lote.numero_lote} ({medicamento.nombre})")
    return jsonify(lote.to_dict()), 201


@lotes_bp.route("/<int:id>", methods=["PUT"])
@requiere_rol("Administrador")
def actualizar(id):
    lote = Lote.query.get_or_404(id)
    data = request.get_json()
    if "numero_lote" in data:
        lote.numero_lote = data["numero_lote"]
    if "fecha_vencimiento" in data:
        lote.fecha_vencimiento = datetime.strptime(data["fecha_vencimiento"], "%Y-%m-%d").date()
    if "cantidad_actual" in data:
        lote.cantidad_actual = int(data["cantidad_actual"])
    if "precio_compra_unitario" in data:
        lote.precio_compra_unitario = float(data["precio_compra_unitario"])
    db.session.commit()
    registrar_auditoria("editar", "Lote", lote.id, lote.numero_lote)
    return jsonify(lote.to_dict())


@lotes_bp.route("/<int:id>", methods=["DELETE"])
@requiere_rol("Administrador")
def eliminar(id):
    lote = Lote.query.get_or_404(id)
    numero_lote = lote.numero_lote
    db.session.delete(lote)
    db.session.commit()
    registrar_auditoria("eliminar", "Lote", id, numero_lote)
    return jsonify({"mensaje": "Lote eliminado"})
