import streamlit as st

from src.analisis import descriptiva as de
from src.app import comun
from src.visualizacion import graficas as gr

comun.encabezado("Cruceros, zonas y sectores", "¿Dónde se registraron más incidentes en 2024?")

df = comun.datos_filtrados()

tab1, tab2, tab3 = st.tabs(["Cruceros", "Zonas", "Sectores"])

with tab1:
    n = st.slider("Número de cruceros a mostrar", 5, 50, 20, step=5)
    rk = de.ranking_cruceros(df, n)
    rk["etiqueta"] = rk["posicion"].astype(str) + ". " + rk["nombre_crucero"]
    st.plotly_chart(gr.barras_horizontales(rk, "etiqueta", "incidentes", f"Los {n} cruceros con más incidentes",
                                           eje_y="Crucero"), width="stretch")
    st.caption("Cruceros empatados comparten la misma posición.")

with tab2:
    zonas = de.agregar_por(df, "zona")
    st.plotly_chart(gr.barras_zona(zonas), width="stretch")
    st.dataframe(zonas, hide_index=True, width="stretch", column_config={
        "zona": "Zona", "cruceros": st.column_config.NumberColumn("Cruceros", format="%d"),
        "incidentes": st.column_config.NumberColumn("Incidentes", format="%d"),
        "porcentaje": st.column_config.NumberColumn("% del total", format="%.2f %%"),
        "promedio_por_crucero": st.column_config.NumberColumn("Incidentes por crucero", format="%.2f"),
    })
    st.caption("Las zonas tienen distinto tamaño y número de cruceros; el promedio por crucero ayuda a compararlas. "
               "Incluye 11 cruceros cuya zona se infirió por cercanía.")

with tab3:
    n_s = st.slider("Número de sectores a mostrar", 5, 40, 15, step=5)
    sec = de.agregar_por(df, "sector").head(n_s)
    sec["etiqueta"] = "Sector " + sec["sector"].astype(int).astype(str)
    st.plotly_chart(gr.barras_horizontales(sec, "etiqueta", "incidentes", f"Los {n_s} sectores con más incidentes",
                                           eje_y="Sector"), width="stretch")
    st.caption("Sectores de Seguridad Pública Municipal. Se excluyen los cruceros con sector sin dato.")
