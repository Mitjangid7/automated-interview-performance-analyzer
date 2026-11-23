"""Focused CO4 tests; all Groq network calls are mocked."""
import json
from unittest.mock import MagicMock, patch
import pytest

from modules import llm_feedback


SAMPLE_EVAL = {
    "question": "What is the difference between a list and a tuple?",
    "candidate_answer": "Lists are mutable and tuples are immutable.",
    "candidate_level": "ty_student",
    "overall_score": 78.5,
    "performance_category": "Good",
    "component_scores": {"semantic": 80.0, "structure": 75.0, "communication": 78.0, "delivery": 80.0},
    "weighted_contributions": {"semantic": 32.0, "structure": 18.75, "communication": 15.6, "delivery": 12.0},
    "semantic_analysis": {
        "keypoint_coverage": {"covered_points": ["mutability"], "missing_points": ["use cases"]},
        "semantic_similarity": {"similarity_percentage": 70.0},
    },
    "sentiment_analysis": {"sentiment_label": "Neutral", "compound": 0.0},
    "information_extraction": {"keywords": ["list", "tuple"], "concepts": ["mutability"]},
    "structure_analysis": {"structure_type": "general", "star_analysis": {}},
}

SAMPLE_RESPONSE = {
    "summary": "A concise answer with the central distinction.",
    "strengths": ["Correctly identifies mutability."],
    "weaknesses": ["Does not explain typical use cases."],
    "missing_concepts": ["Lists suit changing collections; tuples suit fixed records."],
    "improved_answer": "Lists are mutable, so they suit changing collections. Tuples are immutable and suit fixed records.",
    "recommendations": ["Add use cases.", "Give an example.", "Conclude briefly."],
}


def test_prompt_contains_question_answer_and_fixed_scores():
    system, user = llm_feedback.build_llm_prompt(SAMPLE_EVAL, {"category": "Technical"})
    assert "experienced technical interview coach" in system
    assert "difference between a list and a tuple" in user
    assert "Lists are mutable" in user
    assert "Semantic Relevance (40%)" in user
    assert "Do NOT invent" in system


def test_prompt_includes_multilingual_context_when_translated():
    eval_with_ml = dict(SAMPLE_EVAL)
    eval_with_ml["multilingual_analysis"] = {
        "translation_used": True,
        "detected_language": "Hindi",
        "translated_text": "Lists are mutable collections and tuples are immutable records.",
    }
    system, user = llm_feedback.build_llm_prompt(eval_with_ml, {"category": "Technical"})
    assert "Hindi" in user
    assert "Lists are mutable collections and tuples are immutable records" in user


def test_parse_response_normalizes_schema():
    result = llm_feedback._parse_llm_response(SAMPLE_RESPONSE)
    assert result["status"] == "success"
    assert len(result["recommendations"]) == 3
    assert result["model_used"] == llm_feedback.GROQ_LLM_MODEL
    assert result["summary"] == "A concise answer with the central distinction."


def test_parse_response_handles_incomplete_fields():
    # Incomplete response missing several keys
    partial_response = {
        "summary": "Brief summary.",
        "strengths": ["A strength"],
    }
    result = llm_feedback._parse_llm_response(partial_response)
    assert result["status"] == "success"
    assert result["summary"] == "Brief summary."
    assert result["strengths"] == ["A strength"]
    assert result["weaknesses"] == []
    assert result["missing_concepts"] == []
    assert result["improved_answer"] == ""
    assert result["recommendations"] == []


def test_missing_api_key_returns_graceful_status():
    with patch.object(llm_feedback, "_resolve_groq_key", return_value=None):
        result = llm_feedback.generate_llm_feedback(SAMPLE_EVAL, {})
    assert result["status"] == "no_api_key"
    assert result["summary"] == ""
    assert "Groq API key not found" in result["error"]


def test_timeout_returns_graceful_status():
    with patch.object(llm_feedback, "_resolve_groq_key", return_value="fake-key"), \
         patch.object(llm_feedback, "_call_groq_llm", side_effect=TimeoutError("Request timed out")):
        result = llm_feedback.generate_llm_feedback(SAMPLE_EVAL, {})
    assert result["status"] == "timeout"
    assert "timed out" in result["error"].lower()


def test_rate_limit_returns_graceful_status():
    with patch.object(llm_feedback, "_resolve_groq_key", return_value="fake-key"), \
         patch.object(llm_feedback, "_call_groq_llm", side_effect=Exception("429 Too Many Requests: Rate limit exceeded")):
        result = llm_feedback.generate_llm_feedback(SAMPLE_EVAL, {})
    assert result["status"] == "rate_limit"
    assert "rate limit" in result["error"].lower()


def test_auth_error_returns_graceful_status():
    with patch.object(llm_feedback, "_resolve_groq_key", return_value="fake-key"), \
         patch.object(llm_feedback, "_call_groq_llm", side_effect=Exception("401 Unauthorized: Invalid API Key")):
        result = llm_feedback.generate_llm_feedback(SAMPLE_EVAL, {})
    assert result["status"] == "auth_error"
    assert "401" in result["error"]


def test_invalid_json_returns_parse_error():
    with patch.object(llm_feedback, "_resolve_groq_key", return_value="fake-key"), \
         patch.object(llm_feedback, "_call_groq_llm", side_effect=json.JSONDecodeError("Expecting value", "doc", 0)):
        result = llm_feedback.generate_llm_feedback(SAMPLE_EVAL, {})
    assert result["status"] == "parse_error"
    assert "Could not parse" in result["error"]


def test_generate_feedback_success_uses_mocked_llm():
    before_scores = dict(SAMPLE_EVAL["component_scores"])
    before_overall = SAMPLE_EVAL["overall_score"]
    with patch.object(llm_feedback, "_resolve_groq_key", return_value="fake-key"), \
         patch.object(llm_feedback, "_call_groq_llm", return_value=SAMPLE_RESPONSE):
        result = llm_feedback.generate_llm_feedback(SAMPLE_EVAL, {"category": "Technical"})
    assert result["status"] == "success"
    assert result["improved_answer"]
    assert len(result["recommendations"]) == 3
    # Existing scores must never be modified
    assert SAMPLE_EVAL["component_scores"] == before_scores
    assert SAMPLE_EVAL["overall_score"] == before_overall


def test_scoring_weights_unchanged():
    from config.config import SCORING_WEIGHTS
    assert SCORING_WEIGHTS["semantic_relevance"] == 0.40
    assert SCORING_WEIGHTS["answer_structure"] == 0.25
    assert SCORING_WEIGHTS["communication"] == 0.20
    assert SCORING_WEIGHTS["delivery_indicators"] == 0.15


def test_ui_results_generates_and_stores_ai_feedback():
    from ui.results import render_results

    st_mock = MagicMock()
    st_mock.session_state = {}
    st_mock.tabs.return_value = [MagicMock() for _ in range(5)]
    st_mock.columns.side_effect = lambda spec: [MagicMock() for _ in range(spec if isinstance(spec, int) else len(spec))]
    st_mock.button.return_value = True

    parsed_sample = llm_feedback._parse_llm_response(SAMPLE_RESPONSE)
    with patch("modules.llm_feedback.generate_llm_feedback", return_value=parsed_sample):
        render_results(st_mock, SAMPLE_EVAL, {"category": "Technical"})

    stored_keys = [k for k in st_mock.session_state if k.startswith("llm_feedback_")]
    assert len(stored_keys) == 1
    assert st_mock.session_state[stored_keys[0]]["status"] == "success"
    assert st_mock.session_state[stored_keys[0]]["summary"] == SAMPLE_RESPONSE["summary"]

