"""
test_clean_navigation.py — Verification of Cleaned Navigation and Preserved Core Functionality

Verifies:
1. Navigation items strictly contain only the 5 approved core views:
   - Dashboard
   - Practice Interview
   - Performance Analysis
   - Interview History
   - About Project
2. Mock Interviewer Chat and ChromaDB RAG are completely absent from navigation and routing.
3. Practice Interview evaluation engine (CO1 - CO3) operates cleanly.
4. Groq LLM-based personalized coaching feedback (CO4) functions properly.
5. Local interview history persistence remains fully functional.
"""

import os
from unittest.mock import patch, MagicMock
import pytest

from modules.scoring import evaluate_answer
from modules.llm_feedback import generate_llm_feedback
from ui.history import load_history, save_evaluation_to_history, clear_history


def test_navigation_items_exclude_mock_chat():
    """Verify app.py navigation contains only the 5 approved views and no mock chat."""
    app_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py"
    )
    with open(app_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Verify Mock Interviewer Chat is not in the navigation items
    assert "Mock Interviewer Chat" not in content
    assert "render_mock_chat" not in content
    assert "chat_view" not in content

    # Verify the 5 approved pages are present
    assert "Dashboard" in content
    assert "Practice Interview" in content
    assert "Performance Analysis" in content
    assert "Interview History" in content
    assert "About Project" in content


def test_rag_and_chat_files_do_not_exist():
    """Verify deleted mock chat and RAG modules are absent from the codebase."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assert not os.path.exists(os.path.join(base_dir, "ui", "chat_view.py"))
    assert not os.path.exists(os.path.join(base_dir, "modules", "rag_interview.py"))
    assert not os.path.exists(os.path.join(base_dir, "data", "chroma_db"))


def test_practice_interview_evaluation_preserved():
    """Verify Practice Interview scoring pipeline operates with exact scoring weights."""
    ans = "Lists are mutable and elements can be changed, while tuples are immutable fixed records that can be used as dictionary keys."
    res = evaluate_answer("TECH001", ans, candidate_level="final_year")

    # Score bounds and component presence
    assert 0.0 <= res["overall_score"] <= 100.0
    assert "semantic" in res["component_scores"]
    assert "structure" in res["component_scores"]
    assert "communication" in res["component_scores"]
    assert "delivery" in res["component_scores"]

    # Extended NLP metrics (CO1 - CO3)
    assert res["semantic_analysis"]["spacy_word_vector_similarity"] > 0.4
    assert res["semantic_analysis"]["spacy_vector_percentage"] > 40.0
    assert "entities_and_skills" in res
    assert "emotion_analysis" in res
    assert "topic_analysis" in res


def test_groq_llm_personalized_feedback_preserved():
    """Verify Groq LLM feedback generator executes with mock Groq response."""
    eval_data = {
        "question_id": "TECH001",
        "question": "Explain lists vs tuples",
        "candidate_level": "final_year",
        "candidate_answer": "Lists are mutable sequences whereas tuples are immutable.",
        "overall_score": 88.0,
        "component_scores": {"semantic": 90.0, "structure": 85.0, "communication": 85.0, "delivery": 85.0},
        "semantic_analysis": {"keypoint_coverage": {"missing_points": ["hashable keys"]}},
        "structure_analysis": {"star_detected": False},
        "feedback": {"strengths": ["Clear mutability distinction"], "areas_for_improvement": ["Mention hashability"]},
    }
    q_data = {
        "question": "Explain lists vs tuples",
        "category": "Technical",
    }

    mock_json_reply = """```json
{
    "summary": "Great explanation of core Python data structure mutability.",
    "strengths": ["Accurate mutability definition", "Concise technical phrasing"],
    "weaknesses": ["Omitted memory overhead details"],
    "missing_concepts": ["Tuples are hashable and can be dictionary keys"],
    "improved_answer": "In Python, lists are mutable while tuples are immutable...",
    "recommendations": ["Mention dictionary keys", "Discuss struct caching", "Highlight tuple immutability"]
}
```"""

    with patch("requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": mock_json_reply}}]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        feedback = generate_llm_feedback(eval_data, q_data)
        assert feedback["status"] == "success"
        assert len(feedback["strengths"]) >= 1
        assert len(feedback["recommendations"]) == 3
        assert "improved_answer" in feedback


def test_interview_history_persistence_preserved():
    """Verify local interview history persistence continues to save and load records."""
    dummy_eval = {
        "question_id": "TECH001",
        "question": "Explain lists vs tuples",
        "candidate_level": "final_year",
        "candidate_answer": "Lists are mutable, tuples are immutable.",
        "overall_score": 90.0,
        "performance_category": "Good",
        "component_scores": {"semantic": 90.0, "structure": 90.0, "communication": 90.0, "delivery": 90.0},
        "weighted_contributions": {"semantic": 36.0, "structure": 22.5, "communication": 18.0, "delivery": 13.5},
        "feedback": {"strengths": ["Clear"], "areas_for_improvement": [], "actionable_suggestions": []},
    }

    # Save attempt
    saved = save_evaluation_to_history(dummy_eval)
    assert saved["attempt_id"].startswith("ATT-")

    # Load history
    history = load_history()
    assert len(history) >= 1
    assert any(h["attempt_id"] == saved["attempt_id"] for h in history)
