"""Gemini LLM client wrapper, grounding validator, and deterministic fallback engine."""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import pandas as pd
from google.genai import Client, types

from src.config import settings
from src.llm.prompt_templates import SYSTEM_INSTRUCTION, build_recommendation_prompt, serialize_candidates
from src.llm.schemas import (
    CandidateRestaurant,
    RecommendationResponse,
    RestaurantRecommendation,
    UserPreferences,
)

logger = logging.getLogger(__name__)


def _normalize_name(name: str) -> str:
    """Normalize restaurant name for robust comparison."""
    if not name:
        return ""
    # Strip leading/trailing whitespace, punctuation, and lowercase
    cleaned = re.sub(r"[^\w\s]", "", name).strip().lower()
    return " ".join(cleaned.split())


def _extract_candidate_names(
    candidates: Union[List[Dict[str, Any]], List[CandidateRestaurant], pd.DataFrame]
) -> Set[str]:
    """Extract a set of normalized restaurant names from candidate pool."""
    names: Set[str] = set()

    if isinstance(candidates, pd.DataFrame):
        records = candidates.to_dict(orient="records")
    else:
        records = candidates

    for item in records:
        if isinstance(item, CandidateRestaurant):
            name = item.name
        elif isinstance(item, dict):
            name = item.get("name", "")
        else:
            continue

        if name:
            names.add(_normalize_name(name))

    return names


def _normalize_candidates_to_dicts(
    candidates: Union[List[Dict[str, Any]], List[CandidateRestaurant], pd.DataFrame]
) -> List[Dict[str, Any]]:
    """Convert various candidate input representations into a uniform list of dicts."""
    if isinstance(candidates, pd.DataFrame):
        return candidates.to_dict(orient="records")

    normalized: List[Dict[str, Any]] = []
    for item in candidates:
        if isinstance(item, CandidateRestaurant):
            normalized.append(item.model_dump())
        elif isinstance(item, dict):
            normalized.append(item)
    return normalized


def validate_recommendation_grounding(
    response: RecommendationResponse,
    candidates: Union[List[Dict[str, Any]], List[CandidateRestaurant], pd.DataFrame],
) -> Tuple[bool, List[str]]:
    """
    Verify that every restaurant in the response strictly exists in the candidate subset.

    Returns:
        Tuple of (is_grounded, list_of_hallucinated_names)
    """
    candidate_names = _extract_candidate_names(candidates)
    hallucinated: List[str] = []

    for rec in response.recommendations:
        norm_rec_name = _normalize_name(rec.restaurant_name)
        if norm_rec_name not in candidate_names:
            hallucinated.append(rec.restaurant_name)

    is_grounded = len(hallucinated) == 0
    return is_grounded, hallucinated


def generate_fallback_recommendations(
    preferences: UserPreferences,
    candidates: Union[List[Dict[str, Any]], List[CandidateRestaurant], pd.DataFrame],
    reason: str = "",
    top_n: int = 5,
) -> RecommendationResponse:
    """
    Deterministic fallback mechanism sorting candidates by rating and review volume.
    Used when Gemini API is offline, unconfigured, or produces ungrounded output.
    """
    records = _normalize_candidates_to_dicts(candidates)

    if not records:
        return RecommendationResponse(
            recommendations=[],
            executive_summary="No candidate restaurants available matching your criteria.",
            is_fallback=True,
        )

    # Deterministic sorting: highest rating first, then highest votes count
    def _sort_key(c: Dict[str, Any]) -> Tuple[float, int]:
        rating = c.get("rating")
        try:
            r_val = float(rating) if rating is not None and not pd.isna(rating) else 0.0
        except (ValueError, TypeError):
            r_val = 0.0

        votes = c.get("votes")
        try:
            v_val = int(votes) if votes is not None and not pd.isna(votes) else 0
        except (ValueError, TypeError):
            v_val = 0

        return (r_val, v_val)

    sorted_candidates = sorted(records, key=_sort_key, reverse=True)
    selected = sorted_candidates[: min(len(sorted_candidates), top_n)]

    recommendations: List[RestaurantRecommendation] = []
    for idx, c in enumerate(selected, start=1):
        cuisines = c.get("cuisines")
        if isinstance(cuisines, list):
            cuisine_str = ", ".join(cuisines[:3])
        else:
            cuisine_str = str(c.get("cuisines_str", cuisines or "Multi-cuisine"))

        rating_val = c.get("rating")
        try:
            rating_float = round(float(rating_val), 1) if rating_val is not None and not pd.isna(rating_val) else 0.0
        except (ValueError, TypeError):
            rating_float = 0.0

        cost_val = c.get("cost_for_two")
        try:
            cost_int = int(cost_val) if cost_val is not None and not pd.isna(cost_val) else 0
        except (ValueError, TypeError):
            cost_int = 0

        votes = c.get("votes", 0)
        location = str(c.get("location") or preferences.location)
        name = str(c.get("name") or f"Restaurant #{c.get('restaurant_id', idx)}")

        # Build dynamic highlight tags
        highlights: List[str] = []
        if rating_float >= 4.0:
            highlights.append(f"Highly Rated ({rating_float}★)")
        if votes and int(votes) > 100:
            highlights.append(f"Popular Choice ({votes} reviews)")
        if c.get("online_order"):
            highlights.append("Online Delivery Available")
        if c.get("book_table"):
            highlights.append("Table Booking Available")
        if c.get("rest_type"):
            highlights.append(str(c.get("rest_type")))

        dish_liked = c.get("dish_liked")
        if dish_liked and str(dish_liked).strip():
            dishes = [d.strip() for d in str(dish_liked).split(",") if d.strip()]
            if dishes:
                highlights.append(f"Known for: {dishes[0]}")

        # Ensure 2-4 highlights
        if not highlights:
            highlights = ["Local Favorite", "Quality Dining"]
        highlights = highlights[:4]

        # Tailored fallback reasoning
        occasion_ctx = f" for {preferences.occasion}" if preferences.occasion else ""
        why = (
            f"Top-rated venue in {location} with a {rating_float}/5.0 score across {votes} reviews. "
            f"Specializes in {cuisine_str} at approximately ₹{cost_int} for two, matching your "
            f"{preferences.budget_tier} budget tier{occasion_ctx}."
        )

        recommendations.append(
            RestaurantRecommendation(
                rank=idx,
                restaurant_name=name,
                cuisine=cuisine_str,
                rating=rating_float,
                cost_for_two=cost_int,
                location=location,
                why_recommended=why,
                highlights=highlights,
            )
        )

    exec_summary = (
        f"Selected the top {len(recommendations)} highest-rated and most popular restaurants in {preferences.location} "
        f"using deterministic ranking."
    )
    if reason:
        exec_summary += f" (Note: {reason})"

    return RecommendationResponse(
        recommendations=recommendations,
        executive_summary=exec_summary,
        is_fallback=True,
    )


