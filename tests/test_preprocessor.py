import pandas as pd
import pytest

from src.data_ingestion.preprocessor import (
    clean_boolean,
    clean_cost,
    clean_cuisines,
    clean_location,
    clean_rating,
    clean_votes,
    preprocess_dataset,
)

def test_clean_rating():
    # Valid ratings
    assert clean_rating("4.1/5") == 4.1
    assert clean_rating("3.9 / 5") == 3.9
    assert clean_rating("4.5") == 4.5
    assert clean_rating(4.0) == 4.0
    assert clean_rating("5.0/5") == 5.0
    assert clean_rating("0.0/5") == 0.0

    # Unrated or invalid ratings
    assert clean_rating("NEW") is None
    assert clean_rating("-") is None
    assert clean_rating("") is None
    assert clean_rating(None) is None
    assert clean_rating("Opening Soon") is None
    assert clean_rating("6.5/5") is None  # Out of 5.0 range

def test_clean_cost():
    # Standard numbers and formats
    assert clean_cost("800") == 800
    assert clean_cost("1,200") == 1200
    assert clean_cost("₹800 for two") == 800
    assert clean_cost("approx 450") == 450
    assert clean_cost(1500) == 1500

    # Edge cases
    assert clean_cost("0") is None
    assert clean_cost("-") is None
    assert clean_cost("NA") is None
    assert clean_cost("") is None
    assert clean_cost(None) is None

def test_clean_cuisines():
    # Standard comma-separated
    result = clean_cuisines("North Indian, Chinese, Fast Food")
    assert result == ["North Indian", "Chinese", "Fast Food"]

    # Inconsistent casing and whitespace
    result2 = clean_cuisines("  italian , continental  ")
    assert result2 == ["Italian", "Continental"]

    # Empty inputs
    assert clean_cuisines("") == []
    assert clean_cuisines(None) == []

def test_clean_location():
    assert clean_location("Banashankari  ") == "Banashankari"
    assert clean_location("indiranagar") == "Indiranagar"
    assert clean_location("  kalyan   nagar ") == "Kalyan Nagar"
    assert clean_location(None) == "Unknown"
    assert clean_location("") == "Unknown"

def test_clean_boolean():
    assert clean_boolean("Yes") is True
    assert clean_boolean("yes") is True
    assert clean_boolean("True") is True
    assert clean_boolean("No") is False
    assert clean_boolean(None) is False
    assert clean_boolean("") is False

def test_clean_votes():
    assert clean_votes(775) == 775
    assert clean_votes("150") == 150
    assert clean_votes(None) == 0
    assert clean_votes("none") == 0

def test_preprocess_dataset_synthetic():
    sample_data = {
        "name": ["Pasta Street", "Pasta Street", "Invalid Place", "Curry Bowl"],
        "rate": ["4.3/5", "4.3/5", "-", "3.8/5"],
        "approx_cost(for two people)": ["1,200", "1,200", None, "500"],
        "cuisines": ["Italian", "Italian", "Fast Food", "North Indian"],
        "location": ["Indiranagar", "Indiranagar", "Unknown", "Koramangala"],
        "address": ["100ft road", "100ft road", "", "5th block"],
        "votes": [1200, 500, 0, 300],
        "online_order": ["Yes", "Yes", "No", "No"],
        "book_table": ["Yes", "No", "No", "No"],
        "rest_type": ["Casual Dining", "Casual Dining", "Takeaway", "Dine-in"],
        "dish_liked": ["Pasta", "Pasta", "", "Biryani"],
        "listed_in(type)": ["Dine-out", "Delivery", "Delivery", "Dine-out"],
        "listed_in(city)": ["Indiranagar", "Indiranagar", "", "Koramangala"],
        "url": ["http://a.com", "http://a.com", "", "http://b.com"],
    }
    raw_df = pd.DataFrame(sample_data)
    cleaned = preprocess_dataset(raw_df)

    # Invalid place with Unknown location should be filtered out
    assert len(cleaned) == 2  # 1 duplicate Pasta Street removed, 1 Invalid Place removed

    # Pasta street should retain highest votes (1200)
    pasta = cleaned[cleaned["name"] == "Pasta Street"].iloc[0]
    assert pasta["votes"] == 1200
    assert pasta["rating"] == 4.3
    assert pasta["cost_for_two"] == 1200
    assert pasta["cuisines"] == ["Italian"]
    assert bool(pasta["online_order"]) is True

    # No null costs
    assert cleaned["cost_for_two"].isna().sum() == 0
