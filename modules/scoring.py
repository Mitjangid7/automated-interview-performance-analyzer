"""
scoring.py — Core Interview Evaluation & Weighted Scoring Engine

Orchestrates multi-dimensional candidate answer evaluation:
1. Input validation & question resolution
2. Text preprocessing & sentiment analysis
3. Communication & linguistic delivery indicators
4. Semantic relevance, key-point coverage & question relevance
5. Technical correctness and misconception detection
6. Structural organization (STAR framework or General Organization)
7. Configurable weighted scoring (0 - 100)
8. Intelligent feedback synthesis

Adheres to explainable AI principles: no arbitrary score inflation,
transparent component weighting, and fully JSON-serializable outputs.
"""

import json
import os
from typing import Any, Dict, List, Optional

from config.candidate_levels import (
    DEFAULT_CANDIDATE_LEVEL,
    get_candidate_level_info,
    validate_candidate_level,
)
from config.config import QUESTIONS_PATH, SCORING_WEIGHTS
from modules.communication_analysis import (
    analyze_communication,
    analyze_delivery_indicators,
)
from modules.feedback import generate_feedback
from modules.preprocessing import clean_text, preprocess_answer
from modules.semantic_analysis import (
    analyze_semantics,
    analyze_technical_correctness,
)
from modules.structure_analysis import analyze_structure
from utils.helpers import clamp, safe_divide

# Cache for interview questions
_QUESTIONS_CACHE: Optional[Dict[str, Dict[str, Any]]] = None


def load_questions_map() -> Dict[str, Dict[str, Any]]:
    """
    Load questions.json into a lookup dictionary indexed by question_id.
    Caches the dataset in memory.

    Returns:
        Dictionary mapping question_id -> question_data dict.
    """
    global _QUESTIONS_CACHE
    if _QUESTIONS_CACHE is not None:
        return _QUESTIONS_CACHE

    if not os.path.exists(QUESTIONS_PATH):
        return {}

    with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
        questions_list = json.load(f)

    _QUESTIONS_CACHE = {q["question_id"]: q for q in questions_list}
    return _QUESTIONS_CACHE


def _calculate_communication_score(
    comm_analysis: Dict[str, Any],
    prep_stats: Dict[str, Any],
    semantic_score: float = 0.0,
) -> float:
    """
    Compute a normalized communication quality score (0 - 100) from observable features:
    - Vocabulary diversity (TTR)
    - Sentence length balance
    - Readability / sentence organization

    Avoids penalizing technical vocabulary or concise answers that are conceptually accurate.
    """
    word_count = prep_stats.get("word_count", 0)
    if word_count == 0:
        return 0.0

    # Base communication score
    base = 70.0

    # Diversity bonus/adjustment
    ttr = comm_analysis.get("vocabulary_diversity", 0.0)
    if ttr >= 0.60:
        base += 15.0
    elif ttr >= 0.45:
        base += 10.0
    elif ttr < 0.35 and word_count > 30:
        base -= 10.0

    # Sentence length balance (optimal average: 10-26 words)
    avg_len = comm_analysis.get("average_sentence_length", 0.0)
    if 10.0 <= avg_len <= 26.0:
        base += 15.0
    elif avg_len > 35.0:
        base -= 10.0
    elif avg_len < 6.0 and word_count > 15:
        base -= 5.0

    # Excessive long sentences penalty
    long_count = comm_analysis.get("long_sentence_count", 0)
    base -= min(long_count * 5.0, 15.0)

    # Word count calibration: fair handling of concise, technically accurate answers
    if word_count < 12:
        base = min(base, 45.0 if semantic_score >= 75.0 else 35.0)
    elif word_count < 25:
        base = min(base, 78.0 if semantic_score >= 75.0 else 60.0)

    return round(clamp(base, 0.0, 100.0), 2)


def _calculate_delivery_score(
    delivery_analysis: Dict[str, Any],
    comm_analysis: Dict[str, Any],
    semantic_score: float = 0.0,
) -> float:
    """
    Compute linguistic delivery score (0 - 100) based on observable delivery indicators:
    - Filler word frequency per 100 words
    - Excessive hedging
    - Phrasal repetition
    - Very short response indicators

    Does not infer internal emotions, personality, or confidence.
    """
    counts = delivery_analysis.get("counts", {})
    word_count = counts.get("word_count", 0)
    if word_count == 0:
        return 0.0

    base = 100.0

    # Filler frequency penalty: up to 35 points deduction
    filler_freq = comm_analysis.get("filler_frequency", 0.0)
    if filler_freq > 8.0:
        base -= 35.0
    elif filler_freq > 5.0:
        base -= 25.0
    elif filler_freq > 2.0:
        base -= 12.0
    elif filler_freq > 0.0:
        base -= 5.0

    # Excessive hedging penalty (only if 3 or more occurrences): up to 15 points
    hedging_count = comm_analysis.get("hedging_count", 0)
    if hedging_count >= 5:
        base -= 15.0
    elif hedging_count >= 3:
        base -= 8.0

    # Repeated phrases penalty: up to 10 points
    rep_count = counts.get("repeated_phrases_count", 0)
    base -= min(rep_count * 5.0, 10.0)

    # Very short response penalty: fair handling for concise responses
    if word_count < 12:
        base = min(base, 45.0 if semantic_score >= 75.0 else 30.0)
    elif word_count < 25:
        base = min(base, 80.0 if semantic_score >= 75.0 else 55.0)

    return round(clamp(base, 0.0, 100.0), 2)


