import streamlit as st

st.title("Patrones temporales, tipos de incidente y comparación de periodos")

st.markdown("No disponible con los datos del proyecto.")

st.markdown("""
El alcance del proyecto contempla analizar cuándo ocurren los incidentes, de qué tipo son y comparar
periodos. El archivo con el que trabaja esta aplicación (`ACCIDENTES_LIMPIOS.gpkg`, cruceros 2024 del IMIP)
contiene un total anual por crucero y no incluye:

| Análisis | Dato necesario | ¿Está en el archivo? |
|---|---|---|
| Por mes, día de la semana y hora (mapa de calor día × hora) | Fecha y hora de cada incidente | No |
| Tipos más frecuentes (choque, atropello, volcadura…) | Tipo de cada incidente | No |
| Comparar dos periodos | Fecha, o al menos dos años | No (solo 2024) |

Mostrar estas gráficas obligaría a inventar o suponer datos, así que no se muestran.

Cómo se podría completar (trabajo futuro): el IMIP publica en su servicio de mapas registros individuales de
2023 a 2025 con fecha, hora y tipo, y cruceros por año desde 2008 (ver `docs/fuentes_de_datos.md`). Integrarlos
permitiría agregar estas secciones.
""")
