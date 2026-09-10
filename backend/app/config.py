import os
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings for DLAS.
    Reads from environment variables and optional .env file.
    NEVER logs or exposes secret values.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Core Environment
    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "Digital Legal Aid System (DLAS)"
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS: Allow all Vercel domains, Render, local dev, and configured origins
    CORS_ORIGINS: str = "*"

    # Security & Auth (Backend Only)
    SECRET_KEY: str = "dlas_dev_jwt_secret_key_change_in_production_f928e4708a32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Authoritative Database (Render PostgreSQL or SQLite fallback)
    DATABASE_URL: str = "sqlite:///./dlas.db"

    # AI Service (Google Gemini - Backend Only)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # Telephony Service (Twilio - Backend Only)
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    TWILIO_VOICE_LANGUAGE: str = "bn-BD"

    # Mock NID Adapter (Demo mode - zero fictional government claims)
    NID_SERVICE_MODE: str = "mock"
    IDENTITY_PROVIDER: str = "mock"  # mock or authorised

    @property
    def cors_origin_list(self) -> List[str]:
        if not self.CORS_ORIGINS or self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        # Render sometimes provides postgres:// instead of postgresql://
        if isinstance(v, str) and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v


settings = Settings()
