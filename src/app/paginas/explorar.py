import streamlit as st

from src.app import comun

comun.encabezado("Explorar datos", "Tabla de cruceros limpios. Se puede ordenar, buscar y descargar.", aviso=False)

df = comun.datos_filtrados()

MARCAS = {
    "zona_inferida": "Zona inferida por cercanía",
    "sector_sin_dato": "Sector sin dato",
    "sin_id_crucero": "Sin identificador de crucero",
    "no_es_crucero": "Tramo de calle (no es cruce)",
    "coord_repetida": "Ubicación repetida",
    "nombre_corregido": "Nombre corregido (Ñ)",
    "fuera_municipio": "Fuera del municipio",
}

c1, c2 = st.columns([2, 1])
buscar = c1.text_input("Buscar calle", placeholder="Ej. TECNOLOGICO")
marca = c2.selectbox("Mostrar solo registros con la marca", ["(todos)", *MARCAS.values()])

vista = df
if buscar:
    vista = vista[vista["nombre_crucero"].str.contains(buscar.strip().upper(), regex=False)]
if marca != "(todos)":
    col = next(k for k, v in MARCAS.items() if v == marca)
    vista = vista[vista[col]]

vista = vista.sort_values("incidentes", ascending=False)
st.caption(f"{comun.miles(len(vista))} cruceros · {comun.miles(vista['incidentes'].sum())} incidentes")

columnas = ["id_objeto", "nombre_crucero", "calle_1", "calle_2", "zona", "zona_original", "sector",
            "incidentes", "latitud", "longitud", *MARCAS]
st.dataframe(
    vista[columnas], hide_index=True, width="stretch", height=520,
    column_config={
        "id_objeto": st.column_config.NumberColumn("ID original", format="%d",
                                                   help="OBJECTID del archivo original (trazabilidad)"),
        "nombre_crucero": "Crucero", "calle_1": "Calle 1", "calle_2": "Calle 2", "zona": "Zona",
        "zona_original": "Zona original",
        "sector": st.column_config.NumberColumn("Sector", format="%d"),
        "incidentes": st.column_config.NumberColumn("Incidentes 2024", format="%d"),
        "latitud": st.column_config.NumberColumn("Latitud", format="%.5f"),
        "longitud": st.column_config.NumberColumn("Longitud", format="%.5f"),
        **{k: st.column_config.CheckboxColumn(v) for k, v in MARCAS.items()},
    },
)

st.download_button("Descargar CSV", vista[columnas].to_csv(index=False).encode("utf-8-sig"),
                   file_name="cruceros_incidentes_2024_filtrado.csv", mime="text/csv")
