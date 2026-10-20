"""FastAPI route handlers for restaurant recommendations and metadata."""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.llm.schemas import (
    RecommendationResponse,
    UserPreferences,
)
from src.services.recommendation_service import (
    RecommendationService,
    get_recommendation_service,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class UserPreferencesPayload(UserPreferences):
    """API payload extending UserPreferences with optional pipeline tuning options."""
    candidate_limit: Optional[int] = Field(
        None,
        ge=3,
        le=50,
        description="Maximum candidates passed to LLM reasoning stage (default: 15)",
    )


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str
    dataset_loaded: bool
    total_restaurants: int
    gemini_model: str
    gemini_configured: bool
    environment: str


class MetaOptionsResponse(BaseModel):
    """Available filter options for frontend select boxes and autocomplete."""
    locations: List[str]
    cities: List[str]
    cuisines: List[str]
    dining_types: List[str]
    budget_tiers: List[Dict[str, Any]]
    occasions: List[str]
    total_restaurants: int


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health & Dataset Status",
    description="Check the operational status of the service, loaded dataset, and Gemini LLM connection.",
    tags=["System"],
)
def get_health(
    service: RecommendationService = Depends(get_recommendation_service),
) -> HealthResponse:
    try:
        health_info = service.get_health_status()
        return HealthResponse(**health_info)
    except Exception as e:
        logger.error("Health check encountered error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}",
        )


@router.get(
    "/api/v1/meta/options",
    response_model=MetaOptionsResponse,
    summary="Get Filter & Dropdown Metadata",
    description="Retrieve available locations, cities, cuisines, budget tiers, and occasion tags from the dataset.",
    tags=["Metadata"],
)
def get_meta_options(
    service: RecommendationService = Depends(get_recommendation_service),
) -> MetaOptionsResponse:
    try:
        options = service.get_meta_options()
        return MetaOptionsResponse(**options)
    except Exception as e:
        logger.error("Failed to retrieve metadata options: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not load metadata options: {str(e)}",
        )


@router.post(
    "/api/v1/recommendations",
    response_model=RecommendationResponse,
    summary="Generate AI Restaurant Recommendations",
    description="Execute two-stage hybrid retrieval & LLM reasoning to produce personalized restaurant recommendations.",
    tags=["Recommendations"],
)
def create_recommendations(
    payload: UserPreferencesPayload,
    service: RecommendationService = Depends(get_recommendation_service),
) -> RecommendationResponse:
    try:
        recommendations = service.get_recommendations(
            preferences=payload,
            max_candidates=payload.candidate_limit,
        )
        return recommendations
    except ValueError as e:
        logger.warning("Validation error in recommendation request: %s", e)
        raise HTTPException(
            status_code=422,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Error generating recommendations: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation pipeline failed: {str(e)}",
        )
