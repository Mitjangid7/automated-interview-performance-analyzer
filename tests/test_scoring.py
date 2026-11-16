"""
test_scoring.py — Unit Tests for Interview Scoring Engine
"""

import json
import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from config.config import SCORING_WEIGHTS
from modules.scoring import evaluate_answer, get_performance_category


class TestScoringEngine:
    """Tests for evaluate_answer pipeline and scoring logic."""

    def test_evaluate_answer_score_bounds(self):
        cand = (
            "Situation: Our microservice database was failing under peak volume. "
            "Task: I was assigned to refactor the data access layer. "
            "Action: I implemented redis caching and optimized SQL queries. "
            "Result: Query response time decreased by 50% and uptime was restored."
        )
        res = evaluate_answer("BEH001", cand)
        assert 0.0 <= res["overall_score"] <= 100.0
        for comp, score in res["component_scores"].items():
            assert 0.0 <= score <= 100.0, f"Component {comp} out of bounds: {score}"
        for comp, contrib in res["weighted_contributions"].items():
            assert contrib >= 0.0, f"Contribution {comp} negative: {contrib}"

    def test_overall_score_matches_weighted_sum(self):
        cand = "In Python, lists are mutable sequence types, while tuples are immutable."
        res = evaluate_answer("TECH001", cand)
        # Verify overall score matches sum of weighted contributions
        expected_sum = sum(res["weighted_contributions"].values())
        assert pytest.approx(res["overall_score"], 0.05) == expected_sum

    def test_configurable_weights_reflected(self):
        cand = "An INNER JOIN matches records present in both tables."
        res = evaluate_answer("TECH002", cand)
        w_sem = SCORING_WEIGHTS["semantic_relevance"]
        w_comm = SCORING_WEIGHTS["communication"]
        w_del = SCORING_WEIGHTS["delivery_indicators"]
        w_str = SCORING_WEIGHTS["answer_structure"]

        assert pytest.approx(res["weighted_contributions"]["semantic"], 0.05) == res["component_scores"]["semantic"] * w_sem
        assert pytest.approx(res["weighted_contributions"]["communication"], 0.05) == res["component_scores"]["communication"] * w_comm
        assert pytest.approx(res["weighted_contributions"]["delivery"], 0.05) == res["component_scores"]["delivery"] * w_del
        assert pytest.approx(res["weighted_contributions"]["structure"], 0.05) == res["component_scores"]["structure"] * w_str

    def test_invalid_question_id_handled_gracefully(self):
        res = evaluate_answer("NONEXISTENT_QID", "Some answer.")
        assert res["overall_score"] == 0.0
        assert res["analysis_status"] == "error_invalid_question_id"
        assert res["feedback"]["summary"]["overall_score"] == 0.0

    def test_empty_answer_handled_gracefully(self):
        res = evaluate_answer("TECH001", "")
        assert res["overall_score"] == 0.0
        assert res["analysis_status"] == "empty_answer"
        assert res["component_scores"]["semantic"] == 0.0

    def test_json_serializability(self):
        cand = "Decorators in Python wrap functions to extend behavior without modifying source code."
        res = evaluate_answer("TECH005", cand)
        # Must serialize cleanly to JSON
        json_str = json.dumps(res)
        assert len(json_str) > 0
        loaded = json.loads(json_str)
        assert loaded["question_id"] == "TECH005"

    def test_performance_category_thresholds(self):
        assert get_performance_category(90.0) == "Excellent"
        assert get_performance_category(75.0) == "Good"
        assert get_performance_category(55.0) == "Average"
        assert get_performance_category(35.0) == "Needs Improvement"

