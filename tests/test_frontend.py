"""Unit tests for Phase 5: Streamlit frontend components and client."""

from unittest.mock import MagicMock, patch
import pytest

from frontend.components.api_client import fetch_meta_options, fetch_recommendations
from frontend.components.cards import (
    render_empty_state,
    render_executive_summary,
    render_restaurant_card,
)
from src.llm.schemas import RecommendationResponse, RestaurantRecommendation


@pytest.fixture
def sample_recommendation() -> RestaurantRecommendation:
    return RestaurantRecommendation(
        rank=1,
        restaurant_name="Toscano Indiranagar",
        cuisine="Italian, Continental",
        rating=4.5,
        cost_for_two=1400,
        location="Indiranagar",
        why_recommended="Superb candlelit setting for a romantic evening.",
        highlights=["Handmade Pasta", "Romantic Vibe", "Fine Wine"],
    )


class TestFrontendApiClient:
    """Tests for frontend API communication and fallback logic."""

    def test_fetch_meta_options_in_process(self):
        meta = fetch_meta_options(api_base_url="http://invalid-nonexistent-url:9999")
        assert "locations" in meta
        assert "cuisines" in meta
        assert "budget_tiers" in meta
        assert "occasions" in meta
        assert len(meta["locations"]) > 0

    def test_fetch_recommendations_in_process_fallback(self):
        payload = {
            "location": "Indiranagar",
            "budget_tier": "Medium",
            "min_rating": 3.8,
            "cuisines": ["Italian"],
            "occasion": "Date Night",
            "candidate_limit": 5,
        }
        response, err, is_direct = fetch_recommendations(
            payload,
            api_base_url="http://invalid-nonexistent-url:9999",
        )
        assert err is None
        assert response is not None
        assert is_direct is True
        assert isinstance(response, RecommendationResponse)
        assert len(response.recommendations) > 0


class TestFrontendCardRendering:
    """Tests ensuring Streamlit card rendering functions execute cleanly."""

    @patch("streamlit.markdown")
    def test_render_executive_summary(self, mock_markdown):
        render_executive_summary(
            summary="Top romantic spots selected in Indiranagar.",
            is_fallback=False,
            total_found=3,
        )
        assert mock_markdown.called
        call_args = mock_markdown.call_args[0][0]
        assert "Concierge Executive Summary" in call_args
        assert "Top romantic spots" in call_args
        assert "GEMINI AI CURATED" in call_args

    @patch("streamlit.markdown")
    def test_render_restaurant_card(self, mock_markdown, sample_recommendation: RestaurantRecommendation):
        render_restaurant_card(sample_recommendation, index=1)
        assert mock_markdown.called
        call_args = mock_markdown.call_args[0][0]
        assert "Toscano Indiranagar" in call_args
        assert "Indiranagar" in call_args
        assert "4.5" in call_args
        assert "Handmade Pasta" in call_args
        assert "Why We Recommend This" in call_args

    @patch("streamlit.markdown")
    def test_render_empty_state(self, mock_markdown):
        render_empty_state()
        assert mock_markdown.called
        call_args = mock_markdown.call_args[0][0]
        assert "No Restaurants Found" in call_args
        assert "Try adjusting your search" in call_args
