# Etapa 1 — Exploración y calidad de los datos

Scripts que generan estas cifras: `notebooks/eda_estructura.py`, `notebooks/eda_calidad.py`, `notebooks/eda_incidentes.py`.

## 0. Datos del proyecto — `ACCIDENTES_LIMPIOS.gpkg` / `ACCIDENTES_ML.csv` (fuente principal)

2,787 cruceros con 6,423 incidentes en 2024. Los dos archivos son idénticos entre sí y equivalen al shapefile `ACCI2024` del IMIP, con las 11 zonas vacías cambiadas a `SIN_DATO`.

Lo que está bien: no hay nulos ni `PUNTOS_ID` duplicados, todos los conteos son ≥ 1, las coordenadas `X`/`Y` coinciden con la geometría, no hay espacios sobrantes y no hay variantes de escritura de un mismo nombre de calle.

Problemas encontrados:
| Problema | Registros | Ejemplo |
|---|---|---|
| Zona `SIN_DATO` (todos con `SECTOR = 0`) | 11 | EJE VIAL JUAN GABRIEL / PAVO REAL |
| Fuera del límite municipal | 2 | JUAN PABLO II / INTERNACIONAL (5 incidentes); PANAMERICANA / PANAMERICANA (4) |
| `PUNTOS_ID = 99999` (sin identificador de crucero) | 1 | PANAMERICANA / PANAMERICANA |
| Calle 1 = Calle 2 (no es un crucero real; probablemente un tramo de calle) | 64 | MIGUEL HIDALGO / MIGUEL HIDALGO |
| Error de codificación `Ñ` → `¥` | 3 | NI¥OS HEROES, RIVERA DE PE¥ASCO |
| Coordenadas repetidas en dos cruceros distintos | 2 | |
| Un sector asignado a más de una zona | 1 sector | |
| Mismo par de calles en cruceros distintos (puede ser válido: calles que se cruzan dos veces) | 72 | |

Distribución: la mitad de los cruceros tiene 1 solo incidente (1,853 de 2,787); el máximo es 49 (PASEO DE LA VICTORIA / TEOFILO BORUNDA).

**Limitación clave:** el archivo no trae fecha, hora ni tipo de incidente, y solo cubre 2024.

## A. Cruceros con conteo anual (2008–2024, shapefiles)

| Año | Cruceros | Incidentes (suma) | Referencia del proyecto | Diferencia |
|---|---|---|---|---|
| 2008 | 3,022 | 8,184 | | |
| 2009 | 2,748 | 6,318 | | |
| 2010 | 2,134 | 4,921 | | |
| 2011 | 1,979 | 4,423 | | |
| 2012 | 2,120 | 5,160 | | |
| 2013 | 2,394 | 5,595 | | |
| 2014 | 2,285 | 5,191 | | |
| 2015 | 2,610 | 6,549 | | |
| 2016 | 2,542 | 5,841 | | |
| 2017 | 2,613 | 5,441 | | |
| 2018 | 2,874 | 5,890 | 5,899 | −0.2 % |
| 2019 | 3,243 | 7,365 | 7,486 | −1.6 % |
| 2020 | 3,056 | 6,332 | 6,344 | −0.2 % |
| 2021 | 2,666 | 6,188 | 6,207 | −0.3 % |
| 2022 | 1,927 | 3,879 | 3,889 | −0.3 % |
| 2023 | 2,631 | 6,116 | | |
| 2024 | 2,787 | 6,423 | | |

Problemas encontrados:
- **Columnas distintas entre años:** la columna de conteo cambia de nombre (`ACCI2008`, `ACCI2009`…); `DISTRITO` solo existe en 2013; `DicSegPub`/`SECTOR` solo en 2023–2024; `PUNTOS_ID` es entero en unos años y decimal en otros.
- **`PUNTOS_ID = 99999`** (crucero sin identificador): 7 en 2015, 6 en 2016, 3 en 2017.
- **`PUNTOS_ID` repetido** dentro del mismo año: hasta 92 en 2012.
- **Nombres de calle vacíos** (`NOMBRE2` vacío en 6–79 registros por año) y **variantes de escritura** (p. ej. "FRANCISCO VILLAREAL" vs "FRANCISCO VILLARREAL TORRES").
- Algunos puntos lejos de la ciudad (p. ej. longitud −106.93 en 2024): hay que validarlos contra el límite municipal.
- Sin fecha, hora ni tipo: con 2008–2022 **solo se pueden analizar totales anuales y cruceros/zonas**.

## B. Incidentes individuales (2023, 2024, 2025, ArcGIS)

