"""Automated integration tests for Phase 4: FastAPI endpoints and middleware."""

import time
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import pytest

from src.api.main import app
from src.llm.schemas import RecommendationResponse, RestaurantRecommendation

client = TestClient(app)


class TestSystemEndpoints:
    """Tests for system health, root, and documentation endpoints."""

    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert data["documentation"] == "/docs"

    def test_docs_and_openapi_accessible(self):
        # Verification deliverable: FastAPI documentation accessible at /docs
        response = client.get("/docs")
        assert response.status_code == 200
        assert "html" in response.headers.get("content-type", "")

        openapi_resp = client.get("/openapi.json")
        assert openapi_resp.status_code == 200
        spec = openapi_resp.json()
        assert spec["info"]["title"] == "AI-Powered Restaurant Recommendation System API"
        assert "/api/v1/recommendations" in spec["paths"]

    def test_health_check_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("healthy", "degraded")
        assert data["dataset_loaded"] is True
        assert data["total_restaurants"] > 0
        assert "gemini_model" in data

    def test_latency_middleware_header(self):
        response = client.get("/health")
        assert "x-process-time-ms" in response.headers
        latency = float(response.headers["x-process-time-ms"])
        assert latency >= 0.0


class TestMetadataEndpoints:
    """Tests for metadata and filter options endpoint."""

    def test_get_meta_options(self):
        response = client.get("/api/v1/meta/options")
        assert response.status_code == 200
        data = response.json()

        assert "locations" in data
        assert len(data["locations"]) > 0
        assert "Indiranagar" in data["locations"] or "Koramangala" in data["locations"]

        assert "cuisines" in data
        assert len(data["cuisines"]) > 0

        assert "budget_tiers" in data
        assert len(data["budget_tiers"]) >= 3

        assert "occasions" in data
        assert len(data["occasions"]) > 0


class TestRecommendationEndpoint:
    """Tests for POST /api/v1/recommendations endpoint."""

    def test_recommendation_flow_fallback(self):
        # Verification deliverable: POST returns full recommendations in < 2.5 seconds
        payload = {
            "location": "Indiranagar",
            "budget_tier": "Medium",
            "min_rating": 3.8,
            "cuisines": ["Italian", "Continental"],
            "occasion": "Romantic dinner",
            "candidate_limit": 10,
        }

        start_time = time.perf_counter()
        response = client.post("/api/v1/recommendations", json=payload)
        elapsed_sec = time.perf_counter() - start_time

        assert response.status_code == 200
        # Verification deliverable: Latency < 2.5 seconds
        assert elapsed_sec < 2.5, f"Response took {elapsed_sec:.2f}s, exceeding 2.5s threshold!"

        data = response.json()
        assert "recommendations" in data
        assert len(data["recommendations"]) > 0
        assert "executive_summary" in data

        first_rec = data["recommendations"][0]
        assert first_rec["rank"] == 1
        assert "restaurant_name" in first_rec
        assert "why_recommended" in first_rec
        assert len(first_rec["why_recommended"]) > 10
        assert "highlights" in first_rec

    @patch("src.llm.client.Client")
    def test_recommendation_flow_with_llm(self, mock_genai_client):
        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance

        mock_llm_json = """{
            "recommendations": [
                {
                    "rank": 1,
                    "restaurant_name": "Toscano",
                    "cuisine": "Italian, Continental",
                    "rating": 4.4,
                    "cost_for_two": 1400,
                    "location": "Indiranagar",
                    "why_recommended": "Perfect candlelit setting for a romantic dinner with exquisite pasta.",
                    "highlights": ["Great Pasta", "Romantic Ambiance", "Wine Selection"]
                }
            ],
            "executive_summary": "Top romantic dining pick in Indiranagar.",
            "is_fallback": false
        }"""
        mock_response = MagicMock()
        mock_response.text = mock_llm_json
        mock_client_instance.models.generate_content.return_value = mock_response

        # Use recommendation service with mocked LLM client
        with patch("src.config.settings.GEMINI_API_KEY", "dummy-valid-key"):
            payload = {
                "location": "Indiranagar",
                "budget_tier": "Medium",
                "min_rating": 3.5,
                "cuisines": ["Italian"],
                "occasion": "Romantic date",
            }
            response = client.post("/api/v1/recommendations", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert len(data["recommendations"]) >= 1

    def test_validation_error_on_missing_required_fields(self):
        # Missing required 'location'
        invalid_payload = {
            "budget_tier": "Low",
            "min_rating": 4.0,
        }
        response = client.post("/api/v1/recommendations", json=invalid_payload)
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "Validation Error"
        assert "location" in str(data["details"])

    def test_cors_headers(self):
        response = client.options(
            "/api/v1/recommendations",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") in ("*", "http://localhost:3000")
