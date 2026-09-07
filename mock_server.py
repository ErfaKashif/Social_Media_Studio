import hmac
import hashlib
import time
import uuid
import httpx
from fastapi import FastAPI, Header, HTTPException, Request, Response, BackgroundTasks
from pydantic import BaseModel

app = FastAPI(title="Mock Social Platform API")

HMAC_SECRET = b"studio_webhook_secret_key"
VALID_TOKENS = {"mock_access_token_123"}
request_counter = 0


class PublishPayload(BaseModel):
    content: str
    media_url: str | None = None
    callback_url: str | None = None


async def send_signed_webhook(callback_url: str, post_id: str):
    """Sends an HMAC-SHA256 signed POST callback to the specified callback URL."""
    time.sleep(1)  # Simulate processing delay
    payload = f'{{"event": "post.published", "post_id": "{post_id}", "status": "delivered"}}'
    signature = hmac.new(HMAC_SECRET, payload.encode("utf-8"), hashlib.sha256).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "X-Signature": signature
    }

    async with httpx.AsyncClient() as client:
        try:
            await client.post(callback_url, content=payload, headers=headers)
            print(f" [MOCK] Sent signed webhook to {callback_url}")
        except Exception as e:
            print(f" [MOCK] Failed to deliver webhook: {e}")


@app.post("/oauth/token")
def oauth_token(client_id: str, client_secret: str):
    if client_id == "studio_client" and client_secret == "studio_secret":
        return {"access_token": "mock_access_token_123", "token_type": "bearer", "expires_in": 3600}
    raise HTTPException(status_code=401, detail="Invalid client credentials")


@app.post("/v1/posts")
async def create_post(
        payload: PublishPayload,
        background_tasks: BackgroundTasks,
        authorization: str = Header(None),
        idempotency_key: str = Header(None)
):
    global request_counter
    request_counter += 1

    # 1. Auth Validation
    if not authorization or authorization.replace("Bearer ", "") not in VALID_TOKENS:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # 2. Idempotency Check
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Missing required Idempotency-Key header")

    # 3. Rate Limit Simulation (Triggers 429 every 4th request)
    if request_counter % 4 == 0:
        return Response(
            content='{"error": "Rate limit exceeded. Try again later."}',
            status_code=429,
            headers={"Retry-After": "5"},
            media_type="application/json"
        )

    # 4. Success Execution & Background Webhook Schedule
    post_id = f"post_{uuid.uuid4().hex[:8]}"
    if payload.callback_url:
        background_tasks.add_task(send_signed_webhook, payload.callback_url, post_id)

    return {
        "status": "success",
        "post_id": post_id,
        "idempotency_key": idempotency_key,
        "message": "Post published to mock platform."
    }