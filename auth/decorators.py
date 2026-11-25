from functools import wraps
from flask import session, redirect, url_for, jsonify, request


def login_requerido(f):
    @wraps(f)
    def envoltura(*args, **kwargs):
        if "usuario_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "No autenticado"}), 401
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return envoltura


def requiere_rol(*roles_permitidos):
    """Uso: @requiere_rol('Administrador', 'Farmacéutico')"""
    def decorador(f):
        @wraps(f)
        def envoltura(*args, **kwargs):
            if "usuario_id" not in session:
                if request.path.startswith("/api/"):
                    return jsonify({"error": "No autenticado"}), 401
                return redirect(url_for("auth.login"))
            if session.get("rol") not in roles_permitidos:
                if request.path.startswith("/api/"):
                    return jsonify({"error": "No tiene permisos para esta acción"}), 403
                return redirect(url_for("dashboard.index"))
            return f(*args, **kwargs)
        return envoltura
    return decorador
