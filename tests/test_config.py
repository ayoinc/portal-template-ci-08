"""Settings are read from environment variables."""

import pytest
from pydantic import ValidationError

from app.config import DEVELOPMENT_ONLY_DEFAULTS, Settings


def test_defaults_describe_a_development_environment() -> None:
    settings = Settings(_env_file=None)

    assert settings.app_name == "sample-python-api"
    assert settings.app_env == "development"


def test_environment_variables_override_the_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_NAME", "renamed")
    monkeypatch.setenv("APP_ENV", "staging")

    settings = Settings(_env_file=None)

    assert (settings.app_name, settings.app_env) == ("renamed", "staging")


def test_production_refuses_the_development_defaults() -> None:
    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None, app_env="production")

    for name in DEVELOPMENT_ONLY_DEFAULTS:
        assert name.upper() in str(error.value)


def test_production_accepts_replaced_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://service:s3cret@db.internal/app")
    monkeypatch.setenv("AUTH_PASSWORD", "a-password-set-for-production")
    monkeypatch.setenv("JWT_SECRET", "a-signing-secret-set-for-production-0123456789")

    settings = Settings(_env_file=None)

    assert settings.app_env == "production"
