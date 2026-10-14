from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_origin(value: str | None) -> str:
    """Canonical form for comparing origins: "https://Site.app/ " -> "https://site.app"."""
    if not value:
        return ""
    return value.strip().strip("'\"").strip().rstrip("/").lower()


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
        # Tolerate harmless formatting in the env var: spaces/newlines,
        # surrounding quotes, trailing slashes and capital letters.
        origins = []
        for raw in self.cors_origins.replace("\n", ",").split(","):
            origin = normalize_origin(raw)
            if origin:
                origins.append(origin)
        return origins

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