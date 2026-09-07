# app/models/profiles.py
from pydantic import BaseModel

class PlatformConstraint(BaseModel):
    platform: str
    max_length: int
    max_hashtags: int
    allowed_tone: str

# Platform Profiles Engine
CONSTRAINT_PROFILES = {
    "x": PlatformConstraint(platform="x", max_length=280, max_hashtags=2, allowed_tone="concise"),
    "discord": PlatformConstraint(platform="discord", max_length=2000, max_hashtags=5, allowed_tone="informal"),
    "linkedin": PlatformConstraint(platform="linkedin", max_length=3000, max_hashtags=5, allowed_tone="professional"),
    "telegram": PlatformConstraint(platform="telegram", max_length=4096, max_hashtags=10, allowed_tone="direct"),
}