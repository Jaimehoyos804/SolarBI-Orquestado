SELECT
    'analog_measurements' AS tabla,
    COUNT(*) AS total_registros,
    COUNT(DISTINCT inverter) AS cantidad_inversores,
    MIN(read_ts) AS fecha_minima_unix,
    MAX(read_ts) AS fecha_maxima_unix,
    datetime(MIN(read_ts), 'unixepoch') AS primera_fecha,
    datetime(MAX(read_ts), 'unixepoch') AS ultima_fecha
FROM analog_measurements

UNION ALL

SELECT
    'statistics',
    COUNT(*),
    COUNT(DISTINCT inverter),
    MIN(read_ts),
    MAX(read_ts),
    datetime(MIN(read_ts), 'unixepoch'),
    datetime(MAX(read_ts), 'unixepoch')
FROM statistics;



SELECT
    read_ts,
    datetime(read_ts, 'unixepoch') AS fecha,
    inverter,
    battsoc,
    battvolt,
    battcurr,
    pv1power,
    outsumw,
    gridpowerw_a
FROM analog_measurements
ORDER BY read_ts
LIMIT 10;

--Frecuencia de Medicion
WITH mediciones AS (
    SELECT
        inverter,
        read_ts,
        LAG(read_ts) OVER (
            PARTITION BY inverter
            ORDER BY read_ts
        ) AS lectura_anterior
    FROM analog_measurements
),
intervalos AS (
    SELECT
        inverter,
        read_ts - lectura_anterior AS segundos_entre_lecturas
    FROM mediciones
    WHERE lectura_anterior IS NOT NULL
)
SELECT
    inverter,
    COUNT(*) AS intervalos,
    ROUND(AVG(segundos_entre_lecturas), 2) AS promedio_segundos,
    MIN(segundos_entre_lecturas) AS minimo_segundos,
    MAX(segundos_entre_lecturas) AS maximo_segundos,
    SUM(CASE WHEN segundos_entre_lecturas > 600 THEN 1 ELSE 0 END)
        AS intervalos_mayores_10_min
FROM intervalos
GROUP BY inverter
ORDER BY inverter;


--Buscar valores NULOS o ceros
SELECT
    COUNT(*) AS total_registros,

    SUM(CASE WHEN battsoc IS NULL THEN 1 ELSE 0 END) AS soc_nulos,
    SUM(CASE WHEN battsoc = 0 THEN 1 ELSE 0 END) AS soc_ceros,

    SUM(CASE WHEN pv1power IS NULL THEN 1 ELSE 0 END) AS pv_nulos,
    SUM(CASE WHEN pv1power = 0 THEN 1 ELSE 0 END) AS pv_ceros,

    SUM(CASE WHEN outsumw IS NULL THEN 1 ELSE 0 END) AS salida_nulos,
    SUM(CASE WHEN outsumw = 0 THEN 1 ELSE 0 END) AS salida_ceros,

    SUM(CASE WHEN gridpowerw_a IS NULL THEN 1 ELSE 0 END) AS red_nulos,
    SUM(CASE WHEN gridpowerw_a = 0 THEN 1 ELSE 0 END) AS red_ceros

FROM analog_measurements;


--Clasificar Intervalos 
WITH mediciones AS (
    SELECT
        inverter,
        read_ts,
        LAG(read_ts) OVER (
            PARTITION BY inverter
            ORDER BY read_ts
        ) AS lectura_anterior
    FROM analog_measurements
),
intervalos AS (
    SELECT
        inverter,
        read_ts - lectura_anterior AS segundos
    FROM mediciones
    WHERE lectura_anterior IS NOT NULL
)
SELECT
    inverter,
    COUNT(*) AS total_intervalos,

    SUM(CASE WHEN segundos <= 1 THEN 1 ELSE 0 END) AS hasta_1_segundo,

    SUM(CASE WHEN segundos > 1 AND segundos <= 60
        THEN 1 ELSE 0 END) AS entre_1_y_60_segundos,

    SUM(CASE WHEN segundos > 60 AND segundos <= 120
        THEN 1 ELSE 0 END) AS entre_60_y_120_segundos,

    SUM(CASE WHEN segundos > 120 AND segundos <= 600
        THEN 1 ELSE 0 END) AS entre_2_y_10_minutos,

    SUM(CASE WHEN segundos > 600
        THEN 1 ELSE 0 END) AS mas_de_10_minutos

