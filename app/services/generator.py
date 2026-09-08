import re
import httpx
from app.core.config import settings
from app.services.ingestion import create_variant
from app.services.validater import validate_variant, ConstraintViolationError


class GroundingError(Exception):
    """Raised when generated variant claims numbers or stats not in source content."""
    pass


def verify_grounding(source_text: str, variant_text: str) -> bool:
    """Grounding Check: Enforces that all numbers/statistics in variant exist in source."""
    source_numbers = set(re.findall(r'\b\d+(?:\.\d+)?%?\b', source_text))
    variant_numbers = set(re.findall(r'\b\d+(?:\.\d+)?%?\b', variant_text))

    hallucinated_numbers = variant_numbers - source_numbers
    if hallucinated_numbers:
        raise GroundingError(
            f"Grounding check failed: Planted/hallucinated statistic(s) {hallucinated_numbers} not in source content."
        )
    return True


def generate_variant_with_ollama(post_id: int, source_content: str, platform: str) -> dict:
    """Queries local Ollama (llama3.2:3b) to draft platform variant with strict rule checks."""

    prompt = f"""You are a social media copywriter. Generate a single post variant for platform '{platform}'.
Rule: ONLY use facts and numbers present in the source text below. Do NOT invent statistics.

Source Content:
{source_content}

Platform Variant ({platform}):"""

    try:
        # Call local Ollama API endpoint
        response = httpx.post(
            f"{settings.OLLAMA_HOST}/api/generate",
            json={
                "model": settings.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=30.0
        )
        response.raise_for_status()
        raw_variant_text = response.json().get("response", "").strip()
    except Exception as err:
        # Fallback template if local Ollama service is unreachable
        raw_variant_text = f"[{platform.upper()} Post] {source_content[:180]}..."

    # 1. Stretch Goal: Grounding Check (Fails on hallucinated numbers)
    verify_grounding(source_content, raw_variant_text)

    # 2. Section 3 Requirement: Validate constraint profile (Length & Hashtag rules)
    validate_variant_constraints(platform, raw_variant_text)

    # 3. Store valid variant in database
    return create_variant(post_id, platform, raw_variant_text)