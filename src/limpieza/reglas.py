"""Reglas de limpieza y transformación de los cruceros 2024.

Cada regla es una función pura: recibe un DataFrame y devuelve (DataFrame nuevo,
registros afectados). No borra registros con problemas: los marca con una
columna booleana para que la app los pueda reportar.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd
from pyproj import Transformer
from shapely import points
from shapely.geometry.base import BaseGeometry
from sklearn.neighbors import NearestNeighbors

ID_SIN_CRUCERO = 99999
ZONA_SIN_DATO = "SIN_DATO"
VECINOS_ZONA = 5

COLUMNAS = {
    "OBJECTID": "id_objeto",
    "PUNTOS_ID": "id_crucero",
    "NOMBRE1": "calle_1",
    "NOMBRE2": "calle_2",
    "DicSegPub": "zona",
    "SECTOR": "sector",
    "ACCI2024": "incidentes",
    "X": "x_utm",
    "Y": "y_utm",
}


@dataclass(frozen=True)
class Regla:
    codigo: str
    descripcion: str
    accion: str  # corrige / marca / verifica / transforma
    aplicar: Callable[[pd.DataFrame], tuple[pd.DataFrame, int]]


# ---------- Reglas ----------

def renombrar_columnas(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Pasa los nombres originales a snake_case en español y agrega el año."""
    faltan = set(COLUMNAS) - set(df.columns)
    if faltan:
        raise ValueError(f"Faltan columnas en el archivo de origen: {sorted(faltan)}")
    out = df.rename(columns=COLUMNAS)[list(COLUMNAS.values())].copy()
    out["anio"] = 2024
    return out, len(out)