FROM intervalos
GROUP BY inverter
ORDER BY inverter;

--Intervalos mas largos
WITH mediciones AS (
    SELECT
        inverter,
        read_ts,
        LAG(read_ts) OVER (
            PARTITION BY inverter
            ORDER BY read_ts
        ) AS lectura_anterior
    FROM analog_measurements
)
SELECT
    inverter,
    datetime(lectura_anterior, 'unixepoch') AS ultima_lectura,
    datetime(read_ts, 'unixepoch') AS siguiente_lectura,
    ROUND(read_ts - lectura_anterior, 2) AS segundos_sin_lectura,
    ROUND((read_ts - lectura_anterior) / 3600.0, 2) AS horas_sin_lectura
FROM mediciones
WHERE lectura_anterior IS NOT NULL
ORDER BY segundos_sin_lectura DESC
LIMIT 10;

--Mediciones duplicadas
SELECT
    inverter,
    COUNT(*) AS filas,
    COUNT(DISTINCT read_ts) AS timestamps_distintos,
    COUNT(*) - COUNT(DISTINCT read_ts) AS filas_repetidas
FROM analog_measurements
GROUP BY inverter;


--Revisar hueco de no genracíon
WITH limites AS (
    SELECT
        unixepoch('2025-08-03 04:58:15') AS inicio,
        unixepoch('2025-08-29 08:29:25') AS fin
)
SELECT
    'analog_measurements' AS tabla,
    COUNT(*) AS registros_en_periodo
FROM analog_measurements, limites
WHERE read_ts > inicio AND read_ts < fin

UNION ALL

SELECT 'statistics', COUNT(*)
FROM statistics, limites
WHERE read_ts > inicio AND read_ts < fin

UNION ALL

SELECT 'status', COUNT(*)
FROM status, limites
WHERE read_ts > inicio AND read_ts < fin

UNION ALL

SELECT 'fault_history', COUNT(*)
FROM fault_history, limites
WHERE read_ts > inicio AND read_ts < fin

UNION ALL

SELECT 'settings', COUNT(*)
FROM settings, limites
WHERE read_ts > inicio AND read_ts < fin

UNION ALL

SELECT 'specs', COUNT(*)
FROM specs, limites
WHERE read_ts > inicio AND read_ts < fin

UNION ALL

SELECT 'totals', COUNT(*)
FROM totals, limites
WHERE read_ts > inicio AND read_ts < fin;



--7
SELECT
    'Antes del intervalo' AS periodo,
    datetime(MAX(read_ts), 'unixepoch') AS ultima_lectura,
    MAX(read_ts) AS timestamp
FROM analog_measurements
WHERE read_ts < 1754197095.514001

UNION ALL

SELECT
    'Después del intervalo',
    datetime(MIN(read_ts), 'unixepoch'),
    MIN(read_ts)
FROM analog_measurements
WHERE read_ts > 1756456165.514001;


SELECT
    inverter,
    COUNT(*) AS registros,
    datetime(MIN(read_ts), 'unixepoch') AS primera_lectura,
    datetime(MAX(read_ts), 'unixepoch') AS ultima_lectura
FROM analog_measurements
WHERE read_ts BETWEEN 1754197095.514001 AND 1756456165.514001
GROUP BY inverter;

--estado
PRAGMA table_info(status);

--Ultimo estado conocido 
WITH lecturas AS (
    SELECT
        *,
        'ANTES' AS momento,
        ROW_NUMBER() OVER (
            PARTITION BY inverter
            ORDER BY read_ts DESC
        ) AS posicion
    FROM status
    WHERE read_ts < 1754197095.514001

    UNION ALL

    SELECT
        *,
        'DESPUES' AS momento,
        ROW_NUMBER() OVER (
            PARTITION BY inverter
            ORDER BY read_ts ASC
        ) AS posicion
    FROM status
    WHERE read_ts > 1756458670.882613
)
SELECT
    inverter,
    momento,
    datetime(read_ts, 'unixepoch') AS fecha,
    startupstatus,
    outstatus,
    chgstatus,
    sysstateflag,
    sysalarmflag,
    deroperationstate,
    derconnectstate,
    deralarmstatus,
    derinverterstate,
    derbattstate
