from functools import lru_cache
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory for the project
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # LLM Settings
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.8-flash"
    MAX_CANDIDATES_FOR_LLM: int = 5
    LLM_TEMPERATURE: float = 0.2

    # Application Settings
    APP_ENV: str = "development"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    PORT: Optional[int] = None
    DEBUG: bool = True

    # Dataset & Storage Settings
    HUGGINGFACE_DATASET_ID: str = "ManikaSaini/zomato-restaurant-recommendation"
    RAW_DATA_DIR: Path = BASE_DIR / "data" / "raw"
    PROCESSED_DATA_DIR: Path = BASE_DIR / "data" / "processed"
    PROCESSED_DATA_FILE: Path = BASE_DIR / "data" / "processed" / "zomato_cleaned.parquet"

    # Pydantic Settings Config
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()

settings = get_settings()
