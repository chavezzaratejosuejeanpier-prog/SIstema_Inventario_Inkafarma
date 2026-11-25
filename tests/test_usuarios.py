"""Tests del CRUD de usuarios (solo Administrador)."""
from conftest import sesion_admin, sesion_cajero


def test_cajero_no_puede_listar_usuarios(client, datos_base):
    sesion_cajero(client, datos_base)
    r = client.get("/api/usuarios")
    assert r.status_code == 403


def test_admin_puede_crear_usuario(client, datos_base):
    sesion_admin(client, datos_base)
    r = client.post("/api/usuarios", json={
        "nombre": "Nuevo Usuario", "email": "nuevo@test.com", "password": "clave123",
        "rol_id": datos_base["rol_cajero_id"], "sucursal_id": datos_base["sucursal_id"],
    })
    assert r.status_code == 201
    assert r.get_json()["email"] == "nuevo@test.com"


def test_no_se_puede_crear_cajero_sin_sucursal(client, datos_base):
    sesion_admin(client, datos_base)
    r = client.post("/api/usuarios", json={
        "nombre": "Sin Sucursal", "email": "sinsucursal@test.com", "password": "clave123",
        "rol_id": datos_base["rol_cajero_id"],
    })
    assert r.status_code == 400


def test_no_se_puede_crear_usuario_con_email_repetido(client, datos_base):
    sesion_admin(client, datos_base)
    payload = {"nombre": "Dup", "email": "admin@test.com", "password": "clave123", "rol_id": datos_base["rol_cajero_id"]}
    r = client.post("/api/usuarios", json=payload)
    assert r.status_code == 400


def test_toggle_activo_desactiva_y_reactiva_usuario(client, datos_base):
    sesion_admin(client, datos_base)
    r = client.put(f"/api/usuarios/{datos_base['cajero_id']}", json={"activo": False})
    assert r.status_code == 200
    assert r.get_json()["activo"] is False

    r = client.put(f"/api/usuarios/{datos_base['cajero_id']}", json={"activo": True})
    assert r.get_json()["activo"] is True


def test_no_puede_desactivarse_a_si_mismo(client, datos_base):
    sesion_admin(client, datos_base)
    r = client.put(f"/api/usuarios/{datos_base['admin_id']}", json={"activo": False})
    assert r.status_code == 400


def test_no_puede_eliminarse_a_si_mismo(client, datos_base):
    sesion_admin(client, datos_base)
    r = client.delete(f"/api/usuarios/{datos_base['admin_id']}")
    assert r.status_code == 400


def test_eliminar_usuario_sin_dependencias(client, datos_base):
    sesion_admin(client, datos_base)
    r = client.post("/api/usuarios", json={
        "nombre": "Desechable", "email": "desechable@test.com", "password": "clave123",
        "rol_id": datos_base["rol_cajero_id"], "sucursal_id": datos_base["sucursal_id"],
    })
    nuevo_id = r.get_json()["id"]

    r = client.delete(f"/api/usuarios/{nuevo_id}")
    assert r.status_code == 200

    r = client.get("/api/usuarios")
    ids = [u["id"] for u in r.get_json()]
    assert nuevo_id not in ids