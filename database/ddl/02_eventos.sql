CREATE TABLE IF NOT EXISTS silver.context_evento (
    id           bigint       PRIMARY KEY,         
    start_ts     timestamptz  NOT NULL,
    end_ts       timestamptz  NOT NULL,
    context_type text         NOT NULL,
    inverter     smallint,                         
    value        jsonb        NOT NULL            
);
CREATE INDEX IF NOT EXISTS ix_ctx_tipo_inicio ON silver.context_evento (context_type, start_ts);

CREATE TABLE IF NOT EXISTS gold.fact_evento_operativo (
    evento_id      bigint       PRIMARY KEY,
    inverter_key   smallint     REFERENCES gold.dim_inversor,   
    fecha_key      integer      NOT NULL REFERENCES gold.dim_fecha,
    hora_key       smallint     NOT NULL REFERENCES gold.dim_hora,
    context_type   text         NOT NULL,
    inicio         timestamptz  NOT NULL,
    fin            timestamptz  NOT NULL,
    duracion_horas numeric(10,2) NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_fact_evento_tipo ON gold.fact_evento_operativo (context_type, fecha_key);