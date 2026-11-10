"""Configuración central: rutas del proyecto y conexión a PostgreSQL (desde .env)."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import URL, Engine, create_engine

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
DOCS = ROOT / "docs"
DB_DIR = ROOT / "db"

# Fuente principal (archivos del proyecto) y capa de apoyo (límite municipal del IMIP)
RAW_GPKG = DATA_RAW / "proyecto" / "ACCIDENTES_LIMPIOS.gpkg"
RAW_CSV = DATA_RAW / "proyecto" / "ACCIDENTES_ML.csv"
RAW_LIMITE_MUNICIPAL = DATA_RAW / "imip_arcgis" / "limite_municipal" / "page_000000.json"

SCHEMA = "accidentes"
CRS_ORIGEN = 32613  # UTM zona 13N
CRS_WGS84 = 4326

# Por defecto se lee .env; con ACCIDENTES_ENV=.env.nube se usa la base en la nube.
# En Streamlit Cloud no hay archivo: las variables PG* vienen de los "secrets" del servicio.
# load_dotenv no sobrescribe variables que ya existan en el entorno.
load_dotenv(ROOT / os.environ.get("ACCIDENTES_ENV", ".env"))


def database_url(test: bool = False) -> URL:
    """Arma la URL de conexión; con test=True usa la base de pruebas."""
    db = os.environ["PGDATABASE_TEST"] if test else os.environ["PGDATABASE"]
    return URL.create(
        "postgresql+psycopg",
        username=os.environ["PGUSER"],
        password=os.environ.get("PGPASSWORD") or None,
        host=os.environ.get("PGHOST", "localhost"),
        port=int(os.environ.get("PGPORT", "5432")),
        database=db,
    )


def get_engine(test: bool = False) -> Engine:
    """Devuelve un engine de SQLAlchemy para la base real o la de pruebas."""
    # pool_pre_ping: reconecta si la base (p. ej. Neon gratuito) cerró la conexión por inactividad.
    # El cifrado SSL se pide con la variable estándar PGSSLMODE=require, que psycopg lee sola.
    return create_engine(database_url(test), future=True, pool_pre_ping=True)
