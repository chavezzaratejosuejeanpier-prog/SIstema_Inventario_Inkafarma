"""Tests de lotes: CRUD, filtros por medicamento/sucursal y control de rol."""
from conftest import sesion_admin, sesion_cajero


def test_listar_lotes_requiere_login(client):
    r = client.get("/api/lotes")
    assert r.status_code == 401


def test_cajero_puede_listar_lotes(client, datos_base):
    sesion_cajero(client, datos_base)
    r = client.get("/api/lotes")
    assert r.status_code == 200
    assert any(l["id"] == datos_base["lote_id"] for l in r.get_json())


def test_listar_lotes_filtra_por_sucursal(client, datos_base):
    sesion_admin(client, datos_base)
    r = client.get(f"/api/lotes?sucursal_id={datos_base['sucursal2_id']}")
    assert r.status_code == 200
    assert r.get_json() == []


def test_listar_lotes_filtra_por_medicamento(client, datos_base):
    sesion_admin(client, datos_base)
    r = client.get(f"/api/lotes?medicamento_id={datos_base['medicamento_id']}")
    assert r.status_code == 200
    assert all(l["medicamento_id"] == datos_base["medicamento_id"] for l in r.get_json())


def test_admin_puede_crear_lote(client, datos_base):
    sesion_admin(client, datos_base)
    r = client.post("/api/lotes", json={
        "medicamento_id": datos_base["medicamento_id"],
        "sucursal_id": datos_base["sucursal_id"],
        "numero_lote": "LOTE-NUEVO",
        "fecha_vencimiento": "2028-01-01",
        "cantidad_inicial": 50,
    })
    assert r.status_code == 201
    data = r.get_json()
    assert data["numero_lote"] == "LOTE-NUEVO"
    assert data["cantidad_actual"] == 50

    assert data["precio_compra_unitario"] == 5.0


def test_cajero_no_puede_crear_lote(client, datos_base):
    sesion_cajero(client, datos_base)
    r = client.post("/api/lotes", json={
        "medicamento_id": datos_base["medicamento_id"],
        "sucursal_id": datos_base["sucursal_id"],
        "numero_lote": "LOTE-X",
        "fecha_vencimiento": "2028-01-01",
        "cantidad_inicial": 10,
    })
    assert r.status_code == 403


def test_crear_lote_sin_campos_obligatorios_falla(client, datos_base):
    sesion_admin(client, datos_base)
    r = client.post("/api/lotes", json={"medicamento_id": datos_base["medicamento_id"]})
    assert r.status_code == 400


def test_crear_lote_con_medicamento_inexistente_falla(client, datos_base):
    sesion_admin(client, datos_base)
    r = client.post("/api/lotes", json={
        "medicamento_id": 99999,
        "sucursal_id": datos_base["sucursal_id"],
        "numero_lote": "LOTE-X",
        "fecha_vencimiento": "2028-01-01",
        "cantidad_inicial": 10,
    })
    assert r.status_code == 404


def test_admin_puede_actualizar_lote(client, datos_base):
    sesion_admin(client, datos_base)
    r = client.put(f"/api/lotes/{datos_base['lote_id']}", json={"cantidad_actual": 42})
    assert r.status_code == 200
    assert r.get_json()["cantidad_actual"] == 42


def test_cajero_no_puede_actualizar_lote(client, datos_base):
    sesion_cajero(client, datos_base)
    r = client.put(f"/api/lotes/{datos_base['lote_id']}", json={"cantidad_actual": 1})
    assert r.status_code == 403


def test_admin_puede_eliminar_lote(client, datos_base):
    sesion_admin(client, datos_base)
    r = client.delete(f"/api/lotes/{datos_base['lote_id']}")
    assert r.status_code == 200

    r2 = client.get("/api/lotes")
    assert all(l["id"] != datos_base["lote_id"] for l in r2.get_json())


def test_cajero_no_puede_eliminar_lote(client, datos_base):
    sesion_cajero(client, datos_base)
    r = client.delete(f"/api/lotes/{datos_base['lote_id']}")
    assert r.status_code == 403