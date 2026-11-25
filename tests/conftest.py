"""Fixtures compartidas por toda la suite de tests.

Cada test corre contra una base de datos SQLite en memoria (ConfigPruebas),
completamente aislada de la base de datos real de desarrollo: nunca se
toca inkafarma.db ni PostgreSQL.
"""
from datetime import date

import pytest

from app import crear_app
from config import ConfigPruebas
from extensions import db
from models import Laboratorio, Lote, Medicamento, Rol, Sucursal, Usuario


@pytest.fixture
def app():
    aplicacion = crear_app(ConfigPruebas)
    yield aplicacion


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def datos_base(app):
    """Crea roles, dos sucursales, un usuario Administrador, un usuario
    Cajero (asignado a la primera sucursal), un laboratorio, un
    medicamento y un lote con stock en esa sucursal. Devuelve solo IDs
    (no instancias del ORM) para evitar errores de sesión expirada al
    usarlos fuera de este contexto."""
    with app.app_context():
        rol_admin = Rol(nombre="Administrador", descripcion="Acceso total")
        rol_cajero = Rol(nombre="Cajero", descripcion="Ventas")
        db.session.add_all([rol_admin, rol_cajero])
        db.session.flush()

        sucursal = Sucursal(nombre="Sucursal Test", direccion="Av. Test 100")
        sucursal2 = Sucursal(nombre="Sucursal Test 2", direccion="Av. Test 200")
        db.session.add_all([sucursal, sucursal2])
        db.session.flush()

        admin = Usuario(nombre="Admin Test", email="admin@test.com", rol_id=rol_admin.id)
        admin.set_password("admin123")
        cajero = Usuario(nombre="Cajero Test", email="cajero@test.com", rol_id=rol_cajero.id, sucursal_id=sucursal.id)
        cajero.set_password("cajero123")
        db.session.add_all([admin, cajero])
        db.session.flush()

        lab = Laboratorio(nombre="Lab Test", ruc="20123456789", telefono="01-0000000",
                           email="lab@test.com", direccion="Av. Siempre Viva 742")
        db.session.add(lab)
        db.session.flush()

        medicamento = Medicamento(
            codigo="MED-TEST", nombre="Paracetamol Test", laboratorio_id=lab.id,
            categoria="Analgésicos", presentacion="Tabletas", unidad_medida="Caja",
            precio_compra=5.0, precio_venta=10.0, stock_minimo=5,
        )
        db.session.add(medicamento)
        db.session.flush()

        lote = Lote(
            medicamento_id=medicamento.id, sucursal_id=sucursal.id, numero_lote="LOTE-TEST",
            fecha_vencimiento=date(2027, 1, 1), cantidad_inicial=100, cantidad_actual=100,
            precio_compra_unitario=5.0,
        )
        db.session.add(lote)
        db.session.commit()

        return {
            "rol_admin_id": rol_admin.id,
            "rol_cajero_id": rol_cajero.id,
            "admin_id": admin.id,
            "cajero_id": cajero.id,
            "sucursal_id": sucursal.id,
            "sucursal2_id": sucursal2.id,
            "laboratorio_id": lab.id,
            "medicamento_id": medicamento.id,
            "lote_id": lote.id,
        }


def sesion_admin(client, datos):
    with client.session_transaction() as sess:
        sess["usuario_id"] = datos["admin_id"]
        sess["usuario_nombre"] = "Admin Test"
        sess["rol"] = "Administrador"
        sess["sucursal_id"] = None
        sess["sucursal_nombre"] = None


def sesion_cajero(client, datos):
    with client.session_transaction() as sess:
        sess["usuario_id"] = datos["cajero_id"]
        sess["usuario_nombre"] = "Cajero Test"
        sess["rol"] = "Cajero"
        sess["sucursal_id"] = datos["sucursal_id"]
        sess["sucursal_nombre"] = "Sucursal Test"