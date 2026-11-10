"""Estadística descriptiva de los cruceros: rankings, agregados y concentración.

Todas las funciones reciben el DataFrame de cruceros limpios y no consultan la base,
así se pueden probar con datos pequeños calculados a mano.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def resumen_general(df: pd.DataFrame) -> dict:
    """Cifras clave para las tarjetas de la página de inicio."""
    inc = df["incidentes"]
    return {
        "cruceros": int(len(df)),
        "incidentes": int(inc.sum()),
        "promedio_por_crucero": float(inc.mean()) if len(df) else 0.0,
        "mediana_por_crucero": float(inc.median()) if len(df) else 0.0,
        "maximo_crucero": int(inc.max()) if len(df) else 0,
        "cruceros_con_1": int((inc == 1).sum()),
        "zonas": int(df["zona"].nunique()),
        "sectores": int(df["sector"].nunique()),
    }


def ranking_cruceros(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    """Los n cruceros con más incidentes, con su % del total y posición (empates comparten lugar)."""
    total = df["incidentes"].sum()
    out = df.sort_values(["incidentes", "nombre_crucero"], ascending=[False, True]).head(n).copy()
    out["porcentaje"] = 100 * out["incidentes"] / total if total else 0.0
    out["posicion"] = out["incidentes"].rank(method="min", ascending=False).astype(int)
    return out[["posicion", "nombre_crucero", "zona", "sector", "incidentes", "porcentaje",
                "latitud", "longitud", "id_objeto"]].reset_index(drop=True)


def agregar_por(df: pd.DataFrame, columna: str) -> pd.DataFrame:
    """Cruceros, incidentes, % e incidentes promedio por crucero para cada valor de `columna`."""
    g = df.dropna(subset=[columna]).groupby(columna, observed=True)
    out = g.agg(cruceros=("id_objeto", "size"), incidentes=("incidentes", "sum")).reset_index()
    total = df["incidentes"].sum()
    out["porcentaje"] = 100 * out["incidentes"] / total if total else 0.0
    out["promedio_por_crucero"] = out["incidentes"] / out["cruceros"]
    return out.sort_values("incidentes", ascending=False).reset_index(drop=True)


def distribucion_conteos(df: pd.DataFrame, cortes: tuple = (1, 2, 3, 5, 10, 20)) -> pd.DataFrame:
    """Cuántos cruceros tienen 1, 2, 3–4, 5–9, 10–19 y 20 o más incidentes."""
    bordes = list(cortes) + [np.inf]
    etiquetas = []
    for a, b in zip(bordes[:-1], bordes[1:]):
        if b == np.inf:
            etiquetas.append(f"{a} o más")
        elif b - a == 1:
            etiquetas.append(str(a))
        else:
            etiquetas.append(f"{a}–{int(b) - 1}")
    grupo = pd.cut(df["incidentes"], bins=bordes, right=False, labels=etiquetas).rename("rango")
    out = df.groupby(grupo, observed=False).agg(cruceros=("id_objeto", "size"), incidentes=("incidentes", "sum"))
    out = out.reset_index()
    out["pct_cruceros"] = 100 * out["cruceros"] / max(len(df), 1)
    out["pct_incidentes"] = 100 * out["incidentes"] / max(df["incidentes"].sum(), 1)
    return out


def curva_concentracion(df: pd.DataFrame) -> pd.DataFrame:
    """Curva de Pareto: % acumulado de incidentes vs % de cruceros (de más a menos incidentes)."""
    inc = np.sort(df["incidentes"].to_numpy())[::-1]
    n, total = len(inc), inc.sum()
    return pd.DataFrame({
        "pct_cruceros": 100 * np.arange(1, n + 1) / n,
        "pct_incidentes": 100 * np.cumsum(inc) / total,
    })


def pct_cruceros_para(df: pd.DataFrame, pct_incidentes: float) -> float:
    """% mínimo de cruceros (los de más incidentes) que acumula `pct_incidentes` % del total."""
    curva = curva_concentracion(df)
    idx = int(np.searchsorted(curva["pct_incidentes"].to_numpy(), pct_incidentes - 1e-9))
    return float(curva["pct_cruceros"].iloc[min(idx, len(curva) - 1)])


def indice_gini(df: pd.DataFrame) -> float:
    """Gini de la distribución de incidentes entre cruceros (0 = repartidos igual, 1 = todo en uno)."""
    x = np.sort(df["incidentes"].to_numpy(dtype=float))
    n = len(x)
    if n == 0 or x.sum() == 0:
        return 0.0
    return float((2 * np.arange(1, n + 1) - n - 1).dot(x) / (n * x.sum()))
