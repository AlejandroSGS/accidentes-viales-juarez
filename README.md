# Accidentes viales en Ciudad Juárez

Sistema de análisis y visualización de los **incidentes viales registrados en 2024 en los cruceros de Ciudad Juárez, Chihuahua** (datos del IMIP). Limpia y documenta los datos, los guarda en PostgreSQL, calcula estadísticas y zonas de concentración (densidad Kernel y K-means), y los muestra en una aplicación web con tablas, gráficas y mapas.

Proyecto de la materia **Tópicos Selectos de Ingeniería de Software**, Universidad Autónoma de Ciudad Juárez.
Equipo: Ruby Angélica Dávila Ávila · Saúl Fernando Holguín Galván · Alejandro Samuel Gasca Sifuentes. Profesor: Juan Daniel Mata Gallegos.

> **Pregunta de investigación:** ¿Cómo puede el análisis de datos facilitar la identificación de patrones en los incidentes viales de Ciudad Juárez?
>
> **Aviso:** los resultados muestran **dónde se concentran los registros**; **no determinan las causas** de los accidentes.

## Resultados principales (2024)

- **6,423 incidentes** en **2,787 cruceros**. Dos de cada tres cruceros tuvieron un solo incidente.
- El **12.7 % de los cruceros acumula la mitad** de los incidentes (índice de Gini 0.48).
- Cruceros con más incidentes: Paseo de la Victoria y Teófilo Borunda (49), Blvd. Zaragoza y De las Torres (44), Blvd. Talamás Camandari y De las Torres (39).
- Las zonas Sur, Valle y Universidad suman dos tercios del total; Oriente tiene el promedio más alto por crucero.
- La mayor densidad está alrededor de Av. López Mateos y Paseo Triunfo de la República (~74 incidentes/km²).

Detalle en [`docs/reporte_analisis.md`](docs/reporte_analisis.md).

## Instalación paso a paso (Windows)

**Requisitos:** Python 3.14 (probado con 3.14.6), PostgreSQL 18 (probado con 18.4; **no** necesita PostGIS) y Git.

1. **Clonar o copiar** el proyecto y abrir PowerShell en su carpeta.
2. **Crear el entorno virtual e instalar dependencias** (versiones fijadas en `requirements.txt`):
   ```powershell
   python -m venv .venv
   .venv\Scripts\python -m pip install -r requirements.txt
   ```
3. **Configurar la conexión a PostgreSQL:**
   ```powershell
   Copy-Item .env.example .env
   notepad .env      # escribe tu contraseña en PGPASSWORD
   ```
   El archivo `.env` no se sube a Git.
4. **Crear las bases de datos** (la real y la de pruebas), por ejemplo con `psql` o pgAdmin:
   ```sql
   CREATE DATABASE accidentes_viales;
   CREATE DATABASE accidentes_viales_test;
   ```

## Cómo correr el sistema

```powershell
.venv\Scripts\python -m src.db --reset          # 1. crea el esquema desde cero (db/schema.sql + db/migrations/)
.venv\Scripts\python -m src.limpieza.pipeline   # 2. limpia data/raw → data/processed + PostgreSQL
.venv\Scripts\python -m src.analisis.reporte    # 3. (opcional) regenera docs/reporte_analisis.md
.venv\Scripts\streamlit run src/app/app.py      # 4. abre la app en http://localhost:8501
```

- El paso 2 **se puede repetir** cuantas veces se quiera: reemplaza los datos dentro de una transacción (no duplica nada) y agrega una entrada al historial de ejecuciones. También regenera `docs/bitacora_limpieza.md`.
- `python -m src.db` (sin `--reset`) solo crea lo que falte; úsalo después de agregar una migración.
- Opciones del pipeline: `--test` (carga en la base de pruebas) y `--sin-db` (solo genera archivos).

### Pruebas

```powershell
.venv\Scripts\python -m pytest              # 61 pruebas (~20 s)
.venv\Scripts\python -m pytest -m "not db"  # solo las que no necesitan PostgreSQL
```

