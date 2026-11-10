"""Pipeline reproducible: data/raw → reglas de limpieza → data/processed + PostgreSQL.

Uso:  python -m src.limpieza.pipeline [--test] [--sin-db]

Se puede ejecutar varias veces: cada corrida reemplaza las tablas de datos
dentro de una sola transacción (no duplica registros) y agrega su propia
entrada a la bitácora.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from functools import partial
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon
from shapely.ops import unary_union
from sqlalchemy import Engine, text

from src.config import (CRS_ORIGEN, DATA_PROCESSED, DOCS, RAW_CSV, RAW_GPKG,
                        RAW_LIMITE_MUNICIPAL, ROOT, SCHEMA, get_engine)
from src.limpieza import reglas as r

SALIDA_CSV = DATA_PROCESSED / "cruceros_2024_limpio.csv"
SALIDA_GPKG = DATA_PROCESSED / "cruceros_2024_limpio.gpkg"
BITACORA_MD = DOCS / "bitacora_limpieza.md"

COLUMNAS_FINALES = [
    "id_objeto", "id_crucero", "calle_1", "calle_2", "nombre_crucero", "zona", "zona_original",
    "sector", "anio", "incidentes", "x_utm", "y_utm", "latitud", "longitud",
    "zona_inferida", "sector_sin_dato", "sin_id_crucero", "no_es_crucero", "coord_repetida",
    "sector_multizona", "nombre_corregido", "fuera_municipio",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def leer_limite_municipal(path: Path = RAW_LIMITE_MUNICIPAL):
    """Lee el polígono del municipio (Esri JSON del IMIP) en UTM 13N."""
    data = json.loads(path.read_text(encoding="utf-8"))
    wkid = data["spatialReference"].get("latestWkid", data["spatialReference"].get("wkid"))
    if wkid != CRS_ORIGEN:
        raise ValueError(f"El límite municipal viene en EPSG:{wkid}, se esperaba {CRS_ORIGEN}")
    rings = data["features"][0]["geometry"]["rings"]
    return unary_union([Polygon(ring) for ring in rings]).buffer(0)


def definir_reglas(geometria: pd.Series, limite) -> list[r.Regla]:
    """Lista ordenada de reglas que se aplican a los datos."""
    return [
        r.Regla("R02", "Renombrar columnas a snake_case en español y agregar año", "transforma", r.renombrar_columnas),
        r.Regla("R03", "Corregir Ñ mal codificada ('¥' → 'Ñ') en nombres de calle", "corrige", r.corregir_codificacion),
        r.Regla("R04", "Normalizar texto (mayúsculas, espacios)", "corrige", r.normalizar_texto),
        r.Regla("R05", "Verificar X/Y contra la geometría (manda la geometría)", "verifica",
                partial(r.verificar_coordenadas, geometria=geometria)),
        r.Regla("R06", "Convertir coordenadas UTM 13N a latitud/longitud WGS84", "transforma", r.convertir_a_wgs84),
        r.Regla("R07", "Marcar cruceros fuera del límite municipal", "marca",
                partial(r.marcar_fuera_municipio, limite=limite)),
        r.Regla("R08", f"Inferir zona SIN_DATO por los {r.VECINOS_ZONA} cruceros vecinos más cercanos", "corrige", r.inferir_zona),
        r.Regla("R09", "Sector 0 → vacío y marcar sector_sin_dato", "marca", r.marcar_sector_sin_dato),
        r.Regla("R10", "PUNTOS_ID 99999 → vacío y marcar sin_id_crucero", "marca", r.marcar_sin_id_crucero),
        r.Regla("R11", "Marcar calle 1 = calle 2 (tramo, no intersección)", "marca", r.marcar_no_es_crucero),
        r.Regla("R12", "Marcar cruceros distintos con la misma ubicación", "marca", r.marcar_coord_repetida),
        r.Regla("R13", "Marcar sectores repartidos en más de una zona", "marca", r.marcar_sector_multizona),
        r.Regla("R14", "Construir nombre del crucero ('A y B', orden alfabético)", "transforma", r.construir_nombre_crucero),
        r.Regla("R15", "Eliminar duplicados (mismo id_objeto o mismo crucero y ubicación)", "corrige", r.eliminar_duplicados),
        r.Regla("R16", "Validar que el conteo de incidentes sea entero ≥ 1", "verifica", r.validar_conteo),
    ]


def limpiar(gdf: gpd.GeoDataFrame, csv: pd.DataFrame, limite) -> tuple[pd.DataFrame, list[dict]]:
    """Aplica todas las reglas y devuelve los datos limpios y la bitácora."""
    bitacora = [{
        "orden": 1, "codigo": "R01", "accion": "verifica",
        "regla": "Comparar GPKG y CSV del proyecto (deben ser idénticos)",
        "registros_afectados": r.comparar_archivos(gdf, csv),
        "registros_antes": len(gdf), "registros_despues": len(gdf),
    }]
    df = pd.DataFrame(gdf.drop(columns="geometry"))
    for orden, regla in enumerate(definir_reglas(gdf.geometry.reset_index(drop=True), limite), start=2):
        antes = len(df)
        df, afectados = regla.aplicar(df)
        bitacora.append({
            "orden": orden, "codigo": regla.codigo, "regla": regla.descripcion, "accion": regla.accion,
            "registros_afectados": afectados, "registros_antes": antes, "registros_despues": len(df),
        })
    return df[COLUMNAS_FINALES], bitacora


def catalogos(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Catálogo de zonas y de sectores (con su zona principal = la de más cruceros)."""
    zonas = pd.DataFrame({"zona": sorted(df["zona"].unique())})
    con_sector = df.dropna(subset=["sector"])
    conteo = con_sector.groupby(["sector", "zona"]).size().reset_index(name="n")
    principal = conteo.sort_values(["sector", "n", "zona"], ascending=[True, False, True]).drop_duplicates("sector")
    sectores = principal[["sector", "zona"]].rename(columns={"zona": "zona_principal"})
    sectores["num_zonas"] = sectores["sector"].map(conteo.groupby("sector")["zona"].nunique())
    return zonas, sectores.astype({"sector": int}).reset_index(drop=True)


