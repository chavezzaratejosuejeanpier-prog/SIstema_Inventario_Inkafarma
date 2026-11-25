from flask import Blueprint, jsonify, session
from extensions import db
from models import RegistroAuditoria
from auth.decorators import requiere_rol

auditoria_bp = Blueprint("auditoria_api", __name__, url_prefix="/api/auditoria")


def registrar_auditoria(accion, entidad, entidad_id=None, detalle=None):
    """Registra una entrada en el historial de auditoría (quién hizo qué,
    sobre qué entidad y cuándo). Se llama *después* de confirmar la
    operación de negocio, en su propia transacción: si el registro de
    auditoría fallara por algún motivo, nunca debe tumbar ni revertir la
    operación que ya se guardó correctamente.
    """
    try:
        registro = RegistroAuditoria(
            usuario_id=session.get("usuario_id"),
            accion=accion,
            entidad=entidad,
            entidad_id=entidad_id,
            detalle=detalle,
        )
        db.session.add(registro)
        db.session.commit()
    except Exception:
        db.session.rollback()


@auditoria_bp.route("", methods=["GET"])
@requiere_rol("Administrador")
def listar():
    registros = RegistroAuditoria.query.order_by(RegistroAuditoria.fecha.desc()).limit(500).all()
    return jsonify([r.to_dict() for r in registros])