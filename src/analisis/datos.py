"""Lectura de los cruceros limpios desde PostgreSQL (consultas parametrizadas)."""
from __future__ import annotations

from collections.abc import Sequence

import pandas as pd
from sqlalchemy import Engine, bindparam, text

from src.config import SCHEMA


def cargar_cruceros(engine: Engine, zonas: Sequence[str] | None = None,
                    sectores: Sequence[int] | None = None, min_incidentes: int = 1,
                    incluir_fuera_municipio: bool = True) -> pd.DataFrame:
    """Devuelve los cruceros filtrados. Los filtros vacíos (None) no se aplican."""
    condiciones = ["incidentes >= :min_inc"]
    params: dict = {"min_inc": int(min_incidentes)}
    binds = []
    if zonas:
        condiciones.append("zona IN :zonas")
        params["zonas"] = list(zonas)
        binds.append(bindparam("zonas", expanding=True))
    if sectores:
        condiciones.append("sector IN :sectores")
        params["sectores"] = [int(s) for s in sectores]
        binds.append(bindparam("sectores", expanding=True))
    if not incluir_fuera_municipio:
        condiciones.append("NOT fuera_municipio")
    sql = text(f"SELECT * FROM {SCHEMA}.cruceros WHERE {' AND '.join(condiciones)} ORDER BY id_objeto")
    if binds:
        sql = sql.bindparams(*binds)
    with engine.connect() as conn:
        df = pd.read_sql(sql, conn, params=params)
    df["sector"] = df["sector"].astype("Int64")
    df["id_crucero"] = df["id_crucero"].astype("Int64")
    return df


def cargar_tabla(engine: Engine, nombre: str) -> pd.DataFrame:
    """Lee una tabla o vista del esquema (solo nombres de una lista permitida)."""
    permitidas = {"v_incidentes_por_zona", "v_incidentes_por_sector", "v_resumen_calidad",
                  "v_ultima_bitacora", "ejecuciones_pipeline", "cat_zonas", "cat_sectores",
                  "v_ranking_cruceros"}
    if nombre not in permitidas:
        raise ValueError(f"Tabla no permitida: {nombre}")
    with engine.connect() as conn:
        return pd.read_sql(text(f"SELECT * FROM {SCHEMA}.{nombre}"), conn)
