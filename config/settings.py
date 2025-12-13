"""Application configuration via environment variables.

Configuration is loaded from .env file in the project root, or from
the current environment. All service URLs and API keys must be provided.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    """Core application settings loaded from environment or .env file."""

    app_name: str = "AI Arr Control"
    debug: bool = Field(default=False, description="Enable debug mode")

    # Radarr service configuration
    radarr_url: str = Field(
        description="Radarr service URL (e.g., http://radarr:7878)"
    )
    radarr_api_key: str = Field(description="Radarr API key")

    # Sonarr service configuration
    sonarr_url: str = Field(
        description="Sonarr service URL (e.g., http://sonarr:8989)"
    )
    sonarr_api_key: str = Field(description="Sonarr API key")

    # Prowlarr service configuration
    prowlarr_url: str = Field(
        description="Prowlarr service URL (e.g., http://prowlarr:9696)"
    )
    prowlarr_api_key: str = Field(description="Prowlarr API key")

    # Database configuration
    database_url: str = Field(
        default=f"sqlite+aiosqlite:///{BASE_DIR}/db/app.db",
        description="SQLAlchemy database URL",
    )

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra environment variables not in the model
    )


settings = Settings()
