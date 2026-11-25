"""Tests del envío de correos (código de recuperación y boleta de venta).

Nunca se conecta a un servidor SMTP real: se reemplaza smtplib.SMTP por un
mock, así la suite es rápida, determinística y no depende de credenciales
ni de conexión a internet.
"""
from unittest.mock import MagicMock, patch

from conftest import sesion_cajero


def _mock_smtp():
    """Crea un smtplib.SMTP falso que soporta el `with SMTP(...) as smtp:`
    usado en auth/correo.py."""
    instancia = MagicMock()
    contexto = MagicMock()
    contexto.__enter__.return_value = instancia
    return contexto, instancia


def test_enviar_codigo_recuperacion_hace_login_y_sendmail(app):
    with app.app_context():
        with patch("auth.correo.smtplib.SMTP") as smtp_clase:
            contexto, instancia = _mock_smtp()
            smtp_clase.return_value = contexto

            from auth.correo import enviar_codigo_recuperacion
            enviar_codigo_recuperacion("Ana", "ana@test.com", "123456")

            instancia.starttls.assert_called_once()
            instancia.login.assert_called_once()
            instancia.sendmail.assert_called_once()
            destinatario_enviado = instancia.sendmail.call_args[0][1]
            assert destinatario_enviado == "ana@test.com"


def test_enviar_boleta_venta_incluye_el_codigo_de_la_venta(app, datos_base, client):
    sesion_cajero(client, datos_base)
    r = client.post("/api/ventas", json={
        "items": [{"medicamento_id": datos_base["medicamento_id"], "cantidad": 2}],
    })
    venta_id = r.get_json()["id"]

    with app.app_context():
        from models import Venta
        venta = Venta.query.get(venta_id)
        venta.cliente_email = "cliente@test.com"

        with patch("auth.correo.smtplib.SMTP") as smtp_clase:
            contexto, instancia = _mock_smtp()
            smtp_clase.return_value = contexto

            from auth.correo import enviar_boleta_venta
            enviar_boleta_venta(venta)

            instancia.sendmail.assert_called_once()
            mensaje_enviado = instancia.sendmail.call_args[0][2]
            assert venta.numero_venta in mensaje_enviado


def test_venta_con_email_intenta_enviar_boleta(client, datos_base):
    sesion_cajero(client, datos_base)
    with patch("api.ventas.enviar_boleta_venta") as mock_enviar:
        r = client.post("/api/ventas", json={
            "cliente_email": "cliente@test.com",
            "items": [{"medicamento_id": datos_base["medicamento_id"], "cantidad": 1}],
        })
    assert r.status_code == 201
    assert mock_enviar.called
    assert r.get_json()["boleta_enviada"] is True


def test_venta_sin_email_no_intenta_enviar_boleta(client, datos_base):
    sesion_cajero(client, datos_base)
    with patch("api.ventas.enviar_boleta_venta") as mock_enviar:
        r = client.post("/api/ventas", json={
            "items": [{"medicamento_id": datos_base["medicamento_id"], "cantidad": 1}],
        })
    assert not mock_enviar.called
    assert r.get_json()["boleta_enviada"] is False


def test_venta_se_registra_aunque_falle_el_envio_de_correo(client, datos_base):
    sesion_cajero(client, datos_base)
    with patch("api.ventas.enviar_boleta_venta", side_effect=Exception("SMTP caído")):
        r = client.post("/api/ventas", json={
            "cliente_email": "cliente@test.com",
            "items": [{"medicamento_id": datos_base["medicamento_id"], "cantidad": 1}],
        })
    assert r.status_code == 201
    assert r.get_json()["boleta_enviada"] is False