from __future__ import annotations
from cryptography.fernet import Fernet
import base64

import sys
from functools import lru_cache
from pathlib import Path

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Корень проекта = родитель папки backend/
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"

_DEFAULT_SECRETS = {
    "change-me-jwt-secret",
    "change-me-jwt-secret-min-32-chars",
}
_DEFAULT_FERNET = {
    "change-me-fernet-base64-key",
    "change-me-fernet-key",
}
_DEFAULT_PASSWORDS = {"changeme"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Auth
    ADMIN_USERNAME: str = "admin"
    # Хранить bcrypt-хеш пароля. Генерация:
    # python -c "import bcrypt; print(bcrypt.hashpw(b'yourpassword', bcrypt.gensalt()).decode())"
    ADMIN_PASSWORD_HASH: str = "changeme"

    # JWT
    JWT_SECRET_KEY: str = "change-me-jwt-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 8

    # Cookie
    COOKIE_SECURE: bool = True

    # Fernet
    FERNET_SECRET_KEY: str = "change-me-fernet-base64-key"

    # SSH
    SSH_KEY_PATH: str = "/root/.ssh/id_rsa"
    SSH_CONNECT_TIMEOUT: int = 5
    SSH_COMMAND_TIMEOUT: int = 10

    # Database
    DATABASE_URL: str = "sqlite:////data/orchestrator.db"
    DB_CONNECT_TIMEOUT: int = 3

    # App
    APP_VERSION: str = "2.0.0"

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def jwt_key_not_default(cls, v: str) -> str:
        if v in _DEFAULT_SECRETS:
            raise ValueError(
                "FATAL: JWT_SECRET_KEY is set to a default value. "
                "Set a strong random secret (min 32 chars) before starting. "
                "Generate one with: openssl rand -hex 32"
            )
        if len(v) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must be at least 32 characters long."
            )
        return v

    @field_validator("ADMIN_PASSWORD_HASH")
    @classmethod
    def password_hash_not_default(cls, v: str) -> str:
        if v in _DEFAULT_PASSWORDS:
            raise ValueError(
                "FATAL: ADMIN_PASSWORD_HASH is set to a default value. "
                "Generate a bcrypt hash with: "
                "python -c \"import bcrypt; print(bcrypt.hashpw(b'yourpassword', bcrypt.gensalt()).decode())\""
            )
        if not v.startswith(("$2b$", "$2a$", "$2y$")):
            raise ValueError(
                "ADMIN_PASSWORD_HASH must be a valid bcrypt hash "
                "(starts with $2b$, $2a$, or $2y$)."
            )
        return v

    @field_validator("FERNET_SECRET_KEY")
    @classmethod
    def fernet_key_valid(cls, v: str) -> str:
        if v in _DEFAULT_FERNET:
            raise ValueError(
                "FATAL: FERNET_SECRET_KEY is set to a default value. "
                "Generate one with: "
                "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
        try:
            Fernet(v.encode())
        except Exception:
            raise ValueError(
                "FERNET_SECRET_KEY must be a valid URL-safe base64-encoded 32-byte key. "
                "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
        return v

    @model_validator(mode="after")
    def secrets_must_differ(self) -> "Settings":
        if self.JWT_SECRET_KEY == self.FERNET_SECRET_KEY:
            raise ValueError(
                "JWT_SECRET_KEY and FERNET_SECRET_KEY must be different values. "
                "Using the same secret for both is not allowed."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
