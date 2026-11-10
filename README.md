# Accidentes viales en Ciudad Juárez

Sistema de análisis y visualización de incidentes viales en Ciudad Juárez, Chihuahua, a partir de los cruceros con conteo de incidentes de 2024 (IMIP). Proyecto de Tópicos Selectos de Ingeniería de Software, UACJ.

> Documento en construcción. La versión completa se escribe en la Etapa 6.

## Puesta en marcha

Requisitos: Python 3.14 y PostgreSQL 18 (no necesita PostGIS).

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env        # y escribe tu contraseña de PostgreSQL
```

Crea las bases `accidentes_viales` y `accidentes_viales_test` en PostgreSQL. Después:

```powershell
.venv\Scripts\python -m src.db --reset          # crea el esquema desde cero
.venv\Scripts\python -m src.limpieza.pipeline   # limpia los datos y los carga (se puede repetir)
```

## Documentación

- `docs/fuentes_de_datos.md`: origen de cada archivo
- `docs/reporte_etapa1_calidad.md`: exploración inicial y decisiones
- `docs/diccionario_de_datos.md`: tablas y columnas
- `docs/bitacora_limpieza.md`: efecto de cada regla de limpieza (se genera automáticamente)
