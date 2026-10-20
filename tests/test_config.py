from pathlib import Path
from src.config import Settings, get_settings

def test_settings_loaded():
    settings = get_settings()
    assert isinstance(settings, Settings)
    assert settings.HUGGINGFACE_DATASET_ID == "ManikaSaini/zomato-restaurant-recommendation"
    assert settings.RAW_DATA_DIR.name == "raw"
    assert settings.PROCESSED_DATA_DIR.name == "processed"
    assert settings.API_PORT == 8000
