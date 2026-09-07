from abc import ABC, abstractmethod


class SocialPublisher(ABC):
    """Abstract interface for all social media publisher adapters."""

    @abstractmethod
    async def publish(self, content: str, idempotency_key: str) -> dict:
        """Publishes content and returns execution status dictionary."""
        pass