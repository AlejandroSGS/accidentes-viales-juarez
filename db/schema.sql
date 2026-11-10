-- Esquema de la base "Accidentes viales en Ciudad Juárez".
-- Recrear desde cero:  python -m src.db --reset
-- Todas las sentencias son idempotentes (se pueden ejecutar varias veces).

CREATE SCHEMA IF NOT EXISTS accidentes;
SET search_path TO accidentes;

-- Registro de cada ejecución del pipeline (trazabilidad)
CREATE TABLE IF NOT EXISTS ejecuciones_pipeline (
    id_ejecucion      SERIAL PRIMARY KEY,
    inicio            TIMESTAMPTZ NOT NULL,
    fin               TIMESTAMPTZ,
    archivo_origen    TEXT        NOT NULL,
    sha256_origen     CHAR(64)    NOT NULL,
    registros_crudos  INTEGER     NOT NULL,
    registros_limpios INTEGER
);

-- Datos crudos: copia fiel del archivo del proyecto (sin transformar)
CREATE TABLE IF NOT EXISTS raw_cruceros_2024 (
    "OBJECTID"   INTEGER PRIMARY KEY,
    "PUNTOS_ID"  INTEGER,
    "NOMBRE1"    TEXT,
    "NOMBRE2"    TEXT,
    "DicSegPub"  TEXT,
    "SECTOR"     INTEGER,
    "ACCI2024"   INTEGER,
    "X"          DOUBLE PRECISION,
    "Y"          DOUBLE PRECISION,
    id_ejecucion INTEGER NOT NULL REFERENCES ejecuciones_pipeline (id_ejecucion)
);

-- Catálogos
CREATE TABLE IF NOT EXISTS cat_zonas (
    zona TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS cat_sectores (
    sector         INTEGER PRIMARY KEY,
    zona_principal TEXT NOT NULL REFERENCES cat_zonas (zona),
    num_zonas      INTEGER NOT NULL      -- > 1 indica un sector repartido entre zonas
);

-- Datos limpios: un registro por crucero con su conteo de incidentes 2024
CREATE TABLE IF NOT EXISTS cruceros (
    id_objeto        INTEGER PRIMARY KEY,          -- = OBJECTID original (enlace con raw)
    id_crucero       INTEGER,                      -- = PUNTOS_ID; NULL si era 99999
    calle_1          TEXT    NOT NULL,
    calle_2          TEXT    NOT NULL,
    nombre_crucero   TEXT    NOT NULL,             -- calles en orden alfabético, "A y B"
    zona             TEXT    NOT NULL REFERENCES cat_zonas (zona),
    zona_original    TEXT    NOT NULL,             -- valor tal como venía (p. ej. SIN_DATO)
    sector           INTEGER REFERENCES cat_sectores (sector),  -- NULL si venía 0
    anio             SMALLINT NOT NULL,
    incidentes       INTEGER NOT NULL CHECK (incidentes >= 1),
    x_utm            DOUBLE PRECISION NOT NULL,
    y_utm            DOUBLE PRECISION NOT NULL,
    latitud          DOUBLE PRECISION NOT NULL,
    longitud         DOUBLE PRECISION NOT NULL,
    -- Indicadores de calidad (el registro se conserva; la app los reporta)
    zona_inferida    BOOLEAN NOT NULL,
    sector_sin_dato  BOOLEAN NOT NULL,
    sin_id_crucero   BOOLEAN NOT NULL,
    no_es_crucero    BOOLEAN NOT NULL,
    coord_repetida   BOOLEAN NOT NULL,
    sector_multizona BOOLEAN NOT NULL,
    nombre_corregido BOOLEAN NOT NULL,
    fuera_municipio  BOOLEAN NOT NULL,
    id_ejecucion     INTEGER NOT NULL REFERENCES ejecuciones_pipeline (id_ejecucion),
    CONSTRAINT chk_lat CHECK (latitud BETWEEN -90 AND 90),
    CONSTRAINT chk_lon CHECK (longitud BETWEEN -180 AND 180)
);

CREATE INDEX IF NOT EXISTS ix_cruceros_zona       ON cruceros (zona);
CREATE INDEX IF NOT EXISTS ix_cruceros_sector     ON cruceros (sector);
CREATE INDEX IF NOT EXISTS ix_cruceros_incidentes ON cruceros (incidentes DESC);
CREATE INDEX IF NOT EXISTS ix_cruceros_latlon     ON cruceros (latitud, longitud);

-- Bitácora de limpieza: una fila por regla y ejecución
CREATE TABLE IF NOT EXISTS bitacora_limpieza (
    id_ejecucion        INTEGER  NOT NULL REFERENCES ejecuciones_pipeline (id_ejecucion),
    orden               SMALLINT NOT NULL,
    codigo              TEXT     NOT NULL,
    regla               TEXT     NOT NULL,
    accion              TEXT     NOT NULL,         -- corrige / marca / verifica / transforma
    registros_afectados INTEGER  NOT NULL,
    registros_antes     INTEGER  NOT NULL,
    registros_despues   INTEGER  NOT NULL,
    PRIMARY KEY (id_ejecucion, orden)
);

-- ---------- Vistas para la aplicación ----------

CREATE OR REPLACE VIEW v_incidentes_por_zona AS
SELECT zona,
       COUNT(*)                                            AS cruceros,
       SUM(incidentes)                                     AS incidentes,
       ROUND(100.0 * SUM(incidentes) / SUM(SUM(incidentes)) OVER (), 2) AS porcentaje
FROM cruceros
GROUP BY zona;

CREATE OR REPLACE VIEW v_incidentes_por_sector AS
SELECT sector,
       MIN(zona)       AS zona,
       COUNT(*)        AS cruceros,
       SUM(incidentes) AS incidentes
FROM cruceros
WHERE sector IS NOT NULL
GROUP BY sector;

CREATE OR REPLACE VIEW v_resumen_calidad AS
SELECT COUNT(*)                                   AS total_cruceros,
       SUM(incidentes)                            AS total_incidentes,
       COUNT(*) FILTER (WHERE zona_inferida)      AS zona_inferida,
       COUNT(*) FILTER (WHERE sector_sin_dato)    AS sector_sin_dato,
       COUNT(*) FILTER (WHERE sin_id_crucero)     AS sin_id_crucero,
       COUNT(*) FILTER (WHERE no_es_crucero)      AS no_es_crucero,
       COUNT(*) FILTER (WHERE coord_repetida)     AS coord_repetida,
       COUNT(*) FILTER (WHERE sector_multizona)   AS sector_multizona,
       COUNT(*) FILTER (WHERE nombre_corregido)   AS nombre_corregido,
       COUNT(*) FILTER (WHERE fuera_municipio)    AS fuera_municipio,
       SUM(incidentes) FILTER (WHERE fuera_municipio) AS incidentes_fuera_municipio
FROM cruceros;

CREATE OR REPLACE VIEW v_ultima_bitacora AS
SELECT b.*
FROM bitacora_limpieza b
WHERE b.id_ejecucion = (SELECT MAX(id_ejecucion) FROM ejecuciones_pipeline WHERE fin IS NOT NULL);
