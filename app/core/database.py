# app/core/database.py
import sqlite3
import os

# Set database path to data/studio.db relative to root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "studio.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")


def get_db_connection():
    """Returns a connection to the SQLite database with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
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