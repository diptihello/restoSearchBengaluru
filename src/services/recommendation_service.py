"""Recommendation orchestration service connecting retrieval and LLM reasoning."""

from functools import lru_cache
import logging
import time
from typing import Any, Dict, List, Optional

import pandas as pd

from src.config import settings
from src.data_ingestion.loader import get_processed_dataset
from src.llm.client import GeminiLLMClient
from src.llm.schemas import (
    CandidateRestaurant,
    RecommendationResponse,
    UserPreferences,
)
from src.retrieval.candidate_selector import CandidateSelector, to_candidate_models
from src.retrieval.filter_engine import FilterEngine

logger = logging.getLogger(__name__)


class RecommendationService:
    """
    End-to-end orchestration service coordinating:
    User Preferences -> Tabular Filter Engine -> Constraint Relaxation & Ranking -> LLM Reasoning -> Structured Output.
    """

    def __init__(
        self,
        filter_engine: Optional[FilterEngine] = None,
        candidate_selector: Optional[CandidateSelector] = None,
        llm_client: Optional[GeminiLLMClient] = None,
    ):
        self._filter_engine = filter_engine
        self._candidate_selector = candidate_selector
        self._llm_client = llm_client
        self._cached_meta_options: Optional[Dict[str, Any]] = None

    @property
    def filter_engine(self) -> FilterEngine:
        if self._filter_engine is None:
            self._filter_engine = FilterEngine()
        return self._filter_engine

    @property
    def candidate_selector(self) -> CandidateSelector:
        if self._candidate_selector is None:
            self._candidate_selector = CandidateSelector(self.filter_engine)
        return self._candidate_selector

    @property
    def llm_client(self) -> GeminiLLMClient:
        if self._llm_client is None:
            self._llm_client = GeminiLLMClient()
        return self._llm_client

    def get_recommendations(
        self,
        preferences: UserPreferences,
        max_candidates: Optional[int] = None,
    ) -> RecommendationResponse:
        """
        Execute the full two-stage recommendation pipeline:
        Stage 1: Deterministic retrieval & constraint relaxation.
        Stage 2: LLM reasoning & personalized rationale generation.
        """
        start_time = time.perf_counter()
        logger.info(
            "Generating recommendations for location='%s', budget='%s', cuisines=%s, occasion='%s'",
            preferences.location,
            preferences.budget_tier,
            preferences.cuisines,
            preferences.occasion,
        )

        # Stage 1: Deterministic Retrieval
        candidates_df, was_relaxed, relaxation_steps = self.candidate_selector.select_candidates(
            preferences=preferences,
            max_candidates=max_candidates or settings.MAX_CANDIDATES_FOR_LLM,
        )

        stage1_time = (time.perf_counter() - start_time) * 1000
        logger.info(
            "Stage 1 retrieved %d candidates in %.2f ms (was_relaxed=%s)",
            len(candidates_df),
            stage1_time,
            was_relaxed,
        )

        # Stage 2: Convert to typed models and invoke LLM reasoning
        candidate_models = to_candidate_models(candidates_df)
        response = self.llm_client.generate_recommendations(
            preferences=preferences,
            candidates=candidate_models,
        )

        total_time = (time.perf_counter() - start_time) * 1000
        logger.info(
            "Recommendation pipeline finished in %.2f ms. Total recommendations: %d (fallback=%s)",
            total_time,
            len(response.recommendations),
            response.is_fallback,
        )

        # If constraint relaxation occurred, mention it transparently in the executive summary
        if was_relaxed and relaxation_steps and not response.is_fallback:
            relaxation_note = " (Note: " + "; ".join(relaxation_steps[:2]) + " to find the best matching venues)."
            if relaxation_note not in response.executive_summary:
                response.executive_summary += relaxation_note

        return response

    def get_meta_options(self) -> Dict[str, Any]:
        """
        Extract unique locations, cuisines, and options from the dataset for frontend dropdowns.
        Cached in-memory after first computation.
        """
        if self._cached_meta_options is not None:
            return self._cached_meta_options

        dataset = self.filter_engine.dataset

        # 1. Unique locations (sorted by frequency)
        if "location" in dataset.columns:
            loc_counts = dataset["location"].dropna().value_counts()
            locations = [str(loc) for loc in loc_counts.index if str(loc).strip() and str(loc) != "Unknown"]
        else:
            locations = ["Indiranagar", "Koramangala", "Whitefield", "Jayanagar", "HSR Layout"]

        # 2. Unique cities
        cities = ["Bangalore"]
        if "city" in dataset.columns:
            unique_cities = sorted([str(c) for c in dataset["city"].dropna().unique() if str(c).strip()])
            if unique_cities:
                cities = unique_cities

        # 3. Unique cuisines (flatten and count frequency)
        all_cuisines: Dict[str, int] = {}
        if "cuisines" in dataset.columns:
            for clist in dataset["cuisines"].dropna():
                if isinstance(clist, (list, tuple)):
                    for item in clist:
                        name = str(item).strip().title()
                        if name:
                            all_cuisines[name] = all_cuisines.get(name, 0) + 1
        
        # Sort cuisines by popularity, taking top 60
        sorted_cuisines = sorted(all_cuisines.keys(), key=lambda k: all_cuisines[k], reverse=True)
        top_cuisines = sorted_cuisines[:60] if sorted_cuisines else [
            "North Indian", "Chinese", "South Indian", "Fast Food", "Continental",
            "Italian", "Cafe", "Biryani", "Desserts", "Beverages", "Bakery", "Mughlai"
        ]

        # 4. Dining Types
        dining_types = []
        if "dining_type" in dataset.columns:
            dining_types = sorted([
                str(dt).strip() for dt in dataset["dining_type"].dropna().unique()
                if str(dt).strip() and str(dt).lower() != "nan"
            ])
        if not dining_types:
            dining_types = ["Dine-out", "Delivery", "Cafes", "Desserts", "Buffet", "Pubs and Bars", "Drinks & Nightlife"]

        # 5. Preset Budget Tiers
        budget_tiers = [
            {"label": "Low (≤ ₹500 for two)", "value": "Low", "range": "0-500"},
            {"label": "Medium (₹500 - ₹1500 for two)", "value": "Medium", "range": "500-1500"},
            {"label": "High (> ₹1500 for two)", "value": "High", "range": "1500+"},
            {"label": "Any Budget", "value": "Any", "range": "Any"},
        ]

        # 6. Preset Occasions
        common_occasions = [
            "Romantic Date Night",
            "Casual Family Dinner",
            "Catching up with Friends",
            "Quick Weekday Lunch",
            "Late Night Cravings",
            "Celebration / Birthday",
            "Business Meeting",
            "Solo Work / Reading Cafe",
        ]

        self._cached_meta_options = {
            "locations": locations,
            "cities": cities,
            "cuisines": top_cuisines,
            "dining_types": dining_types,
            "budget_tiers": budget_tiers,
            "occasions": common_occasions,
            "total_restaurants": len(dataset),
        }
        return self._cached_meta_options

    def get_health_status(self) -> Dict[str, Any]:
        """
        Check health of the service, loaded dataset, and LLM configuration.
        """
        try:
            ds = self.filter_engine.dataset
            dataset_loaded = True
            total_records = len(ds)
        except Exception as e:
            logger.error("Dataset health check failed: %s", e)
            dataset_loaded = False
            total_records = 0

        has_api_key = bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip())

        return {
            "status": "healthy" if dataset_loaded else "degraded",
            "dataset_loaded": dataset_loaded,
            "total_restaurants": total_records,
            "gemini_model": settings.GEMINI_MODEL,
            "gemini_configured": has_api_key,
            "environment": settings.APP_ENV,
        }


@lru_cache()
def get_recommendation_service() -> RecommendationService:
    """Singleton provider for FastAPI dependency injection."""
    return RecommendationService()
