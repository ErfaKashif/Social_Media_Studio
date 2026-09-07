from app.adapters.base import SocialPublisher

class MockXPublisher(SocialPublisher):
    async def publish(self, content: str, idempotency_key: str) -> dict:
        return {
            "status": "success",
            "platform": "x",
            "idempotency_key": idempotency_key,
            "preview": f"[MOCK X POST] {content[:280]}"
        }