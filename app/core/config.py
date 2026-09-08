import os
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Social Media Studio"
    DEBUG: bool = True

    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DB_PATH: str = os.path.join(BASE_DIR, "data", "studio.db")

    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

    DISCORD_WEBHOOK_URL: str = os.getenv("DISCORD_WEBHOOK_URL", "")

    model_config = ConfigDict(env_file=".env", extra="ignore")


settings = Settings()