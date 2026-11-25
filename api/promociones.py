from datetime import datetime

from flask import Blueprint, request, jsonify
from extensions import db
from models import Promocion, Medicamento
from auth.decorators import login_requerido, requiere_rol
from api.auditoria import registrar_auditoria

promociones_bp = Blueprint("promociones_api", __name__, url_prefix="/api/promociones")

TIPOS_VALIDOS = {"porcentaje", "monto_fijo", "nxm", "cupon"}


def _parsear_fecha(valor, campo):
    try:
        return datetime.strptime(valor, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise ValueError(f"Fecha de {campo} inválida")


def _validar_payload(data, promocion_id_actual=None):
    tipo = data.get("tipo")
    if tipo not in TIPOS_VALIDOS:
        return "Tipo de promoción inválido"

    if tipo in ("porcentaje", "monto_fijo", "nxm"):
        if not data.get("medicamento_id"):
            return "Selecciona el medicamento al que aplica la promoción"
        if not Medicamento.query.get(data["medicamento_id"]):
            return "El medicamento seleccionado no existe"

    if tipo == "porcentaje":
        valor = data.get("valor")
        if not valor or not (0 < float(valor) <= 100):
            return "El porcentaje debe estar entre 1 y 100"

    if tipo == "monto_fijo":
        if not data.get("valor") or float(data["valor"]) <= 0:
            return "El monto de descuento debe ser mayor a 0"

    if tipo == "nxm":
        lleva, paga = data.get("lleva"), data.get("paga")
        if not lleva or not paga or int(paga) >= int(lleva) or int(paga) < 1:
            return "Revisa 'lleva' y 'paga': por ejemplo 3x2 es lleva=3, paga=2"

    if tipo == "cupon":
        codigo = (data.get("codigo") or "").strip().upper()
        if not codigo:
            return "El código del cupón es obligatorio"
        existente = Promocion.query.filter(db.func.upper(Promocion.codigo) == codigo).first()
        if existente and existente.id != promocion_id_actual:
            return "Ya existe un cupón con ese código"
        valor = data.get("valor")
        if not valor or not (0 < float(valor) <= 100):
            return "El porcentaje del cupón debe estar entre 1 y 100"

    if not data.get("fecha_inicio") or not data.get("fecha_fin"):
        return "Las fechas de inicio y fin son obligatorias"

    try:
        inicio = _parsear_fecha(data["fecha_inicio"], "inicio")
        fin = _parsear_fecha(data["fecha_fin"], "fin")
    except ValueError as e:
        return str(e)
    if fin < inicio:
        return "La fecha de fin no puede ser anterior a la de inicio"

    return None


def _aplicar_campos(promocion, data):
    promocion.nombre = data["nombre"]
    promocion.tipo = data["tipo"]
    promocion.fecha_inicio = _parsear_fecha(data["fecha_inicio"], "inicio")
    promocion.fecha_fin = _parsear_fecha(data["fecha_fin"], "fin")
    promocion.sucursal_id = data.get("sucursal_id") or None

    if promocion.tipo in ("porcentaje", "monto_fijo", "nxm"):
        promocion.medicamento_id = data["medicamento_id"]
        promocion.codigo = None
    else:
        promocion.medicamento_id = None
        promocion.codigo = data["codigo"].strip().upper()

    promocion.valor = float(data["valor"]) if data.get("valor") not in (None, "") else None
    promocion.lleva = int(data["lleva"]) if promocion.tipo == "nxm" else None
    promocion.paga = int(data["paga"]) if promocion.tipo == "nxm" else None


@promociones_bp.route("", methods=["GET"])
@login_requerido
def listar():
    query = Promocion.query
    if request.args.get("vigentes") == "1":
        hoy = datetime.utcnow().date()
        query = query.filter(Promocion.activo == True, Promocion.fecha_inicio <= hoy, Promocion.fecha_fin >= hoy)
    promociones = query.order_by(Promocion.fecha_inicio.desc()).all()
    return jsonify([p.to_dict() for p in promociones])


@promociones_bp.route("", methods=["POST"])
@requiere_rol("Administrador")
def crear():
    data = request.get_json()
    if not data.get("nombre"):
        return jsonify({"error": "El nombre es obligatorio"}), 400
    error = _validar_payload(data)
    if error:
        return jsonify({"error": error}), 400

    promocion = Promocion()
    _aplicar_campos(promocion, data)
    db.session.add(promocion)
    db.session.commit()
    registrar_auditoria("crear", "Promocion", promocion.id, promocion.nombre)
    return jsonify(promocion.to_dict()), 201


@promociones_bp.route("/<int:id>", methods=["PUT"])
@requiere_rol("Administrador")
def actualizar(id):
    promocion = Promocion.query.get_or_404(id)
    data = request.get_json()

    if "activo" in data and len(data) == 1:
        promocion.activo = bool(data["activo"])
        db.session.commit()
        registrar_auditoria("editar", "Promocion", promocion.id, promocion.nombre)
        return jsonify(promocion.to_dict())

    if not data.get("nombre"):
        return jsonify({"error": "El nombre es obligatorio"}), 400
    error = _validar_payload(data, promocion_id_actual=id)
    if error:
        return jsonify({"error": error}), 400

    _aplicar_campos(promocion, data)
    if "activo" in data:
        promocion.activo = bool(data["activo"])
    db.session.commit()
    registrar_auditoria("editar", "Promocion", promocion.id, promocion.nombre)
    return jsonify(promocion.to_dict())


@promociones_bp.route("/<int:id>", methods=["DELETE"])
@requiere_rol("Administrador")
def eliminar(id):
    promocion = Promocion.query.get_or_404(id)
    promocion.activo = False
    db.session.commit()
    registrar_auditoria("desactivar", "Promocion", promocion.id, promocion.nombre)
    return jsonify({"mensaje": "Promoción desactivada"})