"""Tests del CRUD de medicamentos."""
from conftest import sesion_admin, sesion_cajero


def test_cajero_puede_listar_medicamentos(client, datos_base):
    sesion_cajero(client, datos_base)
    r = client.get("/api/medicamentos")
    assert r.status_code == 200
    assert len(r.get_json()) == 1


def test_cajero_no_puede_crear_medicamento(client, datos_base):
    sesion_cajero(client, datos_base)
    r = client.post("/api/medicamentos", json={
        "codigo": "MED-999", "nombre": "Prueba", "laboratorio_id": datos_base["laboratorio_id"],
    })
    assert r.status_code == 403


def test_admin_puede_crear_medicamento(client, datos_base):
    sesion_admin(client, datos_base)
    r = client.post("/api/medicamentos", json={
        "codigo": "MED-999", "nombre": "Ibuprofeno Test", "laboratorio_id": datos_base["laboratorio_id"],
        "precio_compra": 3, "precio_venta": 7,
    })
    assert r.status_code == 201
    assert r.get_json()["codigo"] == "MED-999"


def test_no_se_puede_crear_medicamento_con_codigo_repetido(client, datos_base):
    sesion_admin(client, datos_base)
    r = client.post("/api/medicamentos", json={
        "codigo": "MED-TEST", "nombre": "Duplicado", "laboratorio_id": datos_base["laboratorio_id"],
    })
    assert r.status_code == 400


def test_stock_total_del_medicamento_refleja_sus_lotes(client, datos_base):
    sesion_admin(client, datos_base)
    r = client.get(f"/api/medicamentos/{datos_base['medicamento_id']}")
    assert r.get_json()["stock_total"] == 100


def test_eliminar_medicamento_lo_desactiva_sin_borrarlo(client, datos_base):
    sesion_admin(client, datos_base)
    r = client.delete(f"/api/medicamentos/{datos_base['medicamento_id']}")
    assert r.status_code == 200

    r = client.get(f"/api/medicamentos/{datos_base['medicamento_id']}")
    assert r.status_code == 200
    assert r.get_json()["activo"] is False