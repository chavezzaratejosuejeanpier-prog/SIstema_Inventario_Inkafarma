"""Tests de reportes: descargas de Excel/PDF de ventas e inventario (solo Administrador)."""
import pytest

from conftest import sesion_admin, sesion_cajero

RUTAS_REPORTES = [
    ("/api/reportes/ventas/excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ("/api/reportes/ventas/pdf", "application/pdf"),
    ("/api/reportes/inventario/excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ("/api/reportes/inventario/pdf", "application/pdf"),
]


@pytest.mark.parametrize("ruta,mimetype_esperado", RUTAS_REPORTES)
def test_reporte_requiere_login(client, ruta, mimetype_esperado):
    r = client.get(ruta)
    assert r.status_code == 401


@pytest.mark.parametrize("ruta,mimetype_esperado", RUTAS_REPORTES)
def test_cajero_no_puede_descargar_reportes(client, datos_base, ruta, mimetype_esperado):
    sesion_cajero(client, datos_base)
    r = client.get(ruta)
    assert r.status_code == 403


@pytest.mark.parametrize("ruta,mimetype_esperado", RUTAS_REPORTES)
def test_admin_puede_descargar_reporte(client, datos_base, ruta, mimetype_esperado):
    sesion_admin(client, datos_base)
    r = client.get(ruta)
    assert r.status_code == 200
    assert r.mimetype == mimetype_esperado
    assert len(r.data) > 0
    assert "attachment" in r.headers.get("Content-Disposition", "")


def test_reporte_inventario_incluye_medicamento_de_datos_base(client, datos_base):
    """El reporte de inventario en Excel debe reflejar el catálogo real
    (aunque no se pueda leer el binario fácilmente, al menos confirma que
    no falla al generarse con datos reales, incluyendo el stock agregado
    desde los lotes)."""
    sesion_admin(client, datos_base)
    r = client.get("/api/reportes/inventario/excel")
    assert r.status_code == 200
    assert len(r.data) > 500


def test_reporte_ventas_sin_ventas_no_falla(client, datos_base):
    """Antes de registrar cualquier venta, el reporte debe generarse igual
    (tabla vacía) en vez de lanzar un error por división/agregación sobre
    un DataFrame vacío."""
    sesion_admin(client, datos_base)
    r = client.get("/api/reportes/ventas/pdf")
    assert r.status_code == 200
    assert len(r.data) > 0