class GeminiLLMClient:
    """
    Google Gemini LLM client supporting structured output generation,
    grounding validation, and graceful fallback degradation.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ):
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.model = model if model is not None else settings.GEMINI_MODEL
        self.temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
        self.client: Optional[Client] = None

        if self.api_key and self.api_key.strip():
            try:
                self.client = Client(api_key=self.api_key)
                logger.info("Initialized Gemini Client with model '%s'", self.model)
            except Exception as e:
                logger.warning("Failed to initialize Google GenAI Client: %s", e)
                self.client = None
        else:
            logger.info("No Gemini API key supplied; client will default to heuristic fallback.")

    def generate_recommendations(
        self,
        preferences: UserPreferences,
        candidates: Union[List[Dict[str, Any]], List[CandidateRestaurant], pd.DataFrame],
    ) -> RecommendationResponse:
        """
        Generate structured restaurant recommendations via Gemini LLM with anti-hallucination guardrails.
        Falls back seamlessly to deterministic ranking if the LLM is unavailable or fails.
        """
        # 1. Check if candidate pool is empty
        candidate_dicts = _normalize_candidates_to_dicts(candidates)
        if not candidate_dicts:
            return generate_fallback_recommendations(
                preferences,
                candidates,
                reason="No candidate restaurants available in the filtered pool.",
            )

        # 2. Check if client is initialized
        if self.client is None:
            logger.info("Gemini API client not initialized. Activating deterministic fallback.")
            return generate_fallback_recommendations(
                preferences,
                candidates,
                reason="Gemini API key is not configured.",
            )

        # 3. Build prompt and context
        candidate_context = serialize_candidates(candidates)
        prompt = build_recommendation_prompt(preferences, candidate_context)

        try:
            config = types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=self.temperature,
                response_mime_type="application/json",
                response_schema=RecommendationResponse,
            )

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config,
            )

            # 4. Extract and parse response
            raw_text = response.text
            if not raw_text or not raw_text.strip():
                raise ValueError("Received empty response from Gemini API.")

            # Clean potential markdown fences if present
            cleaned_text = raw_text.strip()
            if cleaned_text.startswith("```"):
                cleaned_text = re.sub(r"^```(?:json)?\n?", "", cleaned_text)
                cleaned_text = re.sub(r"\n?```$", "", cleaned_text)

            parsed_response = RecommendationResponse.model_validate_json(cleaned_text)

            # 5. Anti-hallucination grounding verification
            is_grounded, hallucinated_names = validate_recommendation_grounding(
                parsed_response, candidates
            )

            if not is_grounded:
                logger.warning(
                    "Anti-hallucination check detected ungrounded restaurant names: %s",
                    hallucinated_names,
                )
                # Filter out hallucinated recommendations
                valid_recs = [
                    rec
                    for rec in parsed_response.recommendations
                    if rec.restaurant_name not in hallucinated_names
                ]

                if valid_recs:
                    # Re-rank remaining valid recommendations
                    for i, rec in enumerate(valid_recs, start=1):
                        rec.rank = i
                    parsed_response.recommendations = valid_recs
                    return parsed_response
                else:
                    logger.warning(
                        "All LLM recommendations were ungrounded. Reverting to deterministic fallback."
                    )
                    return generate_fallback_recommendations(
                        preferences,
                        candidates,
                        reason="LLM generated unknown restaurants outside candidate pool.",
                    )

            if not parsed_response.recommendations and candidate_dicts:
                logger.info(
                    "LLM returned empty recommendations list despite %d candidates. Using heuristic fallback.",
                    len(candidate_dicts),
                )
                return generate_fallback_recommendations(
                    preferences,
                    candidates,
                    reason="LLM returned no matches. Showing top-rated candidates.",
                )

            return parsed_response

        except Exception as e:
            logger.error("Error executing Gemini recommendation generation: %s", e, exc_info=True)
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "Quota exceeded" in err_str:
                clean_reason = "Gemini API daily quota limit reached. Displaying top-rated dining spots using deterministic ranking."
            elif "503" in err_str or "UNAVAILABLE" in err_str:
                clean_reason = "Gemini service temporarily unavailable. Displaying top-rated dining spots using deterministic ranking."
            elif "API_KEY_INVALID" in err_str or "API key not valid" in err_str:
                clean_reason = "Invalid Gemini API key configured. Displaying top-rated dining spots using deterministic ranking."
            else:
                clean_reason = "AI synthesis unavailable. Displaying top-rated dining spots using deterministic ranking."

            return generate_fallback_recommendations(
                preferences,
                candidates,
                reason=clean_reason,
            )
