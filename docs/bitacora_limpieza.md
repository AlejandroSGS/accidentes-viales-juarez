# Bitácora de limpieza

> Archivo generado automáticamente por `python -m src.limpieza.pipeline`. No editar a mano.

- **Ejecución:** 2026-11-10T06:13:22+00:00 (UTC) · id_ejecucion = 2
- **Origen:** `data/raw/proyecto/ACCIDENTES_LIMPIOS.gpkg` (SHA-256 `f2657da6fa0d0adba3398495b9d37b2d1f27ae946d5d61331787cc807b97fbee`)
- **Salida:** `data/processed/cruceros_2024_limpio.csv`, `data/processed/cruceros_2024_limpio.gpkg` y tabla `accidentes.cruceros`
- **Registros:** 2,787 crudos → 2,787 limpios · incidentes: 6,423

## Reglas aplicadas

| # | Código | Regla | Acción | Afectados | Antes | Después |
|---|---|---|---|---|---|---|
| 1 | R01 | Comparar GPKG y CSV del proyecto (deben ser idénticos) | verifica | 0 | 2,787 | 2,787 |
| 2 | R02 | Renombrar columnas a snake_case en español y agregar año | transforma | 2,787 | 2,787 | 2,787 |
| 3 | R03 | Corregir Ñ mal codificada ('¥' → 'Ñ') en nombres de calle | corrige | 3 | 2,787 | 2,787 |
| 4 | R04 | Normalizar texto (mayúsculas, espacios) | corrige | 0 | 2,787 | 2,787 |
| 5 | R05 | Verificar X/Y contra la geometría (manda la geometría) | verifica | 0 | 2,787 | 2,787 |
| 6 | R06 | Convertir coordenadas UTM 13N a latitud/longitud WGS84 | transforma | 2,787 | 2,787 | 2,787 |
| 7 | R07 | Marcar cruceros fuera del límite municipal | marca | 2 | 2,787 | 2,787 |
| 8 | R08 | Inferir zona SIN_DATO por los 5 cruceros vecinos más cercanos | corrige | 11 | 2,787 | 2,787 |
| 9 | R09 | Sector 0 → vacío y marcar sector_sin_dato | marca | 13 | 2,787 | 2,787 |
| 10 | R10 | PUNTOS_ID 99999 → vacío y marcar sin_id_crucero | marca | 1 | 2,787 | 2,787 |
| 11 | R11 | Marcar calle 1 = calle 2 (tramo, no intersección) | marca | 64 | 2,787 | 2,787 |
| 12 | R12 | Marcar cruceros distintos con la misma ubicación | marca | 2 | 2,787 | 2,787 |
| 13 | R13 | Marcar sectores repartidos en más de una zona | marca | 0 | 2,787 | 2,787 |
| 14 | R14 | Construir nombre del crucero ('A y B', orden alfabético) | transforma | 2,787 | 2,787 | 2,787 |
| 15 | R15 | Eliminar duplicados (mismo id_objeto o mismo crucero y ubicación) | corrige | 0 | 2,787 | 2,787 |
| 16 | R16 | Validar que el conteo de incidentes sea entero ≥ 1 | verifica | 0 | 2,787 | 2,787 |

## Registros marcados (se conservan; la app los reporta)

| Indicador | Cruceros | Incidentes en ellos |
|---|---|---|
| `zona_inferida` | 11 | 29 |
| `sector_sin_dato` | 13 | 36 |
| `sin_id_crucero` | 1 | 4 |
| `no_es_crucero` | 64 | 90 |
| `coord_repetida` | 2 | 7 |
| `sector_multizona` | 0 | 0 |
| `nombre_corregido` | 3 | 5 |
| `fuera_municipio` | 2 | 9 |

El registro limpio se enlaza con el original por `id_objeto` = `OBJECTID` (tabla `accidentes.raw_cruceros_2024`).
