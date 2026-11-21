import csv
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from src.extraction.sqlite_reader import get_connection

LOCAL_TZ = ZoneInfo("Asia/Shanghai")
MAX_GAP_SECONDS = 300

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "data" / "temp"
OUTPUT_FILE = OUTPUT_DIR / "perfil_energia_red_horaria.csv"

def _areas(pa, pb, dt_h):
    """Áreas positiva y negativa de una recta de pa a pb durante dt_h horas."""
    if pa >= 0 and pb >= 0:
        return (pa + pb) / 2 * dt_h, 0.0
    if pa <= 0 and pb <= 0:
        return 0.0, -(pa + pb) / 2 * dt_h
    frac = pa / (pa - pb)               # fracción del tramo hasta el cruce por cero
    a1 = abs(pa) * frac * dt_h / 2
    a2 = abs(pb) * (1 - frac) * dt_h / 2
    return (a1, a2) if pa > 0 else (a2, a1)


def integrate_interval(accumulator, inverter, start, end, p0, p1):
    """Integra un intervalo y lo distribuye por hora local."""
    total_seconds = (end - start).total_seconds()
    if total_seconds <= 0:
        return

    current = start
    while current < end:
        hour = current.replace(minute=0, second=0, microsecond=0)
        segment_end = min(hour + timedelta(hours=1), end)

        f0 = (current - start).total_seconds() / total_seconds
        f1 = (segment_end - start).total_seconds() / total_seconds
        power_start = p0 + (p1 - p0) * f0
        power_end = p0 + (p1 - p0) * f1
        duration = (segment_end - current).total_seconds()

        positive, negative = _areas(power_start, power_end, duration / 3600)

        row = accumulator[(inverter, hour)]
        row["positive"] += positive
        row["negative"] += negative
        row["net"] += positive - negative
        row["coverage_seconds"] += duration
        row["segments"] += 1

        current = segment_end

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    accumulator = defaultdict(
        lambda: {
            "positive": 0.0,
            "negative": 0.0,
            "net": 0.0,
            "coverage_seconds": 0.0,
            "segments": 0,
        }
    )

    summaries = {}

    conn = get_connection()

    try:
        for inverter in (1, 2):
            print(f"\nProcesando inversor {inverter}...")

            summary = {
                "rows": 0,
                "valid": 0,
                "null": 0,
                "integrated": 0,
                "long_gaps": 0,
                "invalid_intervals": 0,
                "max_gap": 0.0,
                "covered_seconds": 0.0,
            }

            cur = conn.cursor()

            cur.execute("""
                SELECT read_ts, gridpowerw_a
                FROM analog_measurements
                WHERE inverter = ?
                ORDER BY read_ts
            """, (inverter,))

            previous = None

            while True:
                batch = cur.fetchmany(50000)

                if not batch:
                    break

                for timestamp, power in batch:
                    summary["rows"] += 1

                    if power is None:
                        summary["null"] += 1
                        previous = None
                        continue

                    summary["valid"] += 1

                    current = (
                        datetime.fromtimestamp(
                            timestamp,
                            timezone.utc
                        ).astimezone(LOCAL_TZ),
                        float(power),
                    )

                    if previous is not None:
                        previous_time, previous_power = previous

                        delta = (
                            current[0] - previous_time
                        ).total_seconds()

                        if 0 < delta <= MAX_GAP_SECONDS:
                            integrate_interval(
                                accumulator,
                                inverter,
                                previous_time,
                                current[0],
                                previous_power,
                                current[1],
                            )

                            summary["integrated"] += 1
                            summary["covered_seconds"] += delta

                        elif delta > MAX_GAP_SECONDS:
                            summary["long_gaps"] += 1
                            summary["max_gap"] = max(
                                summary["max_gap"], delta
                            )

                        else:
                            summary["invalid_intervals"] += 1

                    previous = current

            summaries[inverter] = summary
            cur.close()

    finally:
        conn.close()

    columns = [
        "inverter",
        "hour_local",
        "positive_power_unit_hours",
        "negative_power_unit_hours",
        "net_power_unit_hours",
        "coverage_minutes",
        "contributing_segments",
    ]

    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=columns
        )

        writer.writeheader()

        for (inverter, hour), values in sorted(
            accumulator.items()
        ):
            writer.writerow({
                "inverter": inverter,
                "hour_local": hour.isoformat(),
                "positive_power_unit_hours": round(
                    values["positive"], 6
                ),
                "negative_power_unit_hours": round(
                    values["negative"], 6
                ),
                "net_power_unit_hours": round(
                    values["net"], 6
                ),
                "coverage_minutes": round(
                    values["coverage_seconds"] / 60, 2
                ),
                "contributing_segments": values["segments"],
            })

    print("Resumen del")

    for inverter, summary in summaries.items():
        print(f"\nINVERSOR {inverter}")

        for key, value in summary.items():
            print(f"{key}: {value}")

    print("\nHoras generadas:", len(accumulator))
    print("Archivo generado:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
