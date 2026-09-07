import re
from app.models.profile import CONSTRAINT_PROFILES

class ConstraintViolationError(Exception):
    """Custom exception when a variant breaks a platform rule."""
    pass

def validate_variant(platform: str, content: str) -> bool:
    profile = CONSTRAINT_PROFILES.get(platform.lower())
    if not profile:
        raise ConstraintViolationError(f"Unknown platform profile: '{platform}'")

    # Rule 1: Length Check
    if len(content) > profile.max_length:
        raise ConstraintViolationError(
            f"[{platform.upper()}] Length rule broken: {len(content)} chars exceeds limit of {profile.max_length}."
        )

    # Rule 2: Hashtag Count Check
    hashtags = re.findall(r"#\w+", content)
    if len(hashtags) > profile.max_hashtags:
        raise ConstraintViolationError(
            f"[{platform.upper()}] Hashtag rule broken: Found {len(hashtags)} hashtags, max allowed is {profile.max_hashtags}."
        )

    return True