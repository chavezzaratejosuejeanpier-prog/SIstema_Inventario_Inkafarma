"""Tests del ciclo de vida de una venta: registro, descuento de stock (FEFO),
anulación y restitución de stock, y control de permisos."""
from conftest import sesion_admin, sesion_cajero


def test_cajero_puede_registrar_venta(client, datos_base):
    sesion_cajero(client, datos_base)
    r = client.post("/api/ventas", json={
        "cliente_nombre": "Cliente Test",
        "items": [{"medicamento_id": datos_base["medicamento_id"], "cantidad": 10}],
    })
    assert r.status_code == 201
    venta = r.get_json()
    assert venta["estado"] == "Completada"
    assert venta["total"] > 0


def test_venta_descuenta_stock_del_lote(client, datos_base):
    sesion_cajero(client, datos_base)
    client.post("/api/ventas", json={
        "items": [{"medicamento_id": datos_base["medicamento_id"], "cantidad": 30}],
    })

    sesion_admin(client, datos_base)
    r = client.get(f"/api/medicamentos/{datos_base['medicamento_id']}")
    assert r.get_json()["stock_total"] == 70


def test_venta_rechaza_stock_insuficiente(client, datos_base):
    sesion_cajero(client, datos_base)
    r = client.post("/api/ventas", json={
        "items": [{"medicamento_id": datos_base["medicamento_id"], "cantidad": 999}],
    })
    assert r.status_code == 400
    assert "Stock insuficiente" in r.get_json()["error"]


def test_venta_sin_items_es_rechazada(client, datos_base):
    sesion_cajero(client, datos_base)
    r = client.post("/api/ventas", json={"items": []})
    assert r.status_code == 400


def test_cajero_no_puede_anular_venta(client, datos_base):
    sesion_cajero(client, datos_base)
    r = client.post("/api/ventas", json={
        "items": [{"medicamento_id": datos_base["medicamento_id"], "cantidad": 5}],
    })
    venta_id = r.get_json()["id"]

    r = client.post(f"/api/ventas/{venta_id}/anular")
    assert r.status_code == 403


def test_admin_anula_venta_y_se_restituye_el_stock(client, datos_base):
    sesion_cajero(client, datos_base)
    r = client.post("/api/ventas", json={
        "items": [{"medicamento_id": datos_base["medicamento_id"], "cantidad": 20}],
    })
    venta_id = r.get_json()["id"]

    r = client.get(f"/api/medicamentos/{datos_base['medicamento_id']}")
    assert r.get_json()["stock_total"] == 80

    sesion_admin(client, datos_base)
    r = client.post(f"/api/ventas/{venta_id}/anular")
    assert r.status_code == 200
    assert r.get_json()["estado"] == "Anulada"

    r = client.get(f"/api/medicamentos/{datos_base['medicamento_id']}")
    assert r.get_json()["stock_total"] == 100


def test_no_se_puede_anular_dos_veces(client, datos_base):
    sesion_cajero(client, datos_base)
    r = client.post("/api/ventas", json={
        "items": [{"medicamento_id": datos_base["medicamento_id"], "cantidad": 5}],
    })
    venta_id = r.get_json()["id"]

    sesion_admin(client, datos_base)
    client.post(f"/api/ventas/{venta_id}/anular")
    r = client.post(f"/api/ventas/{venta_id}/anular")
    assert r.status_code == 400


def test_venta_anulada_no_cuenta_en_el_dashboard(client, datos_base):
    sesion_cajero(client, datos_base)
    r = client.post("/api/ventas", json={
        "items": [{"medicamento_id": datos_base["medicamento_id"], "cantidad": 5}],
    })
    venta_id = r.get_json()["id"]

    r = client.get("/api/dashboard/resumen")
    total_antes = r.get_json()["kpis"]["total_ventas"]

    sesion_admin(client, datos_base)
    client.post(f"/api/ventas/{venta_id}/anular")

    r = client.get("/api/dashboard/resumen")
    total_despues = r.get_json()["kpis"]["total_ventas"]
    assert total_despues == total_antes - 1


def test_venta_grande_aplica_descuento_por_volumen(client, datos_base):
    sesion_cajero(client, datos_base)

    r = client.post("/api/ventas", json={
        "items": [{"medicamento_id": datos_base["medicamento_id"], "cantidad": 20}],
    })
    assert r.status_code == 201
    venta = r.get_json()
    assert venta["descuento"] == 10.0
    subtotal_con_descuento = 200 - 10.0
    total_esperado = round(subtotal_con_descuento + subtotal_con_descuento * 0.18, 2)
    assert venta["total"] == total_esperado


def test_venta_pequena_no_aplica_descuento(client, datos_base):
    sesion_cajero(client, datos_base)
    r = client.post("/api/ventas", json={
        "items": [{"medicamento_id": datos_base["medicamento_id"], "cantidad": 2}],
    })
    assert r.get_json()["descuento"] == 0


def test_medicamento_con_receta_exige_numero_de_receta(client, datos_base, app):
    with app.app_context():
        from extensions import db
        from models import Medicamento
        med_receta = Medicamento(
            codigo="MED-RECETA", nombre="Antibiótico Test", laboratorio_id=datos_base["laboratorio_id"],
            precio_venta=10.0, precio_compra=5.0, requiere_receta=True, stock_minimo=5,
        )
        db.session.add(med_receta)
        db.session.commit()
        med_receta_id = med_receta.id

        from models import Lote
        from datetime import date
        lote = Lote(medicamento_id=med_receta_id, sucursal_id=datos_base["sucursal_id"], numero_lote="LOTE-RECETA",
                    fecha_vencimiento=date(2027, 1, 1), cantidad_inicial=50, cantidad_actual=50, precio_compra_unitario=5.0)
        db.session.add(lote)
        db.session.commit()

    sesion_cajero(client, datos_base)

    r = client.post("/api/ventas", json={"items": [{"medicamento_id": med_receta_id, "cantidad": 1}]})
    assert r.status_code == 400
    assert "receta" in r.get_json()["error"].lower()

    r = client.post("/api/ventas", json={
        "items": [{"medicamento_id": med_receta_id, "cantidad": 1, "numero_receta": "RX-001"}],
    })
    assert r.status_code == 201
    assert r.get_json()["detalles"][0]["numero_receta"] == "RX-001"


def test_historial_propio_del_cajero_no_muestra_ventas_de_otros(client, datos_base, app):
    with app.app_context():
        from extensions import db
        from models import Rol, Usuario
        otro_cajero = Usuario(nombre="Otro Cajero", email="otro@test.com", rol_id=datos_base["rol_cajero_id"])
        otro_cajero.set_password("clave123")
        db.session.add(otro_cajero)
        db.session.commit()
        otro_cajero_id = otro_cajero.id

    sesion_cajero(client, datos_base)
    client.post("/api/ventas", json={"items": [{"medicamento_id": datos_base["medicamento_id"], "cantidad": 1}]})

    with client.session_transaction() as sess:
        sess["usuario_id"] = otro_cajero_id
        sess["usuario_nombre"] = "Otro Cajero"
        sess["rol"] = "Cajero"

    r = client.get("/api/ventas?propio=1")
    assert r.get_json() == []