def get_performance_category(overall_score: float) -> str:
    """Map numeric overall score (0 - 100) to standard performance tier."""
    if overall_score >= 85.0:
        return "Excellent"
    elif overall_score >= 70.0:
        return "Good"
    elif overall_score >= 50.0:
        return "Average"
    else:
        return "Needs Improvement"


def evaluate_answer(
    question_id: str,
    candidate_answer: Any,
    candidate_level: str = DEFAULT_CANDIDATE_LEVEL,
) -> Dict[str, Any]:
    """
    Main evaluation pipeline. Analyzes candidate answer across semantic,
    communication, delivery, correctness, and structure dimensions,
    computing explainable weighted scores and actionable feedback adapted
    to candidate level (primary focus: final-year engineering students).

    Args:
        question_id: ID of the question in data/questions.json (e.g. 'TECH001').
        candidate_answer: Candidate's response text.
        candidate_level: Candidate experience level ('final_year', 'ty_student', 'experienced').

    Returns:
        Standardized, JSON-serializable evaluation dictionary.
    """
    valid_level = validate_candidate_level(candidate_level)

    # 1. Validate inputs
    clean_qid = str(question_id).strip() if question_id is not None else ""
    cleaned_ans = clean_text(candidate_answer)

    questions_map = load_questions_map()
    if clean_qid not in questions_map:
        return {
            "question_id": clean_qid,
            "question": "",
            "candidate_answer": cleaned_ans,
            "candidate_level": valid_level,
            "overall_score": 0.0,
            "performance_category": "Needs Improvement",
            "component_scores": {
                "semantic": 0.0,
                "communication": 0.0,
                "delivery": 0.0,
                "structure": 0.0,
            },
            "weighted_contributions": {
                "semantic": 0.0,
                "communication": 0.0,
                "delivery": 0.0,
                "structure": 0.0,
            },
            "semantic_analysis": {},
            "technical_correctness": {},
            "communication_analysis": {},
            "delivery_analysis": {},
            "structure_analysis": {},
            "feedback": {
                "strengths": [],
                "areas_for_improvement": ["Invalid question ID provided."],
                "actionable_suggestions": ["Select a valid question ID from questions.json."],
                "suggested_improved_answer": "",
                "summary": {
                    "overall_score": 0.0,
                    "performance_category": "Needs Improvement",
                    "strongest_component": "None",
                    "weakest_component": "None",
                    "main_improvement_priority": "Provide valid question identifier.",
                }
            },
            "analysis_status": "error_invalid_question_id",
        }

    question_data = questions_map[clean_qid]
    question_text = question_data.get("question", "")

    # Handle empty answer safely
    if not cleaned_ans:
        empty_res = {
            "question_id": clean_qid,
            "question": question_text,
            "candidate_answer": "",
            "candidate_level": valid_level,
            "overall_score": 0.0,
            "performance_category": "Needs Improvement",
            "component_scores": {
                "semantic": 0.0,
                "communication": 0.0,
                "delivery": 0.0,
                "structure": 0.0,
            },
            "weighted_contributions": {
                "semantic": 0.0,
                "communication": 0.0,
                "delivery": 0.0,
                "structure": 0.0,
            },
            "semantic_analysis": {},
            "technical_correctness": {},
            "communication_analysis": {},
            "delivery_analysis": {},
            "structure_analysis": {},
            "feedback": {},
            "analysis_status": "empty_answer",
        }
        empty_res["feedback"] = generate_feedback(empty_res, question_data, candidate_level=valid_level)
        return empty_res

    # 2. Run Preprocessing
    prep_res = preprocess_answer(cleaned_ans)

    # CO3: Multilingual detection and routing (must run before semantic analysis)
    try:
        from modules.multilingual import detect_and_process_multilingual
        multilingual_res = detect_and_process_multilingual(cleaned_ans)
    except Exception as _ml_exc:
        multilingual_res = {
            "original_text": cleaned_ans,
            "detected_language": "English",
            "language_code": "en",
            "detection_confidence": 0.0,
            "evaluation_text": cleaned_ans,
            "translation_used": False,
            "translated_text": None,
            "processing_status": "detection_failed",
            "cloud_service_used": "None",
            "evaluation_note": f"Multilingual processing unavailable: {_ml_exc}",
            "detection_note": "",
        }

    # Use translated text for semantic and structural evaluation if non-English; otherwise unchanged
    _eval_text = multilingual_res.get("evaluation_text", cleaned_ans)

    # 3. Run Communication & Delivery Analyses
    comm_res = analyze_communication(cleaned_ans)
    delivery_res = analyze_delivery_indicators(cleaned_ans)

    # 4. Run Semantic & Correctness Analyses
    semantic_res = analyze_semantics(question_data, _eval_text, candidate_level=valid_level)
    correctness_res = analyze_technical_correctness(_eval_text, question_data)

    # 5. Run Structure Analysis
    structure_res = analyze_structure(_eval_text, question_data, candidate_level=valid_level)

    # 6. Calculate Component Scores (0 - 100)
    # A. Semantic score: base composite from semantic analysis, penalized if known misconceptions exist
    raw_semantic = semantic_res.get("composite_semantic_score", 0.0)
    misconceptions_count = len(correctness_res.get("detected_misconceptions", []))
    semantic_score = clamp(raw_semantic - (misconceptions_count * 15.0), 0.0, 100.0)

    # B. Communication score
    comm_score = _calculate_communication_score(
        comm_res, prep_res.get("statistics", {}), semantic_score=semantic_score
    )

    # C. Delivery score
    delivery_score = _calculate_delivery_score(
        delivery_res, comm_res, semantic_score=semantic_score
    )

    # D. Structure score
    structure_score = clamp(structure_res.get("structure_score", 0.0), 0.0, 100.0)

    component_scores = {
        "semantic": round(semantic_score, 2),
        "communication": round(comm_score, 2),
        "delivery": round(delivery_score, 2),
        "structure": round(structure_score, 2),
    }

    # 7. Apply Configurable Weights from config/config.py
    w_sem = SCORING_WEIGHTS.get("semantic_relevance", 0.40)
    w_comm = SCORING_WEIGHTS.get("communication", 0.20)
    w_del = SCORING_WEIGHTS.get("delivery_indicators", 0.15)
    w_str = SCORING_WEIGHTS.get("answer_structure", 0.25)

    weighted_contributions = {
        "semantic": round(component_scores["semantic"] * w_sem, 2),
        "communication": round(component_scores["communication"] * w_comm, 2),
        "delivery": round(component_scores["delivery"] * w_del, 2),
        "structure": round(component_scores["structure"] * w_str, 2),
    }

    overall_score = round(
        clamp(sum(weighted_contributions.values()), 0.0, 100.0), 2
    )

    performance_category = get_performance_category(overall_score)

    # Include sentiment analysis and information extraction in evaluation output (CO2)
    if multilingual_res.get("translation_used"):
        try:
            from modules.preprocessing import analyze_sentiment
            sentiment_res = analyze_sentiment(_eval_text)
        except Exception:
            sentiment_res = prep_res.get("sentiment", {})
    else:
        sentiment_res = prep_res.get("sentiment", {})

    from modules.semantic_analysis import extract_information
    info_extraction_res = extract_information(_eval_text, question_data)

    # CO2 & CO3: spaCy NER, Skill Extraction, Emotion Analysis & Topic Modeling
    try:
        from modules.ner_skills_emotion import extract_entities_and_skills, analyze_emotions
        ner_res = extract_entities_and_skills(_eval_text)
        emotion_res = analyze_emotions(_eval_text)
    except Exception:
        ner_res = {"entities": [], "technical_skills": [], "behavioral_skills": [], "total_skills_detected": 0}
        emotion_res = {"dominant_emotion": "neutral", "confidence": 1.0, "emotion_scores": {"neutral": 1.0}}

    try:
        from modules.topic_modeling import infer_topics
        topic_res = infer_topics(_eval_text)
    except Exception:
        topic_res = {"dominant_topic": "General", "confidence": 1.0, "topic_distribution": {}}

    evaluation_result: Dict[str, Any] = {
        "question_id": clean_qid,
        "question": question_text,
        "candidate_answer": cleaned_ans,
        "candidate_level": valid_level,
        "overall_score": overall_score,
        "performance_category": performance_category,
        "component_scores": component_scores,
        "weighted_contributions": weighted_contributions,
        "semantic_analysis": semantic_res,
        "technical_correctness": correctness_res,
        "communication_analysis": comm_res,
        "delivery_analysis": delivery_res,
        "structure_analysis": structure_res,
        "sentiment_analysis": sentiment_res,
        "information_extraction": info_extraction_res,
        "multilingual_analysis": multilingual_res,
        "entities_and_skills": ner_res,
        "emotion_analysis": emotion_res,
        "topic_analysis": topic_res,
        "feedback": {},
        "analysis_status": "success",
    }

    # 8. Generate Intelligent Feedback
    evaluation_result["feedback"] = generate_feedback(
        evaluation_result, question_data, candidate_level=valid_level
    )

    return evaluation_result
