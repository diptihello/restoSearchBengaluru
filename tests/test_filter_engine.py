"""Unit and performance benchmark tests for Phase 2: FilterEngine & CandidateSelector."""

import time
import numpy as np
import pandas as pd
import pytest

from src.llm.schemas import CandidateRestaurant, UserPreferences
from src.retrieval.candidate_selector import (
    CandidateSelector,
    format_candidate_markdown_table,
    to_candidate_models,
)
from src.retrieval.filter_engine import (
    FilterEngine,
    compute_cuisine_overlap_vectorized,
    get_budget_range,
)


@pytest.fixture
def synthetic_dataset() -> pd.DataFrame:
    """Create a diverse synthetic restaurant DataFrame for deterministic testing."""
    records = [
        {
            "restaurant_id": 1,
            "name": "Toscano Indiranagar",
            "location": "Indiranagar",
            "city": "Bangalore",
            "address": "100 Feet Road, Indiranagar",
            "rating": 4.5,
            "is_rated": True,
            "votes": 1200,
            "cost_for_two": 1400,
            "cuisines": ["Italian", "Continental"],
            "cuisines_str": "Italian, Continental",
            "rest_type": "Casual Dining",
            "dish_liked": "Pasta, Tiramisu",
            "online_order": True,
            "book_table": True,
            "dining_type": "Dine-out",
        },
        {
            "restaurant_id": 2,
            "name": "Chianti Italian Restaurant",
            "location": "Indiranagar",
            "city": "Bangalore",
            "address": "12th Main, Indiranagar",
            "rating": 4.6,
            "is_rated": True,
            "votes": 850,
            "cost_for_two": 1500,
            "cuisines": ["Italian"],
            "cuisines_str": "Italian",
            "rest_type": "Fine Dining",
            "dish_liked": "Ravioli",
            "online_order": False,
            "book_table": True,
            "dining_type": "Dine-out",
        },
        {
            "restaurant_id": 3,
            "name": "Empire Restaurant",
            "location": "Indiranagar",
            "city": "Bangalore",
            "address": "80 Feet Road, Indiranagar",
            "rating": 3.9,
            "is_rated": True,
            "votes": 3500,
            "cost_for_two": 700,
            "cuisines": ["North Indian", "Biryani", "Mughlai"],
            "cuisines_str": "North Indian, Biryani, Mughlai",
            "rest_type": "Quick Bites",
            "dish_liked": "Ghee Rice, Chicken Kebab",
            "online_order": True,
            "book_table": False,
            "dining_type": "Dine-out",
        },
        {
            "restaurant_id": 4,
            "name": "Corner House Ice Cream",
            "location": "Indiranagar",
            "city": "Bangalore",
            "address": "CMH Road, Indiranagar",
            "rating": 4.7,
            "is_rated": True,
            "votes": 4200,
            "cost_for_two": 300,
            "cuisines": ["Desserts", "Ice Cream"],
            "cuisines_str": "Desserts, Ice Cream",
            "rest_type": "Dessert Parlor",
            "dish_liked": "Death by Chocolate",
            "online_order": True,
            "book_table": False,
            "dining_type": "Delivery",
        },
        {
            "restaurant_id": 5,
            "name": "Toit Brewpub",
            "location": "Indiranagar",
            "city": "Bangalore",
            "address": "100 Feet Road, Indiranagar",
            "rating": 4.8,
            "is_rated": True,
            "votes": 15000,
            "cost_for_two": 2000,
            "cuisines": ["Continental", "Pizza", "Finger Food"],
            "cuisines_str": "Continental, Pizza, Finger Food",
            "rest_type": "Microbrewery",
            "dish_liked": "Craft Beer, Wood Fired Pizza",
            "online_order": False,
            "book_table": True,
            "dining_type": "Pubs and Bars",
        },
        {
            "restaurant_id": 6,
            "name": "Bhojohori Manna",
            "location": "Koramangala",
            "city": "Bangalore",
            "address": "6th Block, Koramangala",
            "rating": 4.1,
            "is_rated": True,
            "votes": 900,
            "cost_for_two": 600,
            "cuisines": ["Bengali"],
            "cuisines_str": "Bengali",
            "rest_type": "Casual Dining",
            "dish_liked": "Fish Fry, Kosha Mangsho",
            "online_order": True,
            "book_table": False,
            "dining_type": "Dine-out",
        },
        {
            "restaurant_id": 7,
            "name": "Unrated Dhaba",
            "location": "Indiranagar",
            "city": "Bangalore",
            "address": "Old Madras Road, Indiranagar",
            "rating": None,
            "is_rated": False,
            "votes": 10,
            "cost_for_two": 400,
            "cuisines": ["North Indian"],
            "cuisines_str": "North Indian",
            "rest_type": "Dhaba",
            "dish_liked": "",
            "online_order": False,
            "book_table": False,
            "dining_type": "Dine-out",
        },
    ]
    return pd.DataFrame(records)


