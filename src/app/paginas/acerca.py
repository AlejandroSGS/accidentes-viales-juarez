import streamlit as st

st.title("Acerca de")

st.markdown("""
### Accidentes viales en Ciudad Juárez

Proyecto de la materia **Tópicos Selectos de Ingeniería de Software**, Universidad Autónoma de Ciudad Juárez
(Instituto de Ingeniería y Tecnología). Profesor: Juan Daniel Mata Gallegos.

**Equipo:** Ruby Angélica Dávila Ávila · Saúl Fernando Holguín Galván · Alejandro Samuel Gasca Sifuentes

**Pregunta de investigación:** ¿Cómo puede el análisis de datos facilitar la identificación de patrones en los
incidentes viales de Ciudad Juárez?

**Objetivo general:** desarrollar un sistema de análisis y visualización de datos que permita procesar registros
de incidentes viales en Ciudad Juárez para identificar patrones temporales y geográficos mediante técnicas de
ciencia de datos.

### Métodos
- Limpieza y validación de los registros, con bitácora de cada regla (Imprialou y Quddus, 2019).
- Estadística descriptiva: rankings, distribución y concentración (curva de Pareto, índice de Gini).
- Densidad Kernel y agrupamiento K-means ponderado para perfilar zonas de concentración (Anderson, 2009).

### Limitaciones
- Solo hay datos de **2024** y en forma de **total anual por crucero**: no hay fecha, hora ni tipo de incidente.
- Solo están los cruceros con al menos un incidente; los cruceros sin incidentes no aparecen.
- La ubicación es la del crucero, no la del punto exacto del incidente.
- 11 zonas fueron inferidas por cercanía y 13 cruceros no tienen sector.
- Los datos dependen de la calidad del registro oficial y no se actualizan en tiempo real.
- **Los resultados no determinan las causas de los accidentes.** Muestran dónde se concentran los registros.

### Fuentes
- Instituto Municipal de Investigación y Planeación (IMIP), Ciudad Juárez: capa *Incidentes viales 2024* y límite municipal, sigimip.org.mx.
- Anderson, T. K. (2009). Kernel density estimation and K-means clustering to profile road accident hotspots. *Accident Analysis & Prevention*, 41(3), 359–364.
- Imprialou, M., & Quddus, M. (2019). Crash data quality for road safety research. *Accident Analysis & Prevention*, 130, 84–90.
""")
