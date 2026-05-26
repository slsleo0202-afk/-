import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "냉장고잇다"
    secret_key: str = "dev-secret-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7
    database_url: str = f"sqlite:///{BASE_DIR / 'data' / 'fridge_share.db'}"
    upload_dir: Path = BASE_DIR / "uploads"
    cors_origins: list[str] = ["*"]
    port: int = 8000
    seed_demo_on_startup: bool = True


settings = Settings()
if os.environ.get("UPLOAD_DIR"):
    settings.upload_dir = Path(os.environ["UPLOAD_DIR"])
if not settings.upload_dir.is_absolute():
    settings.upload_dir = BASE_DIR / settings.upload_dir

settings.upload_dir.mkdir(parents=True, exist_ok=True)
if settings.database_url.startswith("sqlite:///"):
    db_path = settings.database_url.replace("sqlite:///", "", 1)
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
