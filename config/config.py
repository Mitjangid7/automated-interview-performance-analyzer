"""
Configuration file for the Automated Interview Performance Analyzer.

Defines project settings, dataset paths, model configuration placeholders,
and scoring weights. All weights are configurable and validated at import time.
"""

import os

# ── Project Metadata ──────────────────────────────────────────────────────────
PROJECT_NAME = "Automated Interview Performance Analyzer"
VERSION = "0.1.0"

# ── Dataset Paths ─────────────────────────────────────────────────────────────
# Resolve paths relative to the project root (one level above config/).
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(_PROJECT_ROOT, "data")
QUESTIONS_PATH = os.path.join(DATA_DIR, "questions.json")
SYNTHETIC_ANSWERS_PATH = os.path.join(DATA_DIR, "synthetic_answers.csv")

# ── Model Configuration Placeholders ─────────────────────────────────────────
# These will be populated when the ML/NLP analysis engine is implemented.
MODEL_CONFIG = {
    "sentence_transformer_model": "all-MiniLM-L6-v2",  # placeholder
    "similarity_threshold": 0.5,                        # placeholder
    "max_answer_length": 2000,                          # characters
    "min_answer_length": 20,                             # characters
}

# ── Scoring Weights ───────────────────────────────────────────────────────────
# Weights must be non-negative and sum to 1.0 (100%).
SCORING_WEIGHTS = {
    "semantic_relevance": 0.40,    # 40%
    "communication": 0.20,        # 20%
    "delivery_indicators": 0.15,  # 15%
    "answer_structure": 0.25,     # 25%
}

# ── Rating Scale ──────────────────────────────────────────────────────────────
RATING_SCALE_MIN = 1
RATING_SCALE_MAX = 5

# ── Question Categories ──────────────────────────────────────────────────────
QUESTION_CATEGORIES = ["HR", "Behavioral", "Technical"]

# ── Candidate Levels ─────────────────────────────────────────────────────────
from config.candidate_levels import (
    CANDIDATE_LEVELS,
    DEFAULT_CANDIDATE_LEVEL,
    LEVEL_DISPLAY_OPTIONS,
    LEVEL_EXPERIENCED,
    LEVEL_FINAL_YEAR,
    LEVEL_TY_STUDENT,
    get_candidate_level_info,
    validate_candidate_level,
)

# ── Validation ────────────────────────────────────────────────────────────────

def validate_weights(weights: dict) -> None:
    """
    Validate that scoring weights are non-negative and sum to 1.0.

    Args:
        weights: Dictionary mapping component names to their weights.

    Raises:
        ValueError: If any weight is negative or the total does not equal 1.0.
    """
    for name, weight in weights.items():
        if weight < 0:
            raise ValueError(
                f"Scoring weight '{name}' is negative ({weight}). "
                "All weights must be non-negative."
            )

    total = round(sum(weights.values()), 10)
    if abs(total - 1.0) > 1e-9:
        raise ValueError(
            f"Scoring weights must sum to 1.0 (100%), but got {total}. "
            f"Current weights: {weights}"
        )


# Run validation on import to catch configuration errors early.
validate_weights(SCORING_WEIGHTS)