def guardar_procesados(df: pd.DataFrame) -> None:
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_csv(SALIDA_CSV, index=False, encoding="utf-8")
    gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["longitud"], df["latitud"]), crs=4326) \
        .to_file(SALIDA_GPKG, layer="cruceros_2024", driver="GPKG", mode="w")


def cargar_db(engine: Engine, crudo: pd.DataFrame, df: pd.DataFrame, bitacora: list[dict],
              inicio: datetime, sha: str) -> int:
    """Reemplaza las tablas de datos en una sola transacción y registra la ejecución."""
    zonas, sectores = catalogos(df)
    with engine.begin() as conn:
        conn.execute(text(f"SET search_path TO {SCHEMA}"))
        id_ej = conn.execute(text(
            "INSERT INTO ejecuciones_pipeline (inicio, archivo_origen, sha256_origen, registros_crudos) "
            "VALUES (:inicio, :archivo, :sha, :n) RETURNING id_ejecucion"
        ), {"inicio": inicio, "archivo": RAW_GPKG.relative_to(ROOT).as_posix(), "sha": sha, "n": len(crudo)}).scalar_one()
        conn.execute(text("TRUNCATE cruceros, cat_sectores, cat_zonas, raw_cruceros_2024"))
        opts = dict(con=conn, schema=SCHEMA, if_exists="append", index=False, method="multi", chunksize=1000)
        crudo.assign(id_ejecucion=id_ej).to_sql("raw_cruceros_2024", **opts)
        zonas.to_sql("cat_zonas", **opts)
        sectores.to_sql("cat_sectores", **opts)
        df.assign(id_ejecucion=id_ej).to_sql("cruceros", **opts)
        pd.DataFrame(bitacora).assign(id_ejecucion=id_ej).to_sql("bitacora_limpieza", **opts)
        conn.execute(text(
            "UPDATE ejecuciones_pipeline SET fin = :fin, registros_limpios = :n WHERE id_ejecucion = :id"
        ), {"fin": datetime.now(timezone.utc), "n": len(df), "id": id_ej})
    return id_ej


