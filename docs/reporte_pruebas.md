# Etapa 5 — Reporte de pruebas

**Resultado (2026-11-09):** 61 pruebas, 61 aprobadas, 0 fallidas, en ~19 s.

```powershell
.venv\Scripts\python -m pytest            # todas
.venv\Scripts\python -m pytest -m "not db" # solo las que no necesitan PostgreSQL
```

## Reglas de seguridad de las pruebas

- Los **datos sintéticos** están en `tests/conftest.py`, marcados como tales en el código. Son de 5 o 6 registros inventados y nunca se cargan en la base real.
- Las pruebas con base de datos usan **solo** la base de pruebas (`PGDATABASE_TEST`). La borran, la recrean desde `db/` y la llenan con el pipeline real.
- En modo prueba el pipeline no sobrescribe `data/processed/` ni `docs/bitacora_limpieza.md`. Se verificó con sumas MD5 antes y después de correr las pruebas.
- La app se prueba contra la base de pruebas con la variable `ACCIDENTES_BD_PRUEBAS=1`.

## Qué se probó

| Archivo | Pruebas | Qué verifica |
|---|---|---|
| `test_reglas.py` | 24 | Cada una de las 16 reglas de limpieza con datos sintéticos: corrección de `¥`, normalización de texto, conversión a lat/lon, fuera del municipio, inferencia de zona (mayoría de vecinos y desempate), sector 0, ID 99999, tramos de calle, coordenadas repetidas, sectores en varias zonas, nombre del crucero, duplicados y conteos inválidos (0, negativo, decimal y vacío). También verifica que las reglas no modifican los datos de entrada. |
| `test_analisis.py` | 15 | Resumen, ranking con empates, agregados por zona y sector, distribución, curva de Pareto e índice de Gini contra **resultados calculados a mano**. KDE: integra al total de incidentes y excluye los puntos fuera del municipio. K-means: separa dos grupos obvios, es reproducible, perfil y silueta. |
| `test_integridad.py` | 11 | Sobre los datos reales procesados en la base de pruebas: mismos registros e incidentes que el original (2,787 / 6,423); sin duplicados; cada registro limpio enlaza con su original; conteos ≥ 1; zonas y sectores dentro del catálogo; coordenadas dentro del municipio salvo las marcadas; marcas de calidad esperadas; bitácora completa (R01–R16); **idempotencia** (correr dos veces no duplica); las vistas cuadran con la tabla; las consultas son parametrizadas (un texto con `' OR '1'='1` no devuelve nada). |
| `test_app.py` | 11 | Prueba de humo: la app arranca con las cifras correctas y el aviso de no causalidad; las 9 páginas se dibujan sin errores; los filtros compartidos funcionan (Oriente con 3 o más incidentes → 630 incidentes en 79 cruceros). |

## Qué no se probó (y por qué)

- **Aspecto visual de mapas y gráficas.** Las pruebas automáticas confirman que se generan sin errores, pero no cómo se ven. Se revisaron a mano en Chrome las páginas Mapa y Zonas K-means: se corrigió un encuadre muy alejado y un cálculo de densidad lento (24 s → 2 s).
- **Accesibilidad con lector de pantalla y contraste.** No se probó con herramientas; se cuidó en el diseño (valores escritos en las gráficas, patrones, paleta para daltonismo, números en los marcadores).
- **Rendimiento con muchos usuarios** y comportamiento en otros sistemas operativos: solo se probó en Windows 11 con un usuario.
- **Descarga desde el servicio ArcGIS del IMIP** (`src/ingesta/arcgis_imip.py`): depende de un servidor externo; se ejecutó a mano en la Etapa 1. Del IMIP solo se usa el límite municipal.
- **Exactitud de los datos de origen:** las pruebas verifican que la limpieza es correcta y trazable, no que el registro oficial sea completo o esté bien capturado.
