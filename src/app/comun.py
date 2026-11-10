"""Piezas compartidas por las páginas: conexión, caché, filtros y avisos."""
from __future__ import annotations

import os

import pandas as pd
import streamlit as st
from sqlalchemy import text

from src.analisis import datos, espacial as es
from src.config import SCHEMA, get_engine

AVISO_CAUSAS = ("Nota: estos resultados muestran dónde se concentran los registros de incidentes viales de 2024. "
                "No determinan las causas de los accidentes ni el riesgo de un lugar.")


def _secretos_a_entorno() -> None:
    """Copia los Secrets de Streamlit Cloud (p. ej. DATABASE_URL_UNPOOLED) a variables de entorno.

    En local no hay secrets.toml y no pasa nada; nunca sobrescribe variables ya definidas.
    """
    try:
        for clave, valor in st.secrets.items():
            if isinstance(valor, str):
                os.environ.setdefault(clave, valor)
    except Exception:  # sin archivo de secrets (uso local)
        pass


@st.cache_resource
def engine():
    _secretos_a_entorno()
    # Las pruebas automáticas fijan ACCIDENTES_BD_PRUEBAS=1 para no tocar la base real
    return get_engine(test=os.environ.get("ACCIDENTES_BD_PRUEBAS") == "1")


@st.cache_data(ttl=600, show_spinner="Consultando la base de datos…")
def cruceros(zonas: tuple[str, ...] = (), sectores: tuple[int, ...] = (), min_incidentes: int = 1) -> pd.DataFrame:
    return datos.cargar_cruceros(engine(), zonas or None, sectores or None, min_incidentes)


@st.cache_data(ttl=600)
def tabla(nombre: str) -> pd.DataFrame:
    return datos.cargar_tabla(engine(), nombre)


@st.cache_data(ttl=600)
def opciones_filtros() -> pd.DataFrame:
    """Pares (zona, sector) existentes, para llenar los filtros."""
    with engine().connect() as conn:
        return pd.read_sql(text(f"SELECT DISTINCT zona, sector FROM {SCHEMA}.cruceros ORDER BY zona, sector"), conn)


@st.cache_data(ttl=600, show_spinner="Calculando densidad Kernel…")
def densidad_latlon(df: pd.DataFrame, ancho_banda_m: int):
    return es.densidad_kernel_latlon(df, ancho_banda_m)


@st.cache_data(ttl=600, show_spinner="Agrupando cruceros con K-means…")
def grupos_kmeans(df: pd.DataFrame, k: int):
    dentro = df[~df["fuera_municipio"]]
    grupos = es.agrupar_cruceros(dentro, k)
    return grupos, es.perfil_grupos(dentro, grupos)


@st.cache_data(ttl=600, show_spinner="Evaluando de 2 a 12 grupos (puede tardar unos segundos)…")
def evaluar_k(df: pd.DataFrame) -> pd.DataFrame:
    return es.evaluar_k(df[~df["fuera_municipio"]])


def filtros() -> dict:
    """Filtros elegidos en la barra lateral (los define app.py)."""
    return {
        "zonas": tuple(st.session_state.get("f_zonas", [])),
        "sectores": tuple(int(s) for s in st.session_state.get("f_sectores", [])),
        "min_incidentes": int(st.session_state.get("f_min", 1)),
    }


def datos_filtrados() -> pd.DataFrame:
    """Cruceros según los filtros compartidos; detiene la página si no hay resultados."""
    df = cruceros(**filtros())
    if df.empty:
        st.write("Ningún crucero cumple los filtros elegidos. Ajusta los filtros en la barra lateral.")
        st.stop()
    return df


def descripcion_filtros() -> str:
    f = filtros()
    partes = [f"zonas: {', '.join(f['zonas'])}" if f["zonas"] else "todas las zonas",
              f"sectores: {', '.join(map(str, f['sectores']))}" if f["sectores"] else "todos los sectores"]
    if f["min_incidentes"] > 1:
        partes.append(f"cruceros con {f['min_incidentes']} o más incidentes")
    return "Filtros: " + " · ".join(partes)


def encabezado(titulo: str, subtitulo: str | None = None, aviso: bool = True) -> None:
    st.title(titulo)
    if subtitulo:
        st.markdown(subtitulo)
    st.caption(descripcion_filtros())
    if aviso:
        with st.container(border=True):
            st.markdown(AVISO_CAUSAS)


def miles(n) -> str:
    return f"{int(n):,}"
