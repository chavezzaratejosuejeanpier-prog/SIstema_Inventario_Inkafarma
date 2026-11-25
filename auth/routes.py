from datetime import datetime, timedelta
from math import ceil

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from extensions import db
from models import Usuario, CodigoRecuperacion
from auth.correo import enviar_codigo_recuperacion

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")



INTENTOS_MAXIMOS = 5
DURACION_BLOQUEO = timedelta(hours=1)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and usuario.bloqueado:
            minutos_restantes = max(1, ceil((usuario.bloqueado_hasta - datetime.utcnow()).total_seconds() / 60))
            flash(
                f"Cuenta bloqueada temporalmente por demasiados intentos fallidos. "
                f"Intenta de nuevo en {minutos_restantes} min, o usa '¿Olvidaste tu contraseña?' "
                f"para recuperar el acceso ahora mismo.",
                "error",
            )
            return redirect(url_for("auth.login"))

        if usuario and usuario.activo and usuario.check_password(password):
            usuario.intentos_fallidos = 0
            usuario.bloqueado_hasta = None
            db.session.commit()
            session.permanent = True
            session["usuario_id"] = usuario.id
            session["usuario_nombre"] = usuario.nombre
            session["rol"] = usuario.rol.nombre
            session["sucursal_id"] = usuario.sucursal_id
            session["sucursal_nombre"] = usuario.sucursal.nombre if usuario.sucursal else None
            return redirect(url_for("dashboard.index"))

        if usuario and usuario.activo:
            usuario.intentos_fallidos = (usuario.intentos_fallidos or 0) + 1
            if usuario.intentos_fallidos >= INTENTOS_MAXIMOS:
                usuario.bloqueado_hasta = datetime.utcnow() + DURACION_BLOQUEO
                usuario.intentos_fallidos = 0
                db.session.commit()
                flash(
                    "Demasiados intentos fallidos. Tu cuenta quedó bloqueada por 1 hora. "
                    "Si no quieres esperar, usa '¿Olvidaste tu contraseña?' para recuperar el acceso ahora.",
                    "error",
                )
                return redirect(url_for("auth.login"))
            db.session.commit()

        flash("Correo o contraseña incorrectos, o usuario inactivo.", "error")
        return redirect(url_for("auth.login"))

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


@auth_bp.route("/olvide-password", methods=["GET", "POST"])
def olvide_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and usuario.activo:
            codigo = CodigoRecuperacion.crear_para(usuario)
            db.session.commit()
            try:
                enviar_codigo_recuperacion(usuario.nombre, usuario.email, codigo.codigo)
            except Exception:
                flash("No se pudo enviar el correo con el código. Intenta de nuevo en unos minutos.", "error")
                return redirect(url_for("auth.olvide_password"))


        flash("Si el correo está registrado, te enviamos un código de verificación.", "exito")
        return redirect(url_for("auth.verificar_codigo", email=email))

    return render_template("olvide_password.html")


@auth_bp.route("/verificar-codigo", methods=["GET", "POST"])
def verificar_codigo():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        codigo_ingresado = request.form.get("codigo", "").strip()
        password = request.form.get("password", "")
        password2 = request.form.get("password2", "")

        if password != password2:
            flash("Las contraseñas no coinciden.", "error")
            return render_template("verificar_codigo.html", email=email)
        if len(password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "error")
            return render_template("verificar_codigo.html", email=email)

        usuario = Usuario.query.filter_by(email=email).first()



        codigo = (
            CodigoRecuperacion.query.filter_by(usuario_id=usuario.id if usuario else None, usado=False)
            .order_by(CodigoRecuperacion.creado.desc())
            .first()
        )

        if not usuario or not codigo or codigo.expirado or (codigo.intentos or 0) >= CodigoRecuperacion.LIMITE_INTENTOS:
            flash("El código es inválido o ya expiró. Solicita uno nuevo.", "error")
            return render_template("verificar_codigo.html", email=email)

        if codigo.codigo != codigo_ingresado:
            codigo.intentos = (codigo.intentos or 0) + 1
            if codigo.intentos >= CodigoRecuperacion.LIMITE_INTENTOS:
                codigo.usado = True
            db.session.commit()
            flash("El código es inválido o ya expiró. Solicita uno nuevo.", "error")
            return render_template("verificar_codigo.html", email=email)

        usuario.set_password(password)
        usuario.intentos_fallidos = 0
        usuario.bloqueado_hasta = None
        codigo.usado = True
        db.session.commit()

        flash("Contraseña actualizada correctamente. Ya puedes iniciar sesión.", "exito")
        return redirect(url_for("auth.login"))

    email = request.args.get("email", "")
    return render_template("verificar_codigo.html", email=email)