class TestFilterEngine:
    """Tests for deterministic filter rules in FilterEngine."""

    def test_budget_range_translation(self):
        assert get_budget_range("Low") == (0, 500)
        assert get_budget_range("Medium") == (500, 1500)
        assert get_budget_range("High") == (1500, 1000000)
        assert get_budget_range("Any") == (0, 1000000)

        # Explicit max budget override
        assert get_budget_range("Medium", max_budget=1200) == (500, 1200)
        assert get_budget_range("High", max_budget=2000) == (1500, 2000)

    def test_location_filtering(self, synthetic_dataset: pd.DataFrame):
        engine = FilterEngine(synthetic_dataset)
        prefs = UserPreferences(location="Koramangala", min_rating=0.0, budget_tier="Any")

        res = engine.filter(preferences=prefs)
        assert len(res) == 1
        assert res.iloc[0]["name"] == "Bhojohori Manna"

    def test_rating_filtering(self, synthetic_dataset: pd.DataFrame):
        engine = FilterEngine(synthetic_dataset)
        prefs = UserPreferences(location="Indiranagar", min_rating=4.5, budget_tier="Any")

        res = engine.filter(preferences=prefs)
        assert all(res["rating"] >= 4.5)
        # Unrated Dhaba with None rating must be excluded
        assert 7 not in res["restaurant_id"].values

    def test_cuisine_scoring_and_filtering(self, synthetic_dataset: pd.DataFrame):
        engine = FilterEngine(synthetic_dataset)
        prefs = UserPreferences(
            location="Indiranagar",
            budget_tier="Any",
            min_rating=0.0,
            cuisines=["Italian"],
        )

        res = engine.filter(preferences=prefs, require_cuisine_match=True)
        assert len(res) == 2
        # Toscano and Chianti should have score > 0
        assert set(res["restaurant_id"].values) == {1, 2}
        assert all(res["cuisine_score"] > 0)


class TestCandidateSelector:
    """Tests for candidate ranking, conversion, and constraint relaxation."""

    def test_candidate_selector_without_relaxation(self, synthetic_dataset: pd.DataFrame):
        selector = CandidateSelector(FilterEngine(synthetic_dataset))
        prefs = UserPreferences(
            location="Indiranagar",
            budget_tier="Medium",
            min_rating=3.5,
            cuisines=["Italian"],
        )

        candidates, was_relaxed, steps = selector.select_candidates(
            preferences=prefs,
            min_candidates=2,
        )

        assert was_relaxed is False
        assert len(steps) == 0
        assert len(candidates) == 2
        # Chianti (rating 4.6) should be ranked before Toscano (4.5)
        assert candidates.iloc[0]["name"] == "Chianti Italian Restaurant"
        assert candidates.iloc[1]["name"] == "Toscano Indiranagar"

    def test_constraint_relaxation_triggers_on_low_results(
        self, synthetic_dataset: pd.DataFrame
    ):
        selector = CandidateSelector(FilterEngine(synthetic_dataset))
        # Very restrictive preferences: Italian, Indiranagar, Min rating 4.9 (0 direct matches)
        prefs = UserPreferences(
            location="Indiranagar",
            budget_tier="Medium",
            min_rating=4.9,
            cuisines=["Italian"],
        )

        candidates, was_relaxed, steps = selector.select_candidates(
            preferences=prefs,
            min_candidates=2,
        )

        assert was_relaxed is True
        assert len(steps) > 0
        # Relaxation lowers rating threshold and allows candidates through
        assert len(candidates) >= 2
        assert any("rating" in s.lower() for s in steps)

    def test_to_candidate_models_conversion(self, synthetic_dataset: pd.DataFrame):
        models = to_candidate_models(synthetic_dataset.head(3))
        assert len(models) == 3
        assert isinstance(models[0], CandidateRestaurant)
        assert models[0].name == "Toscano Indiranagar"
        assert models[0].cost_for_two == 1400
        assert models[0].book_table is True

    def test_format_candidate_markdown_table(self, synthetic_dataset: pd.DataFrame):
        table = format_candidate_markdown_table(synthetic_dataset.head(2))
        assert "| ID | Name | Location | Rating | Votes | Cost (2) | Cuisines |" in table
        assert "Toscano Indiranagar" in table
        assert "Chianti Italian Restaurant" in table


class TestPerformanceBenchmark:
    """Benchmark test verifying < 15ms retrieval performance on 50,000 rows."""

    def test_filter_50k_rows_sub_15ms(self):
        n_rows = 50000
        np.random.seed(42)

        locations = np.random.choice(
            ["Indiranagar", "Koramangala", "Whitefield", "Jayanagar", "HSR Layout"],
            size=n_rows,
        )
        ratings = np.random.uniform(3.0, 5.0, size=n_rows)
        costs = np.random.randint(150, 3000, size=n_rows)
        votes = np.random.randint(5, 5000, size=n_rows)
        cuisines = np.random.choice(
            ["North Indian, Mughlai", "Italian, Continental", "Chinese, Fast Food", "Desserts, Bakery"],
            size=n_rows,
        )

        large_df = pd.DataFrame({
            "restaurant_id": np.arange(n_rows),
            "name": [f"Restaurant {i}" for i in range(n_rows)],
            "location": locations,
            "city": "Bangalore",
            "address": "Sample Address",
            "rating": ratings,
            "is_rated": True,
            "votes": votes,
            "cost_for_two": costs,
            "cuisines_str": cuisines,
            "cuisines": [c.split(", ") for c in cuisines],
            "rest_type": "Casual Dining",
            "dish_liked": "",
            "online_order": True,
            "book_table": False,
            "dining_type": "Dine-out",
        })

        engine = FilterEngine(large_df)
        prefs = UserPreferences(
            location="Indiranagar",
            budget_tier="Medium",
            min_rating=4.0,
            cuisines=["Italian"],
        )

        # Warm-up run
        _ = engine.filter(preferences=prefs)

        # Timed execution
        start_time = time.perf_counter()
        results = engine.filter(preferences=prefs)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        print(f"\n[BENCHMARK] Filtered {n_rows} rows in {elapsed_ms:.2f} ms ({len(results)} matches).")

        # Must execute in < 15ms per deliverable requirements
        assert elapsed_ms < 15.0, f"Filtering took {elapsed_ms:.2f} ms, exceeding 15ms threshold!"
        assert len(results) > 0
