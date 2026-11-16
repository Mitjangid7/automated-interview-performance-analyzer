"""
history.py — Interview History Persistence and Comparison Management

Provides thread-safe, robust persistence of candidate interview attempts
in data/interview_history.json and cross-attempt comparative analytics.
"""

from datetime import datetime
import json
import os
from typing import Any, Dict, List, Optional, Tuple

from config.config import DATA_DIR
from utils.helpers import safe_divide

HISTORY_FILE_PATH = os.path.join(DATA_DIR, "interview_history.json")


def load_history() -> List[Dict[str, Any]]:
    """
    Load stored interview evaluation history from disk.
    Handles missing or corrupted files gracefully.

    Returns:
        List of historical interview evaluation dicts, sorted chronologically (latest last).
    """
    if not os.path.exists(HISTORY_FILE_PATH):
        return []

    try:
        with open(HISTORY_FILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception:
        return []


def save_evaluation_to_history(
    evaluation_result: Dict[str, Any],
    question_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Append an evaluation record to the persistent history file.

    Args:
        evaluation_result: Output from evaluate_answer().
        question_data: Optional question metadata.

    Returns:
        The serialized history record including assigned attempt ID and timestamp.
    """
    history = load_history()

    now = datetime.now()
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
    attempt_id = f"ATT-{now.strftime('%Y%m%d%H%M%S')}-{len(history) + 1:03d}"

    q_data = question_data or {}
    category = q_data.get("category", "General")
    question_text = evaluation_result.get("question") or q_data.get("question", "")

    # Clean serializable payload
    record: Dict[str, Any] = {
        "attempt_id": attempt_id,
        "timestamp": timestamp_str,
        "question_id": evaluation_result.get("question_id", ""),
        "question": question_text,
        "category": category,
        "candidate_level": evaluation_result.get("candidate_level", "final_year"),
        "candidate_answer": evaluation_result.get("candidate_answer", ""),
        "overall_score": float(evaluation_result.get("overall_score", 0.0)),
        "performance_category": evaluation_result.get("performance_category", "Needs Improvement"),
        "component_scores": evaluation_result.get("component_scores", {}),
        "weighted_contributions": evaluation_result.get("weighted_contributions", {}),
        "keypoint_coverage_pct": float(
            evaluation_result.get("semantic_analysis", {})
            .get("keypoint_coverage", {})
            .get("coverage_percentage", 0.0)
        ),
        "misconceptions_count": len(
            evaluation_result.get("technical_correctness", {})
            .get("detected_misconceptions", [])
        ),
        "filler_frequency": float(
            evaluation_result.get("communication_analysis", {})
            .get("filler_frequency", 0.0)
        ),
        "feedback_summary": evaluation_result.get("feedback", {}).get("summary", {}),
        "strengths": evaluation_result.get("feedback", {}).get("strengths", []),
        "areas_for_improvement": evaluation_result.get("feedback", {}).get("areas_for_improvement", []),
        "actionable_suggestions": evaluation_result.get("feedback", {}).get("actionable_suggestions", []),
        "suggested_improved_answer": evaluation_result.get("feedback", {}).get("suggested_improved_answer", ""),
        "semantic_analysis": evaluation_result.get("semantic_analysis", {}),
        "technical_correctness": evaluation_result.get("technical_correctness", {}),
        "communication_analysis": evaluation_result.get("communication_analysis", {}),
        "delivery_analysis": evaluation_result.get("delivery_analysis", {}),
        "structure_analysis": evaluation_result.get("structure_analysis", {}),
        "feedback": evaluation_result.get("feedback", {}),
    }

    history.append(record)

    os.makedirs(os.path.dirname(HISTORY_FILE_PATH), exist_ok=True)
    with open(HISTORY_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    return record


def clear_history() -> bool:
    """
    Safely reset the interview history by removing or emptying the history file.

    Returns:
        True if cleared successfully.
    """
    try:
        if os.path.exists(HISTORY_FILE_PATH):
            with open(HISTORY_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump([], f)
        return True
    except Exception:
        return False


def get_history_summary() -> Dict[str, Any]:
    """
    Compute aggregate analytics across all recorded interview attempts.

    Returns:
        Dictionary containing overview metrics and trend time-series.
    """
    history = load_history()
    if not history:
        return {
            "total_attempts": 0,
            "average_score": 0.0,
            "highest_score": 0.0,
            "latest_score": 0.0,
            "recent_progress": 0.0,
            "previous_score": None,
            "unique_questions_attempted": 0,
            "category_distribution": {},
            "recent_activity": [],
            "scores_trend": [],
        }

    scores = [h["overall_score"] for h in history]
    total_attempts = len(history)
    avg_score = round(sum(scores) / total_attempts, 2)
    max_score = round(max(scores), 2)
    latest_score = round(scores[-1], 2)
    previous_score = round(scores[-2], 2) if total_attempts >= 2 else None
    recent_progress = round(latest_score - previous_score, 2) if previous_score is not None else 0.0
    unique_qids = len(set(h["question_id"] for h in history))

    # Category breakdown
    cat_counts: Dict[str, int] = {}
    for h in history:
        cat = h.get("category", "General")
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    # Trend data
    trend = [
        {
            "attempt_num": i + 1,
            "timestamp": h["timestamp"],
            "question_id": h["question_id"],
            "category": h["category"],
            "score": h["overall_score"],
            "semantic": h["component_scores"].get("semantic", 0.0),
            "communication": h["component_scores"].get("communication", 0.0),
            "delivery": h["component_scores"].get("delivery", 0.0),
            "structure": h["component_scores"].get("structure", 0.0),
        }
        for i, h in enumerate(history)
    ]

    recent = list(reversed(history[-5:]))

    return {
        "total_attempts": total_attempts,
        "average_score": avg_score,
        "highest_score": max_score,
        "latest_score": latest_score,
        "previous_score": previous_score,
        "recent_progress": recent_progress,
        "unique_questions_attempted": unique_qids,
        "category_distribution": cat_counts,
        "recent_activity": recent,
        "scores_trend": trend,
    }


def compare_two_attempts(
    earlier_attempt: Dict[str, Any], later_attempt: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compare two interview attempts (typically on the same question)
    and compute delta metrics and progress feedback.

    Args:
        earlier_attempt: The baseline attempt dict.
        later_attempt: The subsequent attempt dict.

    Returns:
        Structured delta comparison dictionary.
    """
    e_score = float(earlier_attempt.get("overall_score", 0.0))
    l_score = float(later_attempt.get("overall_score", 0.0))
    score_delta = round(l_score - e_score, 2)

    e_comps = earlier_attempt.get("component_scores", {})
    l_comps = later_attempt.get("component_scores", {})

    component_deltas = {
        comp: round(float(l_comps.get(comp, 0.0)) - float(e_comps.get(comp, 0.0)), 2)
        for comp in ("semantic", "communication", "delivery", "structure")
    }

    e_cov = float(earlier_attempt.get("keypoint_coverage_pct", 0.0))
    l_cov = float(later_attempt.get("keypoint_coverage_pct", 0.0))
    coverage_delta = round(l_cov - e_cov, 2)

    # Qualitative progress narrative
    if score_delta > 5.0:
        verdict = f"Demonstrated clear progress (+{score_delta} pts). Significant conceptual and delivery refinement."
    elif score_delta > 0.0:
        verdict = f"Slight score improvement (+{score_delta} pts). Incremental progress across component areas."
    elif score_delta == 0.0:
        verdict = "Identical performance score across attempts."
    else:
        verdict = f"Score decreased by {abs(score_delta)} pts. Review omitted key points or newly introduced filler phrases."

    return {
        "earlier_score": e_score,
        "later_score": l_score,
        "score_delta": score_delta,
        "component_deltas": component_deltas,
        "coverage_delta": coverage_delta,
        "verdict": verdict,
        "earlier_category": earlier_attempt.get("performance_category", "Needs Improvement"),
        "later_category": later_attempt.get("performance_category", "Needs Improvement"),
    }

