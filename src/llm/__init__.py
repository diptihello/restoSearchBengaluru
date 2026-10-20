"""LLM client, prompt templates, and schema parsing module."""

from src.llm.client import (
    GeminiLLMClient,
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

__all__ = [
    "GeminiLLMClient",
    "generate_fallback_recommendations",
    "validate_recommendation_grounding",
    "SYSTEM_INSTRUCTION",
    "build_recommendation_prompt",
    "serialize_candidates",
    "CandidateRestaurant",
    "RecommendationResponse",
    "RestaurantRecommendation",
    "UserPreferences",
]
