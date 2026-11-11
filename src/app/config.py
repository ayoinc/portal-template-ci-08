"""Settings read from environment variables and an optional .env file."""

from typing import Literal, Self

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Settings whose default is public knowledge and must be replaced before production.
DEVELOPMENT_ONLY_DEFAULTS = [
    "database_url",
    "auth_password",
    "jwt_secret",
]


class Settings(BaseSettings):
    """Every field is set by the environment variable of the same name in upper case."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "sample-python-api"
    app_env: Literal["development", "staging", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # SQLAlchemy URL of the database. The application connects on the first query.
    database_url: str = "postgresql+asyncpg://app:app@localhost:5432/app"

    # Without REDIS_URL items are cached in the memory of each process.
    redis_url: str | None = None
    cache_ttl_seconds: int = 60

    auth_username: str = "admin"
    auth_password: SecretStr = SecretStr("change-me")
    jwt_secret: SecretStr = SecretStr("development-only-secret-replace-me-0123456789")
    jwt_expire_minutes: int = 30

    # Requests allowed per client address, in the notation of the limits library.
    rate_limit: str = "100/minute"

    # JSON list, for example CORS_ORIGINS='["https://app.example.com"]'.
    cors_origins: list[str] = ["http://localhost:3000"]

    @model_validator(mode="after")
    def refuse_development_defaults_in_production(self) -> Self:
        if self.app_env == "production":
            unchanged = [
                name
                for name in DEVELOPMENT_ONLY_DEFAULTS
                if getattr(self, name) == type(self).model_fields[name].default
            ]
            if unchanged:
                variables = ", ".join(name.upper() for name in unchanged)
                raise ValueError(f"set {variables} before running with APP_ENV=production")
        return self