Totales: 6,116 (2023), 6,423 (2024), 6,314 (2025). Los de 2023 y 2024 coinciden **exactamente** con la suma de cruceros de esos años.

Lo que está bien:
- Fechas válidas en el 100 % de los registros; día de la semana y mes coinciden con la fecha (2023 y 2024).
- Hora con formato válido en el 100 % (pero 2023 usa `HH:MM:SS` y 2024–2025 `HH:MM`).
- Todos tienen coordenadas; solo 3/8/3 registros (2023/2024/2025) caen fuera del límite municipal.

Problemas encontrados:
| Problema | 2023 | 2024 | 2025 |
|---|---|---|---|
| Fecha en formato distinto | texto `M/D/AAAA` | fecha + texto | fecha (sin texto) |
| Coordenadas fuera del municipio | 3 | 8 | 3 |
| Columna `X` del atributo = 0 (la geometría sí está bien) | 0 | 0 | 35 |
| `DiaNumero` no es el día del mes (significado cambia) | — | — | 6,054 |
| `MES` no coincide con la fecha | 0 | 0 | 17 |
| Mismo expediente, misma hora, calles y tipo (duplicado probable) | 1 par | 2 pares | 14 pares |
| Mismo expediente con datos distintos (hora, calle o tipo) | 1 par | 0 | 3 pares |
| `Colonia` vacía | 489 | 448 | 434 |
| Condiciones del camino vacías (clima, luz, pavimento…) | 63 | 167 | 125 |
| `Grado` vacío | todos | 0 | todos |
| `Zona` | 6 zonas + "FUERA" | 7 zonas (nueva "RIVERAS") | solo ORIENTE/PONIENTE |
| Valores fuera de lugar en catálogos | p. ej. Clima = "DURANGO", "DEL PARAISO"; Topografía = "BUENA"; Pendiente = "REDONDA" (valores corridos de columna) | similares | similares |
| Día de la semana con y sin acento | "sábado" | "miercoles" | "miércoles" |

**Tipo de incidente** viene como lista separada por comas (75–87 combinaciones), p. ej. `CHOQUE,FUGA,LESIONADOS`. Los componentes son: tipo (CHOQUE, ATROPELLO, VOLCADURA, CAÍDA DE PERSONA, SALIDA DE CAMINO) y consecuencias (LESIONADOS, MUERTE, FUGA, FUGA A PIE, ROBO…).

**Ubicación:** los incidentes están "pegados" al crucero más cercano (más de la mitad comparten coordenadas exactas con otros), así que la precisión espacial es a nivel crucero, no punto exacto.

## C. Decisión de alcance (2026-11-09)

El equipo decidió usar **solo** `ACCIDENTES_LIMPIOS.gpkg` / `ACCIDENTES_ML.csv` (cruceros 2024) como datos de incidentes. Las secciones A y B describen lo que se exploró; **no** se cargan en la app. Del IMIP solo se usa el **límite municipal** (y el centro de población) como capa de apoyo para validar coordenadas.

Por eso la app **no** podrá mostrar patrones por mes, día u hora, tipos de incidente ni comparación de periodos. Esto queda documentado como limitación.

## D. Reglas de limpieza propuestas (solo datos del proyecto)

1. **Nombres de columnas** en `snake_case` español: `id_objeto`, `id_crucero`, `calle_1`, `calle_2`, `zona`, `sector`, `incidentes_2024`, `x_utm`, `y_utm`.
2. **Codificación:** corregir `¥` → `Ñ` (3 registros).
3. **Texto:** mayúsculas, sin espacios sobrantes; nombre de crucero `calle_1 Y calle_2` con las calles en orden alfabético, para poder agrupar.
4. **Coordenadas:** convertir UTM 13N → latitud/longitud (WGS84). Marcar `fuera_municipio` (2 registros); no se borran, pero no aparecen en el mapa.
5. **Zona sin dato:** conservar `SIN_DATO` y marcar `zona_sin_dato` (11). Opcional: asignar la zona por cercanía a los cruceros vecinos, marcando que fue inferida.
6. **Crucero sin identificador** (`PUNTOS_ID = 99999`): marcar `sin_id_crucero` (1).
7. **Calle 1 = Calle 2:** marcar `no_es_crucero` (64); se conservan, porque sí son ubicaciones con incidentes.
8. **Coordenadas repetidas** entre cruceros distintos: marcar `coord_repetida` (2).
9. **Sector con más de una zona:** marcar para revisión (1 sector).
10. **Trazabilidad:** cada registro limpio conserva `OBJECTID` original, archivo de origen y hash; cada regla registra cuántos registros afectó en `bitacora_limpieza.md`.
