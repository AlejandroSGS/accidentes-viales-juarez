"""Pruebas de las funciones de análisis contra resultados calculados a mano (DATOS SINTÉTICOS)."""
import numpy as np
import pandas as pd
import pytest

from src.analisis import descriptiva as de, espacial as es


# ---------- Descriptiva ----------
# Incidentes sintéticos: [10, 5, 2, 1, 1, 1] → total 20

def test_resumen_general(cruceros_sinteticos):
    r = de.resumen_general(cruceros_sinteticos)
    assert r["cruceros"] == 6
    assert r["incidentes"] == 20
    assert r["promedio_por_crucero"] == pytest.approx(20 / 6)
    assert r["mediana_por_crucero"] == 1.5      # (2 + 1) / 2
    assert r["maximo_crucero"] == 10
    assert r["cruceros_con_1"] == 3
    assert r["zonas"] == 2 and r["sectores"] == 3


def test_ranking_con_empates(cruceros_sinteticos):
    rk = de.ranking_cruceros(cruceros_sinteticos, 6)
    assert rk["incidentes"].tolist() == [10, 5, 2, 1, 1, 1]
    assert rk["posicion"].tolist() == [1, 2, 3, 4, 4, 4]
    assert rk.loc[0, "porcentaje"] == pytest.approx(50.0)   # 10 / 20


def test_agregar_por_zona(cruceros_sinteticos):
    z = de.agregar_por(cruceros_sinteticos, "zona").set_index("zona")
    assert z.loc["A", "incidentes"] == 15 and z.loc["A", "cruceros"] == 2
    assert z.loc["B", "incidentes"] == 5 and z.loc["B", "cruceros"] == 4
    assert z.loc["A", "porcentaje"] == pytest.approx(75.0)
    assert z.loc["B", "promedio_por_crucero"] == pytest.approx(1.25)
    assert z.index.tolist() == ["A", "B"]  # ordenado de mayor a menor


def test_agregar_por_sector_ignora_vacios(cruceros_sinteticos):
    s = de.agregar_por(cruceros_sinteticos, "sector")
    assert s["cruceros"].sum() == 5          # el crucero sin sector no cuenta
    assert s.set_index("sector").loc[1, "incidentes"] == 15


def test_distribucion_conteos(cruceros_sinteticos):
    d = de.distribucion_conteos(cruceros_sinteticos).set_index("rango")
    assert d.loc["1", "cruceros"] == 3
    assert d.loc["2", "cruceros"] == 1
    assert d.loc["5–9", "cruceros"] == 1
    assert d.loc["10–19", "cruceros"] == 1
    assert d["cruceros"].sum() == 6 and d["incidentes"].sum() == 20
    assert d["pct_cruceros"].sum() == pytest.approx(100)


def test_curva_y_pct_para(cruceros_sinteticos):
    curva = de.curva_concentracion(cruceros_sinteticos)
    # acumulado: 10, 15, 17, 18, 19, 20 → 50 %, 75 %, 85 %, 90 %, 95 %, 100 %
    assert curva["pct_incidentes"].tolist() == pytest.approx([50, 75, 85, 90, 95, 100])
    assert de.pct_cruceros_para(cruceros_sinteticos, 50) == pytest.approx(100 / 6)
    assert de.pct_cruceros_para(cruceros_sinteticos, 80) == pytest.approx(300 / 6)


def test_gini_casos_extremos():
    iguales = pd.DataFrame({"incidentes": [3, 3, 3, 3]})
    assert de.indice_gini(iguales) == pytest.approx(0.0)
    # [0,0,0,4]: G = (n - 1) / n = 0.75
    concentrado = pd.DataFrame({"incidentes": [0, 0, 0, 4]})
    assert de.indice_gini(concentrado) == pytest.approx(0.75)


def test_gini_sintetico(cruceros_sinteticos):
    # x ordenado = [1,1,1,2,5,10], n = 6, suma = 20
    # Σ (2i - n - 1) x_i = -5 -3 -1 +2 +15 +50 = 58  →  G = 58 / (6 * 20)
    assert de.indice_gini(cruceros_sinteticos) == pytest.approx(58 / 120)


# ---------- Espacial ----------

def test_kde_integra_al_total(cruceros_sinteticos):
    malla = es.densidad_kernel(cruceros_sinteticos, ancho_banda_m=300, celda_m=50, margen_m=2000)
    area_celda_km2 = (50 * 50) / 1e6
    assert (malla["densidad_km2"] * area_celda_km2).sum() == pytest.approx(20, rel=0.02)


def test_kde_es_mayor_donde_hay_mas_incidentes(cruceros_sinteticos):
    dens = es.densidad_en_cruceros(cruceros_sinteticos, ancho_banda_m=300)
    assert dens.iloc[0] > dens.iloc[3]   # grupo A (15 inc.) más denso que grupo B (5 inc.)


def test_kde_excluye_fuera_municipio(cruceros_sinteticos):
    df = cruceros_sinteticos.copy()
    df.loc[0, "fuera_municipio"] = True
    malla = es.densidad_kernel(df, ancho_banda_m=300, celda_m=50, margen_m=2000)
    assert (malla["densidad_km2"] * 0.0025).sum() == pytest.approx(10, rel=0.02)


def test_kmeans_separa_dos_grupos_obvios(cruceros_sinteticos):
    grupos = es.agrupar_cruceros(cruceros_sinteticos, k=2)
    assert grupos.tolist() == [1, 1, 2, 2, 2, 2]  # 1 = grupo con más incidentes (A, 15)


def test_kmeans_es_reproducible(cruceros_sinteticos):
    a = es.agrupar_cruceros(cruceros_sinteticos, k=2)
    b = es.agrupar_cruceros(cruceros_sinteticos, k=2)
    pd.testing.assert_series_equal(a, b)


def test_perfil_grupos(cruceros_sinteticos):
    grupos = es.agrupar_cruceros(cruceros_sinteticos, k=2)
    p = es.perfil_grupos(cruceros_sinteticos, grupos).set_index("grupo")
    assert p.loc[1, "incidentes"] == 15 and p.loc[1, "cruceros"] == 2
    assert p.loc[2, "incidentes"] == 5 and p.loc[2, "cruceros"] == 4
    assert p["porcentaje"].sum() == pytest.approx(100)
    assert p.loc[1, "zona_predominante"] == "A"
    assert p.loc[1, "crucero_principal"] == "UNO y DOS"
    assert p.loc[1, "area_km2"] == 0.0            # menos de 3 cruceros → sin polígono
    assert np.isnan(p.loc[1, "incidentes_por_km2"])


def test_silueta_ponderada_grupos_separados(cruceros_sinteticos):
    xy = cruceros_sinteticos[["x_utm", "y_utm"]].to_numpy()
    etiquetas = np.array([0, 0, 1, 1, 1, 1])
    s = es.silueta_ponderada(xy, etiquetas, cruceros_sinteticos["incidentes"].to_numpy())
    assert s > 0.95