def corregir_codificacion(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Corrige la Ñ mal codificada como '¥' (CP437) en los nombres de calle."""
    out = df.copy()
    mask = out["calle_1"].str.contains("¥", regex=False) | out["calle_2"].str.contains("¥", regex=False)
    for col in ("calle_1", "calle_2"):
        out[col] = out[col].str.replace("¥", "Ñ", regex=False)
    out["nombre_corregido"] = mask
    return out, int(mask.sum())


def normalizar_texto(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Mayúsculas, sin espacios al inicio/fin y sin espacios dobles en calles y zona."""
    out = df.copy()
    cambios = pd.Series(False, index=out.index)
    for col in ("calle_1", "calle_2", "zona"):
        limpio = out[col].fillna("").astype(str).str.upper().str.strip().str.replace(r"\s+", " ", regex=True)
        cambios |= limpio != out[col].fillna("")
        out[col] = limpio
    return out, int(cambios.sum())


def verificar_coordenadas(df: pd.DataFrame, geometria: pd.Series) -> tuple[pd.DataFrame, int]:
    """Compara X/Y del atributo contra la geometría; si difieren, manda la geometría."""
    out = df.copy()
    gx, gy = geometria.x.to_numpy(), geometria.y.to_numpy()
    distinto = (np.abs(out["x_utm"] - gx) > 0.01) | (np.abs(out["y_utm"] - gy) > 0.01)
    out["x_utm"], out["y_utm"] = gx, gy
    return out, int(distinto.sum())


def convertir_a_wgs84(df: pd.DataFrame, crs_origen: int = 32613) -> tuple[pd.DataFrame, int]:
    """Convierte UTM 13N a latitud/longitud (WGS84) para los mapas web."""
    out = df.copy()
    tr = Transformer.from_crs(crs_origen, 4326, always_xy=True)
    lon, lat = tr.transform(out["x_utm"].to_numpy(), out["y_utm"].to_numpy())
    out["longitud"], out["latitud"] = lon, lat
    return out, len(out)


def marcar_fuera_municipio(df: pd.DataFrame, limite: BaseGeometry) -> tuple[pd.DataFrame, int]:
    """Marca los cruceros cuya ubicación cae fuera del límite municipal (no se borran)."""
    out = df.copy()
    pts = points(out["x_utm"].to_numpy(), out["y_utm"].to_numpy())
    out["fuera_municipio"] = ~limite.contains(pts)
    return out, int(out["fuera_municipio"].sum())


def inferir_zona(df: pd.DataFrame, k: int = VECINOS_ZONA) -> tuple[pd.DataFrame, int]:
    """Asigna la zona más común entre los k cruceros vecinos con zona conocida.

    En caso de empate gana la zona del vecino más cercano. El valor original
    se conserva en `zona_original`.
    """
    out = df.copy()
    out["zona_original"] = out["zona"]
    sin = out["zona"].isin([ZONA_SIN_DATO, ""])
    out["zona_inferida"] = sin
    if not sin.any():
        return out, 0
    con = out[~sin]
    nn = NearestNeighbors(n_neighbors=min(k, len(con))).fit(con[["x_utm", "y_utm"]])
    _, idx = nn.kneighbors(out.loc[sin, ["x_utm", "y_utm"]])
    zonas_con = con["zona"].to_numpy()
    asignadas = []
    for fila in idx:
        vecinas = list(zonas_con[fila])  # ordenadas de la más cercana a la más lejana
        conteo = pd.Series(vecinas).value_counts()
        empatadas = set(conteo[conteo == conteo.max()].index)
        asignadas.append(next(z for z in vecinas if z in empatadas))
    out.loc[sin, "zona"] = asignadas
    return out, int(sin.sum())


def marcar_sector_sin_dato(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """El sector 0 no existe: pasa a vacío (NULL) y se marca."""
    out = df.copy()
    mask = out["sector"].isna() | (out["sector"] == 0)
    out["sector_sin_dato"] = mask
    out["sector"] = out["sector"].where(~mask).astype("Int64")
    return out, int(mask.sum())


def marcar_sin_id_crucero(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """PUNTOS_ID = 99999 significa 'sin identificador': pasa a vacío y se marca."""
    out = df.copy()
    mask = out["id_crucero"].isna() | (out["id_crucero"] == ID_SIN_CRUCERO) | (out["id_crucero"] <= 0)
    out["sin_id_crucero"] = mask
    out["id_crucero"] = out["id_crucero"].where(~mask).astype("Int64")
    return out, int(mask.sum())


def marcar_no_es_crucero(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Calle 1 igual a calle 2 (o una vacía): es un tramo de calle, no una intersección."""
    out = df.copy()
    mask = (out["calle_1"] == out["calle_2"]) | (out["calle_1"] == "") | (out["calle_2"] == "")
    out["no_es_crucero"] = mask
    return out, int(mask.sum())


def marcar_coord_repetida(df: pd.DataFrame, tolerancia_m: float = 0.5) -> tuple[pd.DataFrame, int]:
    """Marca cruceros distintos que comparten la misma ubicación (a menos de 0.5 m)."""
    out = df.copy()
    clave = (out["x_utm"] / tolerancia_m).round().astype(int).astype(str) + "_" + \
            (out["y_utm"] / tolerancia_m).round().astype(int).astype(str)
    out["coord_repetida"] = clave.duplicated(keep=False)
    return out, int(out["coord_repetida"].sum())


def marcar_sector_multizona(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Marca los cruceros de sectores que aparecen en más de una zona."""
    out = df.copy()
    zonas_por_sector = out.dropna(subset=["sector"]).groupby("sector")["zona"].nunique()
    multi = zonas_por_sector[zonas_por_sector > 1].index
    out["sector_multizona"] = out["sector"].isin(multi).fillna(False).astype(bool)
    return out, int(out["sector_multizona"].sum())


def construir_nombre_crucero(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Nombre legible 'CALLE A y CALLE B' con las calles en orden alfabético."""
    out = df.copy()

    def nombre(a: str, b: str) -> str:
        if a == b or not b:
            return a
        if not a:
            return b
        x, y = sorted([a, b])
        return f"{x} y {y}"

    out["nombre_crucero"] = [nombre(a, b) for a, b in zip(out["calle_1"], out["calle_2"])]
    return out, len(out)


def eliminar_duplicados(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Elimina registros repetidos: mismo id_objeto, o mismo crucero, calles y ubicación."""
    antes = len(df)
    clave = ["id_crucero", "calle_1", "calle_2", "x_utm", "y_utm"]
    out = df.drop_duplicates(subset=["id_objeto"]).drop_duplicates(subset=clave)
    return out.reset_index(drop=True), antes - len(out)


def validar_conteo(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Verifica que el número de incidentes sea entero y ≥ 1; si no, la carga se detiene."""
    malos = df["incidentes"].isna() | (df["incidentes"] < 1) | (df["incidentes"] % 1 != 0)
    if malos.any():
        raise ValueError(f"{int(malos.sum())} registros con conteo de incidentes inválido")
    out = df.copy()
    out["incidentes"] = out["incidentes"].astype(int)
    return out, 0


def comparar_archivos(gpkg: pd.DataFrame, csv: pd.DataFrame) -> int:
    """Cuenta filas distintas entre el GPKG y el CSV del proyecto (deberían ser iguales)."""
    a = gpkg.drop(columns="geometry", errors="ignore").reset_index(drop=True)
    b = csv.reset_index(drop=True)
    if len(a) != len(b) or list(a.columns) != list(b.columns):
        return max(len(a), len(b))
    distintas = (a.astype(str) != b.astype(str)).any(axis=1)
    return int(distintas.sum())
