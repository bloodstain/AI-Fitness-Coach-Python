from collections.abc import Iterable
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

from app.config import DATABASE_URL


SQL_DIR = Path(__file__).resolve().parents[1] / "sql"


def connect():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def fetch_one(query: str, params: Iterable[Any] = ()) -> dict[str, Any] | None:
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()


def fetch_all(query: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return list(cur.fetchall())


def execute(query: str, params: Iterable[Any] = ()) -> dict[str, Any] | None:
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            row = cur.fetchone() if cur.description else None
        conn.commit()
        return row


def execute_sql_file(path: Path) -> None:
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(path.read_text(encoding="utf-8"))
        conn.commit()


def init_schema_and_seed() -> None:
    execute_sql_file(SQL_DIR / "schema.sql")
    execute_sql_file(SQL_DIR / "seed.sql")
