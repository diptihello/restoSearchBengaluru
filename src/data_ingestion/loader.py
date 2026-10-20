"""Data ingestion and loader module for the Zomato dataset."""

import logging
from pathlib import Path
from typing import Optional
import pandas as pd
from datasets import load_dataset

from src.config import settings
from src.data_ingestion.preprocessor import preprocess_dataset

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

RAW_CACHE_FILE = settings.RAW_DATA_DIR / "zomato_raw.parquet"
PROCESSED_FILE = settings.PROCESSED_DATA_FILE

def fetch_raw_dataset(force_download: bool = False) -> pd.DataFrame:
    """
    Load raw Zomato dataset from local disk cache or download from Hugging Face Hub.
    """
    settings.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not force_download and RAW_CACHE_FILE.exists():
        logger.info("Loading cached raw dataset from %s", RAW_CACHE_FILE)
        return pd.read_parquet(RAW_CACHE_FILE)

    logger.info("Fetching dataset '%s' from Hugging Face Hub...", settings.HUGGINGFACE_DATASET_ID)
    ds = load_dataset(settings.HUGGINGFACE_DATASET_ID, split="train")
    df = ds.to_pandas()

    logger.info("Raw dataset fetched with %d rows. Caching to %s", len(df), RAW_CACHE_FILE)
    df.to_parquet(RAW_CACHE_FILE, index=False)
    return df

def get_processed_dataset(force_reprocess: bool = False) -> pd.DataFrame:
    """
    Get the cleaned, processed dataset from parquet file or trigger pipeline if not present.
    """
    settings.PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not force_reprocess and PROCESSED_FILE.exists():
        logger.info("Loading processed dataset from %s", PROCESSED_FILE)
        return pd.read_parquet(PROCESSED_FILE)

    logger.info("Processed dataset not found. Running ingestion and preprocessing pipeline...")
    raw_df = fetch_raw_dataset()
    cleaned_df = preprocess_dataset(raw_df)
    
    logger.info("Saving cleaned dataset (%d rows) to %s", len(cleaned_df), PROCESSED_FILE)
    cleaned_df.to_parquet(PROCESSED_FILE, index=False)
    return cleaned_df

def run_pipeline() -> Path:
    """
    Entry point to run end-to-end ingestion and preprocessing.
    """
    logger.info("=" * 60)
    logger.info("STARTING PHASE 1 DATA INGESTION & PREPROCESSING")
    logger.info("=" * 60)

    cleaned_df = get_processed_dataset(force_reprocess=True)
    
    # Validation checks
    assert PROCESSED_FILE.exists(), f"Output file {PROCESSED_FILE} was not created!"
    assert len(cleaned_df) > 0, "Processed DataFrame is empty!"
    assert cleaned_df["cost_for_two"].isna().sum() == 0, "Cleaned dataset contains unparseable null cost values!"
    
    logger.info("=" * 60)
    logger.info("PIPELINE COMPLETED SUCCESSFULLY!")
    logger.info("Processed records: %d", len(cleaned_df))
    logger.info("Output file: %s (Size: %.2f MB)", PROCESSED_FILE, PROCESSED_FILE.stat().st_size / (1024 * 1024))
    logger.info("=" * 60)
    return PROCESSED_FILE

if __name__ == "__main__":
    run_pipeline()
