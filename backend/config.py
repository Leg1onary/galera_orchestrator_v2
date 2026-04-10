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


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),      # абсолютный путь, не зависит от CWD
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Auth
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "changeme"

    # JWT
    JWT_SECRET_KEY: str = "change-me-jwt-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24

    # Fernet
    FERNET_SECRET_KEY: str = "change-me-fernet-base64-key"

    # SSH
    SSH_KEY_PATH: str = "/root/.ssh/id_rsa"

    # Database
    DATABASE_URL: str = "sqlite:////data/orchestrator.db"

    # App
    APP_VERSION: str = "2.0.0"

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def jwt_key_not_default(cls, v: str) -> str:
        if v == "change-me-jwt-secret":
            print(
                "WARNING: JWT_SECRET_KEY is set to default value. "
                "Change it before production use.",
                file=sys.stderr,
            )
        return v

    @field_validator("FERNET_SECRET_KEY")
    @classmethod
    def fernet_key_valid(cls, v: str) -> str:
        if v == "change-me-fernet-base64-key":
            print(
                "WARNING: FERNET_SECRET_KEY is set to default value. "
                "Change it before production use.",
                file=sys.stderr,
            )
            # Дефолтный ключ невалиден для Fernet — заменяем на заглушку
            # чтобы не падать при импорте; реальные операции шифрования
            # всё равно не будут выполняться с этим ключом в prod
            return v
        # Валидируем что это корректный Fernet-ключ (32 bytes URL-safe base64)
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