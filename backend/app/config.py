from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    telegram_bot_token: str = ""
    telegram_webapp_url: str = ""
    admin_telegram_id: int = 0
    database_url: str
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
    def is_postgres(self) -> bool:
        url = self.database_url.lower()
        return any(prefix in url for prefix in ("postgresql", "asyncpg", "postgres://"))

    @property
    def async_database_url(self) -> str:
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("sqlite"):
            url = url.replace("sqlite://", "sqlite+aiosqlite://", 1)
        return url

    model_config = {"env_file": ".env"}


settings = Settings()
