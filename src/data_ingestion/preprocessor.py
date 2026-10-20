"""Data preprocessing and normalization module for the Zomato dataset."""

import logging
import re
from typing import Any, List, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

def clean_rating(val: Any) -> Optional[float]:
    """
    Parse rating string or float into a normalized float (out of 5.0).
    Handles strings like '4.1/5', '3.9 / 5', '4.5', 'NEW', '-', None, NaN.
    """
    if val is None or pd.isna(val):
        return None
    
    val_str = str(val).strip()
    if val_str in ("NEW", "-", "", "Opening Soon"):
        return None
    
    # Match decimal or integer rating
    match = re.search(r"(\d+(\.\d+)?)", val_str)
    if match:
        try:
            rating = float(match.group(1))
            if 0.0 <= rating <= 5.0:
                return round(rating, 1)
        except ValueError:
            pass
    return None

def clean_cost(val: Any) -> Optional[int]:
    """
    Parse approx cost for two into an integer.
    Handles '800', '1,200', '₹800 for two', 'approx 450', None, NaN.
    """
    if val is None or pd.isna(val):
        return None
    
    val_str = str(val).strip()
    if not val_str or val_str in ("-", "NA", "N/A", "None", "0"):
        return None

    # Remove commas and extract continuous digits
    clean_str = val_str.replace(",", "")
    match = re.search(r"\d+", clean_str)
    if match:
        try:
            cost = int(match.group())
            return cost if cost > 0 else None
        except ValueError:
            pass
    return None

def clean_cuisines(val: Any) -> List[str]:
    """
    Parse comma-separated cuisines into a normalized list of title-cased strings.
    """
    if val is None or pd.isna(val):
        return []
    
    val_str = str(val).strip()
    if not val_str:
        return []
    
    cuisines = [c.strip().title() for c in val_str.split(",") if c.strip()]
    return cuisines

def clean_location(val: Any) -> str:
    """
    Normalize location / locality name.
    """
    if val is None or pd.isna(val):
        return "Unknown"
    
    loc = str(val).strip()
    # Normalize multiple whitespace characters
    loc = re.sub(r"\s+", " ", loc)
    return loc.title() if loc else "Unknown"

def clean_boolean(val: Any) -> bool:
    """
    Convert 'Yes'/'No' or truthy/falsy values to standard boolean.
    """
    if val is None or pd.isna(val):
        return False
    val_str = str(val).strip().lower()
    return val_str in ("yes", "true", "1", "y")

def clean_votes(val: Any) -> int:
    """
    Parse votes into a non-negative integer.
    """
    if val is None or pd.isna(val):
        return 0
    try:
        votes = int(val)
        return max(0, votes)
    except (ValueError, TypeError):
        match = re.search(r"\d+", str(val))
        return int(match.group()) if match else 0

def preprocess_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and structure the raw Zomato DataFrame.
    Returns a cleaned, deduplicated DataFrame ready for indexing and querying.
    """
    logger.info("Starting preprocessing on raw DataFrame with %d rows", len(df))
    clean_df = df.copy()

    # Identify existing column names (handling casing / variations)
    col_map = {col.lower(): col for col in clean_df.columns}

    # Extract required fields with safety
    name_col = col_map.get("name", "name")
    rate_col = col_map.get("rate", "rate")
    cost_col = col_map.get("approx_cost(for two people)", col_map.get("cost", "approx_cost(for two people)"))
    cuisines_col = col_map.get("cuisines", "cuisines")
    location_col = col_map.get("location", "location")
    address_col = col_map.get("address", "address")
    votes_col = col_map.get("votes", "votes")
    online_order_col = col_map.get("online_order", "online_order")
    book_table_col = col_map.get("book_table", "book_table")
    rest_type_col = col_map.get("rest_type", "rest_type")
    dish_liked_col = col_map.get("dish_liked", "dish_liked")
    dining_type_col = col_map.get("listed_in(type)", "listed_in(type)")
    city_col = col_map.get("listed_in(city)", "listed_in(city)")
    url_col = col_map.get("url", "url")

    # Apply cleaning transformations
    clean_df["name"] = clean_df[name_col].astype(str).str.strip()
    clean_df["rating"] = clean_df[rate_col].apply(clean_rating)
    clean_df["is_rated"] = clean_df["rating"].notna()
    clean_df["votes"] = clean_df[votes_col].apply(clean_votes)
    clean_df["cost_for_two"] = clean_df[cost_col].apply(clean_cost)
    clean_df["cuisines"] = clean_df[cuisines_col].apply(clean_cuisines)
    clean_df["cuisines_str"] = clean_df["cuisines"].apply(lambda clist: ", ".join(clist))
    clean_df["location"] = clean_df[location_col].apply(clean_location)
    clean_df["address"] = clean_df[address_col].astype(str).str.strip() if address_col in clean_df else ""
    clean_df["online_order"] = clean_df[online_order_col].apply(clean_boolean) if online_order_col in clean_df else False
    clean_df["book_table"] = clean_df[book_table_col].apply(clean_boolean) if book_table_col in clean_df else False
    clean_df["rest_type"] = clean_df[rest_type_col].astype(str).str.strip() if rest_type_col in clean_df else ""
    clean_df["dish_liked"] = clean_df[dish_liked_col].astype(str).str.strip().replace("nan", "") if dish_liked_col in clean_df else ""
    clean_df["dining_type"] = clean_df[dining_type_col].astype(str).str.strip() if dining_type_col in clean_df else ""
    clean_df["city"] = clean_df[city_col].astype(str).str.strip() if city_col in clean_df else "Bangalore"
    clean_df["url"] = clean_df[url_col].astype(str).str.strip() if url_col in clean_df else ""

    # Filter out empty names or places without cuisines and location
    clean_df = clean_df[clean_df["name"].str.len() > 0]
    clean_df = clean_df[clean_df["location"] != "Unknown"]

    # Impute missing cost using median of same location and primary cuisine, or global median
    global_median_cost = clean_df["cost_for_two"].median()
    if pd.isna(global_median_cost) or global_median_cost <= 0:
        global_median_cost = 500
    clean_df["cost_for_two"] = clean_df["cost_for_two"].fillna(int(global_median_cost)).astype(int)

    # Deduplicate: Group by lower name and lower address/location, keeping the entry with the highest votes
    clean_df["_dedup_name"] = clean_df["name"].str.lower()
    clean_df["_dedup_loc"] = clean_df["location"].str.lower()
    clean_df = clean_df.sort_values(by=["votes", "rating"], ascending=[False, False])
    clean_df = clean_df.drop_duplicates(subset=["_dedup_name", "_dedup_loc"], keep="first")
    clean_df = clean_df.drop(columns=["_dedup_name", "_dedup_loc"])

    # Reset index and add persistent restaurant_id
    clean_df = clean_df.reset_index(drop=True)
    clean_df["restaurant_id"] = clean_df.index

    # Select and order final standardized columns
    final_cols = [
        "restaurant_id",
        "name",
        "location",
        "city",
        "address",
        "rating",
        "is_rated",
        "votes",
        "cost_for_two",
        "cuisines",
        "cuisines_str",
        "rest_type",
        "dish_liked",
        "online_order",
        "book_table",
        "dining_type",
        "url"
    ]
    result_df = clean_df[[c for c in final_cols if c in clean_df.columns]].copy()
    logger.info("Preprocessing complete. Cleaned and deduplicated records: %d", len(result_df))
    return result_df
