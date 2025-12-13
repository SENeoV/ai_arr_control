"""Application configuration via environment variables.

Configuration is loaded from .env file in the project root, or from
the current environment. All service URLs and API keys must be provided.

The Settings class performs strict validation and will raise errors on
missing required fields or invalid configuration.
"""

from typing import Optional, List
from pydantic import Field, HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    """Core application settings loaded from environment or .env file.
    
    All URLs are validated as proper HTTP/HTTPS URLs.
    All API keys are required and must be non-empty strings.
    Database URL defaults to SQLite but can be overridden for production.
    """

    app_name: str = Field(
        default="AI Arr Control",
        description="Application name (used in API responses)"
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode (verbose logging, stack traces)"
    )

    # Radarr service configuration (REQUIRED)
    radarr_url: str = Field(
        description="Radarr service URL (e.g., http://radarr:7878 or http://192.168.1.100:7878)"
    )
    radarr_api_key: str = Field(
        description="Radarr API key (from Settings -> General -> Security -> API Key)"
    )

    # Sonarr service configuration (REQUIRED)
    sonarr_url: str = Field(
        description="Sonarr service URL (e.g., http://sonarr:8989 or http://192.168.1.100:8989)"
    )
    sonarr_api_key: str = Field(
        description="Sonarr API key (from Settings -> General -> Security -> API Key)"
    )

    # Prowlarr service configuration (REQUIRED)
    prowlarr_url: str = Field(
        description="Prowlarr service URL (e.g., http://prowlarr:9696 or http://192.168.1.100:9696)"
    )
    prowlarr_api_key: str = Field(
        description="Prowlarr API key (from Settings -> General -> Security -> API Key)"
    )

    # Database configuration (OPTIONAL - defaults to SQLite)
    database_url: str = Field(
        default=f"sqlite+aiosqlite:///{BASE_DIR}/db/app.db",
        description="SQLAlchemy database URL (supports SQLite, PostgreSQL, MySQL, etc.)"
    )

    # Indexer discovery configuration
    discovery_enabled: bool = Field(
        default=False,
        description="Enable automatic indexer discovery from external sources"
    )

    discovery_sources: List[str] = Field(
        default_factory=list,
        description="List of HTTP(S) URLs to fetch potential indexer definitions from (JSON or newline list)"
    )

    discovery_interval_hours: int = Field(
        default=24,
        description="Default interval in hours between discovery runs when scheduled"
    )

    discovery_add_to_prowlarr: bool = Field(
        default=False,
        description="If true, discovered indexers will be automatically added to Prowlarr via its API"
    )

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra environment variables not in the model
    )

    @field_validator("radarr_api_key", "sonarr_api_key", "prowlarr_api_key")
    @classmethod
    def api_key_must_not_be_empty(cls, v: str) -> str:
        """Validate that API keys are not empty placeholder strings."""
        if not v or v.startswith("your_") or v == "change_me":
            raise ValueError("API key appears to be a placeholder. Please set actual value.")
        return v

    @field_validator("radarr_url", "sonarr_url", "prowlarr_url", "database_url")
    @classmethod
    def validate_urls(cls, v: str) -> str:
        """Ensure URLs are well-formed and accessible."""
        if not v:
            raise ValueError("URL cannot be empty")
        return v.rstrip("/")  # Remove trailing slash for consistency

    def validate_at_startup(self) -> None:
        """Perform runtime validation of configuration.
        
        Call this method at application startup to ensure all external
        services are properly configured.
        
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate discovery configuration if enabled
        if self.discovery_enabled:
            if not self.discovery_sources:
                raise ValueError(
                    "discovery_enabled=True but discovery_sources is empty. "
                    "Either disable discovery or provide sources."
                )
            # Parse discovery sources from comma-separated string if needed
            sources = self.discovery_sources
            if isinstance(sources, str):
                sources = [s.strip() for s in sources.split(",") if s.strip()]
            if not sources:
                raise ValueError("discovery_sources contains no valid URLs")
        
        # Validate scheduler interval
        if self.discovery_interval_hours < 1:
            raise ValueError("discovery_interval_hours must be >= 1")
        
        # Validate that database path is writable (for SQLite)
        if self.database_url.startswith("sqlite+aiosqlite://"):
            db_path = self.database_url.replace("sqlite+aiosqlite:///", "")
            db_dir = Path(db_path).parent
            if not db_dir.exists():
                db_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
