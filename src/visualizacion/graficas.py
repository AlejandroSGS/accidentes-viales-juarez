"""Gráficas Plotly reutilizables (títulos y ejes en español, formato de miles, texto en barras)."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Paleta sobria: un acento gris azulado oscuro y un gris medio
COLOR_PRINCIPAL = "#2B3A4A"
COLOR_SECUNDARIO = "#9AA3AD"
COLOR_REFERENCIA = "#B5B5B5"
ESCALA_SECUENCIAL = ["#F3F3F1", "#C9D0D7", "#8F9CAA", "#56677A", "#2B3A4A"]
FUENTE = "Fuente: IMIP, cruceros con incidentes viales 2024 (datos del proyecto)."


def _estilo(fig: go.Figure, titulo: str, alto: int = 450) -> go.Figure:
    fig.update_layout(
        title={"text": titulo, "x": 0, "xanchor": "left"},
        height=alto, separators=".,", margin={"l": 10, "r": 10, "t": 60, "b": 60},
        font={"size": 13, "color": "#1C1C1C"}, hoverlabel={"font_size": 13},
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
        annotations=[*fig.layout.annotations, go.layout.Annotation(
            text=FUENTE, showarrow=False, xref="paper", yref="paper", x=0, y=-0.18,
            xanchor="left", font={"size": 11, "color": "#666"})],
    )
    fig.update_xaxes(showline=True, linecolor="#BFBFBF", gridcolor="#ECECEC", zeroline=False)
    fig.update_yaxes(showline=True, linecolor="#BFBFBF", gridcolor="#ECECEC", zeroline=False)
    return fig


def barras_horizontales(df: pd.DataFrame, etiqueta: str, valor: str, titulo: str,
                        eje_x: str = "Incidentes", eje_y: str = "", texto: str | None = None) -> go.Figure:
    """Barras horizontales ordenadas (la mayor arriba) con el valor escrito en cada barra."""
    d = df.sort_values(valor, ascending=True)
    fig = px.bar(d, x=valor, y=etiqueta, orientation="h", text=texto or valor,
                 color_discrete_sequence=[COLOR_PRINCIPAL])
    fig.update_traces(texttemplate="%{text:,}" if texto is None else "%{text}", textposition="outside",
                      hovertemplate=f"%{{y}}<br>{eje_x}: %{{x:,}}<extra></extra>", cliponaxis=False)
    fig.update_xaxes(title=eje_x, tickformat=",")
    fig.update_yaxes(title=eje_y, type="category")
    return _estilo(fig, titulo, alto=max(350, 28 * len(d) + 120))


def barras_zona(zonas: pd.DataFrame) -> go.Figure:
    """Incidentes por zona, con % y promedio por crucero en la etiqueta."""
    d = zonas.assign(texto=[f"{i:,} ({p:.1f} %)" for i, p in zip(zonas["incidentes"], zonas["porcentaje"])])
    return barras_horizontales(d, "zona", "incidentes", "Incidentes por zona de Seguridad Pública",
                               eje_y="Zona", texto="texto")


def curva_pareto(curva: pd.DataFrame, marcas: tuple = (25, 50, 80)) -> go.Figure:
    """% acumulado de incidentes contra % de cruceros, con líneas de referencia rotuladas."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=curva["pct_cruceros"], y=curva["pct_incidentes"], mode="lines",
                             name="Cruceros ordenados de más a menos incidentes",
                             line={"color": COLOR_PRINCIPAL, "width": 3},
                             hovertemplate="%{x:.1f} % de los cruceros → %{y:.1f} % de los incidentes<extra></extra>"))
    fig.add_trace(go.Scatter(x=[0, 100], y=[0, 100], mode="lines", name="Reparto igual (referencia)",
                             line={"color": COLOR_REFERENCIA, "dash": "dash"}, hoverinfo="skip"))
    xs = curva["pct_cruceros"].to_numpy()
    ys = curva["pct_incidentes"].to_numpy()
    for m in marcas:
        x = float(xs[(ys >= m - 1e-9).argmax()])
        fig.add_trace(go.Scatter(x=[x], y=[m], mode="markers+text", showlegend=False,
                                 marker={"size": 8, "color": COLOR_PRINCIPAL, "symbol": "square"},
                                 text=[f"{m} % de incidentes en {x:.1f} % de cruceros"], textposition="middle right",
                                 hoverinfo="skip"))
    fig.update_xaxes(title="% de cruceros (acumulado)", range=[0, 100], ticksuffix=" %")
    fig.update_yaxes(title="% de incidentes (acumulado)", range=[0, 102], ticksuffix=" %")
    fig.update_layout(legend={"orientation": "h", "y": 1.02, "yanchor": "bottom", "x": 0})
    return _estilo(fig, "Concentración de incidentes en los cruceros (curva de Pareto)", alto=500)


