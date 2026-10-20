"""Deterministic filtering engine for high-speed candidate restaurant retrieval (Stage 1)."""

import logging
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np
import pandas as pd

from src.config import settings
from src.data_ingestion.loader import get_processed_dataset
from src.llm.schemas import UserPreferences

logger = logging.getLogger(__name__)

# Standard budget tier cost brackets (cost for two in INR)
BUDGET_TIERS: Dict[str, Tuple[int, int]] = {
    "low": (0, 500),
    "medium": (500, 1500),
    "high": (1500, 1000000),
    "any": (0, 1000000),
}


def get_budget_range(
    tier: Optional[str] = "Medium",
    max_budget: Optional[int] = None,
) -> Tuple[int, int]:
    """
    Translate budget tier and optional explicit max budget into (min_cost, max_cost).
    """
    tier_key = (tier or "any").strip().lower()
    min_cost, max_cost = BUDGET_TIERS.get(tier_key, (0, 1000000))

    if max_budget is not None and max_budget > 0:
        max_cost = min(max_cost, max_budget)
        if min_cost > max_cost:
            min_cost = 0

    return min_cost, max_cost


def compute_cuisine_overlap_vectorized(
    df: pd.DataFrame,
    target_cuisines: List[str],
) -> pd.Series:
    """
    Compute cuisine overlap score for each restaurant using fast vectorized matching.
    Returns a pandas Series with integer match counts.
    """
    if not target_cuisines or len(df) == 0:
        return pd.Series(0, index=df.index, dtype=int)

    normalized_targets = [c.strip().lower() for c in target_cuisines if c.strip()]
    if not normalized_targets:
        return pd.Series(0, index=df.index, dtype=int)

    col = "cuisines_str" if "cuisines_str" in df.columns else "cuisines"
    text_series = df[col].astype(str)

    score_series = pd.Series(0, index=df.index, dtype=int)
    for target in normalized_targets:
        score_series += text_series.str.contains(target, case=False, regex=False, na=False).astype(int)

    return score_series


class FilterEngine:
    """
    High-speed deterministic filter engine for tabular restaurant candidate retrieval.
    Applies optimized ordered masking (numeric filters first, text filters second)
    to achieve sub-10ms performance on 50,000+ records.
    """

    def __init__(self, dataset: Optional[pd.DataFrame] = None):
        if dataset is not None:
            self._dataset = dataset
        else:
            self._dataset = None

    @property
    def dataset(self) -> pd.DataFrame:
        """Lazily load the processed dataset if not explicitly injected."""
        if self._dataset is None:
            self._dataset = get_processed_dataset()
        return self._dataset

    def filter(
        self,
        preferences: UserPreferences,
        df: Optional[pd.DataFrame] = None,
        min_cost: Optional[int] = None,
        max_cost: Optional[int] = None,
        min_rating: Optional[float] = None,
        location: Optional[str] = None,
        require_cuisine_match: bool = False,
    ) -> pd.DataFrame:
        """
        Apply deterministic boolean masks across budget, rating, location, and cuisine.
        Returns a filtered DataFrame copy with an added 'cuisine_score' column.
        """
        data = df if df is not None else self.dataset
        if data.empty:
            empty_res = data.copy()
            empty_res["cuisine_score"] = 0
            return empty_res

        # 1. Budget Bounds
        if min_cost is None or max_cost is None:
            default_min, default_max = get_budget_range(
                tier=preferences.budget_tier,
                max_budget=preferences.max_budget,
            )
            min_cost = default_min if min_cost is None else min_cost
            max_cost = default_max if max_cost is None else max_cost

        # 2. Rating Threshold
        if min_rating is None:
            min_rating = preferences.min_rating if preferences.min_rating is not None else 0.0

        # Optimization: Apply fast numeric masks using NumPy arrays FIRST
        num_mask = np.ones(len(data), dtype=bool)

        if "cost_for_two" in data.columns and (min_cost > 0 or max_cost < 1000000):
            costs = data["cost_for_two"].to_numpy()
            num_mask &= (costs >= min_cost) & (costs <= max_cost)

        if "rating" in data.columns and min_rating > 0.0:
            ratings = data["rating"].to_numpy(dtype=float)
            num_mask &= ~np.isnan(ratings) & (ratings >= min_rating)

        # Early exit if numeric mask eliminates all candidates
        if not np.any(num_mask):
            empty_res = data.iloc[0:0].copy()
            empty_res["cuisine_score"] = 0
            return empty_res

        # Subset dataframe to numeric matches
        subset = data.iloc[num_mask]

        # 3. Location Matching on narrowed subset
        target_loc = (location if location is not None else preferences.location or "").strip()
        loc_mask = pd.Series(True, index=subset.index)

        if target_loc and target_loc.lower() not in ("all", "any"):
            norm_loc = target_loc.lower()
            loc_series = subset["location"].astype(str)
            loc_matched = loc_series.str.contains(norm_loc, case=False, regex=False, na=False)

            # Fallback to city or address only if location yielded no matches
            if not loc_matched.any() and "city" in subset.columns:
                loc_matched = subset["city"].astype(str).str.contains(norm_loc, case=False, regex=False, na=False)
            if not loc_matched.any() and "address" in subset.columns:
                loc_matched = subset["address"].astype(str).str.contains(norm_loc, case=False, regex=False, na=False)

            loc_mask = loc_matched

        # 4. Dining Type filtering
        dt_mask = pd.Series(True, index=subset.index)
        if preferences.dining_type and preferences.dining_type.lower() not in ("any", "all", ""):
            target_dt = preferences.dining_type.strip()
            dt_matched = pd.Series(False, index=subset.index)
            if "dining_type" in subset.columns:
                dt_matched = dt_matched | subset["dining_type"].astype(str).str.contains(
                    target_dt, case=False, regex=False, na=False
                )
            if "rest_type" in subset.columns:
                dt_matched = dt_matched | subset["rest_type"].astype(str).str.contains(
                    target_dt, case=False, regex=False, na=False
                )
            dt_mask = dt_matched

        combined_mask = loc_mask & dt_mask
        filtered_df = subset[combined_mask].copy()

        # 5. Cuisine Scoring & Filter
        if preferences.cuisines:
            filtered_df["cuisine_score"] = compute_cuisine_overlap_vectorized(
                filtered_df, preferences.cuisines
            )
            if require_cuisine_match:
                filtered_df = filtered_df[filtered_df["cuisine_score"] > 0]
        else:
            filtered_df["cuisine_score"] = 0

        return filtered_df
