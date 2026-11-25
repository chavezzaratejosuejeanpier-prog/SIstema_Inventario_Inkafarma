"""Tests de compras: registro (ingreso de stock via lotes nuevos) y anulación."""
from datetime import date, timedelta

from conftest import sesion_admin, sesion_cajero


def test_listar_compras_requiere_login(client):
    r = client.get("/api/compras")
    assert r.status_code == 401


def test_admin_puede_crear_compra_y_genera_lote(client, datos_base):
    sesion_admin(client, datos_base)
    r = client.post("/api/compras", json={
        "laboratorio_id": datos_base["laboratorio_id"],
        "sucursal_id": datos_base["sucursal_id"],
        "items": [{
            "medicamento_id": datos_base["medicamento_id"],
            "cantidad": 30,
            "precio_unitario": 4.5,
            "numero_lote": "LOTE-COMPRA-1",
            "fecha_vencimiento": "2028-01-01",
        }],
    })
    assert r.status_code == 201
    data = r.get_json()
    assert data["total"] == 135.0
    assert data["estado"] == "Completada"
    assert len(data["detalles"]) == 1
    assert data["detalles"][0]["cantidad"] == 30


    r_lotes = client.get(f"/api/lotes?medicamento_id={datos_base['medicamento_id']}")
    lote_nuevo = next(l for l in r_lotes.get_json() if l["numero_lote"] == "LOTE-COMPRA-1")
    assert lote_nuevo["cantidad_actual"] == 30


def test_cajero_no_puede_crear_compra(client, datos_base):
    sesion_cajero(client, datos_base)
    r = client.post("/api/compras", json={
        "laboratorio_id": datos_base["laboratorio_id"],
        "sucursal_id": datos_base["sucursal_id"],
        "items": [{"medicamento_id": datos_base["medicamento_id"], "cantidad": 10,
                    "precio_unitario": 4.5, "fecha_vencimiento": "2028-01-01"}],
    })
    assert r.status_code == 403


def test_crear_compra_sin_campos_obligatorios_falla(client, datos_base):
    sesion_admin(client, datos_base)
    r = client.post("/api/compras", json={"laboratorio_id": datos_base["laboratorio_id"]})
    assert r.status_code == 400


def test_listar_compras_filtra_por_sucursal(client, datos_base):
    sesion_admin(client, datos_base)
    client.post("/api/compras", json={
        "laboratorio_id": datos_base["laboratorio_id"],
        "sucursal_id": datos_base["sucursal_id"],
        "items": [{"medicamento_id": datos_base["medicamento_id"], "cantidad": 5,
                    "precio_unitario": 4.5, "fecha_vencimiento": "2028-01-01"}],
    })
    r = client.get(f"/api/compras?sucursal_id={datos_base['sucursal2_id']}")
    assert r.get_json() == []


def test_admin_puede_anular_compra_y_revierte_stock(client, datos_base):
    sesion_admin(client, datos_base)
    r_crear = client.post("/api/compras", json={
        "laboratorio_id": datos_base["laboratorio_id"],
        "sucursal_id": datos_base["sucursal_id"],
        "items": [{
            "medicamento_id": datos_base["medicamento_id"], "cantidad": 20,
            "precio_unitario": 4.5, "numero_lote": "LOTE-ANULAR", "fecha_vencimiento": "2028-01-01",
        }],
    })
    compra_id = r_crear.get_json()["id"]

    r_anular = client.post(f"/api/compras/{compra_id}/anular")
    assert r_anular.status_code == 200
    assert r_anular.get_json()["estado"] == "Anulada"

    r_lotes = client.get(f"/api/lotes?medicamento_id={datos_base['medicamento_id']}")
    lote = next(l for l in r_lotes.get_json() if l["numero_lote"] == "LOTE-ANULAR")
    assert lote["cantidad_actual"] == 0


def test_no_se_puede_anular_dos_veces(client, datos_base):
    sesion_admin(client, datos_base)
    r_crear = client.post("/api/compras", json={
        "laboratorio_id": datos_base["laboratorio_id"],
        "sucursal_id": datos_base["sucursal_id"],
        "items": [{"medicamento_id": datos_base["medicamento_id"], "cantidad": 10,
                    "precio_unitario": 4.5, "fecha_vencimiento": "2028-01-01"}],
    })
    compra_id = r_crear.get_json()["id"]

    client.post(f"/api/compras/{compra_id}/anular")
    r_segunda = client.post(f"/api/compras/{compra_id}/anular")
    assert r_segunda.status_code == 400


def test_no_se_puede_anular_si_ya_se_vendio_stock_del_lote(client, datos_base):
    sesion_admin(client, datos_base)


    vencimiento_temprano = (date.today() + timedelta(days=30)).isoformat()
    r_crear = client.post("/api/compras", json={
        "laboratorio_id": datos_base["laboratorio_id"],
        "sucursal_id": datos_base["sucursal_id"],
        "items": [{
            "medicamento_id": datos_base["medicamento_id"], "cantidad": 10,
            "precio_unitario": 4.5, "numero_lote": "LOTE-VENDIDO", "fecha_vencimiento": vencimiento_temprano,
        }],
    })
    compra_id = r_crear.get_json()["id"]

    sesion_cajero(client, datos_base)
    client.post("/api/ventas", json={
        "items": [{"medicamento_id": datos_base["medicamento_id"], "cantidad": 5}],
    })

    sesion_admin(client, datos_base)
    r_anular = client.post(f"/api/compras/{compra_id}/anular")
    assert r_anular.status_code == 400


def test_cajero_no_puede_anular_compra(client, datos_base):
    sesion_admin(client, datos_base)
    r_crear = client.post("/api/compras", json={
        "laboratorio_id": datos_base["laboratorio_id"],
        "sucursal_id": datos_base["sucursal_id"],
        "items": [{"medicamento_id": datos_base["medicamento_id"], "cantidad": 10,
                    "precio_unitario": 4.5, "fecha_vencimiento": "2028-01-01"}],
    })
    compra_id = r_crear.get_json()["id"]

    sesion_cajero(client, datos_base)
    r = client.post(f"/api/compras/{compra_id}/anular")
    assert r.status_code == 403