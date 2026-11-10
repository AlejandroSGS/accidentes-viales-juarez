"""EDA inicial (Etapa 1): calidad de los conteos por crucero del IMIP."""
from pathlib import Path

import geopandas as gpd
import pandas as pd

BASE = Path(__file__).resolve().parents[1] / "data" / "interim" / "imip" / "annual"

filas = []
for shp in sorted(BASE.glob("ACCI*/ACCI*.shp")):
    year = int(shp.stem[-4:])
    gdf = gpd.read_file(shp)
    cnt = gdf[f"ACCI{year}"]
    wgs = gdf.to_crs(4326)
    xy = gdf.geometry.apply(lambda g: (round(g.x, 1), round(g.y, 1)))
    calle = gdf["NOMBRE1"].fillna("").str.strip().str.upper() + "|" + gdf["NOMBRE2"].fillna("").str.strip().str.upper()
    filas.append({
        "anio": year,
        "puntos": len(gdf),
        "suma_incidentes": int(cnt.sum()),
        "max_crucero": int(cnt.max()),
        "conteo_<=0": int((cnt <= 0).sum()),
        "conteo_nulo": int(cnt.isna().sum()),
        "geom_vacia": int(gdf.geometry.is_empty.sum() + gdf.geometry.isna().sum()),
        "id_99999": int((gdf["PUNTOS_ID"] == 99999).sum()),
        "id_dup": int(gdf["PUNTOS_ID"].duplicated(keep=False).sum()),
        "xy_dup": int(xy.duplicated(keep=False).sum()),
        "nombre1_nulo": int(gdf["NOMBRE1"].isna().sum()),
        "nombre2_nulo": int(gdf["NOMBRE2"].isna().sum()),
        "calles_dup": int(calle.duplicated(keep=False).sum()),
        "lon_min": round(wgs.geometry.x.min(), 3), "lon_max": round(wgs.geometry.x.max(), 3),
        "lat_min": round(wgs.geometry.y.min(), 3), "lat_max": round(wgs.geometry.y.max(), 3),
    })

df = pd.DataFrame(filas)
pd.set_option("display.width", 250)
print(df.to_string(index=False))
print("\nTotal 2008-2024:", df["suma_incidentes"].sum())

# Ejemplos de valores raros de nombres de calles (variantes de escritura)
g24 = gpd.read_file(BASE / "ACCI2024" / "ACCI2024.shp")
print("\nTop 15 cruceros 2024:")
print(g24.nlargest(15, "ACCI2024")[["PUNTOS_ID", "NOMBRE1", "NOMBRE2", "SECTOR", "ACCI2024"]].to_string(index=False))
print("\nDicSegPub 2024:", g24["DicSegPub"].value_counts(dropna=False).to_dict())
print("SECTOR 2024 únicos:", g24["SECTOR"].nunique(), " nulos:", g24["SECTOR"].isna().sum())
