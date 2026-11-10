"""EDA inicial (Etapa 1): incidentes individuales 2023T/2024T/2025T del ArcGIS del IMIP."""
import json
from pathlib import Path

import pandas as pd

RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "imip_arcgis"
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 50)


def load(folder: str) -> pd.DataFrame:
    rows = []
    for p in sorted((RAW / folder).glob("page_*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        wkid = d.get("spatialReference", {}).get("wkid")
        for f in d["features"]:
            r = dict(f["attributes"])
            g = f.get("geometry") or {}
            r["_gx"], r["_gy"], r["_wkid"] = g.get("x"), g.get("y"), wkid
            rows.append(r)
    return pd.DataFrame(rows)


CAT_COLS = ["Zona", "Grado", "Tipo_Accid", "Causa_Fund", "Clima", "Luminosida", "Visibilida",
            "Topografia", "Tipo_de_Pa", "Estado_del", "Forma_Esqu", "Pendiente", "Factor_Pri",
            "DiaNombre", "Rango", "RANGODOSHO"]

for folder in ["incidentes_2023T", "incidentes_2024T", "incidentes_2025T"]:
    df = load(folder)
    print(f"\n\n######## {folder}: {len(df)} filas, wkid={df['_wkid'].iloc[0]}")
    print("Columnas:", list(df.columns))
    print("\nNulos/vacíos por columna:")
    vac = {c: int(df[c].isna().sum() + (df[c].astype(str).str.strip() == "").sum()) for c in df.columns}
    print({k: v for k, v in vac.items() if v})
    print("\nMuestra:")
    print(df.head(3).T.to_string())
    for fc in ["Fecha", "FECHA", "FechaTXT"]:
        if fc in df:
            s = df[fc]
            if fc == "FECHA":
                s = pd.to_datetime(s, unit="ms", errors="coerce")
                print(f"\n{fc}: min={s.min()} max={s.max()} nulos={s.isna().sum()}")
            else:
                print(f"\n{fc} ejemplos:", s.dropna().head(8).tolist())
    print("HORA ejemplos:", df["HORA"].dropna().sample(10, random_state=1).tolist())
    print("ANIO:", df["ANIO"].value_counts(dropna=False).to_dict(), " MES:", df["MES"].value_counts(dropna=False).sort_index().to_dict())
    print("PERIODO:", df["PERIODO"].value_counts(dropna=False).head(5).to_dict())
    print("Expediente duplicados:", int(df["Expediente"].duplicated(keep=False).sum()),
          " nulos:", int(df["Expediente"].isna().sum()))
    sub = df.drop(columns=[c for c in df.columns if c.upper().startswith("OBJECTID") or c == "GlobalID"])
    print("Filas idénticas (sin IDs internos):", int(sub.duplicated(keep=False).sum()))
    print("Geometría nula:", int(df["_gx"].isna().sum()), " X/Y nulos:", int(df["X"].isna().sum()))
    print("X rango:", df["X"].min(), df["X"].max(), " Y rango:", df["Y"].min(), df["Y"].max())
    print("geom rango:", df["_gx"].min(), df["_gx"].max(), df["_gy"].min(), df["_gy"].max())
    print("Colonia únicos:", df["Colonia"].nunique())
    for c in CAT_COLS:
        if c in df:
            vc = df[c].value_counts(dropna=False)
            print(f"\n[{c}] ({len(vc)} valores)", vc.head(15).to_dict())


# ---- Verificaciones cruzadas de consistencia ----
print("\n\n######## CONSISTENCIA")
DIAS = {0: "lunes", 1: "martes", 2: "miercoles", 3: "jueves", 4: "viernes", 5: "sabado", 6: "domingo"}
for folder in ["incidentes_2023T", "incidentes_2024T", "incidentes_2025T"]:
    df = load(folder)
    fecha = (pd.to_datetime(df["Fecha"], format="%m/%d/%Y", errors="coerce") if "Fecha" in df
             else pd.to_datetime(df["FECHA"], unit="ms", errors="coerce"))
    dia_calc = fecha.dt.dayofweek.map(DIAS)
    dia_norm = df["DiaNombre"].str.lower().str.normalize("NFKD").str.encode("ascii", "ignore").str.decode("ascii")
    hora_ok = df["HORA"].astype(str).str.match(r"^([01]\d|2[0-3]):[0-5]\d(:[0-5]\d)?$")
    tokens = df["Tipo_Accid"].fillna("").str.split(",").explode().str.strip().value_counts()
    print(f"\n{folder}: fechas inválidas={int(fecha.isna().sum())}  DiaNombre≠fecha={int((dia_calc != dia_norm).sum())}"
          f"  MES≠fecha={int((fecha.dt.month != df['MES']).sum())}  DiaNumero≠fecha={int((fecha.dt.day != df['DiaNumero']).sum())}"
          f"  HORA mal formada={int((~hora_ok).sum())} ej={df.loc[~hora_ok, 'HORA'].head(5).tolist()}"
          f"  X≠geom={int(((df['X'] - df['_gx']).abs() > 1).sum())}")
    print("  Tokens de Tipo_Accid:", tokens.to_dict())
    dup_exp = df[df["Expediente"].duplicated(keep=False)].sort_values("Expediente")
    print("  Expedientes repetidos:\n", dup_exp[["Expediente", "HORA", "Calle_Prin", "Cruce_Cerc", "Tipo_Accid", "X", "Y"]].to_string(index=False))
    print("  Zona:", df["Zona"].value_counts().to_dict())
