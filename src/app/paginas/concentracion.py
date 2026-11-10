import streamlit as st

from src.analisis import descriptiva as de
from src.app import comun
from src.visualizacion import graficas as gr

comun.encabezado("Concentración", "¿Los incidentes están repartidos entre muchos cruceros o concentrados en pocos?")

df = comun.datos_filtrados()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Cruceros con el 25 % de incidentes", f"{de.pct_cruceros_para(df, 25):.1f} %")
c2.metric("Cruceros con el 50 % de incidentes", f"{de.pct_cruceros_para(df, 50):.1f} %")
c3.metric("Cruceros con el 80 % de incidentes", f"{de.pct_cruceros_para(df, 80):.1f} %")
c4.metric("Índice de Gini", f"{de.indice_gini(df):.3f}",
          help="0 = todos los cruceros tienen los mismos incidentes; cerca de 1 = casi todos en un solo crucero.")

st.plotly_chart(gr.curva_pareto(de.curva_concentracion(df)), width="stretch")
st.caption("Se ordenan los cruceros de más a menos incidentes y se acumulan. Mientras más se aleja la curva de la "
           "línea punteada, más concentrados están los incidentes.")

dist = de.distribucion_conteos(df)
st.plotly_chart(gr.barras_distribucion(dist), width="stretch")
st.dataframe(dist, hide_index=True, width="stretch", column_config={
    "rango": "Incidentes en el crucero", "cruceros": st.column_config.NumberColumn("Cruceros", format="%d"),
    "incidentes": st.column_config.NumberColumn("Incidentes", format="%d"),
    "pct_cruceros": st.column_config.NumberColumn("% de cruceros", format="%.1f %%"),
    "pct_incidentes": st.column_config.NumberColumn("% de incidentes", format="%.1f %%"),
})
st.caption("Importante: solo aparecen cruceros con al menos un incidente en 2024; los cruceros sin incidentes no "
           "están en los datos, así que la concentración real en la ciudad es mayor.")
