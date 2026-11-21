CREATE TABLE IF NOT EXISTS silver.lectura_vivo (
    inverter         smallint     NOT NULL,
    ts               timestamptz  NOT NULL,
    voltaje_v        numeric(7,2) NOT NULL,
    potencia_linea_w numeric(10,2) NOT NULL,
    modo_sim         text         NOT NULL,      
    PRIMARY KEY (inverter, ts)
);
CREATE INDEX IF NOT EXISTS ix_vivo_ts ON silver.lectura_vivo (ts DESC);

CREATE TABLE IF NOT EXISTS silver.control_simulador (
    id          smallint    PRIMARY KEY CHECK (id = 1),
    modo        text        NOT NULL CHECK (modo IN ('normal', 'corte', 'silencio')),
    actualizado timestamptz NOT NULL DEFAULT now()
);
INSERT INTO silver.control_simulador (id, modo) VALUES (1, 'normal') ON CONFLICT DO NOTHING;

CREATE OR REPLACE VIEW gold.vw_lectura_vivo AS
SELECT l.ts, l.inverter AS inverter_key, i.nombre, l.voltaje_v, l.potencia_linea_w, l.modo_sim
FROM silver.lectura_vivo l
JOIN gold.dim_inversor i ON i.inverter_key = l.inverter;