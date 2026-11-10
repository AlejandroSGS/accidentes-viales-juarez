import streamlit as st

from src.analisis import descriptiva as de
from src.app import comun

comun.encabezado("Accidentes viales en Ciudad Juárez",
                 "Consulta de los cruceros con incidentes viales registrados en 2024 en Ciudad Juárez, "
                 "Chihuahua, para reconocer dónde se concentran.")

df = comun.datos_filtrados()
r = de.resumen_general(df)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Incidentes registrados", comun.miles(r["incidentes"]))
c2.metric("Cruceros con incidentes", comun.miles(r["cruceros"]))
c3.metric("Máximo en un crucero", comun.miles(r["maximo_crucero"]))
c4.metric("Cruceros que suman la mitad", f"{de.pct_cruceros_para(df, 50):.1f} %",
          help="Porcentaje de cruceros (los de más incidentes) que acumula el 50 % de los incidentes.")

c5, c6, c7, c8 = st.columns(4)
c5.metric("Periodo", "Enero–diciembre 2024")
c6.metric("Promedio por crucero", f"{r['promedio_por_crucero']:.2f}")
c7.metric("Cruceros con 1 solo incidente", f"{100 * r['cruceros_con_1'] / r['cruceros']:.1f} %")
c8.metric("Zonas · sectores", f"{r['zonas']} · {r['sectores']}")

st.subheader("Los 5 cruceros con más incidentes")
top = de.ranking_cruceros(df, 5)
st.dataframe(
    top[["posicion", "nombre_crucero", "zona", "sector", "incidentes", "porcentaje"]],
    hide_index=True, width="stretch",
    column_config={
        "posicion": st.column_config.NumberColumn("#", format="%d"),
        "nombre_crucero": "Crucero", "zona": "Zona",
        "sector": st.column_config.NumberColumn("Sector", format="%d"),
        "incidentes": st.column_config.NumberColumn("Incidentes", format="%d"),
        "porcentaje": st.column_config.NumberColumn("% del total", format="%.2f %%"),
    },
)

st.subheader("Sobre los datos")
st.markdown("""
- Cada registro es un crucero (cruce de dos calles) con el número de incidentes viales que tuvo en 2024.
- Los datos no incluyen fecha, hora ni tipo de incidente; por eso no hay análisis por mes, día u hora (ver *Tiempo y tipos*).
- Los filtros de la barra lateral aplican a todas las páginas.
- En *Calidad y trazabilidad* se explica qué se corrigió en los datos y cuántos registros tienen alguna marca.
""")
