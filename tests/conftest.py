"""Fixtures compartidas.

DATOS SINTÉTICOS: `cruceros_sinteticos` y `crudo_sintetico` son inventados, pequeños y
solo sirven para probar la lógica. Nunca se cargan en la base real ni aparecen en la app.

Las pruebas de base de datos usan la base de PRUEBAS (PGDATABASE_TEST), que se borra y
se vuelve a llenar con el pipeline; nunca la base real.
"""
from __future__ import annotations

import pandas as pd
import pytest
from sqlalchemy.exc import OperationalError

from src.config import get_engine
from src.db import apply_schema


@pytest.fixture
def crudo_sintetico() -> pd.DataFrame:
    """SINTÉTICO: 5 registros con el formato original del archivo del proyecto."""
    return pd.DataFrame({
        "OBJECTID": [1, 2, 3, 4, 5],
        "PUNTOS_ID": [10, 20, 99999, 40, 50],
        "NOMBRE1": ["NI¥OS HEROES", "  tecnologico ", "PANAMERICANA", "A", "B"],
        "NOMBRE2": ["REFORMA", "EJERCITO  NACIONAL", "PANAMERICANA", "C", "D"],
        "DicSegPub": ["CENTRO", "SUR", "SIN_DATO", "SUR", "SUR"],
        "SECTOR": [101, 603, 0, 603, 604],
        "ACCI2024": [3, 10, 1, 2, 5],
        "X": [360000.0, 362000.0, 361000.0, 362100.0, 362200.0],
        "Y": [3510000.0, 3505000.0, 3509000.0, 3505100.0, 3505200.0],
    })


@pytest.fixture
def cruceros_sinteticos() -> pd.DataFrame:
    """SINTÉTICO: 6 cruceros limpios con resultados fáciles de calcular a mano.

    Incidentes: 10, 5, 2, 1, 1, 1 → total 20. Zonas: A = 15 (2 cruceros), B = 5 (4 cruceros).
    """
    return pd.DataFrame({
        "id_objeto": [1, 2, 3, 4, 5, 6],
        "nombre_crucero": ["UNO y DOS", "TRES y CUATRO", "CINCO y SEIS", "SIETE y OCHO", "NUEVE y DIEZ", "ONCE y DOCE"],
        "zona": ["A", "A", "B", "B", "B", "B"],
        "sector": pd.array([1, 1, 2, 2, 3, pd.NA], dtype="Int64"),
        "incidentes": [10, 5, 2, 1, 1, 1],
        "x_utm": [0.0, 10.0, 5000.0, 5010.0, 5020.0, 5030.0],
        "y_utm": [0.0, 10.0, 5000.0, 5010.0, 5020.0, 5030.0],
        "latitud": [31.70, 31.70, 31.75, 31.75, 31.75, 31.75],
        "longitud": [-106.40, -106.40, -106.35, -106.35, -106.35, -106.35],
        "fuera_municipio": [False] * 6,
    })


@pytest.fixture(scope="session")
def engine_pruebas():
    """Base de pruebas recreada desde cero y cargada con el pipeline real."""
    from src.limpieza import pipeline

    engine = get_engine(test=True)
    try:
        with engine.connect():
            pass
    except OperationalError as error:
        pytest.skip(f"Base de pruebas no disponible: {error.__class__.__name__}")
    apply_schema(engine, reset=True)
    pipeline.ejecutar(engine, escribir_archivos=False)
    yield engine
    engine.dispose()
