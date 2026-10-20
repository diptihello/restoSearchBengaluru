"""Unit and integration tests for Phase 3: LLM reasoning, schemas, and client."""

import json
from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from src.llm.client import (
    GeminiLLMClient,
    _normalize_name,
    generate_fallback_recommendations,
    validate_recommendation_grounding,
)
from src.llm.prompt_templates import (
    SYSTEM_INSTRUCTION,
    build_recommendation_prompt,
    serialize_candidates,
)
from src.llm.schemas import (
    CandidateRestaurant,
    RecommendationResponse,
    RestaurantRecommendation,
    UserPreferences,
)


@pytest.fixture
def sample_user_preferences() -> UserPreferences:
    return UserPreferences(
        location="Indiranagar",
        budget_tier="Medium",
        max_budget=1500,
        cuisines=["Italian", "Continental"],
        min_rating=4.0,
        occasion="Romantic dinner",
        dining_type="Dine-out",
    )


@pytest.fixture
def sample_candidates() -> list[CandidateRestaurant]:
    return [
        CandidateRestaurant(
            restaurant_id=101,
            name="Toscano",
            location="Indiranagar",
            rating=4.4,
            votes=1250,
            cost_for_two=1400,
            cuisines=["Italian", "Continental"],
            rest_type="Casual Dining",
            dish_liked="Pasta, Tiramisu",
            online_order=True,
            book_table=True,
        ),
        CandidateRestaurant(
            restaurant_id=102,
            name="Chianti",
            location="Indiranagar",
            rating=4.5,
            votes=980,
            cost_for_two=1500,
            cuisines=["Italian"],
            rest_type="Fine Dining",
            dish_liked="Ravioli, Pizza",
            online_order=False,
            book_table=True,
        ),
        CandidateRestaurant(
            restaurant_id=103,
            name="Corner House Ice Cream",
            location="Indiranagar",
            rating=4.6,
            votes=3200,
            cost_for_two=300,
            cuisines=["Desserts", "Ice Cream"],
            rest_type="Dessert Parlor",
            dish_liked="Death by Chocolate",
            online_order=True,
            book_table=False,
        ),
    ]


class TestSchemasAndPrompting:
    """Tests for Pydantic schemas, serialization, and prompt creation."""

    def test_schemas_validation(self, sample_user_preferences: UserPreferences):
        assert sample_user_preferences.location == "Indiranagar"
        assert sample_user_preferences.min_rating == 4.0

        rec = RestaurantRecommendation(
            rank=1,
            restaurant_name="Toscano",
            cuisine="Italian",
            rating=4.4,
            cost_for_two=1400,
            location="Indiranagar",
            why_recommended="Ideal ambiance for romantic dinner.",
            highlights=["Wine Selection", "Pasta"],
        )
        response = RecommendationResponse(
            recommendations=[rec],
            executive_summary="Selected Toscano as top Italian pick.",
            is_fallback=False,
        )
        assert len(response.recommendations) == 1
        assert response.is_fallback is False

    def test_serialize_candidates_list(self, sample_candidates: list[CandidateRestaurant]):
        serialized = serialize_candidates(sample_candidates)
        data = json.loads(serialized)
        assert len(data) == 3
        assert data[0]["name"] == "Toscano"
        assert data[0]["features"]["book_table"] is True

    def test_serialize_candidates_dataframe(self, sample_candidates: list[CandidateRestaurant]):
        df = pd.DataFrame([c.model_dump() for c in sample_candidates])
        serialized = serialize_candidates(df)
        data = json.loads(serialized)
        assert len(data) == 3
        assert data[1]["name"] == "Chianti"

    def test_build_recommendation_prompt(
        self,
        sample_user_preferences: UserPreferences,
        sample_candidates: list[CandidateRestaurant],
    ):
        context = serialize_candidates(sample_candidates)
        prompt = build_recommendation_prompt(sample_user_preferences, context)

        assert "### USER PREFERENCES & INTENT" in prompt
        assert "Indiranagar" in prompt
        assert "Romantic dinner" in prompt
        assert "### AVAILABLE CANDIDATE RESTAURANTS" in prompt
        assert "Toscano" in prompt
        assert "RecommendationResponse schema" in prompt


