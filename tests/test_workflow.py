import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import init_db
from app.services.generator import verify_grounding, GroundingError

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield


def test_refuse_unapproved_variant_schedule():
    """PROBE 3: Scheduling an unapproved variant MUST return a 400 Bad Request error."""
    post_id = \
    client.post("/api/posts", json={"title": "Workflow", "source_type": "markdown", "content": "Content"}).json()[
        "post_id"]
    variant_id = \
    client.post("/api/variants", json={"post_id": post_id, "platform": "discord", "content": "Hello Discord"}).json()[
        "variant_id"]

    # Schedule draft variant -> Fails 400
    res = client.post("/api/schedule", json={
        "variant_id": variant_id,
        "scheduled_time": "2026-12-01 12:00:00"
    })
    assert res.status_code == 400
    assert "Current status is 'draft'" in res.json()["detail"]


def test_refuse_past_date_schedule():
    """Verifies that scheduling timestamps in the past are rejected with 400 Bad Request."""
    post_id = \
    client.post("/api/posts", json={"title": "Past Check", "source_type": "markdown", "content": "Content"}).json()[
        "post_id"]
    variant_id = \
    client.post("/api/variants", json={"post_id": post_id, "platform": "discord", "content": "Hello Discord"}).json()[
        "variant_id"]

    # Approve variant
    client.patch(f"/api/variants/{variant_id}/status?status_value=approved")

    # Attempt past date scheduling
    res = client.post("/api/schedule", json={
        "variant_id": variant_id,
        "scheduled_time": "2020-01-01 10:00:00"
    })
    assert res.status_code == 400
    assert "Cannot schedule post in the past" in res.json()["detail"]


def test_grounding_check_catches_fake_statistic():
    """Grounding Check: Ensures hallucinated stats not present in source content raise GroundingError."""
    source_content = "Revenue grew by 15% in Q3."
    fake_variant = "Revenue grew by 85% in Q3!"  # 85% is ungrounded

    with pytest.raises(GroundingError) as exc_info:
        verify_grounding(source_content, fake_variant)

    assert "Grounding check failed" in str(exc_info.value)