Las pruebas con base de datos usan **solo** `accidentes_viales_test`. Ver [`docs/reporte_pruebas.md`](docs/reporte_pruebas.md).

## Páginas de la aplicación

| Página | Contenido |
|---|---|
| Inicio | Cifras clave, 5 cruceros principales, aviso de no causalidad |
| Explorar datos | Tabla con búsqueda y filtro por marca de calidad; descarga CSV |
| Cruceros y zonas | Rankings de cruceros, zonas y sectores |
| Concentración | Curva de Pareto, distribución e índice de Gini |
| Mapa | Densidad Kernel (radio ajustable), cruceros y ranking numerado; indica cuántos registros no se muestran |
| Zonas K-means | Modelo no supervisado con k ajustable, perfil de grupos, comparación con zonas y evaluación de k |
| Tiempo y tipos | Explica por qué no hay análisis por fecha, hora, tipo ni comparación de periodos |
| Calidad y trazabilidad | Fuente, SHA-256, reglas aplicadas, registros marcados e historial de cargas |
| Acerca de | Objetivo, métodos, limitaciones y créditos |

Los filtros de la barra lateral (zona, sector, mínimo de incidentes) aplican a todas las páginas.

## Estructura del proyecto

```
accidentes-viales-juarez/
├── README.md
├── requirements.txt          # dependencias con versión fijada
├── pytest.ini
├── .env.example              # plantilla de conexión (el .env real no va a Git)
├── *.pdf                     # documento del proyecto (solo local, no se publica)
├── data/
│   ├── raw/                  # originales, nunca se editan
│   │   ├── proyecto/         # ACCIDENTES_LIMPIOS.gpkg y ACCIDENTES_ML.csv (fuente principal)
│   │   └── imip_arcgis/      # límite municipal y centro de población (apoyo)
│   ├── interim/              # pasos intermedios de la exploración (no va a Git)
│   └── processed/            # cruceros_2024_limpio.csv / .gpkg (los genera el pipeline)
├── db/
│   ├── schema.sql            # esquema, tablas, índices y vistas
│   └── migrations/           # cambios posteriores (001: vista de ranking)
├── docs/                     # fuentes, diccionario, bitácora y reportes de cada etapa
├── notebooks/                # exploración de la Etapa 1 (usa datos del IMIP que no están en Git)
├── src/
│   ├── config.py             # rutas y conexión (lee .env)
│   ├── db.py                 # crea / recrea el esquema
│   ├── ingesta/              # descarga del servicio ArcGIS del IMIP
│   ├── limpieza/             # reglas.py (16 reglas) y pipeline.py
│   ├── analisis/             # datos (consultas), descriptiva, espacial (KDE, K-means), reporte
│   ├── visualizacion/        # gráficas Plotly y mapas Folium reutilizables
│   └── app/                  # aplicación Streamlit (app.py, comun.py, paginas/)
└── tests/                    # pruebas de reglas, análisis, integridad y app
```

**Por qué estas capas:** cada una tiene una sola responsabilidad (leer, limpiar, analizar, mostrar), así que se puede probar y cambiar una sin romper las demás. Por ejemplo, la app nunca limpia datos y las funciones de análisis no dependen de Streamlit.

## Flujo de los datos y trazabilidad

```
data/raw/proyecto/ACCIDENTES_LIMPIOS.gpkg ──► 16 reglas de limpieza ──► data/processed/  ──► app
           (SHA-256 registrado)               (bitácora por regla)      accidentes.cruceros
                                                                         (PostgreSQL)
```

- Cada registro limpio conserva su **`id_objeto` = `OBJECTID` original**, y la tabla `raw_cruceros_2024` guarda la copia fiel del archivo.
- Ningún registro con problemas se borra: se **marca** (`zona_inferida`, `fuera_municipio`, `no_es_crucero`, etc.) y la app lo reporta.
- Cada carga queda en `ejecuciones_pipeline` (fecha, archivo, SHA-256, registros) y cada regla en `bitacora_limpieza`.

## Documentación

