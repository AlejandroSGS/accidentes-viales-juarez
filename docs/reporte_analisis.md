# Etapa 3 — Análisis estadístico y espacial

> Generado con `python -m src.analisis.reporte` a partir de la tabla `accidentes.cruceros`.
> **Aviso:** los resultados describen dónde se concentran los registros de 2024; **no determinan las causas** de los accidentes.

## 1. Resumen

- **2,787 cruceros** con **6,423 incidentes** registrados en 2024.
- Promedio: 2.30 incidentes por crucero; mediana: 1; máximo: 49.
- 1,853 cruceros (66.5 %) tuvieron un solo incidente.
- Comparación con el documento del proyecto: sus totales de referencia cubren 2018–2022 y sus porcentajes por tipo son de 2022. Estos datos son de 2024 y no traen tipo de incidente, así que **no hay cifra de referencia contra la cual compararlos**. El total de 2024 (6,423) coincide con la suma del shapefile `ACCI2024` del IMIP.

## 2. Concentración

- El **3.0 %** de los cruceros acumula el 25 % de los incidentes; el **12.7 %** acumula la mitad, y el **53.9 %** acumula el 80 %.
- Índice de Gini: **0.481** (0 = repartidos por igual entre cruceros, 1 = todos en un solo crucero).

| Incidentes por crucero | Cruceros | Incidentes | % cruceros | % incidentes |
|---|---|---|---|---|
| 1 | 1,853 | 1,853 | 66.49 % | 28.85 % |
| 2 | 391 | 782 | 14.03 % | 12.17 % |
| 3–4 | 269 | 897 | 9.65 % | 13.97 % |
| 5–9 | 167 | 1,052 | 5.99 % | 16.38 % |
| 10–19 | 79 | 1,012 | 2.83 % | 15.76 % |
| 20 o más | 28 | 827 | 1.00 % | 12.88 % |

## 3. Cruceros con más incidentes

| # | Crucero | Zona | Sector | Incidentes | % del total |
|---|---|---|---|---|---|
| 1 | PASEO DE LA VICTORIA y TEOFILO BORUNDA | SUR | 603 | 49 | 0.76 % |
| 2 | BOULEVARD ZARAGOZA y DE LAS TORRES | SUR | 612 | 44 | 0.69 % |
| 3 | BOULEVARD MANUEL TALAMAS CAMANDARI y DE LAS TORRES | SUR | 626 | 39 | 0.61 % |
| 4 | PEDRO ROSALES DE LEON y TECNOLOGICO | UNIVERSIDAD | 217 | 37 | 0.58 % |
| 5 | ADOLFO LOPEZ MATEOS y PASEO TRIUNFO DE LA REPUBLICA | UNIVERSIDAD | 205 | 35 | 0.54 % |
| 5 | TECNOLOGICO y TEOFILO BORUNDA | UNIVERSIDAD | 220 | 35 | 0.54 % |
| 7 | BOULEVARD INDEPENDENCIA y JUAREZ A PORVENIR | VALLE | 503 | 34 | 0.53 % |
| 7 | FRANCISCO VILLAREAL y TEOFILO BORUNDA | ORIENTE | 419 | 34 | 0.53 % |
| 9 | DE LA RAZA y TECNOLOGICO | ORIENTE | 405 | 33 | 0.51 % |
| 9 | DE LAS TORRES y MANUEL GOMEZ MORIN | ORIENTE | 416 | 33 | 0.51 % |
| 11 | BOULEVARD INDEPENDENCIA y MANUEL TALAMAS CAMANDARI | VALLE | 520 | 31 | 0.48 % |
| 12 | BOULEVARD INDEPENDENCIA y SANTIAGO TRONCOSO | VALLE | 513 | 30 | 0.47 % |
| 13 | ABRAHAM LINCOLN y BENEMERITO DE LAS AMERICAS | UNIVERSIDAD | 201 | 29 | 0.45 % |
| 14 | BOULEVARD CUATRO SIGLOS y FRANCISCO VILLARREAL TORRES | ORIENTE | 407 | 27 | 0.42 % |
| 14 | BOULEVARD INDEPENDENCIA y BOULEVARD ZARAGOZA | VALLE | 508 | 27 | 0.42 % |

## 4. Por zona de Seguridad Pública

| Zona | Cruceros | Incidentes | % del total | Incidentes por crucero |
|---|---|---|---|---|
| SUR | 585 | 1,527 | 23.77 % | 2.61 |
| VALLE | 663 | 1,437 | 22.37 % | 2.17 |
| UNIVERSIDAD | 490 | 1,378 | 21.45 % | 2.81 |
| ORIENTE | 263 | 847 | 13.19 % | 3.22 |
| PONIENTE | 382 | 647 | 10.07 % | 1.69 |
| CENTRO | 404 | 587 | 9.14 % | 1.45 |

Incluye las 11 zonas inferidas (29 incidentes). Las zonas tienen tamaños distintos, por eso se muestra también el promedio por crucero.

## 5. Sectores con más incidentes (10 primeros de 161)

| Sector | Cruceros | Incidentes | % del total | Incidentes por crucero |
|---|---|---|---|---|
| 201 | 22 | 166 | 2.58 % | 7.55 |
| 620 | 37 | 133 | 2.07 % | 3.59 |
| 626 | 41 | 125 | 1.95 % | 3.05 |
| 220 | 32 | 121 | 1.88 % | 3.78 |
| 416 | 22 | 113 | 1.76 % | 5.14 |
| 601 | 33 | 105 | 1.63 % | 3.18 |
| 217 | 14 | 105 | 1.63 % | 7.50 |
| 537 | 50 | 93 | 1.45 % | 1.86 |
| 205 | 26 | 92 | 1.43 % | 3.54 |
| 208 | 41 | 90 | 1.40 % | 2.20 |

