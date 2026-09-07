import httpx
from app.adapters.base import SocialPublisher


class DiscordPublisher(SocialPublisher):
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def publish(self, content: str, idempotency_key: str) -> dict:
        if not self.webhook_url:
            # Fallback mock mode if webhook URL is not supplied in environment
            return {
                "status": "success",
                "platform": "discord",
                "idempotency_key": idempotency_key,
                "preview": f"[MOCK DISCORD WEBHOOK POST] {content}"
            }

        payload = {"content": content, "username": "Social Media Studio"}

        async with httpx.AsyncClient() as client:
            res = await client.post(self.webhook_url, json=payload)
            if res.status_code in (200, 204):
                return {"status": "success", "platform": "discord", "idempotency_key": idempotency_key}
            return {"status": "failed", "platform": "discord", "error": res.text}