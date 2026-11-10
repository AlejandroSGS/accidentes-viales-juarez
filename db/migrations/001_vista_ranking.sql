-- 001: ranking de cruceros por número de incidentes (Etapa 3)
SET search_path TO accidentes;

CREATE OR REPLACE VIEW v_ranking_cruceros AS
SELECT RANK() OVER (ORDER BY incidentes DESC)                         AS posicion,
       id_objeto,
       nombre_crucero,
       zona,
       sector,
       incidentes,
       ROUND(100.0 * incidentes / SUM(incidentes) OVER (), 2)         AS porcentaje,
       ROUND(100.0 * SUM(incidentes) OVER (ORDER BY incidentes DESC, id_objeto)
             / SUM(incidentes) OVER (), 2)                            AS porcentaje_acumulado,
       latitud,
       longitud
FROM cruceros;
