import sqlite3
from pathlib import Path

from src.config.settings import validate_source


def get_connection() -> sqlite3.Connection:
   #Modo Lectura en SQL lite
    source = validate_source()

    uri = source.resolve().as_uri() + "?mode=ro"

    connection = sqlite3.connect(
        uri,
        uri=True,
        timeout=30
    )

    connection.execute("PRAGMA query_only = ON")

    return connection


def get_tables() -> list[str]:
    #Obtener las tablas 
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        )

        return [row[0] for row in cursor.fetchall()]


def get_table_count(table_name: str) -> int:
    #Obtener el registro total de las tablas
    tables = get_tables()

    if table_name not in tables:
        raise ValueError(f"Tabla inexistente: {table_name}")

    # validar el nombre de la tabla.
    with get_connection() as connection:
        cursor = connection.execute(
            f'SELECT COUNT(*) FROM "{table_name}"'
        )

        return cursor.fetchone()[0]


if __name__ == "__main__":
    tables = get_tables()

    print(f"Tablas encontradas: {len(tables)}")

    for table in tables:
        print(f"{table}: {get_table_count(table):,} registros")
