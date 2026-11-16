"""
test_data.py — Data Validation Tests

Validates the integrity of the interview question dataset and
synthetic development answers. Ensures configuration is consistent.

NOTE: The synthetic_answers.csv contains AI-generated development data
with approximate ratings. These are NOT genuine human expert assessments.
"""

import csv
import json
import os
import sys

import pytest

# Ensure the project root is on the path so config can be imported.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from config.config import (
    QUESTIONS_PATH,
    SYNTHETIC_ANSWERS_PATH,
    SCORING_WEIGHTS,
    QUESTION_CATEGORIES,
    RATING_SCALE_MIN,
    RATING_SCALE_MAX,
    validate_weights,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def questions():
    """Load and return the questions dataset."""
    with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def answers():
    """Load and return the synthetic answers dataset as a list of dicts."""
    with open(SYNTHETIC_ANSWERS_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


# ── Questions JSON Tests ──────────────────────────────────────────────────────

class TestQuestionsDataset:
    """Tests for data/questions.json."""

    def test_questions_json_loads_successfully(self, questions):
        """Verify that questions.json loads without errors."""
        assert isinstance(questions, list), "questions.json should be a list"

    def test_at_least_15_questions(self, questions):
        """There must be at least 15 interview questions."""
        assert len(questions) >= 15, (
            f"Expected at least 15 questions, found {len(questions)}"
        )

    def test_each_category_has_five_questions(self, questions):
        """Each of the three categories must contain exactly five questions."""
        from collections import Counter
        category_counts = Counter(q["category"] for q in questions)
        for category in QUESTION_CATEGORIES:
            assert category_counts.get(category, 0) >= 5, (
                f"Category '{category}' has {category_counts.get(category, 0)} "
                f"questions; expected at least 5"
            )

    def test_required_fields_present(self, questions):
        """Every question must contain all required fields."""
        required_fields = {
            "question_id",
            "category",
            "question",
            "reference_answer",
            "expected_keywords",
            "key_points",
            "optional_key_points",
            "common_misconceptions",
            "uses_star_method",
            "evaluation_criteria",
        }
        for idx, q in enumerate(questions):
            missing = required_fields - set(q.keys())
            assert not missing, (
                f"Question at index {idx} (id={q.get('question_id', '?')}) "
                f"is missing fields: {missing}"
            )

    def test_question_ids_are_unique(self, questions):
        """All question_id values must be unique."""
        ids = [q["question_id"] for q in questions]
        assert len(ids) == len(set(ids)), "Duplicate question_id values found"

    def test_expected_keywords_are_lists(self, questions):
        """expected_keywords must be a non-empty list for every question."""
        for q in questions:
            assert isinstance(q["expected_keywords"], list), (
                f"expected_keywords for {q['question_id']} is not a list"
            )
            assert len(q["expected_keywords"]) > 0, (
                f"expected_keywords for {q['question_id']} is empty"
            )

    def test_behavioral_questions_use_star_method(self, questions):
        """Behavioral questions should have uses_star_method set to True."""
        for q in questions:
            if q["category"] == "Behavioral":
                assert q["uses_star_method"] is True, (
                    f"Behavioral question {q['question_id']} should have "
                    "uses_star_method=True"
                )


# ── Synthetic Answers CSV Tests ───────────────────────────────────────────────

class TestSyntheticAnswers:
    """Tests for data/synthetic_answers.csv."""

    REQUIRED_COLUMNS = {
        "answer_id",
        "question_id",
        "candidate_answer",
        "human_semantic_rating",
        "human_communication_rating",
        "human_structure_rating",
        "human_overall_rating",
    }

    RATING_COLUMNS = [
        "human_semantic_rating",
        "human_communication_rating",
        "human_structure_rating",
        "human_overall_rating",
    ]

    def test_csv_loads_successfully(self, answers):
        """Verify that synthetic_answers.csv loads without errors."""
        assert isinstance(answers, list)
        assert len(answers) > 0, "CSV file is empty"

    def test_at_least_20_answers(self, answers):
        """There must be at least 20 sample answers."""
        assert len(answers) >= 20, (
            f"Expected at least 20 answers, found {len(answers)}"
        )

    def test_required_columns_present(self, answers):
        """The CSV must contain all required columns."""
        actual_columns = set(answers[0].keys())
        missing = self.REQUIRED_COLUMNS - actual_columns
        assert not missing, f"CSV is missing columns: {missing}"

    def test_question_ids_reference_valid_questions(self, answers, questions):
        """All question_id values in the CSV must exist in questions.json."""
        valid_ids = {q["question_id"] for q in questions}
        csv_ids = {row["question_id"] for row in answers}
        invalid = csv_ids - valid_ids
        assert not invalid, (
            f"CSV references question_id(s) not in questions.json: {invalid}"
        )

    def test_ratings_within_scale(self, answers):
        """All rating values must be between RATING_SCALE_MIN and RATING_SCALE_MAX."""
        for row_idx, row in enumerate(answers):
            for col in self.RATING_COLUMNS:
                value = int(row[col])
                assert RATING_SCALE_MIN <= value <= RATING_SCALE_MAX, (
                    f"Row {row_idx}, {col} has value {value} outside "
                    f"[{RATING_SCALE_MIN}, {RATING_SCALE_MAX}]"
                )

    def test_answer_ids_are_unique(self, answers):
        """All answer_id values must be unique."""
        ids = [row["answer_id"] for row in answers]
        assert len(ids) == len(set(ids)), "Duplicate answer_id values found"


# ── Configuration Tests ───────────────────────────────────────────────────────

class TestConfiguration:
    """Tests for config/config.py scoring weights."""

    def test_weights_sum_to_one(self):
        """Scoring weights must sum to 1.0."""
        total = round(sum(SCORING_WEIGHTS.values()), 10)
        assert abs(total - 1.0) < 1e-9, (
            f"Scoring weights sum to {total}, expected 1.0"
        )

    def test_weights_are_non_negative(self):
        """All scoring weights must be non-negative."""
        for name, weight in SCORING_WEIGHTS.items():
            assert weight >= 0, f"Weight '{name}' is negative: {weight}"

    def test_validate_weights_rejects_negative(self):
        """validate_weights should raise ValueError for negative weights."""
        bad_weights = {"a": -0.1, "b": 1.1}
        with pytest.raises(ValueError, match="negative"):
            validate_weights(bad_weights)

    def test_validate_weights_rejects_wrong_total(self):
        """validate_weights should raise ValueError when total != 1.0."""
        bad_weights = {"a": 0.5, "b": 0.3}
        with pytest.raises(ValueError, match="sum to 1.0"):
            validate_weights(bad_weights)
