"""Deterministic retrieval and candidate selection module (Stage 1)."""

from src.retrieval.candidate_selector import (
    CandidateSelector,
    format_candidate_markdown_table,
    to_candidate_models,
)
from src.retrieval.filter_engine import (
    BUDGET_TIERS,
    FilterEngine,
    compute_cuisine_overlap_vectorized,
    get_budget_range,
)

__all__ = [
    "FilterEngine",
    "CandidateSelector",
    "get_budget_range",
    "compute_cuisine_overlap_vectorized",
    "to_candidate_models",
    "format_candidate_markdown_table",
    "BUDGET_TIERS",
]
