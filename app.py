from flask import Flask, render_template, redirect, url_for, session
from sqlalchemy import inspect, text

from config import Config
from extensions import db, csrf
from auth.decorators import login_requerido, requiere_rol
from auth.routes import auth_bp
from api.medicamentos import medicamentos_bp, laboratorios_bp
from api.lotes import lotes_bp
from api.compras import compras_bp
from api.ventas import ventas_bp
from api.usuarios import usuarios_bp
from api.dashboard import dashboard_bp
from api.reportes import reportes_bp
from api.auditoria import auditoria_bp
from api.sucursales import sucursales_bp
from api.promociones import promociones_bp


def _migrar_columnas_faltantes():
    """Agrega columnas nuevas a tablas que ya existían antes de que el
    modelo las incorporara (db.create_all() solo crea tablas nuevas, no
    altera las existentes). Es idempotente: si la columna ya existe, no
    hace nada.
    """
    inspector = inspect(db.engine)
    tablas = inspector.get_table_names()

    with db.engine.begin() as conexion:
        if "usuarios" in tablas:
            columnas = {c["name"] for c in inspector.get_columns("usuarios")}
            if "intentos_fallidos" not in columnas:
                conexion.execute(text("ALTER TABLE usuarios ADD COLUMN intentos_fallidos INTEGER DEFAULT 0"))
            if "bloqueado_hasta" not in columnas:
                conexion.execute(text("ALTER TABLE usuarios ADD COLUMN bloqueado_hasta TIMESTAMP"))

            if "sucursal_id" not in columnas:
                conexion.execute(text("ALTER TABLE usuarios ADD COLUMN sucursal_id INTEGER"))

        if "ventas" in tablas:
            columnas_ventas = {c["name"] for c in inspector.get_columns("ventas")}
            if "cliente_email" not in columnas_ventas:
                conexion.execute(text("ALTER TABLE ventas ADD COLUMN cliente_email VARCHAR(120)"))
            if "descuento" not in columnas_ventas:
                conexion.execute(text("ALTER TABLE ventas ADD COLUMN descuento FLOAT DEFAULT 0"))
            if "sucursal_id" not in columnas_ventas:
                conexion.execute(text("ALTER TABLE ventas ADD COLUMN sucursal_id INTEGER"))
            if "cupon_codigo" not in columnas_ventas:
                conexion.execute(text("ALTER TABLE ventas ADD COLUMN cupon_codigo VARCHAR(30)"))
            if "referencia_pago" not in columnas_ventas:
                conexion.execute(text("ALTER TABLE ventas ADD COLUMN referencia_pago VARCHAR(60)"))

        if "detalle_ventas" in tablas:
            columnas_detalle = {c["name"] for c in inspector.get_columns("detalle_ventas")}
            if "numero_receta" not in columnas_detalle:
                conexion.execute(text("ALTER TABLE detalle_ventas ADD COLUMN numero_receta VARCHAR(50)"))
            if "promocion_id" not in columnas_detalle:
                conexion.execute(text("ALTER TABLE detalle_ventas ADD COLUMN promocion_id INTEGER"))
            if "descuento" not in columnas_detalle:
                conexion.execute(text("ALTER TABLE detalle_ventas ADD COLUMN descuento FLOAT DEFAULT 0"))

        if "lotes" in tablas:
            columnas_lotes = {c["name"] for c in inspector.get_columns("lotes")}
            if "sucursal_id" not in columnas_lotes:
                conexion.execute(text("ALTER TABLE lotes ADD COLUMN sucursal_id INTEGER"))

        if "compras" in tablas:
            columnas_compras = {c["name"] for c in inspector.get_columns("compras")}
            if "sucursal_id" not in columnas_compras:
                conexion.execute(text("ALTER TABLE compras ADD COLUMN sucursal_id INTEGER"))

        if "sucursales" in tablas:
            columnas_sucursales = {c["name"] for c in inspector.get_columns("sucursales")}
            if "latitud" not in columnas_sucursales:
                conexion.execute(text("ALTER TABLE sucursales ADD COLUMN latitud FLOAT"))
            if "longitud" not in columnas_sucursales:
                conexion.execute(text("ALTER TABLE sucursales ADD COLUMN longitud FLOAT"))

        if "laboratorios" in tablas:
            columnas_laboratorios = {c["name"] for c in inspector.get_columns("laboratorios")}
            if "latitud" not in columnas_laboratorios:
                conexion.execute(text("ALTER TABLE laboratorios ADD COLUMN latitud FLOAT"))
            if "longitud" not in columnas_laboratorios:
                conexion.execute(text("ALTER TABLE laboratorios ADD COLUMN longitud FLOAT"))

        if "codigos_recuperacion" in tablas:
            columnas_codigos = {c["name"] for c in inspector.get_columns("codigos_recuperacion")}
            if "intentos" not in columnas_codigos:
                conexion.execute(text("ALTER TABLE codigos_recuperacion ADD COLUMN intentos INTEGER DEFAULT 0"))


