"""Aplicación Streamlit "Accidentes viales en Ciudad Juárez".

Uso:  streamlit run src/app/app.py
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import streamlit as st  # noqa: E402
from sqlalchemy.exc import OperationalError, ProgrammingError  # noqa: E402

from src.app import comun  # noqa: E402

st.set_page_config(page_title="Accidentes viales en Ciudad Juárez", layout="wide")


try:
    opciones = comun.opciones_filtros()
except KeyError as error:
    st.error("Falta configurar la conexión a la base de datos. En local, revisa el archivo `.env`; "
             "en Streamlit Cloud, agrega `DATABASE_URL_UNPOOLED` en Settings → Secrets.")
    st.caption(f"Variable faltante: {error}")
    st.stop()
except (OperationalError, ProgrammingError) as error:
    st.error("No se pudo leer la base de datos. Revisa que PostgreSQL esté encendido, que el archivo `.env` "
             "tenga los datos correctos y que hayas corrido `python -m src.db --reset` y "
             "`python -m src.limpieza.pipeline`.")
    st.caption(f"Detalle técnico: {type(error).__name__}")
    st.stop()

# ---------- Filtros compartidos (aplican a todas las páginas) ----------
with st.sidebar:
    st.header("Filtros")
    zonas_disp = sorted(opciones["zona"].unique())
    zonas = st.multiselect("Zona de Seguridad Pública", zonas_disp, key="f_zonas",
                           placeholder="Todas las zonas")
    sect = opciones[opciones["zona"].isin(zonas)] if zonas else opciones
    sectores_disp = sorted(int(s) for s in sect["sector"].dropna().unique())
    st.session_state["f_sectores"] = [s for s in st.session_state.get("f_sectores", []) if s in sectores_disp]
    st.multiselect("Sector", sectores_disp, key="f_sectores", placeholder="Todos los sectores")
    st.slider("Mínimo de incidentes por crucero", 1, 20, key="f_min",
              help="Muestra solo los cruceros con al menos este número de incidentes en 2024.")
    if st.button("Quitar filtros", width="stretch"):
        for clave in ("f_zonas", "f_sectores", "f_min"):
            st.session_state.pop(clave, None)
        st.rerun()
    st.divider()
    st.caption("Datos: cruceros con incidentes viales 2024, IMIP Ciudad Juárez. Sin actualización en tiempo real.")

paginas = {
    "Resultados": [
        st.Page("paginas/inicio.py", title="Inicio", default=True),
        st.Page("paginas/explorar.py", title="Explorar datos"),
        st.Page("paginas/ranking.py", title="Cruceros y zonas"),
        st.Page("paginas/concentracion.py", title="Concentración"),
        st.Page("paginas/mapa.py", title="Mapa"),
        st.Page("paginas/kmeans.py", title="Zonas K-means"),
        st.Page("paginas/no_disponible.py", title="Tiempo y tipos"),
    ],
    "Información": [
        st.Page("paginas/calidad.py", title="Calidad y trazabilidad"),
        st.Page("paginas/acerca.py", title="Acerca de"),
    ],
}
st.navigation(paginas).run()
