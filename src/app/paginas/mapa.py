import folium
import streamlit as st
from streamlit_folium import st_folium

from src.analisis import descriptiva as de
from src.app import comun
from src.visualizacion import mapas

comun.encabezado("Mapa", "Ubicación de los cruceros y zonas con mayor concentración de incidentes en 2024.")

df = comun.datos_filtrados()
fuera = df[df["fuera_municipio"]]
dentro = df[~df["fuera_municipio"]]

c1, c2, c3 = st.columns([1.3, 1, 1])
capas = c1.multiselect("Capas", ["Densidad Kernel", "Cruceros", "Cruceros con más incidentes"],
                       default=["Densidad Kernel", "Cruceros con más incidentes"])
banda = c2.slider("Radio de suavizado del KDE (m)", 200, 1500, 500, step=100,
                  help="Más chico = zonas calientes más detalladas; más grande = patrón general.")
n_top = c3.slider("Cruceros principales a numerar", 5, 30, 10, step=5)

st.markdown(
    f"Se muestran {comun.miles(len(dentro))} cruceros ({comun.miles(dentro['incidentes'].sum())} incidentes). "
    f"No se muestran {comun.miles(len(fuera))} cruceros ({comun.miles(fuera['incidentes'].sum())} incidentes) "
    "porque su ubicación cae fuera del límite municipal. Todos los registros tienen coordenadas; la ubicación "
    "corresponde al crucero, no al punto exacto del incidente."
)

if not capas:
    st.write("Elige al menos una capa.")
    st.stop()

m = mapas.mapa_base()
if "Densidad Kernel" in capas and len(dentro) >= 2:
    dens, limites = comun.densidad_latlon(dentro, banda)
    mapas.capa_densidad(m, dens, limites)
if "Cruceros" in capas:
    mapas.capa_puntos(m, dentro)
if "Cruceros con más incidentes" in capas:
    mapas.capa_ranking(m, de.ranking_cruceros(dentro, n_top))
mapas.ajustar_vista(m, dentro)
folium.LayerControl(collapsed=False).add_to(m)
st_folium(m, height=620, use_container_width=True, returned_objects=[])

with st.expander("Notas sobre el mapa"):
    st.markdown(f"""
- Densidad Kernel: suaviza los incidentes de cada crucero en un radio de unos {banda} m. Los colores más oscuros
  indican más incidentes por km² considerando también a los cruceros vecinos (escala en la esquina superior derecha).
- Cruceros: el tamaño del círculo es proporcional al número de incidentes. Pasa el cursor para ver el detalle.
- Cruceros con más incidentes: el número es la posición en el ranking (1 = el de más incidentes).
- Método basado en Anderson (2009). Describe concentración de registros, no causas.
""")

st.subheader("Cruceros numerados en el mapa")
rk = de.ranking_cruceros(dentro, n_top)
st.dataframe(rk[["posicion", "nombre_crucero", "zona", "sector", "incidentes"]], hide_index=True,
             width="stretch", column_config={
                 "posicion": st.column_config.NumberColumn("#", format="%d"), "nombre_crucero": "Crucero",
                 "zona": "Zona", "sector": st.column_config.NumberColumn("Sector", format="%d"),
                 "incidentes": st.column_config.NumberColumn("Incidentes", format="%d")})
