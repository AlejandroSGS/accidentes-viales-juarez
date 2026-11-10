# Diccionario de datos

Base: PostgreSQL, esquema `accidentes`. Definición completa en `db/schema.sql`.
Unidad de análisis: **crucero (intersección vial) con su número de incidentes en 2024**. Los datos no incluyen fecha, hora ni tipo de incidente.

## `cruceros` (datos limpios)

También disponible en `data/processed/cruceros_2024_limpio.csv` y `.gpkg` (WGS84).

| Columna | Tipo | Origen | Descripción |
|---|---|---|---|
| `id_objeto` | entero, PK | `OBJECTID` | Identificador del registro original; enlaza con `raw_cruceros_2024` |
| `id_crucero` | entero, puede ser vacío | `PUNTOS_ID` | Identificador del nodo o intersección (IMIP). Vacío si venía `99999` |
| `calle_1`, `calle_2` | texto | `NOMBRE1`, `NOMBRE2` | Calles que forman el crucero, con la Ñ corregida y el texto normalizado |
| `nombre_crucero` | texto | derivado | "CALLE A y CALLE B" en orden alfabético; una sola calle si ambas son iguales |
| `zona` | texto, FK `cat_zonas` | `DicSegPub` | Zona de Seguridad Pública Municipal (CENTRO, ORIENTE, PONIENTE, SUR, UNIVERSIDAD, VALLE); inferida si venía `SIN_DATO` |
| `zona_original` | texto | `DicSegPub` | Valor tal como venía en el archivo |
| `sector` | entero, puede ser vacío, FK `cat_sectores` | `SECTOR` | Sector de Seguridad Pública Municipal. Vacío si venía `0` |
| `anio` | entero | constante | Año de los datos (2024) |
| `incidentes` | entero ≥ 1 | `ACCI2024` | Número de incidentes viales registrados en el crucero en 2024 |
| `x_utm`, `y_utm` | decimal (m) | geometría | Coordenadas UTM zona 13N (EPSG:32613) |
| `latitud`, `longitud` | decimal (grados) | derivado | Coordenadas WGS84 (EPSG:4326) para los mapas web |

### Indicadores de calidad (verdadero/falso)

El registro **se conserva** aunque tenga una marca; la app informa cuántos hay.

| Columna | Significado | Regla |
|---|---|---|
| `zona_inferida` | La zona venía `SIN_DATO` y se asignó por la mayoría de los 5 cruceros vecinos más cercanos (en empate, el más cercano) | R08 |
| `sector_sin_dato` | El sector venía `0` | R09 |
| `sin_id_crucero` | `PUNTOS_ID` venía `99999` | R10 |
| `no_es_crucero` | Calle 1 = calle 2: es un tramo de calle, no una intersección | R11 |
| `coord_repetida` | Otro crucero tiene la misma ubicación (a menos de 0.5 m) | R12 |
| `sector_multizona` | El sector aparece en más de una zona | R13 |
| `nombre_corregido` | Se corrigió `¥` → `Ñ` en algún nombre de calle | R03 |
| `fuera_municipio` | La ubicación cae fuera del límite municipal del IMIP. No se dibuja en el mapa | R07 |

## Otras tablas

| Tabla | Contenido |
|---|---|
| `raw_cruceros_2024` | Copia fiel de `ACCIDENTES_LIMPIOS.gpkg` (mismos nombres de columna), sin transformar |
| `cat_zonas` | Zonas válidas |
| `cat_sectores` | Sector, su zona principal (la de más cruceros) y número de zonas en que aparece |
| `ejecuciones_pipeline` | Una fila por corrida: inicio, fin, archivo de origen, SHA-256, registros crudos y limpios |
| `bitacora_limpieza` | Por corrida y regla: código, descripción, acción y registros afectados, antes y después |

## Vistas

| Vista | Uso |
|---|---|
| `v_incidentes_por_zona` | Cruceros, incidentes y % por zona |
| `v_incidentes_por_sector` | Cruceros e incidentes por sector |
| `v_resumen_calidad` | Totales y número de registros con cada indicador de calidad |
| `v_ultima_bitacora` | Bitácora de la última corrida completa |
