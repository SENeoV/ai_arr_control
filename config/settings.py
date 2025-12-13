from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

class Settings(BaseSettings):
    app_name: str = "AI Arr Control"
    debug: bool = False
    radarr_url: str
    radarr_api_key: str
    sonarr_url: str
    sonarr_api_key: str
    prowlarr_url: str
    prowlarr_api_key: str
    database_url: str = f"sqlite+aiosqlite:///{BASE_DIR}/db/app.db"

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env")

settings = Settings()
