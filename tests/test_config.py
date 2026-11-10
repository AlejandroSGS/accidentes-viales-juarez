"""Pruebas de la selección de conexión (con cadenas FICTICIAS, sin conectarse a nada)."""
from src import config

FICTICIA = "postgresql://usuario:clave@ep-ejemplo.us-east-2.aws.neon.tech/neondb?sslmode=require"


def test_usa_database_url_si_existe(monkeypatch):
    monkeypatch.delenv("DATABASE_URL_UNPOOLED", raising=False)
    monkeypatch.setenv("DATABASE_URL", FICTICIA)
    url = config.database_url()
    assert url.drivername == "postgresql+psycopg"
    assert url.host == "ep-ejemplo.us-east-2.aws.neon.tech"
    assert url.query["sslmode"] == "require"


def test_prefiere_la_conexion_directa(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", FICTICIA)
    monkeypatch.setenv("DATABASE_URL_UNPOOLED", FICTICIA.replace("ep-ejemplo", "ep-directa"))
    assert config.database_url().host == "ep-directa.us-east-2.aws.neon.tech"


def test_pruebas_siempre_usan_la_base_local(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", FICTICIA)
    monkeypatch.setenv("PGDATABASE_TEST", "accidentes_viales_test")
    monkeypatch.setenv("PGHOST", "localhost")
    url = config.database_url(test=True)
    assert url.host == "localhost" and url.database == "accidentes_viales_test"


def test_sin_database_url_usa_variables_pg(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL_UNPOOLED", raising=False)
    monkeypatch.setenv("PGDATABASE", "accidentes_viales")
    monkeypatch.setenv("PGHOST", "localhost")
    assert config.database_url().database == "accidentes_viales"