## 6. Densidad Kernel (KDE)

Cada crucero pesa según su número de incidentes. Parámetros: suavizado gaussiano de **500 m** (≈ 4–5 cuadras) y malla de 200 m. Se excluyen los 2 cruceros fuera del municipio. La densidad se expresa en incidentes por km².

- Densidad máxima: **74.2 incidentes/km²**, alrededor de (31.7361, -106.4482).
- Celdas en el 0.5 % más denso: 59.

Cruceros ubicados en las zonas de mayor densidad (no siempre son los de más incidentes propios: la densidad también cuenta a los vecinos):

| Crucero | Zona | Incidentes | Densidad (inc/km²) |
|---|---|---|---|
| ADOLFO LOPEZ MATEOS y PASEO TRIUNFO DE LA REPUBLICA | UNIVERSIDAD | 35 | 73.3 |
| ALCIBIADES y PASEO TRIUNFO DE LA REPUBLICA | UNIVERSIDAD | 3 | 72.7 |
| ADOLFO LOPEZ MATEOS y JOSE BORUNDA | UNIVERSIDAD | 3 | 71.6 |
| PASEO TRIUNFO DE LA REPUBLICA y PLATON | UNIVERSIDAD | 1 | 70.6 |
| ADOLFO LOPEZ MATEOS y MEJIA | UNIVERSIDAD | 1 | 68.9 |
| BOULEVARD ZARAGOZA y DE LAS TORRES | SUR | 44 | 68.5 |
| ADOLFO LOPEZ MATEOS y VICENTE GUERRERO | UNIVERSIDAD | 9 | 68.3 |
| ADOLFO DE LA HUERTA y PASEO TRIUNFO DE LA REPUBLICA | UNIVERSIDAD | 11 | 67.8 |
| ADOLFO DE LA HUERTA y VICENTE GUERRERO | UNIVERSIDAD | 3 | 67.8 |
| 16 DE SEPTIEMBRE y BENITO JUAREZ | CENTRO | 1 | 67.6 |

## 7. Modelo K-means ponderado (Anderson, 2009)

Agrupa los cruceros por cercanía, con cada crucero pesado por sus incidentes. Es **no supervisado**: describe zonas, no predice.

**Elección de k:** se probaron k = 2 a 12.

| k | Inercia (km²) | Silueta |
|---|---|---|
| 2 | 145,771 | 0.504 |
| 3 | 103,420 | 0.399 |
| 4 | 83,079 | 0.396 |
| 5 | 65,975 | 0.374 |
| 6 | 56,030 | 0.369 |
| 7 | 48,987 | 0.355 |
| 8 | 43,994 | 0.342 |
| 9 | 39,074 | 0.348 |
| 10 | 35,150 | 0.366 |
| 11 | 32,037 | 0.359 |
| 12 | 29,363 | 0.364 |

La silueta (qué tan separados quedan los grupos) es mayor con k = 2, pero dos grupos no sirven para describir la ciudad. De k = 3 a 12 baja poco y la inercia no muestra un "codo" claro. Se eligió **k = 6** porque tiene una silueta similar a k = 4 o 5 y es el mismo número de zonas de Seguridad Pública, lo que permite compararlas. El resultado es idéntico con otra semilla aleatoria (índice de Rand ajustado = 1.0). En la app se puede cambiar k.

**Perfil de los grupos** (1 = el de más incidentes):

| Grupo | Cruceros | Incidentes | % del total | Inc. por crucero | Área (km²) | Inc. por km² | Zona predominante | Crucero principal |
|---|---|---|---|---|---|---|---|---|
| 1 | 503 | 1,489 | 23.21 % | 2.96 | 41.4 | 35.9 | UNIVERSIDAD | PEDRO ROSALES DE LEON y TECNOLOGICO |
| 2 | 376 | 1,106 | 17.24 % | 2.94 | 50.8 | 21.8 | ORIENTE | PASEO DE LA VICTORIA y TEOFILO BORUNDA |
| 3 | 527 | 1,099 | 17.13 % | 2.09 | 95.1 | 11.6 | SUR | TECNOLOGICO y TEOFILO BORUNDA |
| 4 | 595 | 941 | 14.67 % | 1.58 | 90.8 | 10.4 | CENTRO | EJE VIAL JUAN GABRIEL y MUNICIPIO LIBRE |
| 5 | 459 | 926 | 14.44 % | 2.02 | 94.8 | 9.8 | VALLE | BOULEVARD INDEPENDENCIA y MANUEL TALAMAS CAMANDARI |
| 6 | 325 | 853 | 13.30 % | 2.62 | 155.9 | 5.5 | SUR | BOULEVARD MANUEL TALAMAS CAMANDARI y DE LAS TORRES |

El área es la del polígono que envuelve los cruceros del grupo.

## 8. Lo que no se puede analizar con estos datos

- **Patrones temporales** (mes, día, hora) y **comparación de periodos**: el archivo solo tiene el total de 2024 por crucero.
- **Tipos de incidente** (choque, atropello, volcadura): no vienen en el archivo.
- **Autocorrelación espacial (Moran, Getis-Ord Gi\*)**: es opcional y queda como trabajo futuro.