class TestGroundingValidation:
    """Tests for anti-hallucination verification against candidate whitelist."""

    def test_grounding_passes_for_valid_candidates(
        self, sample_candidates: list[CandidateRestaurant]
    ):
        response = RecommendationResponse(
            recommendations=[
                RestaurantRecommendation(
                    rank=1,
                    restaurant_name="Toscano",
                    cuisine="Italian",
                    rating=4.4,
                    cost_for_two=1400,
                    location="Indiranagar",
                    why_recommended="Top Italian dinner.",
                    highlights=["Great Pasta"],
                ),
                RestaurantRecommendation(
                    rank=2,
                    restaurant_name="Chianti",
                    cuisine="Italian",
                    rating=4.5,
                    cost_for_two=1500,
                    location="Indiranagar",
                    why_recommended="Authentic Italian feel.",
                    highlights=["Romantic Vibe"],
                ),
            ],
            executive_summary="Solid Italian picks in Indiranagar.",
        )

        is_grounded, hallucinated = validate_recommendation_grounding(response, sample_candidates)
        assert is_grounded is True
        assert len(hallucinated) == 0

    def test_grounding_detects_hallucinated_restaurant(
        self, sample_candidates: list[CandidateRestaurant]
    ):
        response = RecommendationResponse(
            recommendations=[
                RestaurantRecommendation(
                    rank=1,
                    restaurant_name="Toscano",
                    cuisine="Italian",
                    rating=4.4,
                    cost_for_two=1400,
                    location="Indiranagar",
                    why_recommended="Known spot.",
                    highlights=["Pasta"],
                ),
                RestaurantRecommendation(
                    rank=2,
                    restaurant_name="Imaginary Bistro 99",
                    cuisine="Fusion",
                    rating=4.8,
                    cost_for_two=2000,
                    location="Indiranagar",
                    why_recommended="Hallucinated place not in candidates.",
                    highlights=["Made Up"],
                ),
            ],
            executive_summary="Contains a hallucination.",
        )

        is_grounded, hallucinated = validate_recommendation_grounding(response, sample_candidates)
        assert is_grounded is False
        assert "Imaginary Bistro 99" in hallucinated


class TestFallbackMechanism:
    """Tests for deterministic heuristic ranking fallback."""

    def test_fallback_ranking_order(
        self,
        sample_user_preferences: UserPreferences,
        sample_candidates: list[CandidateRestaurant],
    ):
        # Corner House (4.6 rating, 3200 votes) -> Chianti (4.5 rating, 980 votes) -> Toscano (4.4 rating, 1250 votes)
        fallback = generate_fallback_recommendations(
            preferences=sample_user_preferences,
            candidates=sample_candidates,
            reason="Gemini offline test",
            top_n=3,
        )

        assert fallback.is_fallback is True
        assert len(fallback.recommendations) == 3

        # Rank 1 should be Corner House (highest rating 4.6)
        assert fallback.recommendations[0].rank == 1
        assert fallback.recommendations[0].restaurant_name == "Corner House Ice Cream"
        assert fallback.recommendations[0].rating == 4.6

        # Rank 2 should be Chianti (4.5)
        assert fallback.recommendations[1].rank == 2
        assert fallback.recommendations[1].restaurant_name == "Chianti"

        # Rank 3 should be Toscano (4.4)
        assert fallback.recommendations[2].rank == 3
        assert fallback.recommendations[2].restaurant_name == "Toscano"

        assert "Gemini offline test" in fallback.executive_summary

    def test_fallback_empty_candidates(self, sample_user_preferences: UserPreferences):
        fallback = generate_fallback_recommendations(
            preferences=sample_user_preferences,
            candidates=[],
            reason="Empty candidate list",
        )
        assert fallback.is_fallback is True
        assert len(fallback.recommendations) == 0


