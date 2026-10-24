"""
app/core/config.py
------------------
Centralized configuration management using Pydantic Settings.
Loads environment variables safely from .env file or host environment.
"""

import os
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application Info
    APP_NAME: str = "SIMS — Sales Intelligence and Management System"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # Host & Port
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000

    # Security & JWT
    SECRET_KEY: str = "default-insecure-dev-secret-key-change-in-production-32chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Demo Credentials
    DEMO_PASSWORD: str = "Demo12345!"

    # Database Configuration (MongoDB)
    MONGODB_URI: str = "mongodb://localhost:27017/"
    MONGODB_DB_NAME: str = "sims_db"
    TEST_MONGODB_DB_NAME: str = "sims_test_db"
    USE_MOCK_MONGO: bool = False
    REQUIRE_PERSISTENT_DB: bool = False
    AUTO_SEED_DEMO_DATA: bool = True
    MONGODB_TIMEOUT_MS: int = 20000

    # Rate Limiting & Security Controls
    LOGIN_RATE_LIMIT_MAX_ATTEMPTS: int = 5
    LOGIN_RATE_LIMIT_WINDOW_SECONDS: int = 900
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    MAX_UPLOAD_SIZE_BYTES: int = 15 * 1024 * 1024  # 15 MB limit for file uploads

    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    def validate_runtime_security(self):
        """Validates critical security constraints based on environment."""
        known_insecure_keys = {
            "default-insecure-dev-secret-key-change-in-production-32chars",
            "sims-super-secret-development-key-change-in-production-1234567890",
        }
        if self.ENVIRONMENT.lower() in ("production", "staging"):
            if "default" in self.SECRET_KEY.lower() or len(self.SECRET_KEY) < 32 or self.SECRET_KEY in known_insecure_keys:
                raise ValueError(
                    "CRITICAL SECURITY FAILURE: Production environment requires a cryptographically strong "
                    "SECRET_KEY with at least 32 characters and no default or example insecure values."
                )
            if self.USE_MOCK_MONGO:
                raise ValueError(
                    "CRITICAL CONFIGURATION ERROR: USE_MOCK_MONGO cannot be enabled in production or staging."
                )
            # Enforce persistent DB and disable auto-seed in production and staging
            self.REQUIRE_PERSISTENT_DB = True
            self.AUTO_SEED_DEMO_DATA = False

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
settings.validate_runtime_security()
