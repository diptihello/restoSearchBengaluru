"""End-to-End Persona Testing & Performance Benchmarking for Phase 6."""

import time
import pytest

from src.llm.client import validate_recommendation_grounding
from src.llm.prompt_templates import build_recommendation_prompt, serialize_candidates
from src.llm.schemas import RecommendationResponse, UserPreferences
from src.retrieval.candidate_selector import CandidateSelector, to_candidate_models
from src.retrieval.filter_engine import FilterEngine
from src.services.recommendation_service import RecommendationService


@pytest.fixture(scope="module")
def rec_service() -> RecommendationService:
    """Shared RecommendationService instance."""
    return RecommendationService()


class TestPersonaEvaluations:
    """
    Persona evaluations across realistic user scenarios as defined in Phase 6:
    - Persona A (College Students): Budget Low, Fast Food/Momos, Min Rating 3.5.
    - Persona B (Romantic Dinner): Indiranagar, Budget High, Italian, Min Rating 4.2.
    - Persona C (Family Sunday Brunch): Multi-cuisine/Buffet, Medium budget.
    """

    def test_persona_a_college_students(self, rec_service: RecommendationService):
        """
        Persona A: College students looking for cheap, delicious food in a student hub.
        """
        prefs = UserPreferences(
            location="Koramangala",
            budget_tier="Low",
            max_budget=500,
            cuisines=["Fast Food", "Chinese"],
            min_rating=3.5,
            occasion="Quick budget bite after classes with college friends",
            dining_type="Quick Bites",
        )

        response = rec_service.get_recommendations(prefs, max_candidates=10)

        assert isinstance(response, RecommendationResponse)
        assert len(response.recommendations) >= 3, "Persona A should receive at least 3 recommendations"
        assert response.executive_summary is not None

        # Verify low budget constraint is satisfied
        for rec in response.recommendations:
            assert rec.cost_for_two <= 700, f"Recommendation {rec.restaurant_name} cost {rec.cost_for_two} exceeds low budget"
            assert rec.why_recommended is not None
            assert len(rec.highlights) >= 2

        # Anti-hallucination check: ensure names strictly match candidate pool
        candidates_df, _, _ = rec_service.candidate_selector.select_candidates(prefs, max_candidates=10)
        is_grounded, hallucinated = validate_recommendation_grounding(response, candidates_df)
        assert is_grounded is True, f"Found hallucinated restaurants: {hallucinated}"

    def test_persona_b_romantic_dinner(self, rec_service: RecommendationService):
        """
        Persona B: Upscale romantic dinner date in Indiranagar with high rating.
        """
        prefs = UserPreferences(
            location="Indiranagar",
            budget_tier="High",
            cuisines=["Italian", "Continental"],
            min_rating=4.2,
            occasion="Romantic candlelit anniversary dinner date with wine",
            dining_type="Dine-out",
        )

        response = rec_service.get_recommendations(prefs, max_candidates=10)

        assert isinstance(response, RecommendationResponse)
        assert len(response.recommendations) >= 3, "Persona B should receive at least 3 recommendations"

        # Verify high rating and romantic vibe reasoning
        for rec in response.recommendations:
            assert rec.rating >= 4.0, f"Recommendation {rec.restaurant_name} rating {rec.rating} is too low for Persona B"
            assert "romantic" in rec.why_recommended.lower() or "vibe" in rec.why_recommended.lower() or "score" in rec.why_recommended.lower()

        # Anti-hallucination check
        candidates_df, _, _ = rec_service.candidate_selector.select_candidates(prefs, max_candidates=10)
        is_grounded, hallucinated = validate_recommendation_grounding(response, candidates_df)
        assert is_grounded is True, f"Found hallucinated restaurants: {hallucinated}"

    def test_persona_c_family_sunday_brunch(self, rec_service: RecommendationService):
        """
        Persona C: Sunday family gathering brunch with multi-cuisine offerings.
        """
        prefs = UserPreferences(
            location="Bangalore",
            budget_tier="Medium",
            cuisines=["North Indian", "Continental", "South Indian"],
            min_rating=3.8,
            occasion="Sunday family brunch with parents and kids",
            dining_type="Dine-out",
        )

        response = rec_service.get_recommendations(prefs, max_candidates=10)

        assert isinstance(response, RecommendationResponse)
        assert len(response.recommendations) >= 3, "Persona C should receive at least 3 recommendations"

        # Verify medium budget range
        for rec in response.recommendations:
            assert rec.cost_for_two <= 2000, f"Cost {rec.cost_for_two} too high for Medium tier"
            assert len(rec.highlights) >= 2

        # Anti-hallucination check
        candidates_df, _, _ = rec_service.candidate_selector.select_candidates(prefs, max_candidates=10)
        is_grounded, hallucinated = validate_recommendation_grounding(response, candidates_df)
        assert is_grounded is True, f"Found hallucinated restaurants: {hallucinated}"


class TestSystemBenchmarking:
    """Performance and token budget benchmarks."""

    def test_prompt_token_budget_under_1500_tokens(self, rec_service: RecommendationService):
        """
        Verify that serialized candidate context and total prompt token payload is < 1500 tokens (~6000 characters).
        """
        prefs = UserPreferences(
            location="Indiranagar",
            budget_tier="Medium",
            cuisines=["Italian", "Continental"],
            min_rating=3.8,
            occasion="Anniversary dinner",
        )

        candidates_df, _, _ = rec_service.candidate_selector.select_candidates(prefs, max_candidates=15)
        candidate_models = to_candidate_models(candidates_df)

        serialized_context = serialize_candidates(candidate_models)
        complete_prompt = build_recommendation_prompt(prefs, serialized_context)

        # Rough token estimation: 1 token ~= 4 characters in English JSON/markdown
        estimated_tokens = len(complete_prompt) / 4.0

        print(f"\n[BENCHMARK] Prompt length: {len(complete_prompt)} chars (~{estimated_tokens:.0f} tokens).")
        assert estimated_tokens < 1500, f"Prompt estimated at {estimated_tokens:.0f} tokens, exceeding 1500 token ceiling!"

    def test_end_to_end_pipeline_latency(self, rec_service: RecommendationService):
        """
        Verify end-to-end recommendation pipeline latency is within acceptable sub-second bounds for Stage 1.
        """
        prefs = UserPreferences(
            location="Indiranagar",
            budget_tier="Medium",
            cuisines=["North Indian"],
            min_rating=3.5,
        )

        start_time = time.perf_counter()
        response = rec_service.get_recommendations(prefs, max_candidates=10)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        print(f"\n[BENCHMARK] End-to-end pipeline executed in {elapsed_ms:.2f} ms.")
        assert elapsed_ms < 500, f"Pipeline took {elapsed_ms:.2f} ms, exceeding 500ms target!"
        assert len(response.recommendations) > 0
