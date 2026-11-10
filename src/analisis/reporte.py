"""Genera docs/reporte_analisis.md con los resultados de la Etapa 3.

Uso:  python -m src.analisis.reporte
"""
from __future__ import annotations

import pandas as pd

from src.analisis import datos, descriptiva as de, espacial as es
from src.config import DOCS, get_engine

K_GRUPOS = 6
SALIDA = DOCS / "reporte_analisis.md"


def _tabla(df: pd.DataFrame, formatos: dict | None = None) -> str:
    """DataFrame → tabla Markdown con formato de miles y decimales."""
    formatos = formatos or {}
    cab = "| " + " | ".join(df.columns) + " |\n|" + "---|" * len(df.columns)
    filas = []
    for _, fila in df.iterrows():
        celdas = []
        for c in df.columns:
            v = fila[c]
            if c in formatos:
                celdas.append(formatos[c].format(v))
            elif isinstance(v, (int,)) or (hasattr(v, "is_integer") and float(v).is_integer() and not isinstance(v, bool)):
                celdas.append(f"{int(v):,}" if pd.notna(v) else "—")
            else:
                celdas.append(str(v) if pd.notna(v) else "—")
        filas.append("| " + " | ".join(celdas) + " |")
    return cab + "\n" + "\n".join(filas)


