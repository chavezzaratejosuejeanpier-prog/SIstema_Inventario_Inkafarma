"""Tests de login, protección contra fuerza bruta y recuperación de contraseña."""
from unittest.mock import patch

from models import Usuario


def test_login_correcto_redirige_al_dashboard(client, datos_base):
    r = client.post("/auth/login", data={"email": "admin@test.com", "password": "admin123"})
    assert r.status_code == 302
    assert r.headers["Location"] == "/dashboard"


def test_login_password_incorrecta_no_autentica(client, datos_base):
    client.post("/auth/login", data={"email": "admin@test.com", "password": "incorrecta"})

    r = client.get("/dashboard")
    assert r.status_code == 302
    assert "/auth/login" in r.headers["Location"]


def test_bloqueo_tras_cinco_intentos_fallidos(app, client, datos_base):
    for _ in range(4):
        client.post("/auth/login", data={"email": "admin@test.com", "password": "mala"})

    with app.app_context():
        u = Usuario.query.filter_by(email="admin@test.com").first()
        assert u.intentos_fallidos == 4
        assert not u.bloqueado


    client.post("/auth/login", data={"email": "admin@test.com", "password": "mala"})
    with app.app_context():
        u = Usuario.query.filter_by(email="admin@test.com").first()
        assert u.bloqueado is True
        assert u.intentos_fallidos == 0


    r = client.post("/auth/login", data={"email": "admin@test.com", "password": "admin123"}, follow_redirects=True)
    assert b"bloqueada" in r.data.lower()


def test_recuperar_password_desbloquea_la_cuenta(app, client, datos_base):
    with app.app_context():
        u = Usuario.query.filter_by(email="admin@test.com").first()
        u.intentos_fallidos = 0
        from datetime import datetime, timedelta
        u.bloqueado_hasta = datetime.utcnow() + timedelta(hours=1)
        from extensions import db
        db.session.commit()

    with patch("auth.routes.enviar_codigo_recuperacion") as mock_enviar:
        client.post("/auth/olvide-password", data={"email": "admin@test.com"})
        assert mock_enviar.called

    with app.app_context():
        from models import CodigoRecuperacion
        codigo = CodigoRecuperacion.query.filter_by(usuario_id=datos_base["admin_id"]).order_by(
            CodigoRecuperacion.id.desc()
        ).first()

    r = client.post("/auth/verificar-codigo", data={
        "email": "admin@test.com", "codigo": codigo.codigo, "password": "nueva123", "password2": "nueva123",
    })
    assert r.status_code == 302
    assert r.headers["Location"] == "/auth/login"

    with app.app_context():
        u = Usuario.query.filter_by(email="admin@test.com").first()
        assert u.bloqueado is False
        assert u.check_password("nueva123")


def test_verificar_codigo_incorrecto_no_cambia_password(client, datos_base):
    r = client.post("/auth/verificar-codigo", data={
        "email": "admin@test.com", "codigo": "000000", "password": "otra123", "password2": "otra123",
    })
    assert r.status_code == 200


def test_verificar_codigo_se_invalida_tras_intentos_maximos(app, client, datos_base):
    with patch("auth.routes.enviar_codigo_recuperacion"):
        client.post("/auth/olvide-password", data={"email": "admin@test.com"})

    with app.app_context():
        from models import CodigoRecuperacion
        codigo = CodigoRecuperacion.query.filter_by(usuario_id=datos_base["admin_id"]).order_by(
            CodigoRecuperacion.id.desc()
        ).first()
        codigo_real = codigo.codigo

        codigo_incorrecto = "000000" if codigo_real != "000000" else "111111"


    for _ in range(5):
        client.post("/auth/verificar-codigo", data={
            "email": "admin@test.com", "codigo": codigo_incorrecto, "password": "nueva123", "password2": "nueva123",
        })

    with app.app_context():
        from models import CodigoRecuperacion
        codigo = CodigoRecuperacion.query.filter_by(usuario_id=datos_base["admin_id"]).order_by(
            CodigoRecuperacion.id.desc()
        ).first()
        assert codigo.intentos == 5
        assert codigo.usado is True


    r = client.post("/auth/verificar-codigo", data={
        "email": "admin@test.com", "codigo": codigo_real, "password": "nueva123", "password2": "nueva123",
    })
    assert r.status_code == 200
    with app.app_context():
        u = Usuario.query.filter_by(email="admin@test.com").first()
        assert not u.check_password("nueva123")