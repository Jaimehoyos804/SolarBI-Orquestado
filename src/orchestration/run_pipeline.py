import subprocess
import sys
import time

PASOS = (
    ("Transformación horaria", "src.transformation.hourly_grid_energy"),
    ("Validación del CSV", "src.validation.validate_hourly"),
    ("Carga de lecturas horarias", "src.loading.load_hourly"),
    ("Carga de eventos de contexto", "src.loading.load_context"),
)


def main():
    for nombre, modulo in PASOS:
        print(f"\n=== {nombre} ({modulo}) ===", flush=True)
        inicio = time.time()
        resultado = subprocess.run([sys.executable, "-m", modulo])
        if resultado.returncode != 0:
            print(f"\nFALLÓ: {nombre} (código {resultado.returncode}). Se detiene el pipeline.")
            sys.exit(resultado.returncode)
        print(f"--- {nombre}: OK en {time.time() - inicio:.0f} s", flush=True)
    print("\nPipeline completo.")


if __name__ == "__main__":
    main()