import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.append(str(Path(__file__).resolve().parents[1]))

import psycopg

from app.config import DATABASE_URL
from app.db import init_schema_and_seed


def ensure_database() -> None:
    parsed = urlparse(DATABASE_URL)
    database_name = parsed.path.lstrip("/") or "ai_fitness_coach"
    admin_url = DATABASE_URL.replace(f"/{database_name}", "/postgres")

    with psycopg.connect(admin_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database_name,))
            if cur.fetchone() is None:
                cur.execute(f'CREATE DATABASE "{database_name}"')


if __name__ == "__main__":
    ensure_database()
    init_schema_and_seed()
    print("PostgreSQL database initialized: ai_fitness_coach")
