import os
import secrets
from datetime import timedelta
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))




load_dotenv(os.path.join(BASE_DIR, ".env"))


class Config:





    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)





    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'inkafarma.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)










    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
    SESSION_COOKIE_HTTPONLY = True




    WTF_CSRF_TIME_LIMIT = None


    DIAS_ALERTA_VENCIMIENTO = 30



    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", MAIL_USERNAME)


class ConfigPruebas(Config):
    """Configuración usada por la suite de tests (ver tests/conftest.py):
    base de datos SQLite en memoria, aislada por completo de la base de
    datos real de desarrollo."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"



    WTF_CSRF_ENABLED = False
