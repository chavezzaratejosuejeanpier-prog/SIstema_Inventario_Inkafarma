"""Tests de promociones: los 4 tipos (porcentaje, monto fijo, nxm, cupón)
y su aplicación real durante una venta."""
from conftest import sesion_admin, sesion_cajero


def _crear_promocion(client, **overrides):
    payload = {
        "nombre": "Promo Test", "tipo": "porcentaje", "valor": 20,
        "fecha_inicio": "2020-01-01", "fecha_fin": "2030-01-01",
    }
    payload.update(overrides)
    return client.post("/api/promociones", json=payload)


def test_cajero_no_puede_crear_promocion(client, datos_base):
    sesion_cajero(client, datos_base)
    r = _crear_promocion(client, medicamento_id=datos_base["medicamento_id"])
    assert r.status_code == 403


def test_crear_promocion_porcentaje(client, datos_base):
    sesion_admin(client, datos_base)
    r = _crear_promocion(client, medicamento_id=datos_base["medicamento_id"], valor=15)
    assert r.status_code == 201
    assert r.get_json()["vigente"] is True


def test_porcentaje_fuera_de_rango_falla(client, datos_base):
    sesion_admin(client, datos_base)
    r = _crear_promocion(client, medicamento_id=datos_base["medicamento_id"], valor=150)
    assert r.status_code == 400


def test_crear_promocion_nxm_valida_paga_menor_que_lleva(client, datos_base):
    sesion_admin(client, datos_base)
    r = _crear_promocion(client, tipo="nxm", medicamento_id=datos_base["medicamento_id"], lleva=3, paga=2, valor=None)
    assert r.status_code == 201

    r_invalido = _crear_promocion(client, tipo="nxm", medicamento_id=datos_base["medicamento_id"], lleva=2, paga=2, valor=None)
    assert r_invalido.status_code == 400


def test_crear_cupon_requiere_codigo_unico(client, datos_base):
    sesion_admin(client, datos_base)
    r = _crear_promocion(client, tipo="cupon", codigo="UNICO10", valor=10)
    assert r.status_code == 201

    r_dup = _crear_promocion(client, tipo="cupon", codigo="unico10", valor=5)
    assert r_dup.status_code == 400


def test_venta_aplica_promocion_porcentaje(client, datos_base):
    sesion_admin(client, datos_base)
    _crear_promocion(client, medicamento_id=datos_base["medicamento_id"], valor=20)

    sesion_cajero(client, datos_base)
    r = client.post("/api/ventas", json={
        "items": [{"medicamento_id": datos_base["medicamento_id"], "cantidad": 1}],
    })
    venta = r.get_json()

    assert venta["detalles"][0]["descuento"] == 2.0
    assert venta["detalles"][0]["promocion"] == "Promo Test"


def test_venta_aplica_promocion_nxm(client, datos_base):
    sesion_admin(client, datos_base)
    _crear_promocion(client, tipo="nxm", medicamento_id=datos_base["medicamento_id"], lleva=3, paga=2, valor=None)

    sesion_cajero(client, datos_base)
    r = client.post("/api/ventas", json={
        "items": [{"medicamento_id": datos_base["medicamento_id"], "cantidad": 6}],
    })
    venta = r.get_json()

    assert venta["detalles"][0]["descuento"] == 20.0


def test_venta_aplica_cupon_sobre_total(client, datos_base):
    sesion_admin(client, datos_base)
    _crear_promocion(client, tipo="cupon", codigo="DESC10", valor=10)

    sesion_cajero(client, datos_base)
    r = client.post("/api/ventas", json={
        "cupon": "desc10",
        "items": [{"medicamento_id": datos_base["medicamento_id"], "cantidad": 1}],
    })
    venta = r.get_json()
    assert venta["cupon_codigo"] == "DESC10"
    assert venta["descuento"] == 1.0


def test_cupon_invalido_rechaza_la_venta(client, datos_base):
    sesion_cajero(client, datos_base)
    r = client.post("/api/ventas", json={
        "cupon": "NOEXISTE",
        "items": [{"medicamento_id": datos_base["medicamento_id"], "cantidad": 1}],
    })
    assert r.status_code == 400
    assert "cupón" in r.get_json()["error"].lower()


def test_promocion_de_otra_sucursal_no_aplica(client, datos_base):
    """Una promoción atada a la sucursal 2 no debe descontar nada en una
    venta hecha en la sucursal 1."""
    sesion_admin(client, datos_base)
    _crear_promocion(
        client, medicamento_id=datos_base["medicamento_id"], valor=50, sucursal_id=datos_base["sucursal2_id"],
    )

    sesion_cajero(client, datos_base)
    r = client.post("/api/ventas", json={
        "items": [{"medicamento_id": datos_base["medicamento_id"], "cantidad": 1}],
    })
    venta = r.get_json()
    assert venta["descuento"] == 0
    assert venta["detalles"][0]["promocion"] is None


def test_desactivar_promocion_deja_de_aplicarse(client, datos_base):
    sesion_admin(client, datos_base)
    r = _crear_promocion(client, medicamento_id=datos_base["medicamento_id"], valor=20)
    promo_id = r.get_json()["id"]
    client.put(f"/api/promociones/{promo_id}", json={"activo": False})

    sesion_cajero(client, datos_base)
    r2 = client.post("/api/ventas", json={
        "items": [{"medicamento_id": datos_base["medicamento_id"], "cantidad": 1}],
    })
    assert r2.get_json()["descuento"] == 0