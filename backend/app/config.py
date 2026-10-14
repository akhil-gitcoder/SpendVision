from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = (
        "postgresql://finance_user:finance_password"
        "@localhost:5432/finance_dashboard"
    )

    ai_provider: str = "mock"
    ai_api_key: str = ""
    ai_model: str = "claude-3-5-haiku-20241022"

    cors_origins: str = "http://localhost:3000"
    environment: str = "development"

    # A login session lasts 7 days by default.
    session_lifetime_hours: int = Field(
        default=168,
        ge=1,
        le=720,
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    @property
    def is_ai_configured(self) -> bool:
        return (
            self.ai_provider.lower() != "mock"
            and bool(self.ai_api_key)
        )

    @property
    def secure_cookies(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()