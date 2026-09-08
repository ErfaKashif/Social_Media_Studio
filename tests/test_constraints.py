import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import init_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield

def test_ingest_post_success():
    """Verifies valid blog post ingestion."""
    res = client.post("/api/posts", json={
        "title": "Capstone Launch",
        "source_type": "markdown",
        "content": "Social Media Studio backend built with Python and FastAPI."
    })
    assert res.status_code == 201
    assert "post_id" in res.json()

def test_blocked_variant_constraint_violation():
    """PROBE 2: Verifies that rule-breaking variants are blocked with 422 Unprocessable Entity."""
    # 1. Ingest valid post
    post_res = client.post("/api/posts", json={
        "title": "Rule Check",
        "source_type": "markdown",
        "content": "Testing constraint rules."
    })
    post_id = post_res.json()["post_id"]

    # 2. Attempt creating X variant that violates hashtag limits (>3 hashtags)
    invalid_content = "Post breaking hashtag limits " + " ".join([f"#tag{i}" for i in range(8)])
    res = client.post("/api/variants", json={
        "post_id": post_id,
        "platform": "x",
        "content": invalid_content
    })

    assert res.status_code == 422
    assert "Hashtag rule broken" in res.json()["detail"]