"""Constraint relaxation strategy and candidate ranking before LLM reasoning (Stage 1)."""

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.config import settings
from src.llm.schemas import CandidateRestaurant, UserPreferences
from src.retrieval.filter_engine import FilterEngine, get_budget_range

logger = logging.getLogger(__name__)


def to_candidate_models(candidates_df: pd.DataFrame) -> List[CandidateRestaurant]:
    """
    Convert a candidate DataFrame into a list of validated CandidateRestaurant Pydantic models.
    """
    candidate_models: List[CandidateRestaurant] = []

    for idx, row in candidates_df.iterrows():
        # Clean and safely extract fields
        r_id = int(row.get("restaurant_id", idx))
        name = str(row.get("name", f"Restaurant {r_id}"))
        location = str(row.get("location", "Bangalore"))

        rating_val = row.get("rating")
        try:
            rating = float(rating_val) if rating_val is not None and not pd.isna(rating_val) else None
        except (ValueError, TypeError):
            rating = None

        votes_val = row.get("votes")
        try:
            votes = int(votes_val) if votes_val is not None and not pd.isna(votes_val) else 0
        except (ValueError, TypeError):
            votes = 0

        cost_val = row.get("cost_for_two")
        try:
            cost_for_two = int(cost_val) if cost_val is not None and not pd.isna(cost_val) else 0
        except (ValueError, TypeError):
            cost_for_two = 0

        cuisines = row.get("cuisines")
        if isinstance(cuisines, (list, np.ndarray)):
            cuisines_list = [str(c).strip() for c in cuisines if str(c).strip()]
        elif isinstance(cuisines, str) and cuisines.strip():
            cuisines_list = [c.strip() for c in cuisines.split(",") if c.strip()]
        else:
            cuisines_list = []

        candidate_models.append(
            CandidateRestaurant(
                restaurant_id=r_id,
                name=name,
                location=location,
                rating=rating,
                votes=votes,
                cost_for_two=cost_for_two,
                cuisines=cuisines_list,
                rest_type=str(row.get("rest_type", "")).strip(),
                dish_liked=str(row.get("dish_liked", "")).strip(),
                online_order=bool(row.get("online_order", False)),
                book_table=bool(row.get("book_table", False)),
            )
        )

    return candidate_models


def format_candidate_markdown_table(candidates_df: pd.DataFrame, max_rows: int = 15) -> str:
    """
    Formats candidate records into a compact, token-efficient Markdown table.
    """
    if candidates_df.empty:
        return "No candidate restaurants found."

    subset = candidates_df.head(max_rows)
    headers = ["ID", "Name", "Location", "Rating", "Votes", "Cost (2)", "Cuisines"]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]

    for idx, row in subset.iterrows():
        r_id = row.get("restaurant_id", idx)
        name = str(row.get("name", "")).replace("|", "/")
        loc = str(row.get("location", "")).replace("|", "/")
        rating = f"{row.get('rating'):.1f}" if pd.notna(row.get("rating")) else "N/A"
        votes = str(row.get("votes", 0))
        cost = f"₹{row.get('cost_for_two', 0)}"

        cuisines = row.get("cuisines")
        if isinstance(cuisines, list):
            c_str = ", ".join(cuisines[:3])
        else:
            c_str = str(row.get("cuisines_str", cuisines or ""))[:40]
        c_str = c_str.replace("|", "/")

        lines.append(f"| {r_id} | {name} | {loc} | {rating} | {votes} | {cost} | {c_str} |")

    return "\n".join(lines)


