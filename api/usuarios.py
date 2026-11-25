from flask import Blueprint, request, jsonify, session
from sqlalchemy.exc import IntegrityError
from extensions import db
from models import Usuario, Rol
from auth.decorators import login_requerido, requiere_rol
from api.auditoria import registrar_auditoria

usuarios_bp = Blueprint("usuarios_api", __name__, url_prefix="/api/usuarios")


@usuarios_bp.route("", methods=["GET"])
@requiere_rol("Administrador")
def listar():
    usuarios = Usuario.query.order_by(Usuario.nombre).all()
    return jsonify([u.to_dict() for u in usuarios])


@usuarios_bp.route("", methods=["POST"])
@requiere_rol("Administrador")
def crear():
    data = request.get_json()
    if not all([data.get("nombre"), data.get("email"), data.get("password"), data.get("rol_id")]):
        return jsonify({"error": "Todos los campos son obligatorios"}), 400
    if Usuario.query.filter_by(email=data["email"].lower()).first():
        return jsonify({"error": "Ese correo ya está registrado"}), 400

    rol = Rol.query.get(data["rol_id"])
    if rol and rol.nombre == "Cajero" and not data.get("sucursal_id"):
        return jsonify({"error": "Selecciona la sucursal donde trabajará el cajero"}), 400

    usuario = Usuario(
        nombre=data["nombre"], email=data["email"].lower(), rol_id=data["rol_id"],
        sucursal_id=data.get("sucursal_id") or None,
    )
    usuario.set_password(data["password"])
    db.session.add(usuario)
    db.session.commit()
    registrar_auditoria("crear", "Usuario", usuario.id, f"{usuario.nombre} ({usuario.email})")
    return jsonify(usuario.to_dict()), 201


@usuarios_bp.route("/<int:id>", methods=["PUT"])
@requiere_rol("Administrador")
def actualizar(id):
    usuario = Usuario.query.get_or_404(id)
    data = request.get_json()
    if "activo" in data and id == session.get("usuario_id") and not data["activo"]:
        return jsonify({"error": "No puedes desactivar tu propio usuario"}), 400

    rol_id_final = data.get("rol_id", usuario.rol_id)
    sucursal_id_final = data["sucursal_id"] if "sucursal_id" in data else usuario.sucursal_id
    if "rol_id" in data or "sucursal_id" in data:
        rol_final = Rol.query.get(rol_id_final)
        if rol_final and rol_final.nombre == "Cajero" and not sucursal_id_final:
            return jsonify({"error": "Selecciona la sucursal donde trabajará el cajero"}), 400

    if "nombre" in data:
        usuario.nombre = data["nombre"]
    if "rol_id" in data:
        usuario.rol_id = data["rol_id"]
    if "sucursal_id" in data:
        usuario.sucursal_id = data["sucursal_id"] or None
    if "activo" in data:
        usuario.activo = bool(data["activo"])
    if data.get("password"):
        usuario.set_password(data["password"])
    db.session.commit()

    if "activo" in data and len(data) == 1:
        accion = "activar" if usuario.activo else "desactivar"
    else:
        accion = "editar"
    registrar_auditoria(accion, "Usuario", usuario.id, f"{usuario.nombre} ({usuario.email})")
    return jsonify(usuario.to_dict())


@usuarios_bp.route("/<int:id>", methods=["DELETE"])
@requiere_rol("Administrador")
def eliminar(id):
    if id == session.get("usuario_id"):
        return jsonify({"error": "No puedes eliminar tu propio usuario"}), 400
    usuario = Usuario.query.get_or_404(id)
    descripcion = f"{usuario.nombre} ({usuario.email})"
    db.session.delete(usuario)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "error": "No se puede eliminar: este usuario tiene ventas o compras registradas. Desactívalo en su lugar."
        }), 400
    registrar_auditoria("eliminar", "Usuario", id, descripcion)
    return jsonify({"mensaje": "Usuario eliminado correctamente"})


@usuarios_bp.route("/roles", methods=["GET"])
@login_requerido
def listar_roles():
    roles = Rol.query.all()
    return jsonify([r.to_dict() for r in roles])


@usuarios_bp.route("/me", methods=["GET"])
@login_requerido
def mi_perfil():
    usuario = Usuario.query.get_or_404(session["usuario_id"])
    return jsonify(usuario.to_dict())


@usuarios_bp.route("/me/password", methods=["PUT"])
@login_requerido
def cambiar_mi_password():
    """Permite a cualquier usuario autenticado (Administrador o Cajero)
    cambiar su propia contraseña, verificando primero la actual. A
    diferencia de PUT /api/usuarios/<id>, esta ruta no requiere rol de
    Administrador porque solo modifica al usuario de la sesión activa."""
    usuario = Usuario.query.get_or_404(session["usuario_id"])
    data = request.get_json()
    actual = data.get("password_actual", "")
    nueva = data.get("password_nueva", "")

    if not actual or not nueva:
        return jsonify({"error": "Completa ambos campos de contraseña"}), 400
    if not usuario.check_password(actual):
        return jsonify({"error": "La contraseña actual es incorrecta", "campo": "actual"}), 400
    if len(nueva) < 6:
        return jsonify({"error": "La nueva contraseña debe tener al menos 6 caracteres", "campo": "nueva"}), 400
    if usuario.check_password(nueva):
        return jsonify({"error": "La nueva contraseña debe ser diferente de la actual", "campo": "nueva"}), 400

    usuario.set_password(nueva)
    db.session.commit()
    registrar_auditoria("editar", "Usuario", usuario.id, "Cambió su propia contraseña")
    return jsonify({"mensaje": "Contraseña actualizada correctamente"})
