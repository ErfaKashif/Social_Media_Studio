# app/services/workflow.py
from app.core.database import get_db_connection

class WorkflowError(Exception):
    """Custom exception for invalid workflow operations."""
    pass

def update_variant_status(variant_id: int, new_status: str) -> dict:
    """Updates a variant's status to 'approved' or 'rejected'."""
    allowed_statuses = ("approved", "rejected", "draft")
    if new_status.lower() not in allowed_statuses:
        raise WorkflowError(f"Invalid status '{new_status}'. Allowed: {allowed_statuses}")

    conn = get_db_connection()
    cur = conn.execute("SELECT id FROM variants WHERE id = ?", (variant_id,))
    if not cur.fetchone():
        conn.close()
        raise WorkflowError(f"Variant with ID {variant_id} does not exist.")

    conn.execute(
        "UPDATE variants SET status = ? WHERE id = ?",
        (new_status.lower(), variant_id)
    )
    conn.commit()
    conn.close()
    return {"variant_id": variant_id, "status": new_status.lower()}

def schedule_variant(variant_id: int, scheduled_time: str) -> dict:
    """Schedules a variant for publication. STRICTLY blocks unapproved variants."""
    conn = get_db_connection()
    cur = conn.execute("SELECT id, status FROM variants WHERE id = ?", (variant_id,))
    variant = cur.fetchone()

    if not variant:
        conn.close()
        raise WorkflowError(f"Variant with ID {variant_id} does not exist.")

    # REQUIREMENT: Only approved variants can be scheduled
    if variant["status"] != "approved":
        conn.close()
        raise WorkflowError(
            f"Cannot schedule variant {variant_id}. Current status is '{variant['status']}', but 'approved' is required."
        )

    # Generate composite idempotency key
    idempotency_key = f"variant_{variant_id}_time_{scheduled_time}"

    cur = conn.execute(
        """INSERT INTO schedule_slots (variant_id, scheduled_time, idempotency_key, status)
           VALUES (?, ?, ?, 'queued')""",
        (variant_id, scheduled_time, idempotency_key)
    )
    slot_id = cur.lastrowid
    conn.commit()
    conn.close()

    return {"slot_id": slot_id, "variant_id": variant_id, "idempotency_key": idempotency_key, "status": "queued"}