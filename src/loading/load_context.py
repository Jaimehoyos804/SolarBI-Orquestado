import json
from collections import Counter
from datetime import datetime, timezone

from src.extraction.sqlite_reader import get_connection
from src.loading.load_hourly import connect

TIPOS = (
    "grid_unavailable_or_islanded", "power_transition", "data_gap",
    "battery_charging", "battery_discharging", "high_ac_load",
    "unexpected_shutdown", "telemetry_quality_note", "data_coverage_summary",
)

UPSERT_SILVER = """
INSERT INTO silver.context_evento (id, start_ts, end_ts, context_type, inverter, value)
VALUES (%s, %s, %s, %s, %s, %s::jsonb)
ON CONFLICT (id) DO UPDATE SET
  start_ts = EXCLUDED.start_ts, end_ts = EXCLUDED.end_ts,
  context_type = EXCLUDED.context_type, inverter = EXCLUDED.inverter,
  value = EXCLUDED.value
"""

UPSERT_GOLD = """
INSERT INTO gold.fact_evento_operativo
  (evento_id, inverter_key, fecha_key, hora_key, context_type, inicio, fin, duracion_horas)
SELECT e.id,
       CASE WHEN e.inverter IN (1, 2) THEN e.inverter END,
       d.fecha_key,
       extract(hour FROM e.start_ts AT TIME ZONE 'Asia/Shanghai')::smallint,
       e.context_type, e.start_ts, e.end_ts,
       round(extract(epoch FROM e.end_ts - e.start_ts) / 3600.0, 2)
FROM silver.context_evento e
JOIN gold.dim_fecha d ON d.fecha = (e.start_ts AT TIME ZONE 'Asia/Shanghai')::date
ON CONFLICT (evento_id) DO UPDATE SET
  inverter_key = EXCLUDED.inverter_key, fecha_key = EXCLUDED.fecha_key,
  hora_key = EXCLUDED.hora_key, context_type = EXCLUDED.context_type,
  inicio = EXCLUDED.inicio, fin = EXCLUDED.fin,
  duracion_horas = EXCLUDED.duracion_horas
"""


def leer_fuente():
    marcas = ",".join("?" * len(TIPOS))
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            f'SELECT id, start, "end", value FROM context '
            f"WHERE json_extract(value, '$.context_type') IN ({marcas})",
            TIPOS,
        )
        return cur.fetchall()
    finally:
        conn.close()


def main():
    filas, esperado = [], Counter()
    for id_, start, end, value in leer_fuente():
        doc = json.loads(value)
        esperado[doc["context_type"]] += 1
        filas.append((
            id_,
            datetime.fromtimestamp(start, timezone.utc),
            datetime.fromtimestamp(end, timezone.utc),
            doc["context_type"],
            doc.get("inverter"),          # NULL si no existe: no se inventa
            value,                        # JSON original
        ))

    ok = True
    with connect() as conn:
        with conn.cursor() as cur:
            cur.executemany(UPSERT_SILVER, filas)
            cur.execute(UPSERT_GOLD)

            for tabla, col in (("silver.context_evento", "context_type"),
                               ("gold.fact_evento_operativo", "context_type")):
                cur.execute(f"SELECT {col}, count(*) FROM {tabla} GROUP BY 1")
                bd = dict(cur.fetchall())
                print(f"\nConciliación fuente vs {tabla}")
                for tipo in TIPOS:
                    e, b = esperado.get(tipo, 0), bd.get(tipo, 0)
                    ok &= (e == b)
                    print(f"  {tipo:<30} fuente={e:>4}  BD={b:>4}  {'OK' if e == b else 'FALLA'}")
        if not ok:
            conn.rollback()
            print("\nConciliación fallida: se revierte.")
            raise SystemExit(1)
    print("\nEventos cargados y conciliados.")


if __name__ == "__main__":
    main()