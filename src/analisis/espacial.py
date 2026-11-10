"""Análisis espacial: densidad Kernel (KDE) y K-means ponderado, siguiendo a Anderson (2009).

Ambos métodos trabajan en coordenadas UTM (metros) y pesan cada crucero por su
número de incidentes. Son métodos descriptivos: muestran dónde se concentran los
registros, no por qué ocurren.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from pyproj import Transformer
from shapely import MultiPoint
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.neighbors import KernelDensity

ANCHO_BANDA_M = 500     # radio de suavizado del KDE (≈ 4–5 cuadras)
TAMANO_CELDA_M = 200    # resolución de la malla del mapa de densidad
SEMILLA = 42            # para que K-means dé siempre el mismo resultado

_A_WGS84 = Transformer.from_crs(32613, 4326, always_xy=True)


def _solo_dentro(df: pd.DataFrame) -> pd.DataFrame:
    """Excluye los cruceros marcados fuera del municipio (si la columna existe)."""
    if "fuera_municipio" in df:
        return df[~df["fuera_municipio"].astype(bool)]
    return df


# ---------- Densidad Kernel ----------

def densidad_kernel(df: pd.DataFrame, ancho_banda_m: float = ANCHO_BANDA_M,
                    celda_m: float = TAMANO_CELDA_M, margen_m: float = 1500) -> pd.DataFrame:
    """Evalúa el KDE ponderado en una malla regular.

    Devuelve una fila por celda con su centro (UTM y lat/lon) y la densidad en
    **incidentes por km²**, de modo que la suma de densidad × área ≈ total de incidentes.
    """
    d = _solo_dentro(df)
    xy = d[["x_utm", "y_utm"]].to_numpy()
    w = d["incidentes"].to_numpy(dtype=float)
    kde = KernelDensity(bandwidth=ancho_banda_m, kernel="gaussian").fit(xy, sample_weight=w)
    xmin, ymin = xy.min(axis=0) - margen_m
    xmax, ymax = xy.max(axis=0) + margen_m
    gx, gy = np.meshgrid(np.arange(xmin, xmax, celda_m) + celda_m / 2, np.arange(ymin, ymax, celda_m) + celda_m / 2)
    malla = np.column_stack([gx.ravel(), gy.ravel()])
    dens_m2 = np.exp(kde.score_samples(malla))          # probabilidad por m²
    lon, lat = _A_WGS84.transform(malla[:, 0], malla[:, 1])
    return pd.DataFrame({
        "x_utm": malla[:, 0], "y_utm": malla[:, 1], "latitud": lat, "longitud": lon,
        "densidad_km2": dens_m2 * w.sum() * 1e6,
    })


def densidad_en_cruceros(df: pd.DataFrame, ancho_banda_m: float = ANCHO_BANDA_M) -> pd.Series:
    """Densidad KDE (incidentes/km²) en la ubicación de cada crucero."""
    d = _solo_dentro(df)
    kde = KernelDensity(bandwidth=ancho_banda_m).fit(d[["x_utm", "y_utm"]].to_numpy(),
                                                     sample_weight=d["incidentes"].to_numpy(dtype=float))
    dens = np.exp(kde.score_samples(df[["x_utm", "y_utm"]].to_numpy())) * d["incidentes"].sum() * 1e6
    return pd.Series(dens, index=df.index, name="densidad_km2")


def celdas_calientes(malla: pd.DataFrame, percentil: float = 99) -> pd.DataFrame:
    """Celdas con densidad igual o mayor al percentil indicado (solo celdas con densidad > 0.1)."""
    con_dato = malla[malla["densidad_km2"] > 0.1]
    umbral = np.percentile(con_dato["densidad_km2"], percentil)
    return con_dato[con_dato["densidad_km2"] >= umbral].sort_values("densidad_km2", ascending=False)


# ---------- K-means ponderado ----------

def ajustar_kmeans(df: pd.DataFrame, k: int, semilla: int = SEMILLA) -> KMeans:
    d = _solo_dentro(df)
    return KMeans(n_clusters=k, n_init=20, random_state=semilla).fit(
        d[["x_utm", "y_utm"]].to_numpy(), sample_weight=d["incidentes"].to_numpy(dtype=float))


def silueta_ponderada(xy: np.ndarray, etiquetas: np.ndarray, pesos: np.ndarray) -> float:
    """Silueta contando cada crucero tantas veces como incidentes tiene."""
    rep = np.repeat(np.arange(len(xy)), pesos.astype(int))
    return float(silhouette_score(xy[rep], etiquetas[rep]))


def evaluar_k(df: pd.DataFrame, ks=range(2, 13), semilla: int = SEMILLA) -> pd.DataFrame:
    """Inercia (método del codo) y silueta para cada número de grupos k."""
    d = _solo_dentro(df)
    xy = d[["x_utm", "y_utm"]].to_numpy()
    w = d["incidentes"].to_numpy()
    filas = []
    for k in ks:
        m = ajustar_kmeans(d, k, semilla)
        filas.append({"k": k, "inercia_km2": m.inertia_ / 1e6,
                      "silueta": silueta_ponderada(xy, m.labels_, w)})
    return pd.DataFrame(filas)


def agrupar_cruceros(df: pd.DataFrame, k: int, semilla: int = SEMILLA) -> pd.Series:
    """Grupo (1..k) de cada crucero; 1 = el grupo con más incidentes. Fuera del municipio → NA."""
    d = _solo_dentro(df)
    m = ajustar_kmeans(d, k, semilla)
    inc = pd.Series(d["incidentes"].to_numpy()).groupby(m.labels_).sum().sort_values(ascending=False)
    renumerar = {etq: i + 1 for i, etq in enumerate(inc.index)}
    grupos = pd.Series(pd.NA, index=df.index, dtype="Int64", name="grupo")
    grupos.loc[d.index] = [renumerar[e] for e in m.labels_]
    return grupos


def perfil_grupos(df: pd.DataFrame, grupos: pd.Series) -> pd.DataFrame:
    """Describe cada grupo: tamaño, incidentes, área, densidad, zona predominante y crucero principal."""
    d = df.assign(grupo=grupos).dropna(subset=["grupo"])
    total = d["incidentes"].sum()
    filas = []
    for g, sub in d.groupby("grupo"):
        w = sub["incidentes"].to_numpy(dtype=float)
        cx, cy = np.average(sub["x_utm"], weights=w), np.average(sub["y_utm"], weights=w)
        lon, lat = _A_WGS84.transform(cx, cy)
        area = MultiPoint(sub[["x_utm", "y_utm"]].to_numpy()).convex_hull.area / 1e6 if len(sub) >= 3 else 0.0
        zona = sub.groupby("zona")["incidentes"].sum().idxmax()
        top = sub.sort_values("incidentes", ascending=False).iloc[0]
        filas.append({
            "grupo": int(g), "cruceros": len(sub), "incidentes": int(w.sum()),
            "porcentaje": 100 * w.sum() / total, "promedio_por_crucero": w.mean(),
            "area_km2": area, "incidentes_por_km2": w.sum() / area if area else np.nan,
            "zona_predominante": zona, "crucero_principal": top["nombre_crucero"],
            "incidentes_crucero_principal": int(top["incidentes"]),
            "latitud_centro": lat, "longitud_centro": lon,
        })
    return pd.DataFrame(filas).sort_values("grupo").reset_index(drop=True)
