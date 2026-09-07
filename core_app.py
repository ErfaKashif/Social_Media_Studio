import hmac
import hashlib
import time
import uuid
import httpx
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Social Media Studio Core")

HMAC_SECRET = b"studio_webhook_secret_key"
MOCK_SERVER_URL = "http://127.0.0.1:8001"


class CampaignPostRequest(BaseModel):
    content: str
    discord_webhook_url: str | None = None
    callback_url: str = "http://127.0.0.1:8000/webhooks/callback"


# --- ADAPTER 1: REAL DISCORD PLATFORM ---
async def publish_to_discord(webhook_url: str, content: str) -> dict:
    async with httpx.AsyncClient() as client:
        res = await client.post(webhook_url, json={"content": content, "username": "Social Media Studio"})
        if res.status_code == 429:
            retry_after = res.json().get("retry_after", 5)
            return {"platform": "Discord", "status": "rate_limited", "retry_after": retry_after}
        res.raise_for_status()
        return {"platform": "Discord", "status": "success"}


# --- ADAPTER 2: MOCK PLATFORM ADAPTER (WITH RETRY & IDEMPOTENCY) ---
async def publish_to_mock_platform(content: str, callback_url: str) -> dict:
    idempotency_key = str(uuid.uuid4())
    headers = {
        "Authorization": "Bearer mock_access_token_123",
        "Idempotency-Key": idempotency_key
    }
    payload = {"content": content, "callback_url": callback_url}

    async with httpx.AsyncClient() as client:
        # Initial Request
        res = await client.post(f"{MOCK_SERVER_URL}/v1/posts", json=payload, headers=headers)

        # Handle Rate Limit (429) automatically
        if res.status_code == 429:
            retry_after = int(res.headers.get("Retry-After", 5))
            print(f" [STUDIO] Hit 429 Rate Limit. Sleeping for {retry_after} seconds...")
            time.sleep(retry_after)
            # Retry request using the SAME Idempotency-Key
            res = await client.post(f"{MOCK_SERVER_URL}/v1/posts", json=payload, headers=headers)

        return res.json()


# --- STUDIO PUBLISHING ENDPOINT ---
@app.post("/api/campaign/publish")
async def publish_campaign(request: CampaignPostRequest):
    results = {}

    # 1. Publish to Mock Server
    try:
        mock_res = await publish_to_mock_platform(request.content, request.callback_url)
        results["mock_platform"] = mock_res
    except Exception as e:
        results["mock_platform"] = {"status": "failed", "error": str(e)}

    # 2. Publish to Real Discord (if webhook provided)
    if request.discord_webhook_url:
        discord_res = await publish_to_discord(request.discord_webhook_url, request.content)
        results["discord"] = discord_res

    return {"campaign_status": "processed", "results": results}


# --- HMAC SIGNED WEBHOOK RECEIVER ---
@app.post("/webhooks/callback")
async def receive_webhook(request: Request):
    signature = request.headers.get("X-Signature")
    body_bytes = await request.body()

    # Verify HMAC-SHA256 Signature
    expected_sig = hmac.new(HMAC_SECRET, body_bytes, hashlib.sha256).hexdigest()
    if not signature or not hmac.compare_digest(signature, expected_sig):
        raise HTTPException(status_code=401, detail="Invalid HMAC Signature")

    data = await request.json()
    print(f" [STUDIO] Webhook Received & Verified: {data}")
    return {"status": "verified_and_processed"}