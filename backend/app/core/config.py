"""Application settings loaded from environment / .env."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "I2C"
    app_mode: Literal["development", "production", "test"] = "development"
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60 * 24 * 7
    public_base_url: str = "http://localhost:3000"
    api_base_url: str = "http://localhost:8000"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    database_url: str = "sqlite:///./i2c.db"

    # Storage
    storage_provider: Literal["local", "s3"] = "local"
    media_root: Path = Path("./media")
    media_url: str = "/media"
    s3_endpoint_url: str = ""
    s3_bucket: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_region: str = ""

    # Upload limits
    max_upload_mb: int = 12
    max_image_dimension: int = 6000
    min_image_dimension: int = 100

    # Feature flags
    ai_recognition_enabled: bool = True
    ai_descriptions_enabled: bool = True
    background_removal_enabled: bool = True
    virtual_model_enabled: bool = False
    video_enabled: bool = False
    ninerouter_enabled: bool = False
    mock_providers_enabled: bool = True

    # AI providers
    ai_request_timeout_seconds: float = 45.0
    health_check_interval_seconds: float = 300.0
    local_rembg_enabled: bool = True
    ninerouter_base_url: str = ""
    ninerouter_api_key: str = ""
    ninerouter_vision_model: str = ""
    ninerouter_text_model: str = ""

    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_api_key: str = ""
    openrouter_vision_model: str = "qwen/qwen2.5-vl-72b-instruct:free"
    openrouter_text_model: str = "meta-llama/llama-3.3-70b-instruct:free"

    openai_compatible_base_url: str = ""
    openai_compatible_api_key: str = ""
    openai_compatible_vision_model: str = ""
    openai_compatible_text_model: str = ""

    openai_image_base_url: str = ""
    openai_image_api_key: str = ""
    openai_image_model: str = ""
    openai_image_cost_per_image: float = 0.0
    ai_image_timeout_seconds: float = 120.0

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-haiku-4-5-20251001"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, v: object) -> object:
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @property
    def is_production(self) -> bool:
        return self.app_mode == "production"

    @property
    def mocks_allowed(self) -> bool:
        return self.mock_providers_enabled and not self.is_production

    def feature_flags(self) -> dict[str, bool]:
        return {
            "ai_recognition": self.ai_recognition_enabled,
            "ai_descriptions": self.ai_descriptions_enabled,
            "background_removal": self.background_removal_enabled,
            "virtual_model": self.virtual_model_enabled,
            "video_generation": self.video_enabled,
            "ninerouter": self.ninerouter_enabled,
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
