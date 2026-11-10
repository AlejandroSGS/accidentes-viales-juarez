"""Pruebas de integridad sobre los datos procesados, en la BASE DE PRUEBAS.

La fixture `engine_pruebas` recrea el esquema y corre el pipeline real sobre
data/raw (no sobre la base real).
"""
import json

import pandas as pd
import pytest
from sqlalchemy import text

from src.config import RAW_GPKG, SCHEMA
from src.limpieza import pipeline

pytestmark = pytest.mark.db


def q(engine, sql: str) -> pd.DataFrame:
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn)


def escalar(engine, sql: str):
    with engine.connect() as conn:
        return conn.execute(text(sql)).scalar_one()


def test_mismos_registros_e_incidentes_que_el_original(engine_pruebas):
    import geopandas as gpd
    original = gpd.read_file(RAW_GPKG)
    assert escalar(engine_pruebas, f"SELECT COUNT(*) FROM {SCHEMA}.cruceros") == len(original)
    assert escalar(engine_pruebas, f"SELECT SUM(incidentes) FROM {SCHEMA}.cruceros") == original["ACCI2024"].sum()


def test_sin_duplicados(engine_pruebas):
    assert escalar(engine_pruebas, f"SELECT COUNT(*) - COUNT(DISTINCT id_objeto) FROM {SCHEMA}.cruceros") == 0
    dup = q(engine_pruebas, f"""SELECT id_crucero FROM {SCHEMA}.cruceros WHERE id_crucero IS NOT NULL
                                GROUP BY id_crucero HAVING COUNT(*) > 1""")
    assert dup.empty


def test_cada_registro_limpio_enlaza_con_su_original(engine_pruebas):
    sin_enlace = escalar(engine_pruebas, f"""
        SELECT COUNT(*) FROM {SCHEMA}.cruceros c
        LEFT JOIN {SCHEMA}.raw_cruceros_2024 r ON r."OBJECTID" = c.id_objeto
        WHERE r."OBJECTID" IS NULL OR r."ACCI2024" <> c.incidentes""")
    assert sin_enlace == 0


def test_conteos_validos_y_anio(engine_pruebas):
    df = q(engine_pruebas, f"SELECT incidentes, anio FROM {SCHEMA}.cruceros")
    assert (df["incidentes"] >= 1).all()
    assert (df["anio"] == 2024).all()


def test_categorias_dentro_del_catalogo(engine_pruebas):
    zonas = set(q(engine_pruebas, f"SELECT zona FROM {SCHEMA}.cat_zonas")["zona"])
    assert zonas == {"CENTRO", "ORIENTE", "PONIENTE", "SUR", "UNIVERSIDAD", "VALLE"}
    assert "SIN_DATO" not in set(q(engine_pruebas, f"SELECT DISTINCT zona FROM {SCHEMA}.cruceros")["zona"])
    sin_cat = escalar(engine_pruebas, f"""
        SELECT COUNT(*) FROM {SCHEMA}.cruceros c LEFT JOIN {SCHEMA}.cat_sectores s USING (sector)
        WHERE c.sector IS NOT NULL AND s.sector IS NULL""")
    assert sin_cat == 0


def test_coordenadas_dentro_del_municipio_salvo_marcados(engine_pruebas):
    from shapely import points

    limite = pipeline.leer_limite_municipal()
    df = q(engine_pruebas, f"SELECT x_utm, y_utm, latitud, longitud, fuera_municipio FROM {SCHEMA}.cruceros")
    dentro = limite.contains(points(df["x_utm"].to_numpy(), df["y_utm"].to_numpy()))
    assert (dentro == ~df["fuera_municipio"]).all()
    # Caja amplia del municipio de Juárez en grados
    no_marcados = df[~df["fuera_municipio"]]
    assert no_marcados["latitud"].between(31.0, 31.85).all()
    assert no_marcados["longitud"].between(-107.0, -106.1).all()


def test_marcas_de_calidad_esperadas(engine_pruebas):
    rc = q(engine_pruebas, f"SELECT * FROM {SCHEMA}.v_resumen_calidad").iloc[0]
    assert rc["zona_inferida"] == 11
    assert rc["sin_id_crucero"] == 1
    assert rc["nombre_corregido"] == 3
    assert rc["fuera_municipio"] == 2
    nombres = q(engine_pruebas, f"SELECT calle_1, calle_2 FROM {SCHEMA}.cruceros")
    assert not (nombres["calle_1"].str.contains("¥").any() or nombres["calle_2"].str.contains("¥").any())


def test_bitacora_completa(engine_pruebas):
    bit = q(engine_pruebas, f"SELECT * FROM {SCHEMA}.v_ultima_bitacora ORDER BY orden")
    assert bit["codigo"].tolist() == [f"R{i:02d}" for i in range(1, 17)]
    assert bit.loc[bit["codigo"] == "R01", "registros_afectados"].item() == 0   # GPKG = CSV
    assert (bit["registros_antes"] >= bit["registros_despues"]).all()


def test_pipeline_idempotente(engine_pruebas):
    """Correrlo otra vez no duplica datos; solo agrega una ejecución a la bitácora."""
    antes = escalar(engine_pruebas, f"SELECT COUNT(*) FROM {SCHEMA}.ejecuciones_pipeline")
    pipeline.ejecutar(engine_pruebas, escribir_archivos=False)
    assert escalar(engine_pruebas, f"SELECT COUNT(*) FROM {SCHEMA}.cruceros") == 2787
    assert escalar(engine_pruebas, f"SELECT COUNT(*) FROM {SCHEMA}.raw_cruceros_2024") == 2787
    assert escalar(engine_pruebas, f"SELECT COUNT(*) FROM {SCHEMA}.ejecuciones_pipeline") == antes + 1


def test_vistas_cuadran_con_la_tabla(engine_pruebas):
    total = escalar(engine_pruebas, f"SELECT SUM(incidentes) FROM {SCHEMA}.cruceros")
    zonas = q(engine_pruebas, f"SELECT * FROM {SCHEMA}.v_incidentes_por_zona")
    assert zonas["incidentes"].sum() == total
    assert zonas["porcentaje"].sum() == pytest.approx(100, abs=0.05)
    rk = q(engine_pruebas, f"SELECT * FROM {SCHEMA}.v_ranking_cruceros ORDER BY posicion, id_objeto")
    assert rk["posicion"].iloc[0] == 1
    assert rk["porcentaje_acumulado"].max() == pytest.approx(100, abs=0.01)


def test_consulta_filtrada_parametrizada(engine_pruebas):
    from src.analisis import datos
    df = datos.cargar_cruceros(engine_pruebas, zonas=["ORIENTE"], min_incidentes=3)
    assert set(df["zona"]) == {"ORIENTE"} and (df["incidentes"] >= 3).all()
    # Un valor malicioso se trata como texto, no como SQL
    assert datos.cargar_cruceros(engine_pruebas, zonas=["SUR' OR '1'='1"]).empty
    with pytest.raises(ValueError):
        datos.cargar_tabla(engine_pruebas, "cruceros; DROP TABLE x")
