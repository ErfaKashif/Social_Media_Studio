from app.core.database import get_db_connection
from app.services.validater import validate_variant


def ingest_post(title: str, source_type: str, content: str) -> int:
    """Stores the blog post into SQLite as the single source of truth."""
    conn = get_db_connection()
    cur = conn.execute(
        "INSERT INTO posts (title, source_type, content) VALUES (?, ?, ?)",
        (title, source_type, content)
    )
    post_id = cur.lastrowid
    conn.commit()
    conn.close()
    return post_id


def create_variant(post_id: int, platform: str, content: str) -> dict:
    """Validates variant rules before saving to the database."""
    # Enforce profile constraints (raises error if invalid)
    validate_variant(platform, content)

    conn = get_db_connection()
    cur = conn.execute(
        """INSERT INTO variants (post_id, platform, content, status, validation_passed)
           VALUES (?, ?, ?, 'draft', 1)""",
        (post_id, platform.lower(), content)
    )
    variant_id = cur.lastrowid
    conn.commit()
    conn.close()

    return {"variant_id": variant_id, "platform": platform, "status": "draft", "validation_passed": True}