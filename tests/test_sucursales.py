"""Tests de sucursales: CRUD y escopado del stock/ventas por sucursal."""
from datetime import date

from conftest import sesion_admin, sesion_cajero


def test_listar_sucursales_requiere_login(client):
    r = client.get("/api/sucursales")
    assert r.status_code == 401


def test_admin_puede_crear_sucursal(client, datos_base):
    sesion_admin(client, datos_base)
    r = client.post("/api/sucursales", json={"nombre": "Sucursal Nueva", "direccion": "Av. Nueva 123"})
    assert r.status_code == 201
    assert r.get_json()["nombre"] == "Sucursal Nueva"


def test_cajero_no_puede_crear_sucursal(client, datos_base):
    sesion_cajero(client, datos_base)
    r = client.post("/api/sucursales", json={"nombre": "Otra"})
    assert r.status_code == 403


def test_no_se_puede_desactivar_la_ultima_sucursal_activa(client, datos_base, app):
    sesion_admin(client, datos_base)




    with app.app_context():
        from models import Sucursal
        otras_ids = [
            s.id for s in Sucursal.query.filter(Sucursal.activo == True).all()
            if s.id != datos_base["sucursal_id"]
        ]

    for otro_id in otras_ids:
        r = client.delete(f"/api/sucursales/{otro_id}")
        assert r.status_code == 200

    r = client.delete(f"/api/sucursales/{datos_base['sucursal_id']}")
    assert r.status_code == 400


def test_venta_no_ve_stock_de_otra_sucursal(client, datos_base, app):
    """El stock de un lote en la sucursal 2 no debe estar disponible para
    una venta hecha por un cajero de la sucursal 1, aunque sea el mismo
    medicamento a nivel de catálogo."""
    with app.app_context():
        from extensions import db
        from models import Lote
        lote_otra_sucursal = Lote(
            medicamento_id=datos_base["medicamento_id"], sucursal_id=datos_base["sucursal2_id"],
            numero_lote="LOTE-OTRA-SUCURSAL", fecha_vencimiento=date(2027, 1, 1),
            cantidad_inicial=500, cantidad_actual=500, precio_compra_unitario=5.0,
        )
        db.session.add(lote_otra_sucursal)
        db.session.commit()

    sesion_cajero(client, datos_base)
    r = client.post("/api/ventas", json={
        "items": [{"medicamento_id": datos_base["medicamento_id"], "cantidad": 150}],
    })
    assert r.status_code == 400
    assert "Stock insuficiente" in r.get_json()["error"]


def test_medicamentos_con_sucursal_id_muestra_stock_de_esa_sucursal(client, datos_base):
    sesion_admin(client, datos_base)
    r = client.get(f"/api/medicamentos?sucursal_id={datos_base['sucursal_id']}")
    med = next(m for m in r.get_json() if m["id"] == datos_base["medicamento_id"])
    assert med["stock_total"] == 100

    r2 = client.get(f"/api/medicamentos?sucursal_id={datos_base['sucursal2_id']}")
    med2 = next(m for m in r2.get_json() if m["id"] == datos_base["medicamento_id"])
    assert med2["stock_total"] == 0