| Documento | Contenido |
|---|---|
| [`docs/fuentes_de_datos.md`](docs/fuentes_de_datos.md) | URL, fecha de descarga, formato y uso de cada fuente |
| [`docs/reporte_etapa1_calidad.md`](docs/reporte_etapa1_calidad.md) | Exploración inicial, problemas encontrados y decisiones |
| [`docs/diccionario_de_datos.md`](docs/diccionario_de_datos.md) | Tablas, columnas, marcas de calidad y vistas |
| [`docs/bitacora_limpieza.md`](docs/bitacora_limpieza.md) | Efecto de cada regla (generado automáticamente) |
| [`docs/reporte_analisis.md`](docs/reporte_analisis.md) | Resultados estadísticos, KDE y K-means (generado automáticamente) |
| [`docs/reporte_pruebas.md`](docs/reporte_pruebas.md) | Qué se probó y qué no |

## Limitaciones conocidas

Alineadas con la sección 1.6 del documento del proyecto:

- **Periodo histórico limitado:** solo hay datos de **2024**. No se pueden ver tendencias entre años ni comparar periodos.
- **Formato de los datos:** cada registro es un **total anual por crucero**. No hay fecha, hora ni tipo de incidente, así que no hay patrones por mes, día u hora ni porcentaje de choques o atropellos. La app lo explica en vez de inventar datos.
- **Información geográfica:** la ubicación es la del crucero, no la del punto exacto del incidente. 2 cruceros (9 incidentes) caen fuera del límite municipal y no se dibujan. 64 registros son tramos de calle y no cruces.
- **Registros incompletos:** 11 cruceros sin zona (se infirió por cercanía y se marcó), 13 sin sector y 1 sin identificador.
- **Solo cruceros con incidentes:** los cruceros sin incidentes no están en el archivo, así que la concentración real es mayor que la calculada.
- **Dependencia de la fuente oficial:** los resultados son tan completos como el registro del IMIP y la Dirección de Tránsito. No hay actualización en tiempo real.
- **Métodos descriptivos:** la densidad Kernel y K-means describen dónde se concentran los registros. **No determinan causas ni predicen accidentes.** El número de grupos (6) y el radio del KDE (500 m) son decisiones razonadas, pero no únicas; la app permite cambiarlos.

## Trabajo futuro

Ideas que no se implementaron:

1. **Integrar los incidentes individuales 2023–2025 del IMIP** (fecha, hora, tipo, causa, condiciones del camino) para agregar patrones temporales, tipos de incidente y comparación de periodos. El script de descarga ya existe (`src/ingesta/arcgis_imip.py`).
2. **Serie histórica 2008–2025** con los shapefiles anuales de cruceros del IMIP, para ver tendencias por crucero y zona.
3. **Actualización automática** de los datos cuando el IMIP publique un nuevo año, con validación y aviso de cambios.
4. **Integración con ATUS/INEGI** para comparar totales municipales y causas.
5. **Indicadores de autocorrelación espacial** (I de Moran, Getis-Ord Gi\*) para saber qué zonas calientes son estadísticamente significativas.
6. **Tasas en lugar de conteos**, usando aforos vehiculares o población, para comparar zonas de distinto tamaño de forma más justa.
7. **Modelos de riesgo** (por ejemplo, regresión geográficamente ponderada como en Hernández, 2024) con variables de uso de suelo e infraestructura.
8. **API pública** de solo lectura sobre las vistas de PostgreSQL, y despliegue de la app en un servidor.
9. **PostGIS** si el volumen de datos crece y se necesitan consultas espaciales en la base.

## Créditos y fuentes

- Datos: **Instituto Municipal de Investigación y Planeación (IMIP), Ciudad Juárez**, sigimip.org.mx.
- Mapa base: © colaboradores de OpenStreetMap.
- Método de zonas: Anderson, T. K. (2009). Kernel density estimation and K-means clustering to profile road accident hotspots. *Accident Analysis & Prevention*, 41(3), 359–364.
- Desarrollado con apoyo de Claude Code (Anthropic).
