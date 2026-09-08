import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield


def test_idempotent_publishing_and_retry_guard():
    """PROBE 4 & 5: Verifies single publication on first attempt and duplicate blocking on retry."""
    # 1. Ingest, create, approve, and schedule post
    post_id = client.post("/api/posts",
                          json={"title": "Idempotency", "source_type": "markdown", "content": "Publish Test"}).json()[
        "post_id"]
    variant_id = \
    client.post("/api/variants", json={"post_id": post_id, "platform": "x", "content": "Valid X content"}).json()[
        "variant_id"]
    client.patch(f"/api/variants/{variant_id}/status?status_value=approved")

    slot_id = client.post("/api/schedule", json={
        "variant_id": variant_id,
        "scheduled_time": "2026-12-01 12:00:00"
    }).json()["slot_id"]

    # 2. First Publish Execution -> Status 200 Success
    res1 = client.post(f"/api/schedule/{slot_id}/publish")
    assert res1.status_code == 200
    assert res1.json()["status"] == "success"

    # 3. Duplicate Retry -> Status 200 Ignored by Idempotency Key
    res2 = client.post(f"/api/schedule/{slot_id}/publish")
    assert res2.status_code == 200
    assert res2.json()["status"] == "ignored"
    assert "Duplicate execution blocked" in res2.json()["reason"]


def test_publish_history_logging():
    """Verifies that execution history audit records are logged properly."""
    res = client.get("/api/history")
    assert res.status_code == 200
    assert "history" in res.json()