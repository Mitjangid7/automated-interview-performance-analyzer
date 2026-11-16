"""
test_feedback.py — Unit Tests for Personalized Feedback Generator
"""

import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from modules.feedback import generate_feedback
from modules.scoring import evaluate_answer


class TestFeedbackGeneration:
    """Tests for generate_feedback."""

    def test_strengths_and_improvements_generated(self):
        cand = (
            "Situation: Our team was tasked with improving database reliability. "
            "Task: I had to lead the migration. "
            "Action: I scheduled daily standups and refactored the database schema. "
            "Result: System uptime increased to 99.9%."
        )
        eval_res = evaluate_answer("BEH001", cand)
        feedback = eval_res["feedback"]

        assert "strengths" in feedback
        assert len(feedback["strengths"]) > 0
        assert "areas_for_improvement" in feedback
        assert "actionable_suggestions" in feedback
        assert "suggested_improved_answer" in feedback
        assert "summary" in feedback
        assert feedback["summary"]["overall_score"] > 0.0

    def test_improvements_refer_to_missing_concepts(self):
        # Brief incomplete answer missing key concepts
        cand = "I worked on a team once and it was fine."
        eval_res = evaluate_answer("BEH001", cand)
        feedback = eval_res["feedback"]

        areas = " ".join(feedback["areas_for_improvement"]).lower()
        # Should flag missing STAR components or missing coverage
        assert "missing" in areas or "brief" in areas

    def test_suggested_answer_does_not_invent_candidate_achievements(self):
        cand = "Lists are mutable and tuples are immutable."
        eval_res = evaluate_answer("TECH001", cand)
        suggested = eval_res["feedback"]["suggested_improved_answer"]

        # Must be clearly labeled as a template / blueprint
        assert "[Example Revision Blueprint]" in suggested or "[Suggested Template]" in suggested
        assert "Lists are mutable and tuples are immutable" in suggested

    def test_feedback_handles_empty_answer(self):
        eval_res = evaluate_answer("TECH001", "")
        feedback = eval_res["feedback"]
        assert len(feedback["areas_for_improvement"]) > 0
        assert "[Suggested Template]" in feedback["suggested_improved_answer"]
        assert feedback["summary"]["overall_score"] == 0.0