class CandidateSelector:
    """
    Candidate selector with intelligent constraint relaxation and multi-factor ranking.
    Isolates top 10-20 relevant candidates from the dataset before invoking LLM Stage 2.
    """

    def __init__(self, filter_engine: Optional[FilterEngine] = None):
        self.filter_engine = filter_engine if filter_engine is not None else FilterEngine()

    def select_candidates(
        self,
        preferences: UserPreferences,
        df: Optional[pd.DataFrame] = None,
        max_candidates: Optional[int] = None,
        min_candidates: int = 5,
    ) -> Tuple[pd.DataFrame, bool, List[str]]:
        """
        Execute candidate retrieval with automated multi-step constraint relaxation if results < min_candidates.

        Returns:
            Tuple of:
                - candidates_df: Ranked top candidates (DataFrame)
                - was_relaxed: Boolean indicating if constraint relaxation was applied
                - relaxation_steps: List of explanations for any relaxation steps taken
        """
        limit = max_candidates if max_candidates is not None else settings.MAX_CANDIDATES_FOR_LLM
        base_df = df if df is not None else self.filter_engine.dataset

        min_cost, max_cost = get_budget_range(
            tier=preferences.budget_tier,
            max_budget=preferences.max_budget,
        )
        min_rating = preferences.min_rating if preferences.min_rating is not None else 0.0
        require_cuisine = bool(preferences.cuisines)

        # 1. Initial Strict Retrieval
        filtered = self.filter_engine.filter(
            preferences=preferences,
            df=base_df,
            min_cost=min_cost,
            max_cost=max_cost,
            min_rating=min_rating,
            require_cuisine_match=require_cuisine,
        )

        was_relaxed = False
        relaxation_steps: List[str] = []

        # 2. Step 1: Expand budget bounds by +/- 25% if count < min_candidates
        if len(filtered) < min_candidates and (preferences.budget_tier != "Any" or preferences.max_budget):
            expanded_min = max(0, int(min_cost * 0.75))
            expanded_max = int(max_cost * 1.25)
            step_msg = f"Expanded budget bounds from ₹{min_cost}-₹{max_cost} to ₹{expanded_min}-₹{expanded_max} (±25%)"
            relaxation_steps.append(step_msg)
            was_relaxed = True

            min_cost, max_cost = expanded_min, expanded_max
            filtered = self.filter_engine.filter(
                preferences=preferences,
                df=base_df,
                min_cost=min_cost,
                max_cost=max_cost,
                min_rating=min_rating,
                require_cuisine_match=require_cuisine,
            )

        # 3. Step 2: Progressively lower minimum rating threshold by 0.3 if count < min_candidates
        while len(filtered) < min_candidates and min_rating > 3.0:
            relaxed_rating = max(0.0, round(min_rating - 0.3, 2))
            step_msg = f"Lowered minimum rating threshold from {min_rating} to {relaxed_rating} (-0.3)"
            relaxation_steps.append(step_msg)
            was_relaxed = True

            min_rating = relaxed_rating
            filtered = self.filter_engine.filter(
                preferences=preferences,
                df=base_df,
                min_cost=min_cost,
                max_cost=max_cost,
                min_rating=min_rating,
                require_cuisine_match=require_cuisine,
            )

        # 4. Step 3: Match broader cuisine categories / relax strict cuisine match if count < min_candidates
        if len(filtered) < min_candidates and require_cuisine:
            step_msg = "Broadened cuisine filter to include all matching and related dining venues in the area"
            relaxation_steps.append(step_msg)
            was_relaxed = True

            require_cuisine = False
            filtered = self.filter_engine.filter(
                preferences=preferences,
                df=base_df,
                min_cost=min_cost,
                max_cost=max_cost,
                min_rating=min_rating,
                require_cuisine_match=False,
            )

        # 5. Step 4: Fallback to broader location if still < min_candidates
        if len(filtered) < min_candidates and preferences.location:
            step_msg = f"Broadened locality search beyond '{preferences.location}' to city-wide popular spots"
            relaxation_steps.append(step_msg)
            was_relaxed = True

            filtered = self.filter_engine.filter(
                preferences=preferences,
                df=base_df,
                min_cost=min_cost,
                max_cost=max_cost,
                min_rating=min_rating,
                location="All",
                require_cuisine_match=False,
            )

        # Multi-factor ranking: cuisine_score -> rating -> votes
        if not filtered.empty:
            sort_cols = []
            ascending_order = []

            if "cuisine_score" in filtered.columns:
                sort_cols.append("cuisine_score")
                ascending_order.append(False)
            if "rating" in filtered.columns:
                sort_cols.append("rating")
                ascending_order.append(False)
            if "votes" in filtered.columns:
                sort_cols.append("votes")
                ascending_order.append(False)

            if sort_cols:
                ranked = filtered.sort_values(by=sort_cols, ascending=ascending_order)
            else:
                ranked = filtered

            top_candidates = ranked.head(limit).copy().reset_index(drop=True)
        else:
            top_candidates = filtered.copy()

        return top_candidates, was_relaxed, relaxation_steps
