"""Client helper for communicating with FastAPI backend with fallback to direct service."""

import logging
import os
from typing import Any, Dict, Optional, Tuple
import httpx

from src.config import settings
from src.llm.schemas import RecommendationResponse, UserPreferences
from src.services.recommendation_service import get_recommendation_service

logger = logging.getLogger(__name__)

DEFAULT_API_URL = os.getenv("API_BASE_URL", f"http://localhost:{settings.API_PORT}").rstrip("/")


def fetch_meta_options(api_base_url: str = DEFAULT_API_URL) -> Dict[str, Any]:
    """
    Fetch metadata options from FastAPI backend, or fallback to direct service in-process.
    """
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(f"{api_base_url}/api/v1/meta/options")
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        logger.debug("FastAPI server not reachable at %s (%s). Using in-process service.", api_base_url, e)

    # In-process fallback
    service = get_recommendation_service()
    return service.get_meta_options()


def fetch_recommendations(
    payload: Dict[str, Any],
    api_base_url: str = DEFAULT_API_URL,
) -> Tuple[Optional[RecommendationResponse], Optional[str], bool]:
    """
    Fetch recommendations from FastAPI backend, or fallback to in-process service.

    Returns:
        Tuple of (RecommendationResponse, error_message, is_direct_in_process)
    """
    # 1. Try FastAPI endpoint first
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(f"{api_base_url}/api/v1/recommendations", json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return RecommendationResponse.model_validate(data), None, False
            elif resp.status_code == 422:
                err_data = resp.json()
                return None, f"Input validation error: {err_data.get('details', err_data)}", False
            else:
                logger.warning("API returned status %d. Falling back to in-process.", resp.status_code)
    except Exception as e:
        logger.debug("API call failed: %s. Using in-process recommendation service.", e)

    # 2. In-process direct execution fallback
    try:
        service = get_recommendation_service()
        prefs = UserPreferences(
            location=payload.get("location", "Bangalore"),
            budget_tier=payload.get("budget_tier", "Medium"),
            max_budget=payload.get("max_budget"),
            cuisines=payload.get("cuisines", []),
            min_rating=float(payload.get("min_rating", 3.5)),
            occasion=payload.get("occasion"),
            dining_type=payload.get("dining_type"),
        )
        rec_response = service.get_recommendations(
            preferences=prefs,
            max_candidates=payload.get("candidate_limit"),
        )
        return rec_response, None, True
    except Exception as exc:
        logger.error("In-process recommendation failed: %s", exc, exc_info=True)
        return None, f"Failed to generate recommendations: {str(exc)}", True
