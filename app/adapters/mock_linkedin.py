from app.adapters.base import SocialPublisher

class MockLinkedInPublisher(SocialPublisher):
    async def publish(self, content: str, idempotency_key: str) -> dict:
        return {
            "status": "success",
            "platform": "linkedin",
            "idempotency_key": idempotency_key,
            "preview": f"[MOCK LINKEDIN POST] {content}"
        }