def _asegurar_sucursal_principal():
    """Crea una sucursal por defecto si todavía no existe ninguna, y le
    asigna los usuarios/lotes/compras/ventas que hayan quedado sin
    sucursal_id (datos creados antes de que existiera este concepto).
    Así el sistema sigue funcionando igual que antes sin perder nada al
    activar el soporte multi-sucursal."""
    from models import Compra, Lote, Sucursal, Usuario, Venta

    sucursal = Sucursal.query.first()
    if not sucursal:
        sucursal = Sucursal(nombre="Sucursal Principal", direccion="Casa Matriz")
        db.session.add(sucursal)
        db.session.commit()

    Usuario.query.filter_by(sucursal_id=None).update({"sucursal_id": sucursal.id})
    Lote.query.filter_by(sucursal_id=None).update({"sucursal_id": sucursal.id})
    Compra.query.filter_by(sucursal_id=None).update({"sucursal_id": sucursal.id})
    Venta.query.filter_by(sucursal_id=None).update({"sucursal_id": sucursal.id})
    db.session.commit()


def crear_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    csrf.init_app(app)





    with app.app_context():
        db.create_all()
        _migrar_columnas_faltantes()
        _asegurar_sucursal_principal()


    app.register_blueprint(auth_bp)
    app.register_blueprint(medicamentos_bp)
    app.register_blueprint(laboratorios_bp)
    app.register_blueprint(lotes_bp)
    app.register_blueprint(compras_bp)
    app.register_blueprint(ventas_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(reportes_bp)
    app.register_blueprint(auditoria_bp)
    app.register_blueprint(sucursales_bp)
    app.register_blueprint(promociones_bp)




    @app.route("/")
    def raiz():
        if "usuario_id" in session:
            return redirect(url_for("dashboard.index"))
        return redirect(url_for("auth.login"))

    @app.context_processor
    def variables_globales():
        return {
            "usuario_id": session.get("usuario_id"),
            "usuario_nombre": session.get("usuario_nombre"),
            "usuario_rol": session.get("rol"),
            "usuario_sucursal_id": session.get("sucursal_id"),
            "usuario_sucursal_nombre": session.get("sucursal_nombre"),
        }

    from flask import Blueprint
    dashboard_pages = Blueprint("dashboard", __name__)

    @dashboard_pages.route("/dashboard")
    @login_requerido
    def index():
        if session.get("rol") == "Administrador":
            return render_template("admin/dashboard.html")
        return render_template("cajero/dashboard.html")

    @dashboard_pages.route("/medicamentos")
    @login_requerido
    def medicamentos_page():
        return render_template("medicamentos.html")

    @dashboard_pages.route("/laboratorios")
    @requiere_rol("Administrador")
    def laboratorios_page():
        return render_template("admin/laboratorios.html")

    @dashboard_pages.route("/lotes")
    @requiere_rol("Administrador")
    def lotes_page():
        return render_template("admin/lotes.html")

    @dashboard_pages.route("/compras")
    @requiere_rol("Administrador")
    def compras_page():
        return render_template("admin/compras.html")

    @dashboard_pages.route("/ventas")
    @requiere_rol("Administrador", "Cajero")
    def ventas_page():
        if session.get("rol") == "Administrador":
            return render_template("admin/ventas.html")
        return render_template("cajero/ventas.html")

    @dashboard_pages.route("/mis-ventas")
    @requiere_rol("Cajero")
    def historial_ventas_page():
        return render_template("cajero/historial.html")

    @dashboard_pages.route("/alertas")
    @requiere_rol("Administrador")
    def alertas_page():
        return render_template("admin/alertas.html")

    @dashboard_pages.route("/usuarios")
    @requiere_rol("Administrador")
    def usuarios_page():
        return render_template("admin/usuarios.html")

    @dashboard_pages.route("/auditoria")
    @requiere_rol("Administrador")
    def auditoria_page():
        return render_template("admin/auditoria.html")

    @dashboard_pages.route("/sucursales")
    @requiere_rol("Administrador")
    def sucursales_page():
        return render_template("admin/sucursales.html")

    @dashboard_pages.route("/promociones")
    @requiere_rol("Administrador")
    def promociones_page():
        return render_template("admin/promociones.html")

    @dashboard_pages.route("/perfil")
    @login_requerido
    def perfil_page():
        return render_template("perfil.html")

    app.register_blueprint(dashboard_pages)

    return app


app = crear_app()

if __name__ == "__main__":




    app.run(port=5000)
