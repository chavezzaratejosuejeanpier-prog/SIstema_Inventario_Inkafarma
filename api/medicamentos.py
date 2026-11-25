from flask import Blueprint, request, jsonify
from extensions import db
from models import Medicamento, Laboratorio, Lote
from auth.decorators import login_requerido, requiere_rol
from api.auditoria import registrar_auditoria

medicamentos_bp = Blueprint("medicamentos_api", __name__, url_prefix="/api/medicamentos")


@medicamentos_bp.route("", methods=["GET"])
@login_requerido
def listar():
    activos_only = request.args.get("activos") == "1"
    sucursal_id = request.args.get("sucursal_id")

    query = Medicamento.query
    if activos_only:
        query = query.filter_by(activo=True)
    medicamentos = query.order_by(Medicamento.nombre).all()
    resultado = [m.to_dict() for m in medicamentos]

    if sucursal_id:



        stock_por_medicamento = {}
        for lote in Lote.query.filter_by(sucursal_id=sucursal_id).all():
            stock_por_medicamento[lote.medicamento_id] = stock_por_medicamento.get(lote.medicamento_id, 0) + lote.cantidad_actual
        for d in resultado:
            d["stock_total"] = stock_por_medicamento.get(d["id"], 0)

    return jsonify(resultado)


@medicamentos_bp.route("/<int:id>", methods=["GET"])
@login_requerido
def obtener(id):
    m = Medicamento.query.get_or_404(id)
    return jsonify(m.to_dict())


@medicamentos_bp.route("", methods=["POST"])
@requiere_rol("Administrador")
def crear():
    data = request.get_json()
    if not data.get("codigo") or not data.get("nombre") or not data.get("laboratorio_id"):
        return jsonify({"error": "Código, nombre y laboratorio son obligatorios"}), 400
    if Medicamento.query.filter_by(codigo=data["codigo"]).first():
        return jsonify({"error": "Ya existe un medicamento con ese código"}), 400

    m = Medicamento(
        codigo=data["codigo"],
        nombre=data["nombre"],
        laboratorio_id=data["laboratorio_id"],
        categoria=data.get("categoria"),
        presentacion=data.get("presentacion"),
        unidad_medida=data.get("unidad_medida"),
        precio_compra=float(data.get("precio_compra", 0)),
        precio_venta=float(data.get("precio_venta", 0)),
        requiere_receta=bool(data.get("requiere_receta", False)),
        stock_minimo=int(data.get("stock_minimo", 10)),
    )
    db.session.add(m)
    db.session.commit()
    registrar_auditoria("crear", "Medicamento", m.id, f"{m.codigo} - {m.nombre}")
    return jsonify(m.to_dict()), 201


@medicamentos_bp.route("/<int:id>", methods=["PUT"])
@requiere_rol("Administrador")
def actualizar(id):
    m = Medicamento.query.get_or_404(id)
    data = request.get_json()
    for campo in ["nombre", "categoria", "presentacion", "unidad_medida"]:
        if campo in data:
            setattr(m, campo, data[campo])
    if "laboratorio_id" in data:
        m.laboratorio_id = data["laboratorio_id"]
    if "precio_compra" in data:
        m.precio_compra = float(data["precio_compra"])
    if "precio_venta" in data:
        m.precio_venta = float(data["precio_venta"])
    if "requiere_receta" in data:
        m.requiere_receta = bool(data["requiere_receta"])
    if "stock_minimo" in data:
        m.stock_minimo = int(data["stock_minimo"])
    if "activo" in data:
        m.activo = bool(data["activo"])
    db.session.commit()
    registrar_auditoria("editar", "Medicamento", m.id, f"{m.codigo} - {m.nombre}")
    return jsonify(m.to_dict())


@medicamentos_bp.route("/<int:id>", methods=["DELETE"])
@requiere_rol("Administrador")
def eliminar(id):
    m = Medicamento.query.get_or_404(id)
    m.activo = False
    db.session.commit()
    registrar_auditoria("desactivar", "Medicamento", m.id, f"{m.codigo} - {m.nombre}")
    return jsonify({"mensaje": "Medicamento desactivado"})


laboratorios_bp = Blueprint("laboratorios_api", __name__, url_prefix="/api/laboratorios")


@laboratorios_bp.route("", methods=["GET"])
@login_requerido
def listar_laboratorios():
    labs = Laboratorio.query.order_by(Laboratorio.nombre).all()
    return jsonify([l.to_dict() for l in labs])


@laboratorios_bp.route("", methods=["POST"])
@requiere_rol("Administrador")
def crear_laboratorio():
    data = request.get_json()
    if not data.get("nombre"):
        return jsonify({"error": "El nombre es obligatorio"}), 400
    lab = Laboratorio(
        nombre=data["nombre"],
        ruc=data.get("ruc"),
        telefono=data.get("telefono"),
        email=data.get("email"),
        direccion=data.get("direccion"),
        latitud=data.get("latitud"),
        longitud=data.get("longitud"),
    )
    db.session.add(lab)
    db.session.commit()
    registrar_auditoria("crear", "Laboratorio", lab.id, lab.nombre)
    return jsonify(lab.to_dict()), 201


@laboratorios_bp.route("/<int:id>", methods=["PUT"])
@requiere_rol("Administrador")
def actualizar_laboratorio(id):
    lab = Laboratorio.query.get_or_404(id)
    data = request.get_json()
    for campo in ["nombre", "ruc", "telefono", "email", "direccion", "latitud", "longitud"]:
        if campo in data:
            setattr(lab, campo, data[campo])
    if "activo" in data:
        lab.activo = bool(data["activo"])
    db.session.commit()
    registrar_auditoria("editar", "Laboratorio", lab.id, lab.nombre)
    return jsonify(lab.to_dict())


@laboratorios_bp.route("/<int:id>", methods=["DELETE"])
@requiere_rol("Administrador")
def eliminar_laboratorio(id):
    lab = Laboratorio.query.get_or_404(id)
    lab.activo = False
    db.session.commit()
    registrar_auditoria("desactivar", "Laboratorio", lab.id, lab.nombre)
    return jsonify({"mensaje": "Laboratorio desactivado"})
