"""Prompt engineering, system instructions, and candidate context serialization."""

import json
from typing import Any, Dict, List, Union
import pandas as pd

from src.llm.schemas import CandidateRestaurant, UserPreferences

SYSTEM_INSTRUCTION = """You are an expert food concierge and culinary advisor inspired by Zomato.
Your task is to analyze a pre-filtered list of candidate restaurants and recommend the TOP 3 to 5 options that best match the user's specific dining preferences, budget, cuisine, rating threshold, and occasion.

CRITICAL GROUNDING RULES:
1. ONLY RECOMMEND RESTAURANTS FROM THE PROVIDED CANDIDATE LIST.
2. DO NOT invent, hallucinate, or recommend any restaurant that is not explicitly present in the provided candidates.
3. Use the exact restaurant name as given in the candidate list.
4. If a user preference cannot be satisfied perfectly, select the closest candidate and clearly explain the trade-off.
5. Provide persuasive, personalized reasoning in 'why_recommended' explaining why this specific restaurant fits their context (e.g. occasion, budget, cuisine).
6. Return your response in STRICT JSON matching the required schema without any extra markdown commentary or conversational preamble outside the JSON.
"""

def serialize_candidates(candidates: Union[List[Dict[str, Any]], List[CandidateRestaurant], pd.DataFrame]) -> str:
    """
    Serialize candidate restaurants into a compact, token-efficient JSON string for LLM context.
    """
    compact_records = []

    if isinstance(candidates, pd.DataFrame):
        records = candidates.to_dict(orient="records")
    else:
        records = candidates

    for item in records:
        if isinstance(item, CandidateRestaurant):
            data = item.model_dump()
        elif isinstance(item, dict):
            data = item
        else:
            continue

        cuisines = data.get("cuisines")
        if isinstance(cuisines, list):
            cuisine_str = ", ".join(cuisines[:4])
        else:
            cuisine_str = str(data.get("cuisines_str", cuisines or ""))

        record = {
            "id": data.get("restaurant_id"),
            "name": data.get("name"),
            "location": data.get("location"),
            "rating": data.get("rating"),
            "votes": data.get("votes", 0),
            "cost_for_two": data.get("cost_for_two"),
            "cuisines": cuisine_str,
            "dishes_liked": str(data.get("dish_liked", "") or "")[:60],
            "features": {
                "online_order": bool(data.get("online_order", False)),
                "book_table": bool(data.get("book_table", False)),
                "rest_type": str(data.get("rest_type", "") or "")[:30],
            },
        }
        compact_records.append(record)

    return json.dumps(compact_records, separators=(",", ":"))

def build_recommendation_prompt(preferences: UserPreferences, candidate_context: str) -> str:
    """
    Construct the complete LLM prompt combining user intent and candidate context.
    """
    cuisines_str = ", ".join(preferences.cuisines) if preferences.cuisines else "Any / Multi-cuisine"
    budget_info = f"Budget Tier: {preferences.budget_tier}"
    if preferences.max_budget:
        budget_info += f" (Max budget: ₹{preferences.max_budget} for two)"

    prompt = f"""### USER PREFERENCES & INTENT
- Location: {preferences.location}
- {budget_info}
- Preferred Cuisines: {cuisines_str}
- Minimum Rating: {preferences.min_rating} / 5.0
- Occasion / Vibe: {preferences.occasion or 'General dining'}
- Dining Type: {preferences.dining_type or 'Any'}

### AVAILABLE CANDIDATE RESTAURANTS (Pick ONLY from this list)
{candidate_context}

### TASK INSTRUCTIONS
1. Evaluate the candidate restaurants against the user's preferences and occasion.
2. Rank the top 3 to 5 best matching restaurants (Rank 1 = best overall match).
3. For each recommendation, provide:
   - 'rank': integer (1, 2, 3...)
   - 'restaurant_name': EXACT name from the candidate list
   - 'cuisine': brief summary of cuisines offered
   - 'rating': float rating from candidate data
   - 'cost_for_two': integer cost from candidate data
   - 'location': location string from candidate data
   - 'why_recommended': 2-3 sentences explaining why this fits their requested occasion and preferences
   - 'highlights': 2-4 notable attributes, signature dishes, or vibe highlights
4. Provide an 'executive_summary' (2-3 sentences) comparing your top picks and guiding their final choice.

Respond ONLY with valid JSON matching the RecommendationResponse schema.
"""
    return prompt
