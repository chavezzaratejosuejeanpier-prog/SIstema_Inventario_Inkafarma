"""Tests de auditoría: control de rol y registro automático de acciones."""
from conftest import sesion_admin, sesion_cajero


def test_listar_auditoria_requiere_login(client):
    r = client.get("/api/auditoria")
    assert r.status_code == 401


def test_cajero_no_puede_ver_auditoria(client, datos_base):
    sesion_cajero(client, datos_base)
    r = client.get("/api/auditoria")
    assert r.status_code == 403


def test_admin_puede_ver_auditoria(client, datos_base):
    sesion_admin(client, datos_base)
    r = client.get("/api/auditoria")
    assert r.status_code == 200
    assert isinstance(r.get_json(), list)


def test_crear_sucursal_registra_entrada_de_auditoria(client, datos_base):
    sesion_admin(client, datos_base)
    client.post("/api/sucursales", json={"nombre": "Sucursal Auditada", "direccion": "Av. Test 999"})

    r = client.get("/api/auditoria")
    registros = r.get_json()
    entrada = next((x for x in registros if x["entidad"] == "Sucursal" and x["detalle"] == "Sucursal Auditada"), None)
    assert entrada is not None
    assert entrada["accion"] == "crear"
    assert entrada["usuario"] == "Admin Test"


def test_auditoria_ordena_mas_reciente_primero(client, datos_base):
    sesion_admin(client, datos_base)
    client.post("/api/sucursales", json={"nombre": "Primera"})
    client.post("/api/sucursales", json={"nombre": "Segunda"})

    r = client.get("/api/auditoria")
    registros = r.get_json()
    detalles = [x["detalle"] for x in registros if x["entidad"] == "Sucursal"]
    assert detalles.index("Segunda") < detalles.index("Primera")