def generar() -> str:
    df = datos.cargar_cruceros(get_engine())
    dentro = df[~df["fuera_municipio"]]
    r = de.resumen_general(df)
    pct = "{:.2f} %"
    ranking = de.ranking_cruceros(df, 15)[["posicion", "nombre_crucero", "zona", "sector", "incidentes", "porcentaje"]]
    zonas = de.agregar_por(df, "zona")
    sectores = de.agregar_por(df, "sector").head(10)
    dist = de.distribucion_conteos(df)
    ev = es.evaluar_k(dentro)
    grupos = es.agrupar_cruceros(dentro, K_GRUPOS)
    perfil = es.perfil_grupos(dentro, grupos)
    malla = es.densidad_kernel(dentro)
    calientes = es.celdas_calientes(malla, 99.5)
    dens_cruceros = es.densidad_en_cruceros(dentro).rename("densidad_km2")
    top_kde = dentro.assign(densidad_km2=dens_cruceros).nlargest(10, "densidad_km2")[
        ["nombre_crucero", "zona", "incidentes", "densidad_km2"]]

    texto = f"""# Etapa 3 — Análisis estadístico y espacial

> Generado con `python -m src.analisis.reporte` a partir de la tabla `accidentes.cruceros`.
> **Aviso:** los resultados describen dónde se concentran los registros de 2024; **no determinan las causas** de los accidentes.

## 1. Resumen

- **{r['cruceros']:,} cruceros** con **{r['incidentes']:,} incidentes** registrados en 2024.
- Promedio: {r['promedio_por_crucero']:.2f} incidentes por crucero; mediana: {r['mediana_por_crucero']:.0f}; máximo: {r['maximo_crucero']}.
- {r['cruceros_con_1']:,} cruceros ({100 * r['cruceros_con_1'] / r['cruceros']:.1f} %) tuvieron un solo incidente.
- Comparación con el documento del proyecto: sus totales de referencia cubren 2018–2022 y sus porcentajes por tipo son de 2022. Estos datos son de 2024 y no traen tipo de incidente, así que **no hay cifra de referencia contra la cual compararlos**. El total de 2024 (6,423) coincide con la suma del shapefile `ACCI2024` del IMIP.

## 2. Concentración

- El **{de.pct_cruceros_para(df, 25):.1f} %** de los cruceros acumula el 25 % de los incidentes; el **{de.pct_cruceros_para(df, 50):.1f} %** acumula la mitad, y el **{de.pct_cruceros_para(df, 80):.1f} %** acumula el 80 %.
- Índice de Gini: **{de.indice_gini(df):.3f}** (0 = repartidos por igual entre cruceros, 1 = todos en un solo crucero).

{_tabla(dist.rename(columns={'rango': 'Incidentes por crucero', 'cruceros': 'Cruceros', 'incidentes': 'Incidentes', 'pct_cruceros': '% cruceros', 'pct_incidentes': '% incidentes'}), {'% cruceros': pct, '% incidentes': pct})}

## 3. Cruceros con más incidentes

{_tabla(ranking.rename(columns={'posicion': '#', 'nombre_crucero': 'Crucero', 'zona': 'Zona', 'sector': 'Sector', 'incidentes': 'Incidentes', 'porcentaje': '% del total'}), {'% del total': pct})}

## 4. Por zona de Seguridad Pública

{_tabla(zonas.rename(columns={'zona': 'Zona', 'cruceros': 'Cruceros', 'incidentes': 'Incidentes', 'porcentaje': '% del total', 'promedio_por_crucero': 'Incidentes por crucero'}), {'% del total': pct, 'Incidentes por crucero': '{:.2f}'})}

Incluye las 11 zonas inferidas (29 incidentes). Las zonas tienen tamaños distintos, por eso se muestra también el promedio por crucero.

## 5. Sectores con más incidentes (10 primeros de {r['sectores']})

{_tabla(sectores.rename(columns={'sector': 'Sector', 'cruceros': 'Cruceros', 'incidentes': 'Incidentes', 'porcentaje': '% del total', 'promedio_por_crucero': 'Incidentes por crucero'}), {'% del total': pct, 'Incidentes por crucero': '{:.2f}'})}

## 6. Densidad Kernel (KDE)

Cada crucero pesa según su número de incidentes. Parámetros: suavizado gaussiano de **{es.ANCHO_BANDA_M} m** (≈ 4–5 cuadras) y malla de {es.TAMANO_CELDA_M} m. Se excluyen los 2 cruceros fuera del municipio. La densidad se expresa en incidentes por km².

- Densidad máxima: **{malla['densidad_km2'].max():.1f} incidentes/km²**, alrededor de ({calientes.iloc[0]['latitud']:.4f}, {calientes.iloc[0]['longitud']:.4f}).
- Celdas en el 0.5 % más denso: {len(calientes):,}.

Cruceros ubicados en las zonas de mayor densidad (no siempre son los de más incidentes propios: la densidad también cuenta a los vecinos):

{_tabla(top_kde.rename(columns={'nombre_crucero': 'Crucero', 'zona': 'Zona', 'incidentes': 'Incidentes', 'densidad_km2': 'Densidad (inc/km²)'}), {'Densidad (inc/km²)': '{:.1f}'})}

## 7. Modelo K-means ponderado (Anderson, 2009)

Agrupa los cruceros por cercanía, con cada crucero pesado por sus incidentes. Es **no supervisado**: describe zonas, no predice.

**Elección de k:** se probaron k = 2 a 12.

{_tabla(ev.rename(columns={'k': 'k', 'inercia_km2': 'Inercia (km²)', 'silueta': 'Silueta'}), {'Inercia (km²)': '{:,.0f}', 'Silueta': '{:.3f}'})}

La silueta (qué tan separados quedan los grupos) es mayor con k = 2, pero dos grupos no sirven para describir la ciudad. De k = 3 a 12 baja poco y la inercia no muestra un "codo" claro. Se eligió **k = {K_GRUPOS}** porque tiene una silueta similar a k = 4 o 5 y es el mismo número de zonas de Seguridad Pública, lo que permite compararlas. El resultado es idéntico con otra semilla aleatoria (índice de Rand ajustado = 1.0). En la app se puede cambiar k.

**Perfil de los grupos** (1 = el de más incidentes):

{_tabla(perfil[['grupo', 'cruceros', 'incidentes', 'porcentaje', 'promedio_por_crucero', 'area_km2', 'incidentes_por_km2', 'zona_predominante', 'crucero_principal']].rename(columns={'grupo': 'Grupo', 'cruceros': 'Cruceros', 'incidentes': 'Incidentes', 'porcentaje': '% del total', 'promedio_por_crucero': 'Inc. por crucero', 'area_km2': 'Área (km²)', 'incidentes_por_km2': 'Inc. por km²', 'zona_predominante': 'Zona predominante', 'crucero_principal': 'Crucero principal'}), {'% del total': pct, 'Inc. por crucero': '{:.2f}', 'Área (km²)': '{:.1f}', 'Inc. por km²': '{:.1f}'})}

El área es la del polígono que envuelve los cruceros del grupo.

## 8. Lo que no se puede analizar con estos datos

- **Patrones temporales** (mes, día, hora) y **comparación de periodos**: el archivo solo tiene el total de 2024 por crucero.
- **Tipos de incidente** (choque, atropello, volcadura): no vienen en el archivo.
- **Autocorrelación espacial (Moran, Getis-Ord Gi\\*)**: es opcional y queda como trabajo futuro.
"""
    SALIDA.write_text(texto, encoding="utf-8")
    return texto


if __name__ == "__main__":
    generar()
    print(f"Reporte escrito en {SALIDA}")
