import sys
from pathlib import Path
import pandas as pd

path = Path("data/temp/perfil_energia_red_horaria.csv")
df = pd.read_csv(path)

df["dif"] = df["net_power_unit_hours"] - (
    df["positive_power_unit_hours"] - df["negative_power_unit_hours"]
)

checks = {
    "net = pos - neg (tol 1e-5)": (df["dif"].abs() > 1e-5).sum() == 0,
    "cobertura <= 60 min": (df["coverage_minutes"] > 60.0001).sum() == 0,
    "(inverter, hour_local) único": df.duplicated(["inverter", "hour_local"]).sum() == 0,
    "sin NULL": df.isna().sum().sum() == 0,
}

print("REGISTROS:", len(df))
print("DIFERENCIA MÁXIMA:", df["dif"].abs().max())
print("HORAS CON COBERTURA PARCIAL (<59.9 min):")
print((df["coverage_minutes"] < 59.9).groupby(df["inverter"]).sum().to_string())

for name, ok in checks.items():
    print(("OK   " if ok else "FALLA"), name)

sys.exit(0 if all(checks.values()) else 1)