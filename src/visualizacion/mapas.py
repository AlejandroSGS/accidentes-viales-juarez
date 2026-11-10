"""Mapas Folium reutilizables: puntos, densidad Kernel, cruceros principales y grupos K-means."""
from __future__ import annotations

import html

import branca.colormap as bcm
import folium
import numpy as np
import pandas as pd

CENTRO_JUAREZ = (31.69, -106.42)
# Paleta Okabe-Ito: distinguible para personas con daltonismo
PALETA_GRUPOS = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D55E00",
                 "#F0E442", "#000000", "#999999", "#882255", "#44AA99", "#117733"]


def mapa_base(zoom: int = 11) -> folium.Map:
    return folium.Map(location=CENTRO_JUAREZ, zoom_start=zoom, tiles="OpenStreetMap", control_scale=True)


def ajustar_vista(m: folium.Map, df: pd.DataFrame) -> folium.Map:
    """Encuadra el mapa en los cruceros (percentiles 1–99, para que un punto aislado no aleje la vista)."""
    if len(df):
        lat = df["latitud"].quantile([0.01, 0.99]).to_numpy()
        lon = df["longitud"].quantile([0.01, 0.99]).to_numpy()
        m.fit_bounds([[lat[0], lon[0]], [lat[1], lon[1]]])
    return m


def _tooltip(fila: pd.Series, extra: str = "") -> str:
    sector = "sin dato" if pd.isna(fila["sector"]) else int(fila["sector"])
    return (f"<b>{html.escape(fila['nombre_crucero'])}</b><br>Incidentes 2024: {int(fila['incidentes']):,}"
            f"<br>Zona: {html.escape(fila['zona'])} · Sector: {sector}{extra}")


def _radio(incidentes: int) -> float:
    """Radio proporcional a la raíz del conteo, para que el área represente los incidentes."""
    return 2.5 + 1.6 * np.sqrt(incidentes)


def capa_puntos(m: folium.Map, df: pd.DataFrame, nombre: str = "Cruceros") -> folium.Map:
    """Un círculo por crucero; el tamaño indica el número de incidentes."""
    capa = folium.FeatureGroup(name=nombre)
    for _, f in df.sort_values("incidentes").iterrows():
        folium.CircleMarker((f["latitud"], f["longitud"]), radius=_radio(f["incidentes"]),
                            color="#1f5f8b", weight=1, fill=True, fill_color="#1f5f8b", fill_opacity=0.45,
                            tooltip=_tooltip(f)).add_to(capa)
    capa.add_to(m)
    return m


def capa_densidad(m: folium.Map, densidad: np.ndarray, limites: list, opacidad: float = 0.7) -> folium.Map:
    """Superpone la malla KDE como imagen, con leyenda en incidentes por km²."""
    colores = ["#ffffb2", "#fecc5c", "#fd8d3c", "#f03b20", "#bd0026"]
    vmax = float(np.nanmax(densidad)) or 1.0
    escala = bcm.LinearColormap(colores, vmin=0, vmax=vmax, caption="Densidad Kernel (incidentes por km²)")
    paradas = np.linspace(0, vmax, len(colores))
    rgb = np.array([[int(c[k:k + 2], 16) / 255 for k in (1, 3, 5)] for c in colores])
    rgba = np.zeros((*densidad.shape, 4))
    for canal in range(3):
        rgba[..., canal] = np.interp(densidad, paradas, rgb[:, canal])
    rgba[..., 3] = (densidad > 0.02 * vmax).astype(float)  # lo casi nulo se deja transparente
    folium.raster_layers.ImageOverlay(rgba, bounds=limites, opacity=opacidad, mercator_project=True,
                                      name="Densidad Kernel").add_to(m)
    escala.add_to(m)
    return m


def capa_ranking(m: folium.Map, ranking: pd.DataFrame) -> folium.Map:
    """Marcadores numerados con la posición de los cruceros con más incidentes."""
    capa = folium.FeatureGroup(name="Cruceros con más incidentes")
    for _, f in ranking.iterrows():
        icono = folium.DivIcon(html=(
            f'<div style="background:#bd0026;color:#fff;border:2px solid #fff;border-radius:50%;'
            f'width:26px;height:26px;line-height:22px;text-align:center;font:bold 12px sans-serif;'
            f'box-shadow:0 0 3px #000">{int(f["posicion"])}</div>'), icon_size=(26, 26), icon_anchor=(13, 13))
        folium.Marker((f["latitud"], f["longitud"]), icon=icono,
                      tooltip=f"#{int(f['posicion'])} · {_tooltip(f)}").add_to(capa)
    capa.add_to(m)
    return m


def capa_grupos(m: folium.Map, df: pd.DataFrame, grupos: pd.Series, perfil: pd.DataFrame) -> folium.Map:
    """Cruceros coloreados por grupo K-means y un marcador numerado en el centro de cada grupo."""
    d = df.assign(grupo=grupos).dropna(subset=["grupo"])
    for g, sub in d.groupby("grupo"):
        color = PALETA_GRUPOS[(int(g) - 1) % len(PALETA_GRUPOS)]
        capa = folium.FeatureGroup(name=f"Grupo {int(g)}")
        for _, f in sub.iterrows():
            folium.CircleMarker((f["latitud"], f["longitud"]), radius=_radio(f["incidentes"]),
                                color=color, weight=1, fill=True, fill_color=color, fill_opacity=0.6,
                                tooltip=_tooltip(f, f"<br><b>Grupo {int(g)}</b>")).add_to(capa)
        capa.add_to(m)
    for _, p in perfil.iterrows():
        color = PALETA_GRUPOS[(int(p["grupo"]) - 1) % len(PALETA_GRUPOS)]
        icono = folium.DivIcon(html=(
            f'<div style="background:{color};color:#fff;border:3px solid #000;border-radius:4px;'
            f'width:30px;height:30px;line-height:24px;text-align:center;font:bold 15px sans-serif;'
            f'text-shadow:0 0 2px #000">{int(p["grupo"])}</div>'), icon_size=(30, 30), icon_anchor=(15, 15))
        folium.Marker((p["latitud_centro"], p["longitud_centro"]), icon=icono,
                      tooltip=(f"<b>Centro del grupo {int(p['grupo'])}</b><br>{int(p['incidentes']):,} incidentes"
                               f" en {int(p['cruceros']):,} cruceros ({p['porcentaje']:.1f} %)")).add_to(m)
    return m


def color_grupo(g: int) -> str:
    return PALETA_GRUPOS[(int(g) - 1) % len(PALETA_GRUPOS)]
