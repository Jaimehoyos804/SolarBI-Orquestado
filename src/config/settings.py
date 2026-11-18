import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


#Rutas del proyecto

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"

BRONZE_DIR = DATA_DIR / "bronze"
SILVER_DIR = DATA_DIR / "silver"
GOLD_DIR = DATA_DIR / "gold"
TEMP_DIR = DATA_DIR / "temp"

CHECKSUM_DIR = DATA_DIR / "checksums"

DATABASE_DIR = PROJECT_ROOT / "database"
DOCS_DIR = PROJECT_ROOT / "docs"

# Fuente original
BRONZE_DB = BRONZE_DIR / "opencem-v1.0.0.sqlite"

# Configuración de entorno.
ENV_FILE = PROJECT_ROOT / ".env"
load_dotenv(ENV_FILE, override=False)


#Configuracion BD postgreSQL

@dataclass(frozen=True)
class PostgreSQLSettings:
    host: str = os.getenv("POSTGRES_HOST", "localhost")
    port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    database: str = os.getenv("POSTGRES_DB", "solarbi")
    user: str = os.getenv("POSTGRES_USER", "postgres")
    password: str = os.getenv("POSTGRES_PASSWORD", "")


POSTGRES = PostgreSQLSettings()


#Validaciones
def validate_source() -> Path:
    """
    Comprueba que la fuente Bronze exista y tenga contenido.
    No modifica ni abre la base de datos.
    """
    if not BRONZE_DB.is_file():
        raise FileNotFoundError(
            f"No se encontró la fuente Bronze: {BRONZE_DB}"
        )

    if BRONZE_DB.stat().st_size == 0:
        raise ValueError("La fuente Bronze está vacía.")

    return BRONZE_DB


def validate_directories() -> None:
    #Verificacion que las rutas de directorios existan (no modifica ni crea directorios)
    required = [
        PROJECT_ROOT,
        BRONZE_DIR,
        SILVER_DIR,
        GOLD_DIR,
        TEMP_DIR,
    ]

    missing = [str(path) for path in required if not path.is_dir()]

    if missing:
        raise FileNotFoundError(
            "No se encontraron los siguientes directorios:\n"
            + "\n".join(missing)
        )


def get_postgres_config() -> dict:
   #Devuelve la configuración de PostgreSQL como un diccionario.
    if not POSTGRES.password:
        raise ValueError(
            "Falta configurar POSTGRES_PASSWORD en el archivo .env"
        )

    return {
        "host": POSTGRES.host,
        "port": POSTGRES.port,
        "dbname": POSTGRES.database,
        "user": POSTGRES.user,
        "password": POSTGRES.password,
    }
