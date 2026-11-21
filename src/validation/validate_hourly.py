import sys
from pathlib import Path
import pandas as pd

df = pd.read_csv(Path("data/temp/perfil_energia_red_horaria.csv"))
df["dif"] = df["net_power_unit_hours"] - (
    df["positive_power_unit_hours"] - df["negative_power_unit_hours"])

checks = {
    "net = pos - neg (tol 1e-5)": (df["dif"].abs() > 1e-5).sum() == 0,
    "cobertura <= 60 min": (df["coverage_minutes"] > 60.0001).sum() == 0,
    "(inverter, variable, hour_local) único": df.duplicated(["inverter", "variable", "hour_local"]).sum() == 0,
    "sin NULL": df.isna().sum().sum() == 0,
}
print("REGISTROS:", len(df), " DIFERENCIA MÁXIMA:", df["dif"].abs().max())
print(df.groupby(["inverter", "variable"]).size().to_string())
for name, ok in checks.items():
    print(("OK   " if ok else "FALLA"), name)
sys.exit(0 if all(checks.values()) else 1)