class TestGeminiLLMClient:
    """Tests for GeminiLLMClient initialization, execution, and error resilience."""

    def test_client_defaults_to_fallback_without_api_key(
        self,
        sample_user_preferences: UserPreferences,
        sample_candidates: list[CandidateRestaurant],
    ):
        client = GeminiLLMClient(api_key="")
        response = client.generate_recommendations(sample_user_preferences, sample_candidates)

        assert response.is_fallback is True
        assert len(response.recommendations) > 0
        assert "not configured" in response.executive_summary.lower()

    @patch("src.llm.client.Client")
    def test_successful_llm_generation(
        self,
        mock_client_cls,
        sample_user_preferences: UserPreferences,
        sample_candidates: list[CandidateRestaurant],
    ):
        mock_client_instance = MagicMock()
        mock_client_cls.return_value = mock_client_instance

        mock_gemini_json = json.dumps({
            "recommendations": [
                {
                    "rank": 1,
                    "restaurant_name": "Toscano",
                    "cuisine": "Italian, Continental",
                    "rating": 4.4,
                    "cost_for_two": 1400,
                    "location": "Indiranagar",
                    "why_recommended": "Exquisite candlelit dining tailored for a romantic evening.",
                    "highlights": ["Handmade Pasta", "Romantic Vibe", "Fine Wine"],
                },
                {
                    "rank": 2,
                    "restaurant_name": "Chianti",
                    "cuisine": "Italian",
                    "rating": 4.5,
                    "cost_for_two": 1500,
                    "location": "Indiranagar",
                    "why_recommended": "Intimate setting with authentic Northern Italian fare.",
                    "highlights": ["Wood-fired Pizza", "Cozy Seating"],
                },
            ],
            "executive_summary": "Top romantic Italian venues in Indiranagar.",
            "is_fallback": False,
        })

        mock_response = MagicMock()
        mock_response.text = mock_gemini_json
        mock_client_instance.models.generate_content.return_value = mock_response

        client = GeminiLLMClient(api_key="valid-dummy-key")
        client.client = mock_client_instance

        result = client.generate_recommendations(sample_user_preferences, sample_candidates)

        assert result.is_fallback is False
        assert len(result.recommendations) == 2
        assert result.recommendations[0].restaurant_name == "Toscano"
        assert result.recommendations[1].restaurant_name == "Chianti"
        assert "Top romantic" in result.executive_summary

    @patch("src.llm.client.Client")
    def test_llm_markdown_fence_cleaning(
        self,
        mock_client_cls,
        sample_user_preferences: UserPreferences,
        sample_candidates: list[CandidateRestaurant],
    ):
        mock_client_instance = MagicMock()
        mock_client_cls.return_value = mock_client_instance

        raw_json = json.dumps({
            "recommendations": [
                {
                    "rank": 1,
                    "restaurant_name": "Toscano",
                    "cuisine": "Italian",
                    "rating": 4.4,
                    "cost_for_two": 1400,
                    "location": "Indiranagar",
                    "why_recommended": "Top pick.",
                    "highlights": ["Pasta"],
                }
            ],
            "executive_summary": "Cleaned response.",
            "is_fallback": False,
        })
        mock_response = MagicMock()
        mock_response.text = f"```json\n{raw_json}\n```"
        mock_client_instance.models.generate_content.return_value = mock_response

        client = GeminiLLMClient(api_key="dummy-key")
        client.client = mock_client_instance

        result = client.generate_recommendations(sample_user_preferences, sample_candidates)
        assert result.is_fallback is False
        assert result.recommendations[0].restaurant_name == "Toscano"

    @patch("src.llm.client.Client")
    def test_anti_hallucination_filters_unknown_restaurant(
        self,
        mock_client_cls,
        sample_user_preferences: UserPreferences,
        sample_candidates: list[CandidateRestaurant],
    ):
        mock_client_instance = MagicMock()
        mock_client_cls.return_value = mock_client_instance

        # LLM returns one valid candidate ("Toscano") and one hallucination ("Ghost Bistro")
        mock_gemini_json = json.dumps({
            "recommendations": [
                {
                    "rank": 1,
                    "restaurant_name": "Ghost Bistro",
                    "cuisine": "Fusion",
                    "rating": 4.9,
                    "cost_for_two": 1200,
                    "location": "Indiranagar",
                    "why_recommended": "Fake place.",
                    "highlights": ["Fictional"],
                },
                {
                    "rank": 2,
                    "restaurant_name": "Toscano",
                    "cuisine": "Italian",
                    "rating": 4.4,
                    "cost_for_two": 1400,
                    "location": "Indiranagar",
                    "why_recommended": "Real place.",
                    "highlights": ["Pasta"],
                },
            ],
            "executive_summary": "Mixed results.",
            "is_fallback": False,
        })
        mock_response = MagicMock()
        mock_response.text = mock_gemini_json
        mock_client_instance.models.generate_content.return_value = mock_response

        client = GeminiLLMClient(api_key="dummy-key")
        client.client = mock_client_instance

        result = client.generate_recommendations(sample_user_preferences, sample_candidates)

        # Ghost Bistro must be stripped out; Toscano kept and re-ranked to 1
        assert len(result.recommendations) == 1
        assert result.recommendations[0].restaurant_name == "Toscano"
        assert result.recommendations[0].rank == 1

    @patch("src.llm.client.Client")
    def test_api_exception_falls_back_gracefully(
        self,
        mock_client_cls,
        sample_user_preferences: UserPreferences,
        sample_candidates: list[CandidateRestaurant],
    ):
        mock_client_instance = MagicMock()
        mock_client_cls.return_value = mock_client_instance
        # Simulate network timeout or Gemini quota error
        mock_client_instance.models.generate_content.side_effect = RuntimeError(
            "API quota exceeded (503)"
        )

        client = GeminiLLMClient(api_key="dummy-key")
        client.client = mock_client_instance

        result = client.generate_recommendations(sample_user_preferences, sample_candidates)

        assert result.is_fallback is True
        assert len(result.recommendations) > 0
        assert "API quota exceeded" in result.executive_summary
