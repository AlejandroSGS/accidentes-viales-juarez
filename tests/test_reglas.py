"""Pruebas unitarias de cada regla de limpieza (con DATOS SINTÉTICOS de conftest.py)."""
import pandas as pd
import pytest
from shapely import points
from shapely.geometry import box

from src.limpieza import reglas as r


@pytest.fixture
def base(crudo_sintetico):
    """Datos sintéticos ya renombrados (punto de partida de casi todas las reglas)."""
    df, _ = r.renombrar_columnas(crudo_sintetico)
    return df


def test_renombrar_columnas(crudo_sintetico):
    df, n = r.renombrar_columnas(crudo_sintetico)
    assert n == 5
    assert list(df.columns) == [*r.COLUMNAS.values(), "anio"]
    assert (df["anio"] == 2024).all()


def test_renombrar_falla_si_falta_columna(crudo_sintetico):
    with pytest.raises(ValueError, match="ACCI2024"):
        r.renombrar_columnas(crudo_sintetico.drop(columns="ACCI2024"))


def test_corregir_codificacion(base):
    df, n = r.corregir_codificacion(base)
    assert n == 1
    assert df.loc[0, "calle_1"] == "NIÑOS HEROES"
    assert df["nombre_corregido"].tolist() == [True, False, False, False, False]
    assert not df["calle_1"].str.contains("¥").any()


def test_normalizar_texto(base):
    df, n = r.normalizar_texto(base)
    assert df.loc[1, "calle_1"] == "TECNOLOGICO"
    assert df.loc[1, "calle_2"] == "EJERCITO NACIONAL"
    assert n == 1  # solo la fila 1 tenía minúsculas y espacios de más


def test_verificar_coordenadas_manda_la_geometria(base):
    geom = pd.Series(points(base["x_utm"] + [0, 0, 0, 0, 5], base["y_utm"]))
    geom = pd.Series(list(geom))
    import geopandas as gpd
    df, n = r.verificar_coordenadas(base, gpd.GeoSeries(geom))
    assert n == 1
    assert df.loc[4, "x_utm"] == base.loc[4, "x_utm"] + 5


def test_convertir_a_wgs84(base):
    df, n = r.convertir_a_wgs84(base)
    assert n == 5
    # Ciudad Juárez está alrededor de 31.7 N, -106.4 O
    assert df["latitud"].between(31.5, 31.9).all()
    assert df["longitud"].between(-106.6, -106.2).all()


def test_marcar_fuera_municipio(base):
    limite = box(359000, 3504000, 362150, 3511000)  # deja fuera la fila 4 (x = 362200)
    df, n = r.marcar_fuera_municipio(base, limite)
    assert n == 1
    assert df["fuera_municipio"].tolist() == [False, False, False, False, True]


def test_inferir_zona_por_mayoria_de_vecinos():
    # SINTÉTICO: 3 vecinos SUR cerca y 2 CENTRO lejos del crucero sin zona
    df = pd.DataFrame({
        "zona": ["SIN_DATO", "SUR", "SUR", "SUR", "CENTRO", "CENTRO"],
        "x_utm": [0, 10, 20, 30, 1000, 1010], "y_utm": [0, 0, 0, 0, 0, 0],
    })
    out, n = r.inferir_zona(df, k=5)
    assert n == 1
    assert out.loc[0, "zona"] == "SUR"
    assert out.loc[0, "zona_original"] == "SIN_DATO"
    assert out["zona_inferida"].tolist() == [True, False, False, False, False, False]


def test_inferir_zona_empate_gana_el_mas_cercano():
    df = pd.DataFrame({"zona": ["SIN_DATO", "CENTRO", "SUR", "SUR", "CENTRO"],
                       "x_utm": [0, 5, 10, 20, 30], "y_utm": [0, 0, 0, 0, 0]})
    out, _ = r.inferir_zona(df, k=4)
    assert out.loc[0, "zona"] == "CENTRO"


def test_inferir_zona_sin_faltantes_no_cambia_nada():
    df = pd.DataFrame({"zona": ["SUR", "CENTRO"], "x_utm": [0, 1], "y_utm": [0, 1]})
    out, n = r.inferir_zona(df)
    assert n == 0 and out["zona"].tolist() == ["SUR", "CENTRO"]


def test_marcar_sector_sin_dato(base):
    df, n = r.marcar_sector_sin_dato(base)
    assert n == 1
    assert pd.isna(df.loc[2, "sector"])
    assert df["sector_sin_dato"].tolist() == [False, False, True, False, False]


def test_marcar_sin_id_crucero(base):
    df, n = r.marcar_sin_id_crucero(base)
    assert n == 1
    assert pd.isna(df.loc[2, "id_crucero"])
    assert df.loc[0, "id_crucero"] == 10


def test_marcar_no_es_crucero(base):
    df, n = r.marcar_no_es_crucero(base)
    assert n == 1 and df.loc[2, "no_es_crucero"]


def test_marcar_coord_repetida():
    df = pd.DataFrame({"x_utm": [0.0, 0.2, 100.0], "y_utm": [0.0, 0.1, 100.0]})
    out, n = r.marcar_coord_repetida(df)
    assert n == 2
    assert out["coord_repetida"].tolist() == [True, True, False]


def test_marcar_sector_multizona():
    df = pd.DataFrame({"sector": pd.array([1, 1, 2, pd.NA], dtype="Int64"),
                       "zona": ["SUR", "CENTRO", "SUR", "SUR"]})
    out, n = r.marcar_sector_multizona(df)
    assert n == 2
    assert out["sector_multizona"].tolist() == [True, True, False, False]


def test_construir_nombre_crucero():
    df = pd.DataFrame({"calle_1": ["ZARAGOZA", "HIDALGO", "JUAREZ"], "calle_2": ["ABETO", "HIDALGO", ""]})
    out, _ = r.construir_nombre_crucero(df)
    assert out["nombre_crucero"].tolist() == ["ABETO y ZARAGOZA", "HIDALGO", "JUAREZ"]


def test_eliminar_duplicados():
    df = pd.DataFrame({
        "id_objeto": [1, 1, 2, 3],
        "id_crucero": [10, 10, 20, 20], "calle_1": ["A", "A", "B", "B"], "calle_2": ["C", "C", "D", "D"],
        "x_utm": [0, 0, 5, 5], "y_utm": [0, 0, 5, 5],
    })
    out, n = r.eliminar_duplicados(df)
    assert n == 2  # una por id_objeto repetido y otra por mismo crucero y ubicación
    assert out["id_objeto"].tolist() == [1, 2]


def test_validar_conteo_acepta_validos(base):
    out, n = r.validar_conteo(base)
    assert n == 0 and out["incidentes"].dtype.kind == "i"


@pytest.mark.parametrize("malo", [0, -1, 2.5, None])
def test_validar_conteo_rechaza_invalidos(base, malo):
    base["incidentes"] = base["incidentes"].astype(float)
    base.loc[0, "incidentes"] = malo
    with pytest.raises(ValueError):
        r.validar_conteo(base)


def test_comparar_archivos(crudo_sintetico):
    assert r.comparar_archivos(crudo_sintetico, crudo_sintetico.copy()) == 0
    otro = crudo_sintetico.copy()
    otro.loc[3, "ACCI2024"] = 99
    assert r.comparar_archivos(crudo_sintetico, otro) == 1


def test_reglas_no_modifican_la_entrada(base):
    copia = base.copy()
    r.corregir_codificacion(base)
    r.normalizar_texto(base)
    r.marcar_sector_sin_dato(base)
    pd.testing.assert_frame_equal(base, copia)
