"""
test_structure.py — Unit Tests for Answer Structure and STAR Method Detection
"""

import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from modules.structure_analysis import detect_star_structure


class TestSTARStructureDetection:
    """Tests for detect_star_structure."""

    def test_complete_star_response(self):
        text = (
            "Situation: In my previous role at our analytics company, our database was crashing under peak loads. "
            "Task: My responsibility was to identify bottlenecks and optimize the slow-performing queries. "
            "Action: I analyzed slow query logs, implemented redis caching for repeated joins, and added composite indexes. "
            "Result: We achieved a 65% reduction in query latency, and our uptime improved to 99.9%."
        )
        res = detect_star_structure(text, is_behavioral=True)
        assert res["applicable"] is True
        assert res["situation_detected"] is True
        assert res["task_detected"] is True
        assert res["action_detected"] is True
        assert res["result_detected"] is True
        assert res["star_completeness_ratio"] == 1.0
        assert len(res["components_detected"]) == 4
        assert len(res["components_missing"]) == 0
        assert len(res["supporting_sentences"]["Situation"]) > 0
        assert len(res["supporting_sentences"]["Task"]) > 0
        assert len(res["supporting_sentences"]["Action"]) > 0
        assert len(res["supporting_sentences"]["Result"]) > 0

    def test_missing_result_component(self):
        text = (
            "During my internship at tech corp, our team had to build a dashboard. "
            "My responsibility was to design the REST endpoints. "
            "I developed three endpoints using FastAPI and wrote automated tests."
        )
        res = detect_star_structure(text, is_behavioral=True)
        assert res["applicable"] is True
        assert res["situation_detected"] is True
        assert res["task_detected"] is True
        assert res["action_detected"] is True
        assert res["result_detected"] is False
        assert "Result" in res["components_missing"]
        assert res["star_completeness_ratio"] == 0.75

    def test_missing_action_component(self):
        text = (
            "At my previous job, our payment service stopped processing transactions. "
            "I was assigned to fix the outage and report to the VP. "
            "As a result, we recovered all lost records and our client renewed the contract."
        )
        res = detect_star_structure(text, is_behavioral=True)
        assert res["applicable"] is True
        assert res["situation_detected"] is True
        assert res["task_detected"] is True
        assert res["action_detected"] is False
        assert res["result_detected"] is True
        assert "Action" in res["components_missing"]
        assert res["star_completeness_ratio"] == 0.75

    def test_non_star_technical_answer_when_behavioral_flag_set(self):
        # A purely factual definition (e.g., Python lists vs tuples) evaluated in STAR
        text = "Lists are mutable sequences in Python, while tuples are immutable."
        res = detect_star_structure(text, is_behavioral=True)
        assert res["applicable"] is True
        assert res["star_completeness_ratio"] < 0.5
        assert len(res["components_missing"]) >= 3

    def test_empty_response(self):
        res = detect_star_structure("", is_behavioral=True)
        assert res["applicable"] is True
        assert res["star_completeness_ratio"] == 0.0
        assert len(res["components_missing"]) == 4

    def test_non_behavioral_flag_returns_not_applicable(self):
        text = "Lists and tuples are sequences in Python."
        res = detect_star_structure(text, is_behavioral=False)
        assert res["applicable"] is False
        assert res["star_completeness_ratio"] == 0.0
        assert "not applicable" in res["observations"][0].lower()

    def test_with_question_metadata_behavioral(self):
        question = {
            "question_id": "BEH001",
            "category": "Behavioral",
            "uses_star_method": True
        }
        text = (
            "In my previous project, we were tasked with a data migration. "
            "My responsibility was ETL architecture. "
            "I implemented a distributed worker pool. "
            "We achieved completion two weeks early."
        )
        res = detect_star_structure(text, question=question)
        assert res["applicable"] is True
        assert res["situation_detected"] is True
        assert res["star_completeness_ratio"] == 1.0

    def test_with_question_metadata_technical(self):
        question = {
            "question_id": "TECH001",
            "category": "Technical",
            "uses_star_method": False
        }
        text = "An INNER JOIN returns matching records, whereas LEFT JOIN returns all left rows."
        res = detect_star_structure(text, question=question)
        assert res["applicable"] is False
        assert "not applicable" in res["observations"][0].lower()

