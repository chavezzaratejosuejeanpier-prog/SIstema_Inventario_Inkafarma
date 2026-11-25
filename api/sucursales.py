from flask import Blueprint, request, jsonify
from extensions import db
from models import Sucursal
from auth.decorators import login_requerido, requiere_rol
from api.auditoria import registrar_auditoria

sucursales_bp = Blueprint("sucursales_api", __name__, url_prefix="/api/sucursales")


@sucursales_bp.route("", methods=["GET"])
@login_requerido
def listar():
    sucursales = Sucursal.query.order_by(Sucursal.nombre).all()
    return jsonify([s.to_dict() for s in sucursales])


@sucursales_bp.route("", methods=["POST"])
@requiere_rol("Administrador")
def crear():
    data = request.get_json()
    if not data.get("nombre"):
        return jsonify({"error": "El nombre es obligatorio"}), 400

    sucursal = Sucursal(
        nombre=data["nombre"],
        direccion=data.get("direccion"),
        telefono=data.get("telefono"),
        latitud=data.get("latitud"),
        longitud=data.get("longitud"),
    )
    db.session.add(sucursal)
    db.session.commit()
    registrar_auditoria("crear", "Sucursal", sucursal.id, sucursal.nombre)
    return jsonify(sucursal.to_dict()), 201


@sucursales_bp.route("/<int:id>", methods=["PUT"])
@requiere_rol("Administrador")
def actualizar(id):
    sucursal = Sucursal.query.get_or_404(id)
    data = request.get_json()
    for campo in ["nombre", "direccion", "telefono", "latitud", "longitud"]:
        if campo in data:
            setattr(sucursal, campo, data[campo])
    if "activo" in data:
        sucursal.activo = bool(data["activo"])
    db.session.commit()
    registrar_auditoria("editar", "Sucursal", sucursal.id, sucursal.nombre)
    return jsonify(sucursal.to_dict())


@sucursales_bp.route("/<int:id>", methods=["DELETE"])
@requiere_rol("Administrador")
def eliminar(id):
    sucursal = Sucursal.query.get_or_404(id)
    if Sucursal.query.filter_by(activo=True).count() <= 1 and sucursal.activo:
        return jsonify({"error": "Debe existir al menos una sucursal activa"}), 400
    sucursal.activo = False
    db.session.commit()
    registrar_auditoria("desactivar", "Sucursal", sucursal.id, sucursal.nombre)
    return jsonify({"mensaje": "Sucursal desactivada"})