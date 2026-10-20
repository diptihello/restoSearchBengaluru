"""Pydantic schemas for LLM reasoning, inputs, and structured outputs."""

from typing import List, Optional
from pydantic import BaseModel, Field

class UserPreferences(BaseModel):
    """User preferences provided for restaurant recommendations."""
    location: str = Field(..., description="Target locality, neighborhood, or city (e.g., Indiranagar, Banashankari)")
    budget_tier: Optional[str] = Field("Medium", description="Budget tier: 'Low' (<=500), 'Medium' (500-1500), 'High' (>1500), or 'Any'")
    max_budget: Optional[int] = Field(None, description="Explicit max cost for two in INR (optional)")
    cuisines: List[str] = Field(default_factory=list, description="List of preferred cuisines (e.g., ['North Indian', 'Chinese'])")
    min_rating: float = Field(3.5, ge=0.0, le=5.0, description="Minimum acceptable rating out of 5.0")
    occasion: Optional[str] = Field(None, description="Specific dining context or mood (e.g., 'romantic dinner', 'quick lunch', 'family gathering')")
    dining_type: Optional[str] = Field(None, description="Preferred dining type: Dine-out, Delivery, Buffet, Cafes, etc.")

class CandidateRestaurant(BaseModel):
    """Structured representation of a candidate restaurant passed into LLM context."""
    restaurant_id: int
    name: str
    location: str
    rating: Optional[float] = None
    votes: int = 0
    cost_for_two: int
    cuisines: List[str] = Field(default_factory=list)
    rest_type: Optional[str] = ""
    dish_liked: Optional[str] = ""
    online_order: bool = False
    book_table: bool = False

class RestaurantRecommendation(BaseModel):
    """A single ranked restaurant recommendation with personalized rationale."""
    rank: int = Field(..., description="Recommendation rank, starting at 1")
    restaurant_name: str = Field(..., description="Name of the restaurant (must match a candidate)")
    cuisine: str = Field(..., description="Cuisine summary for the restaurant")
    rating: float = Field(..., description="Aggregate rating (e.g., 4.2)")
    cost_for_two: int = Field(..., description="Approximate cost for two in INR")
    location: str = Field(..., description="Locality or address")
    why_recommended: str = Field(..., description="Personalized reasoning explaining why this venue fits user preferences and occasion")
    highlights: List[str] = Field(default_factory=list, description="Notable features, standout dishes, or ambiance tags")

class RecommendationResponse(BaseModel):
    """Structured output returned by the LLM recommendation engine."""
    recommendations: List[RestaurantRecommendation] = Field(default_factory=list, description="Ranked list of top recommendations (typically 3 to 5)")
    executive_summary: str = Field(..., description="Concise summary highlighting why these venues were selected and comparing them")
    is_fallback: bool = Field(False, description="Flag indicating if heuristic fallback was used instead of LLM")
