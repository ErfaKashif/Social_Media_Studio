import os
import sqlite3
from app.core.config import settings
# Set database path to data/studio.db relative to root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "studio.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")


def get_db_connection():
    """Returns an SQLite connection configured for WAL mode and multi-thread safety."""
    conn = sqlite3.connect(settings.DB_PATH, timeout=20.0)  # Wait up to 20s if database is busy
    conn.row_factory = sqlite3.Row

    # Enable Write-Ahead Logging for concurrent read/write support
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def init_db():
    """Reads schema.sql and creates all tables if they do not exist."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    if not os.path.exists(SCHEMA_PATH):
        raise FileNotFoundError(f"Schema file not found at {SCHEMA_PATH}")

    with open(SCHEMA_PATH, "r") as f:
        schema_script = f.read()

    conn = get_db_connection()
    conn.executescript(schema_script)
    conn.commit()
    conn.close()
    print(f"SQLite database initialized at: {DB_PATH}")


if __name__ == "__main__":
    init_db()