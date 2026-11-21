import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import psycopg
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = PROJECT_ROOT / "data" / "temp" / "perfil_energia_red_horaria.csv"
TOL = 1e-4

UPSERT_SILVER = """
INSERT INTO silver.energia_red_hora
  (inverter, variable, hour_local, positive_power_unit_hours, negative_power_unit_hours,
   net_power_unit_hours, coverage_minutes, contributing_segments)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (inverter, variable, hour_local) DO UPDATE SET
  positive_power_unit_hours = EXCLUDED.positive_power_unit_hours,
  negative_power_unit_hours = EXCLUDED.negative_power_unit_hours,
  net_power_unit_hours      = EXCLUDED.net_power_unit_hours,
  coverage_minutes          = EXCLUDED.coverage_minutes,
  contributing_segments     = EXCLUDED.contributing_segments
"""

UPSERT_GOLD = """
INSERT INTO gold.fact_energia_red_hora
  (inverter_key, variable_key, fecha_key, hora_key, hour_local, positive_power_unit_hours,
   negative_power_unit_hours, net_power_unit_hours, coverage_minutes)
SELECT inverter, variable,
       to_char(hour_local AT TIME ZONE 'Asia/Shanghai', 'YYYYMMDD')::int,
       extract(hour FROM hour_local AT TIME ZONE 'Asia/Shanghai')::smallint,
       hour_local, positive_power_unit_hours, negative_power_unit_hours,
       net_power_unit_hours, coverage_minutes
FROM silver.energia_red_hora
ON CONFLICT (inverter_key, variable_key, hour_local) DO UPDATE SET
  fecha_key = EXCLUDED.fecha_key,
  hora_key = EXCLUDED.hora_key,
  positive_power_unit_hours = EXCLUDED.positive_power_unit_hours,
  negative_power_unit_hours = EXCLUDED.negative_power_unit_hours,
  net_power_unit_hours      = EXCLUDED.net_power_unit_hours,
  coverage_minutes          = EXCLUDED.coverage_minutes
"""

SUMS = """
SELECT {inv}, {var}, count(*), sum(positive_power_unit_hours),
       sum(negative_power_unit_hours), sum(net_power_unit_hours)
FROM {table} GROUP BY {inv}, {var} ORDER BY {inv}, {var}
"""


def connect():
    load_dotenv(PROJECT_ROOT / ".env", override=True)
    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5434"),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )


def main():
    df = pd.read_csv(CSV_PATH)
    rows = [
        (int(r.inverter), r.variable, datetime.fromisoformat(r.hour_local),
         r.positive_power_unit_hours, r.negative_power_unit_hours,
         r.net_power_unit_hours, r.coverage_minutes, int(r.contributing_segments))
        for r in df.itertuples(index=False)
    ]
    expected = df.groupby(["inverter", "variable"]).agg(
        n=("hour_local", "count"),
        pos=("positive_power_unit_hours", "sum"),
        neg=("negative_power_unit_hours", "sum"),
        net=("net_power_unit_hours", "sum"),
    )

    ok = True
    with connect() as conn:
        with conn.cursor() as cur:
            cur.executemany(UPSERT_SILVER, rows)
            cur.execute(UPSERT_GOLD)

            for table, inv, var in (("silver.energia_red_hora", "inverter", "variable"),
                                    ("gold.fact_energia_red_hora", "inverter_key", "variable_key")):
                cur.execute(SUMS.format(table=table, inv=inv, var=var))
                print(f"\nConciliación CSV vs {table}")
                for i, v, n, pos, neg, net in cur.fetchall():
                    e = expected.loc[(i, v)]
                    good = (n == e.n and abs(float(pos) - e.pos) < TOL
                            and abs(float(neg) - e.neg) < TOL
                            and abs(float(net) - e.net) < TOL)
                    ok &= good
                    print(f"  inv {i} · {v}: CSV={int(e.n)} / BD={n} filas "
                          f"| net CSV={e.net:.4f} BD={float(net):.4f} -> {'OK' if good else 'FALLA'}")
        if not ok:
            conn.rollback()
            print("\nConciliación fallida: se revierte la transacción.")
            sys.exit(1)
    print("\nCarga completa y conciliada.")


if __name__ == "__main__":
    main()