def escribir_bitacora_md(bitacora: list[dict], df: pd.DataFrame, sha: str, inicio: datetime,
                         id_ejecucion: int | None) -> None:
    """Genera docs/bitacora_limpieza.md con el efecto de cada regla."""
    filas = "\n".join(
        f"| {b['orden']} | {b['codigo']} | {b['regla']} | {b['accion']} | {b['registros_afectados']:,} "
        f"| {b['registros_antes']:,} | {b['registros_despues']:,} |" for b in bitacora
    )
    marcas = ["zona_inferida", "sector_sin_dato", "sin_id_crucero", "no_es_crucero", "coord_repetida",
              "sector_multizona", "nombre_corregido", "fuera_municipio"]
    resumen = "\n".join(f"| `{m}` | {int(df[m].sum()):,} | {int(df.loc[df[m], 'incidentes'].sum()):,} |" for m in marcas)
    BITACORA_MD.write_text(f"""# Bitácora de limpieza

> Archivo generado automáticamente por `python -m src.limpieza.pipeline`. No editar a mano.

- **Ejecución:** {inicio.isoformat(timespec='seconds')} (UTC){f' · id_ejecucion = {id_ejecucion}' if id_ejecucion else ' · sin carga a base de datos'}
- **Origen:** `{RAW_GPKG.relative_to(ROOT).as_posix()}` (SHA-256 `{sha}`)
- **Salida:** `{SALIDA_CSV.relative_to(ROOT).as_posix()}`, `{SALIDA_GPKG.relative_to(ROOT).as_posix()}` y tabla `{SCHEMA}.cruceros`
- **Registros:** {bitacora[0]['registros_antes']:,} crudos → {len(df):,} limpios · incidentes: {int(df['incidentes'].sum()):,}

## Reglas aplicadas

| # | Código | Regla | Acción | Afectados | Antes | Después |
|---|---|---|---|---|---|---|
{filas}

## Registros marcados (se conservan; la app los reporta)

| Indicador | Cruceros | Incidentes en ellos |
|---|---|---|
{resumen}

El registro limpio se enlaza con el original por `id_objeto` = `OBJECTID` (tabla `{SCHEMA}.raw_cruceros_2024`).
""", encoding="utf-8")


def ejecutar(engine: Engine | None, escribir_archivos: bool = True) -> pd.DataFrame:
    """Corre el pipeline completo. Con escribir_archivos=False (pruebas) no toca data/processed ni docs/."""
    inicio = datetime.now(timezone.utc)
    sha = sha256(RAW_GPKG)
    gdf = gpd.read_file(RAW_GPKG)
    if gdf.crs is None or gdf.crs.to_epsg() != CRS_ORIGEN:
        raise ValueError(f"Se esperaba EPSG:{CRS_ORIGEN} en {RAW_GPKG.name}, llegó {gdf.crs}")
    csv = pd.read_csv(RAW_CSV, encoding="utf-8-sig")
    df, bitacora = limpiar(gdf, csv, leer_limite_municipal())
    crudo = pd.DataFrame(gdf.drop(columns="geometry"))
    id_ej = cargar_db(engine, crudo, df, bitacora, inicio, sha) if engine is not None else None
    if escribir_archivos:
        guardar_procesados(df)
        escribir_bitacora_md(bitacora, df, sha, inicio, id_ej)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Limpia los datos y los carga en PostgreSQL")
    parser.add_argument("--test", action="store_true",
                        help="carga en la base de pruebas (no toca data/processed ni la bitácora)")
    parser.add_argument("--sin-db", action="store_true", help="solo genera data/processed y la bitácora")
    args = parser.parse_args()
    df = ejecutar(None if args.sin_db else get_engine(test=args.test), escribir_archivos=not args.test)
    destino = "base de pruebas" if args.test else f"bitácora en {BITACORA_MD.relative_to(ROOT).as_posix()}"
    print(f"Listo: {len(df):,} cruceros limpios, {int(df['incidentes'].sum()):,} incidentes ({destino}).")


if __name__ == "__main__":
    main()
