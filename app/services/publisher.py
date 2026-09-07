import json
import os
from app.adapters.base import SocialPublisher
from app.adapters.discord import DiscordPublisher
from app.adapters.mock_x import MockXPublisher
from app.adapters.mock_linkedin import MockLinkedInPublisher
from app.core.database import get_db_connection

def get_publisher_adapter(platform: str) -> SocialPublisher:
    """Factory to swap adapters dynamically based on configuration."""
    platform = platform.lower()
    if platform == "discord":
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "")
        return DiscordPublisher(webhook_url=webhook_url)
    elif platform == "x":
        return MockXPublisher()
    elif platform == "linkedin":
        return MockLinkedInPublisher()
    else:
        raise ValueError(f"No adapter registered for platform: {platform}")

async def execute_idempotent_publish(slot_id: int) -> dict:
    """Publishes a scheduled slot strictly once, enforcing idempotency via SQLite."""
    conn = get_db_connection()
    cur = conn.execute(
        """SELECT s.id as slot_id, s.idempotency_key, s.status as slot_status, 
                  v.id as variant_id, v.platform, v.content, v.status as variant_status
           FROM schedule_slots s
           JOIN variants v ON s.variant_id = v.id
           WHERE s.id = ?""",
        (slot_id,)
    )
    job = cur.fetchone()

    if not job:
        conn.close()
        return {"status": "failed", "reason": "Job slot not found"}

    # IDEMPOTENCY GUARD: Block execution if slot is already marked as completed
    if job["slot_status"] == "completed":
        conn.close()
        return {
            "status": "ignored",
            "reason": "Duplicate execution blocked by Idempotency Key",
            "idempotency_key": job["idempotency_key"]
        }

    # Execute publication via target adapter
    adapter = get_publisher_adapter(job["platform"])
    res = await adapter.publish(job["content"], job["idempotency_key"])

    if res["status"] == "success":
        # Atomically update slot status and record in publish_history
        conn.execute("UPDATE schedule_slots SET status = 'completed' WHERE id = ?", (slot_id,))
        conn.execute("UPDATE variants SET status = 'published' WHERE id = ?", (job["variant_id"],))
        conn.execute(
            """INSERT INTO publish_history (slot_id, variant_id, platform, status, response_payload)
               VALUES (?, ?, ?, 'success', ?)""",
            (slot_id, job["variant_id"], job["platform"], json.dumps(res))
        )
        conn.commit()

    conn.close()
    return res