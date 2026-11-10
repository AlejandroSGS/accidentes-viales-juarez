"""EDA inicial (Etapa 1): estructura de cada shapefile anual del IMIP."""
from pathlib import Path

import geopandas as gpd

BASE = Path(__file__).resolve().parents[1] / "data" / "interim" / "imip" / "annual"

for shp in sorted(BASE.glob("ACCI*/ACCI*.shp")):
    gdf = gpd.read_file(shp)
    print(f"\n===== {shp.stem}  filas={len(gdf)}  crs={gdf.crs.to_epsg() if gdf.crs else None}  geom={gdf.geom_type.unique().tolist()}")
    print("columnas:", list(gdf.columns))
    print(gdf.drop(columns="geometry").head(2).to_string())