FROM lecturas
WHERE posicion = 1
ORDER BY inverter, momento;


---
SELECT
    inverter,
    chgstatus,
    COUNT(*) AS cantidad_registros,
    ROUND(
        100.0 * COUNT(*) /
        SUM(COUNT(*)) OVER (PARTITION BY inverter),
        2
    ) AS porcentaje,
    datetime(MIN(read_ts), 'unixepoch') AS primera_aparicion,
    datetime(MAX(read_ts), 'unixepoch') AS ultima_aparicion
FROM status
GROUP BY inverter, chgstatus
ORDER BY inverter, chgstatus;

--
SELECT
    id,
    datetime(recorded, 'unixepoch') AS fecha_registro,
    datetime(start, 'unixepoch') AS inicio_evento,
    datetime(end, 'unixepoch') AS fin_evento,
    value
FROM context
WHERE
    recorded BETWEEN 1754190000 AND 1756460000
    OR start BETWEEN 1754190000 AND 1756460000
    OR end BETWEEN 1754190000 AND 1756460000
ORDER BY recorded;


SELECT * FROM context c 

---
SELECT
    id,
    json_extract(value, '$.context_type') AS tipo_evento,
    json_extract(value, '$.device') AS dispositivo,
    json_extract(value, '$.inverter') AS inversor,
    value
FROM context
WHERE json_extract(value, '$.context_type') = 'data_gap'
ORDER BY recorded
LIMIT 10;

--Validar las anomalias en las diferencias horrarias
SELECT
    id,
    json_extract(value, '$.inverter') AS inversor,
    datetime(start, 'unixepoch') AS inicio_sql,
    datetime("end", 'unixepoch') AS fin_sql,

    ROUND("end" - start, 3) AS segundos_calculados,

    ROUND(
        json_extract(value, '$.gap_seconds'), 3
    ) AS segundos_json,

    ROUND(
        ("end" - start) -
        json_extract(value, '$.gap_seconds'), 3
    ) AS diferencia,

    json_extract(value, '$.previous_sample_local') AS muestra_anterior,
    json_extract(value, '$.next_sample_local') AS muestra_siguiente

FROM context
WHERE json_extract(value, '$.context_type') = 'data_gap'
ORDER BY ("end" - start) DESC
LIMIT 10;

--validar zona horraria
SELECT
    read_ts,
    datetime(read_ts, 'unixepoch') AS fecha_utc_sql,
    strftime(
        '%Y-%m-%d %H:%M:%S',
        read_ts,
        'unixepoch',
        '+8 hours'
    ) AS fecha_mas_8h
FROM analog_measurements
WHERE inverter = 1
  AND read_ts BETWEEN
      1754196984 AND 1756458671
ORDER BY read_ts
LIMIT 10;


------------COMPROBAR NULOS
SELECT
    inverter,
    date(read_ts, 'unixepoch') AS fecha,
    COUNT(*) AS total_registros,

    SUM(CASE
        WHEN generatedacpowertoday IS NULL
         AND batchgenergytoday IS NULL
         AND batdischgenergytoday IS NULL
         AND pvgeneratenergytoday IS NULL
         AND usedenergytoday IS NULL
         AND linechgenergytday IS NULL
         AND loadconsumlinetday IS NULL
        THEN 1 ELSE 0
    END) AS todas_diarias_null,

    SUM(CASE
        WHEN generatedacpowertoday IS NOT NULL
         AND batchgenergytoday IS NOT NULL
         AND batdischgenergytoday IS NOT NULL
         AND pvgeneratenergytoday IS NOT NULL
         AND usedenergytoday IS NOT NULL
         AND linechgenergytday IS NOT NULL
         AND loadconsumlinetday IS NOT NULL
        THEN 1 ELSE 0
    END) AS todas_diarias_completas,

    SUM(CASE
        WHEN generatedacpowertoday IS NULL
          OR batchgenergytoday IS NULL
          OR batdischgenergytoday IS NULL
          OR pvgeneratenergytoday IS NULL
          OR usedenergytoday IS NULL
          OR linechgenergytday IS NULL
          OR loadconsumlinetday IS NULL
        THEN 1 ELSE 0
    END) AS alguna_diaria_null

FROM statistics
GROUP BY inverter, date(read_ts, 'unixepoch')
HAVING todas_diarias_null > 0
ORDER BY inverter, fecha;

