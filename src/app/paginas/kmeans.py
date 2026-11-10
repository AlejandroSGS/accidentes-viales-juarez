import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from src.app import comun
from src.visualizacion import graficas as gr, mapas

comun.encabezado("Zonas K-means",
                 "Modelo de *machine learning* **no supervisado**: agrupa los cruceros cercanos entre sí, dando más "
                 "peso a los que tienen más incidentes (K-means ponderado, Anderson 2009). Sirve para describir zonas "
                 "de concentración; **no predice** accidentes.")

df = comun.datos_filtrados()
dentro = df[~df["fuera_municipio"]]
max_k = min(12, len(dentro))
if max_k < 2:
    st.info("Se necesitan al menos 2 cruceros para formar grupos. Ajusta los filtros.")
    st.stop()

k = st.slider("Número de grupos (k)", 2, max_k, min(6, max_k),
              help="Se eligió 6 por defecto: tiene una calidad similar a 4 o 5 grupos y coincide con el número de "
                   "zonas de Seguridad Pública, lo que permite compararlas.")
grupos, perfil = comun.grupos_kmeans(dentro, k)

m = mapas.mapa_base()
mapas.capa_grupos(m, dentro, grupos, perfil)
mapas.ajustar_vista(m, dentro)
folium.LayerControl(collapsed=True).add_to(m)
st_folium(m, height=580, use_container_width=True, returned_objects=[])
st.caption("Cada color es un grupo; el cuadro numerado marca el centro del grupo (promedio ponderado por "
           "incidentes). El número del grupo también aparece al pasar el cursor sobre cada crucero. "
           f"No se incluyen {comun.miles(df['fuera_municipio'].sum())} cruceros fuera del municipio.")

st.subheader("Perfil de cada grupo")
perfil_vista = perfil.assign(color=perfil["grupo"].map(mapas.color_grupo))
st.dataframe(
    perfil_vista[["grupo", "cruceros", "incidentes", "porcentaje", "promedio_por_crucero", "area_km2",
                  "incidentes_por_km2", "zona_predominante", "crucero_principal", "incidentes_crucero_principal"]],
    hide_index=True, width="stretch", column_config={
        "grupo": st.column_config.NumberColumn("Grupo", format="%d"),
        "cruceros": st.column_config.NumberColumn("Cruceros", format="%d"),
        "incidentes": st.column_config.NumberColumn("Incidentes", format="%d"),
        "porcentaje": st.column_config.NumberColumn("% del total", format="%.1f %%"),
        "promedio_por_crucero": st.column_config.NumberColumn("Inc. por crucero", format="%.2f"),
        "area_km2": st.column_config.NumberColumn("Área (km²)", format="%.1f"),
        "incidentes_por_km2": st.column_config.NumberColumn("Inc. por km²", format="%.1f"),
        "zona_predominante": "Zona predominante", "crucero_principal": "Crucero con más incidentes",
        "incidentes_crucero_principal": st.column_config.NumberColumn("Sus incidentes", format="%d"),
    })
st.caption("Grupo 1 = el de más incidentes. Área = polígono que envuelve los cruceros del grupo. "
           "La densidad (incidentes por km²) permite comparar grupos de distinto tamaño.")

st.subheader("Grupos frente a zonas de Seguridad Pública")
cruce = pd.crosstab(grupos.dropna().astype(int).map(lambda g: f"Grupo {g}"),
                    dentro.loc[grupos.dropna().index, "zona"],
                    values=dentro.loc[grupos.dropna().index, "incidentes"], aggfunc="sum").fillna(0).astype(int)
st.plotly_chart(gr.mapa_calor_tabla(cruce, "Incidentes por grupo K-means y zona", "Zona", "Grupo"),
                width="stretch")

with st.expander("¿Por qué este número de grupos? (evaluación de k = 2 a 12)"):
    if st.button("Calcular evaluación"):
        ev = comun.evaluar_k(dentro)
        st.plotly_chart(gr.evaluacion_k(ev, k), width="stretch")
        st.dataframe(ev, hide_index=True, column_config={
            "k": "k", "inercia_km2": st.column_config.NumberColumn("Inercia (km² × incidentes)", format="%.0f"),
            "silueta": st.column_config.NumberColumn("Silueta", format="%.3f")})
    st.markdown("La **silueta** mide qué tan separados quedan los grupos (de −1 a 1). Con los datos completos es "
                "mayor con k = 2, pero dos grupos no describen la ciudad; de 3 a 12 cambia poco. El resultado no "
                "depende del azar: se usa una semilla fija y con otra semilla se obtienen los mismos grupos.")
