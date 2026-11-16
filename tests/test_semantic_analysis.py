"""
test_semantic_analysis.py — Unit Tests for Semantic Analysis & Technical Correctness
"""

import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from modules.semantic_analysis import (
    calculate_cosine_similarity,
    calculate_tfidf_similarity,
    calculate_semantic_similarity,
    calculate_keypoint_coverage,
    calculate_question_relevance,
    analyze_technical_correctness,
    analyze_semantics,
    load_embedding_model,
)


class TestCosineAndTFIDFSimilarity:
    """Tests for vector math and TF-IDF baseline."""

    def test_cosine_similarity_identical(self):
        v = [1.0, 2.0, 3.0]
        assert pytest.approx(calculate_cosine_similarity(v, v), 0.001) == 1.0

    def test_cosine_similarity_orthogonal(self):
        v1 = [1.0, 0.0]
        v2 = [0.0, 1.0]
        assert calculate_cosine_similarity(v1, v2) == 0.0

    def test_cosine_similarity_zero_vector(self):
        assert calculate_cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0

    def test_tfidf_similarity_identical_text(self):
        text = "Lists and tuples are sequences in Python."
        sim = calculate_tfidf_similarity(text, text)
        assert pytest.approx(sim, 0.05) == 1.0

    def test_tfidf_similarity_unrelated_text(self):
        t1 = "Relational SQL database inner join"
        t2 = "Cooking pasta with tomato sauce and basil"
        sim = calculate_tfidf_similarity(t1, t2)
        assert sim < 0.15

    def test_tfidf_empty_inputs(self):
        assert calculate_tfidf_similarity("", "Sample text") == 0.0
        assert calculate_tfidf_similarity("Sample text", "") == 0.0


class TestSemanticSimilarity:
    """Tests for calculate_semantic_similarity."""

    def test_semantic_similarity_similar_answers(self):
        cand = "Lists in Python are mutable collections, whereas tuples cannot be modified after creation."
        ref = "Lists are mutable and tuples are immutable in Python."
        res = calculate_semantic_similarity(cand, ref)
        assert res["similarity_score"] > 0.35
        assert res["similarity_percentage"] > 35.0
        assert res["analysis_status"] in ("success", "fallback_tfidf")
        assert res["model_name"] in ("all-MiniLM-L6-v2", "tfidf_baseline")

    def test_semantic_similarity_empty(self):
        res = calculate_semantic_similarity("", "Reference answer.")
        assert res["similarity_score"] == 0.0
        assert res["analysis_status"] == "empty_input"


class TestKeypointCoverage:
    """Tests for key-point coverage calculation."""

    def test_keypoint_coverage_full(self):
        key_points = [
            "Lists are mutable; tuples are immutable",
            "Tuples are hashable and can be dictionary keys",
            "Performance and memory differences"
        ]
        answer = (
            "The main distinction is mutability: lists are mutable while tuples are immutable. "
            "Because tuples are immutable, they are hashable and can be used as dictionary keys. "
            "Tuples also use less memory and have slight performance advantages."
        )
        res = calculate_keypoint_coverage(answer, key_points)
        assert res["total_essential_points"] == 3
        assert len(res["covered_essential_points"]) >= 2
        assert res["coverage_percentage"] >= 60.0

    def test_keypoint_coverage_missing(self):
        key_points = [
            "Lists are mutable; tuples are immutable",
            "Tuples are hashable and can be dictionary keys",
            "Performance and memory differences"
        ]
        answer = "I prefer using lists because square brackets look nicer in my code editor."
        res = calculate_keypoint_coverage(answer, key_points)
        assert len(res["missing_essential_points"]) >= 2
        assert res["coverage_percentage"] < 40.0

    def test_optional_points_not_counted_in_essential_denominator(self):
        key_points = ["Concept A", "Concept B"]
        optional = ["Optional detail C"]
        answer = "Concept A is addressed here thoroughly. Optional detail C is also mentioned."
        res = calculate_keypoint_coverage(answer, key_points, optional_key_points=optional)
        assert res["total_essential_points"] == 2
        assert len(res["optional_points_covered"]) >= 0


class TestQuestionRelevance:
    """Tests for calculate_question_relevance."""

    def test_question_relevance_relevant(self):
        q = "What is the difference between INNER JOIN and LEFT JOIN in SQL?"
        a = "An INNER JOIN returns matching records, while a LEFT JOIN includes all rows from the left table."
        res = calculate_question_relevance(q, a)
        assert res["is_relevant"] is True
        assert res["relevance_score"] > 0.15

    def test_question_relevance_unrelated(self):
        q = "Explain precision and recall."
        a = "Yesterday I went grocery shopping and bought oranges and apples."
        res = calculate_question_relevance(q, a)
        assert res["relevance_score"] < 0.20


class TestTechnicalCorrectness:
    """Tests for analyze_technical_correctness."""

    def test_detects_known_misconception(self):
        q_data = {
            "question_id": "TECH001",
            "common_misconceptions": [
                "Tuples are just read-only lists with no other differences",
                "Lists and tuples are the same thing basically"
            ]
        }
        cand_answer = "Lists and tuples are the same thing basically, just different brackets."
        res = analyze_technical_correctness(cand_answer, q_data)
        assert res["has_misconceptions"] is True
        assert len(res["detected_misconceptions"]) >= 1

    def test_correct_answer_no_misconceptions(self):
        q_data = {
            "question_id": "TECH001",
            "common_misconceptions": [
                "Tuples are just read-only lists with no other differences",
                "Lists are always faster than tuples"
            ]
        }
        cand_answer = (
            "Lists are mutable while tuples are immutable. Tuples can be hashed and "
            "used as dictionary keys, whereas lists cannot."
        )
        res = analyze_technical_correctness(cand_answer, q_data)
        assert res["has_misconceptions"] is False
        assert len(res["detected_misconceptions"]) == 0

