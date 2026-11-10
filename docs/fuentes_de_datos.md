# Fuentes de datos

Todas las fechas de descarga están en UTC. Los archivos originales están en `data/raw/` y **no se modifican**.

## 0. Datos del proyecto (fuente principal)

- **Origen:** archivos entregados por el equipo del proyecto; son los que se usaron en el documento del proyecto. Derivan de la capa **"Incidentes viales 2024"** del IMIP (`ACCI2024`, fuente 1).
- **Recibidos:** 2026-11-09 (hora local). Están en `data/raw/proyecto/`.

| Archivo | Formato | SHA-256 |
|---|---|---|
| `ACCIDENTES_LIMPIOS.gpkg` | GeoPackage, capa `ACCIDENTES_LIMPIOS`, puntos, EPSG:32613 | f2657da6fa0d0adba3398495b9d37b2d1f27ae946d5d61331787cc807b97fbee |
| `ACCIDENTES_ML.csv` | CSV UTF-8 con BOM, separador coma | 82941bd07758f3cfab09cd0a5d413e1d6f90f2cabff74bc07e8b766da214cf8e |

**Contenido:** 2,787 cruceros con su número de incidentes en 2024 (6,423 en total). Columnas: `OBJECTID`, `PUNTOS_ID`, `NOMBRE1`, `NOMBRE2`, `DicSegPub` (zona de Seguridad Pública), `SECTOR`, `ACCI2024` (conteo), `X`, `Y` (UTM 13N).

**Relación con el original del IMIP** (verificado registro por registro con `OBJECTID`): los dos archivos son idénticos entre sí. Respecto a `ACCI2024.shp`, el único cambio es que las 11 zonas vacías (`DicSegPub`) se reemplazaron por `SIN_DATO`; además se agregaron las columnas `X`/`Y`, iguales a la geometría.

## 1. IMIP — Portal de descargas del SIG (shapefiles)

- **Institución:** Instituto Municipal de Investigación y Planeación (IMIP), Ciudad Juárez.
- **Página:** https://sigimip.org.mx/descargas.html
- **Fecha de descarga:** 2026-11-10 (05:22 UTC)
- **Condiciones de uso:** el portal es público y no declara una licencia explícita en los metadatos. Se cita al IMIP como fuente.

| Archivo en `data/raw/imip/` | URL | Formato | Contenido |
|---|---|---|---|
| `Acci2008-2022.zip` | https://sigimip.org.mx/download/imip/descargas/Acci2008-2022.zip | ZIP con un ZIP por año (SHP + KMZ + metadatos XML/HTML) | **Cruceros con conteo anual** de incidentes, 2008–2024 (pese al nombre, incluye 2023 y 2024) |
| `ACCI2024.zip` | https://sigimip.org.mx/download/imip/descargas/ACCI2024.zip | SHP | Cruceros con conteo 2024 (igual al incluido en el anterior) |
| `ACCI2024.html` | https://sigimip.org.mx/download/imip/descargas/ACCI2024.html | HTML (metadatos FGDC) | Definición de campos |
| `Colonias.zip` / `Colonias.html` | https://sigimip.org.mx/download/imip/descargas/Colonias.zip | SHP (WGS84) + metadatos | Polígonos de colonias |

SHA-256: `Acci2008-2022.zip` a3e3e8f1…94b1 · `ACCI2024.zip` b9c2f406…92ae · `Colonias.zip` 3e9c9237…a5 (hashes completos se registrarán en el pipeline).

**Importante:** en estos shapefiles cada registro es un **crucero** (intersección) con el **número de incidentes del año**. No incluyen fecha, hora ni tipo de incidente. Sistema de coordenadas: UTM zona 13N (EPSG:32613).

## 2. IMIP — Servicio ArcGIS REST (incidentes individuales)

- **Servicio:** https://sigimip.org.mx/server/rest/services/incidentesviales/FeatureServer (ArcGIS Server 11.5, público)
- **Descarga:** `python -m src.ingesta.arcgis_imip` — guarda las respuestas tal como las entrega el servidor (Esri JSON paginado, 2,000 registros por página) en `data/raw/imip_arcgis/`, con un `manifiesto.json` que registra URL, número de registros, fecha y SHA-256 de cada página.
- **Fecha de descarga:** 2026-11-10 (05:28 UTC)

| Carpeta | Capa | Registros | Contenido |
|---|---|---|---|
| `incidentes_2023T` | 16 | 6,116 | **Un registro por incidente**: expediente, fecha, hora, tipo, causa, factor, colonia, zona, clima, luz, pavimento, etc. |
| `incidentes_2024T` | 18 | 6,423 | Igual, 2024 (incluye "Grado") |
| `incidentes_2025T` | 20 | 6,314 | Igual, 2025 |
| `cruceros_2025` | 19 | 2,964 cruceros | Conteo por crucero 2025 |
| `cruceros_mayor_incidencia` | 41 | 29 | Cruceros con más incidentes y conteo por año |
| `limite_municipal` | limitesyareasV2/15 | 1 | Polígono del municipio de Juárez (para validar coordenadas) |
| `centro_de_poblacion` | limitesyareasV2/14 | 1 | Polígono del área urbana |

El mismo servicio alimenta los mapas del IMIP (`sigimip.org.mx/sigmunmapas/incidentes`, `Incidenciatime23`, `Incidenciatime24`).

## 3. INEGI — ATUS (complementaria, **no descargada**)

- **Página:** https://www.inegi.org.mx/programas/accidentes/
- **Estado:** las rutas de datos abiertos probadas devuelven páginas HTML en lugar de archivos; no se pudo descargar automáticamente. Si se decide usarla, se requiere descarga manual (ver reporte de la Etapa 1).
- **Aporte potencial:** serie municipal desde 1997 con fecha, hora, tipo y causa, pero **sin coordenadas** (solo a nivel municipio), útil para comparar totales.
