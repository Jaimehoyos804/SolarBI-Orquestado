import os
import random
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from src.loading.load_hourly import connect

INTERVALO = float(os.getenv("SIM_INTERVALO_S", "5"))
V_NOMINAL = 235.0
TZ = ZoneInfo("Asia/Shanghai")    


PERFIL_SQL = """
SELECT inverter_key, hora_key,
       sum(positive_power_unit_hours) / NULLIF(sum(coverage_minutes) / 60.0, 0)
FROM gold.fact_energia_red_hora
WHERE variable_key = 'linepowerw_a' AND fecha_key < 20260503
GROUP BY 1, 2
"""

INSERT_SQL = """
INSERT INTO silver.lectura_vivo (inverter, ts, voltaje_v, potencia_linea_w, modo_sim)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT DO NOTHING
"""


def esperar_perfil():
    """Espera a que la base y el ETL estén listos (útil al arrancar en un clúster)."""
    while True:
        try:
            with connect() as conn, conn.cursor() as cur:
                cur.execute(PERFIL_SQL)
                perfil = {(i, h): float(w) for i, h, w in cur.fetchall() if w is not None}
            if perfil:
                return perfil
            print("Sin perfil en gold todavía; esperando al ETL...", flush=True)
        except Exception as exc:
            print(f"Base de datos no lista: {exc}", flush=True)
        time.sleep(10)


def main():
    perfil = esperar_perfil()
    print(f"Simulador iniciado: {len(perfil)} puntos de perfil, cada {INTERVALO:.0f} s", flush=True)
    ciclo = 0
    with connect() as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            while True:
                cur.execute("SELECT modo FROM silver.control_simulador WHERE id = 1")
                modo = cur.fetchone()[0]
                if modo != "silencio":
                    hora = datetime.now(TZ).hour
                    ahora = datetime.now(timezone.utc)
                    for inv in (1, 2):
                        if modo == "corte":
                            voltaje, potencia = random.uniform(0, 2), 0.0
                        else:
                            base = perfil.get((inv, hora), 0.0)
                            voltaje = random.gauss(V_NOMINAL, 1.5)
                            potencia = max(0.0, random.gauss(base, base * 0.05))
                        cur.execute(INSERT_SQL, (inv, ahora, round(voltaje, 2), round(potencia, 2), modo))
                ciclo += 1
                if ciclo % 200 == 0:     
                    cur.execute("DELETE FROM silver.lectura_vivo WHERE ts < now() - interval '2 days'")
                time.sleep(INTERVALO)


if __name__ == "__main__":
    main()