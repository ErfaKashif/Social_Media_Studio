from datetime import datetime
from app.core.database import get_db_connection
import sqlite3

class WorkflowError(Exception):
    """Custom exception for invalid workflow operations."""
    pass


def update_variant_status(variant_id: int, new_status: str) -> dict:
    """Updates a variant's status to 'approved' or 'rejected'."""
    allowed_statuses = ("approved", "rejected", "draft")
    if new_status.lower() not in allowed_statuses:
        raise WorkflowError(f"Invalid status '{new_status}'. Allowed: {allowed_statuses}")

    conn = get_db_connection()
    try:
        cur = conn.execute("SELECT id FROM variants WHERE id = ?", (variant_id,))
        if not cur.fetchone():
            raise WorkflowError(f"Variant with ID {variant_id} does not exist.")

        conn.execute(
            "UPDATE variants SET status = ? WHERE id = ?",
            (new_status.lower(), variant_id)
        )
        conn.commit()
        return {"variant_id": variant_id, "status": new_status.lower()}
    finally:
        conn.close()


def schedule_variant(variant_id: int, scheduled_time_str: str) -> dict:
    """Schedules a variant for publication. Strictly blocks past dates and unapproved variants."""

    # Past-date Guardrail
    try:
        normalized_time_str = scheduled_time_str.replace("T", " ")
        if len(normalized_time_str) == 16:  # Handles 'YYYY-MM-DD HH:MM'
            normalized_time_str += ":00"

        scheduled_dt = datetime.strptime(normalized_time_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise WorkflowError("Invalid time format. Use 'YYYY-MM-DD HH:MM:SS'.")

    if scheduled_dt < datetime.now():
        raise WorkflowError(
            f"Cannot schedule post in the past ({normalized_time_str}). Scheduled time must be in the future."
        )

    conn = get_db_connection()
    try:
        cur = conn.execute("SELECT id, status FROM variants WHERE id = ?", (variant_id,))
        variant = cur.fetchone()

        if not variant:
            raise WorkflowError(f"Variant with ID {variant_id} does not exist.")

        if variant["status"] != "approved":
            raise WorkflowError(
                f"Cannot schedule variant {variant_id}. Current status is '{variant['status']}', but 'approved' is required."
            )

        # Composite idempotency key
        idempotency_key = f"variant_{variant_id}_time_{normalized_time_str}"

        try:
            cur = conn.execute(
                """INSERT INTO schedule_slots (variant_id, scheduled_time, idempotency_key, status)
                   VALUES (?, ?, ?, 'queued')""",
                (variant_id, normalized_time_str, idempotency_key)
            )
            slot_id = cur.lastrowid
            conn.commit()

            return {
                "slot_id": slot_id,
                "variant_id": variant_id,
                "scheduled_time": normalized_time_str,
                "idempotency_key": idempotency_key,
                "status": "queued"
            }
        except sqlite3.IntegrityError:
            # Handle duplicate schedule attempt gracefully instead of 500
            existing_slot = conn.execute(
                "SELECT id, status FROM schedule_slots WHERE idempotency_key = ?",
                (idempotency_key,)
            ).fetchone()

            return {
                "status": "ignored",
                "slot_id": existing_slot["id"] if existing_slot else None,
                "reason": f"Slot already queued for variant {variant_id} at {normalized_time_str}."
            }
    finally:
        conn.close()