"""Crea (o recrea) el esquema de la base a partir de db/schema.sql y db/migrations/*.sql.

Uso:
    python -m src.db            # crea lo que falte (idempotente)
    python -m src.db --reset    # borra el esquema y lo crea desde cero
    python -m src.db --test     # lo mismo, sobre la base de pruebas
"""
from __future__ import annotations

import argparse

from sqlalchemy import Engine, text

from src.config import DB_DIR, SCHEMA, get_engine


def sql_files() -> list:
    """schema.sql primero y luego las migraciones en orden alfabético."""
    return [DB_DIR / "schema.sql", *sorted((DB_DIR / "migrations").glob("*.sql"))]


def apply_schema(engine: Engine, reset: bool = False) -> None:
    """Ejecuta los archivos SQL en una sola transacción."""
    raw = engine.raw_connection()
    try:
        with raw.cursor() as cur:
            if reset:
                cur.execute(f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE")
            for path in sql_files():
                cur.execute(path.read_text(encoding="utf-8"))
        raw.commit()
    except Exception:
        raw.rollback()
        raise
    finally:
        raw.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Crea el esquema de la base de datos")
    parser.add_argument("--reset", action="store_true", help="borra y recrea el esquema")
    parser.add_argument("--test", action="store_true", help="usa la base de pruebas")
    args = parser.parse_args()
    engine = get_engine(test=args.test)
    apply_schema(engine, reset=args.reset)
    with engine.connect() as conn:
        tablas = conn.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = :s ORDER BY 1"
        ), {"s": SCHEMA}).scalars().all()
    print(f"Esquema '{SCHEMA}' listo en {engine.url.database}: {', '.join(tablas)}")


if __name__ == "__main__":
    main()