def barras_distribucion(dist: pd.DataFrame) -> go.Figure:
    """Cruceros e incidentes por rango de incidentes, en barras agrupadas con patrón distinto."""
    fig = go.Figure()
    fig.add_trace(go.Bar(x=dist["rango"].astype(str), y=dist["pct_cruceros"], name="% de cruceros",
                         marker={"color": COLOR_PRINCIPAL}, text=dist["pct_cruceros"].map("{:.1f} %".format),
                         textposition="outside"))
    fig.add_trace(go.Bar(x=dist["rango"].astype(str), y=dist["pct_incidentes"], name="% de incidentes",
                         marker={"color": COLOR_SECUNDARIO, "pattern": {"shape": "/"}},
                         text=dist["pct_incidentes"].map("{:.1f} %".format), textposition="outside"))
    fig.update_xaxes(title="Incidentes en el crucero durante 2024", type="category")
    fig.update_yaxes(title="Porcentaje", ticksuffix=" %")
    fig.update_layout(barmode="group", legend={"orientation": "h", "y": 1.02, "yanchor": "bottom", "x": 0})
    return _estilo(fig, "¿Cuántos incidentes tiene cada crucero?")


def evaluacion_k(ev: pd.DataFrame, k_elegido: int) -> go.Figure:
    """Silueta por número de grupos, con el k elegido resaltado."""
    fig = go.Figure(go.Scatter(x=ev["k"], y=ev["silueta"], mode="lines+markers+text",
                               text=ev["silueta"].map("{:.3f}".format), textposition="top center",
                               line={"color": COLOR_PRINCIPAL}, marker={"size": 8},
                               hovertemplate="k = %{x}<br>Silueta = %{y:.3f}<extra></extra>"))
    fila = ev[ev["k"] == k_elegido]
    if len(fila):
        fig.add_trace(go.Scatter(x=fila["k"], y=fila["silueta"], mode="markers", showlegend=False,
                                 marker={"size": 14, "color": "#FFFFFF", "symbol": "square-open", "line": {"width": 2, "color": "#1C1C1C"}},
                                 hovertemplate="k elegido<extra></extra>"))
    fig.update_xaxes(title="Número de grupos (k)", dtick=1)
    fig.update_yaxes(title="Silueta (más alto = grupos más separados)")
    fig.update_layout(showlegend=False)
    return _estilo(fig, "Calidad de los grupos según el número de grupos", alto=400)


def mapa_calor_tabla(tabla: pd.DataFrame, titulo: str, eje_x: str, eje_y: str) -> go.Figure:
    """Tabla de doble entrada como mapa de calor, con el número escrito en cada celda."""
    fig = px.imshow(tabla, text_auto=",", color_continuous_scale=ESCALA_SECUENCIAL, aspect="auto")
    fig.update_traces(hovertemplate=f"{eje_y}: %{{y}}<br>{eje_x}: %{{x}}<br>Incidentes: %{{z:,}}<extra></extra>")
    fig.update_xaxes(title=eje_x, type="category")
    fig.update_yaxes(title=eje_y, type="category")
    fig.update_coloraxes(colorbar_title="Incidentes")
    return _estilo(fig, titulo, alto=420)
