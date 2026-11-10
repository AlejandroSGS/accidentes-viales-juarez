import streamlit as st

from src.app import comun

st.title("Calidad y trazabilidad de los datos")
st.markdown("Qué datos se usaron, qué se les hizo y cuántos registros tienen alguna observación. "
            "Esta página no usa los filtros: describe el conjunto completo.")

st.subheader("Fuente")
st.markdown("""
| | |
|---|---|
| Archivo | `data/raw/proyecto/ACCIDENTES_LIMPIOS.gpkg` (y su copia `ACCIDENTES_ML.csv`, verificada idéntica) |
| Origen | Capa *Incidentes viales 2024* del IMIP Ciudad Juárez (sigimip.org.mx), usada en el documento del proyecto |
| Contenido | Un registro por crucero con su número de incidentes en 2024 |
| Apoyo | Límite municipal del IMIP (servicio ArcGIS `limitesyareasV2`), para validar ubicaciones |
| Actualización | Sin actualización en tiempo real; corte anual 2024 |
""")

ej = comun.tabla("ejecuciones_pipeline").sort_values("id_ejecucion")
ultima = ej.iloc[-1]
st.markdown(f"Última carga: {ultima['fin']:%Y-%m-%d %H:%M} UTC (ejecución #{int(ultima['id_ejecucion'])}) · "
            f"SHA-256 del archivo: `{ultima['sha256_origen']}`")

st.subheader("Resumen de calidad")
rc = comun.tabla("v_resumen_calidad").iloc[0]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Registros originales", comun.miles(ultima["registros_crudos"]))
c2.metric("Registros limpios", comun.miles(ultima["registros_limpios"]))
c3.metric("Eliminados", comun.miles(ultima["registros_crudos"] - ultima["registros_limpios"]))
c4.metric("Fuera del mapa (fuera del municipio)", f"{comun.miles(rc['fuera_municipio'])} "
          f"({comun.miles(rc['incidentes_fuera_municipio'])} inc.)")

marcas = [
    ("zona_inferida", "Zona inferida por los 5 cruceros vecinos (venía SIN_DATO)"),
    ("sector_sin_dato", "Sector sin dato (venía 0)"),
    ("sin_id_crucero", "Sin identificador de crucero (venía 99999)"),
    ("no_es_crucero", "Misma calle dos veces: es un tramo, no un cruce"),
    ("coord_repetida", "Otro crucero en la misma ubicación"),
    ("sector_multizona", "Sector repartido en más de una zona"),
    ("nombre_corregido", "Nombre de calle con Ñ corregida (¥ → Ñ)"),
    ("fuera_municipio", "Ubicación fuera del límite municipal"),
]
st.dataframe(
    [{"Marca": m, "Descripción": d, "Registros": int(rc[m])} for m, d in marcas],
    hide_index=True, width="stretch",
)
st.caption("Ningún registro se elimina por tener una marca; se conservan y se reportan. "
           "Cada registro limpio conserva su ID original (OBJECTID).")

st.subheader("Reglas de limpieza aplicadas (última ejecución)")
bit = comun.tabla("v_ultima_bitacora").sort_values("orden")
st.dataframe(bit[["orden", "codigo", "regla", "accion", "registros_afectados", "registros_antes",
                  "registros_despues"]], hide_index=True, width="stretch", column_config={
    "orden": "#", "codigo": "Código", "regla": "Regla", "accion": "Acción",
    "registros_afectados": st.column_config.NumberColumn("Afectados", format="%d"),
    "registros_antes": st.column_config.NumberColumn("Antes", format="%d"),
    "registros_despues": st.column_config.NumberColumn("Después", format="%d")})

with st.expander("Historial de ejecuciones del pipeline"):
    st.dataframe(ej, hide_index=True, width="stretch")
