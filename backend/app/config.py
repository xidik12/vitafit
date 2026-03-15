import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    telegram_bot_token: str = ""
    telegram_webapp_url: str = ""
    admin_telegram_id: int = 0
    database_url: str = "sqlite:///./vitafit.db"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24
    bot_username: str = ""
    spoonacular_api_key: str = ""
    usda_api_key: str = ""
    pexels_api_key: str = ""

    @property
    def effective_webapp_url(self) -> str:
        """Return the webapp URL, falling back to Railway's public domain if available."""
        if self.telegram_webapp_url:
            return self.telegram_webapp_url
        # Railway injects RAILWAY_PUBLIC_DOMAIN at runtime (e.g. vitafit-production.up.railway.app)
        railway_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")
        if railway_domain:
            return f"https://{railway_domain}"
        return ""

    @property
    def is_postgres(self) -> bool:
        url = self.database_url.lower()
        return any(prefix in url for prefix in ("postgresql", "asyncpg", "postgres://"))

    @property
    def async_database_url(self) -> str:
        url = self.database_url
        # Normalize all postgres variants to asyncpg
        for sync_prefix in (
            "postgresql+psycopg2://",
            "postgresql+psycopg://",
            "postgresql://",
            "postgres://",
        ):
            if url.startswith(sync_prefix):
                return "postgresql+asyncpg://" + url[len(sync_prefix):]
        if url.startswith("sqlite:///"):
            return "sqlite+aiosqlite:///" + url[len("sqlite:///"):]
        if url.startswith("sqlite://"):
            return "sqlite+aiosqlite://" + url[len("sqlite://"):]
        return url

    model_config = {"env_file": ".env"}


settings = Settings()
