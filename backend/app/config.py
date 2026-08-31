from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_database_url(url: str) -> str:
    """Render/Railway often provide postgres:// — asyncpg needs postgresql+asyncpg://."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+asyncpg://postgres:devpass@localhost:5432/razorpay_merchant_website"
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    upload_dir: str = "/tmp/feed_uploads"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    # Public HTTPS URL of the deployed API (no trailing slash), e.g. https://your-app.onrender.com
    public_base_url: str = "http://localhost:8000"
    # Comma-separated browser origins allowed to call the REST API
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_db_url(cls, value: str) -> str:
        return normalize_database_url(value)

    @property
    def mcp_resource_url(self) -> str:
        return f"{self.public_base_url.rstrip('/')}/mcp"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def database_connect_args(self) -> dict:
        """Render Postgres requires SSL for external URLs."""
        if "sslmode=require" in self.database_url or "ssl=true" in self.database_url:
            return {"ssl": True}
        return {}


@lru_cache
def get_settings() -> Settings:
    return Settings()
