CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

CREATE TABLE IF NOT EXISTS silver.energia_red_hora (
    inverter                  smallint        NOT NULL,
    hour_local                timestamptz     NOT NULL,
    positive_power_unit_hours numeric(18,6)   NOT NULL,
    negative_power_unit_hours numeric(18,6)   NOT NULL,
    net_power_unit_hours      numeric(18,6)   NOT NULL,
    coverage_minutes          numeric(5,2)    NOT NULL CHECK (coverage_minutes BETWEEN 0 AND 60),
    contributing_segments     integer         NOT NULL CHECK (contributing_segments > 0),
    PRIMARY KEY (inverter, hour_local),
    CHECK (abs(net_power_unit_hours - (positive_power_unit_hours - negative_power_unit_hours)) < 0.00001)
);


CREATE TABLE IF NOT EXISTS gold.dim_inversor (
    inverter_key smallint PRIMARY KEY,
    nombre       text NOT NULL
);
INSERT INTO gold.dim_inversor VALUES (1, 'Inversor 1'), (2, 'Inversor 2')
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS gold.dim_fecha (
    fecha_key        integer PRIMARY KEY,         
    fecha            date    NOT NULL UNIQUE,
    anio             smallint NOT NULL,
    trimestre        smallint NOT NULL,
    mes              smallint NOT NULL,
    nombre_mes       text NOT NULL,
    dia              smallint NOT NULL,
    dia_semana       smallint NOT NULL,            
    nombre_dia       text NOT NULL,
    es_fin_de_semana boolean NOT NULL
);
INSERT INTO gold.dim_fecha
SELECT to_char(d, 'YYYYMMDD')::int, d::date,
       extract(year from d), extract(quarter from d), extract(month from d),
       (ARRAY['enero','febrero','marzo','abril','mayo','junio','julio','agosto',
              'septiembre','octubre','noviembre','diciembre'])[extract(month from d)::int],
       extract(day from d), extract(isodow from d),
       (ARRAY['lunes','martes','miércoles','jueves','viernes','sábado','domingo'])[extract(isodow from d)::int],
       extract(isodow from d) >= 6
FROM generate_series('2025-07-01'::date, '2026-12-31'::date, interval '1 day') AS d
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS gold.dim_hora (          
    hora_key smallint PRIMARY KEY CHECK (hora_key BETWEEN 0 AND 23),
    franja   text NOT NULL,
    es_hora_solar boolean NOT NULL
);
INSERT INTO gold.dim_hora
SELECT h,
       CASE WHEN h < 6 THEN 'madrugada' WHEN h < 12 THEN 'mañana'
            WHEN h < 18 THEN 'tarde' ELSE 'noche' END,
       h BETWEEN 6 AND 17
FROM generate_series(0, 23) AS h
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS gold.fact_energia_red_hora (
    inverter_key              smallint     NOT NULL REFERENCES gold.dim_inversor,
    fecha_key                 integer      NOT NULL REFERENCES gold.dim_fecha,
    hora_key                  smallint     NOT NULL REFERENCES gold.dim_hora,
    hour_local                timestamptz  NOT NULL,
    positive_power_unit_hours numeric(18,6) NOT NULL,
    negative_power_unit_hours numeric(18,6) NOT NULL,
    net_power_unit_hours      numeric(18,6) NOT NULL,
    coverage_minutes          numeric(5,2)  NOT NULL,
    cobertura_pct numeric(5,2) GENERATED ALWAYS AS (round(coverage_minutes / 60 * 100, 2)) STORED,
    PRIMARY KEY (inverter_key, hour_local)
);
CREATE INDEX IF NOT EXISTS ix_fact_fecha ON gold.fact_energia_red_hora (fecha_key, hora_key);