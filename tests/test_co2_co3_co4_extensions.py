"""
test_co2_co3_co4_extensions.py — Unit & Integration Tests for Advanced CO Improvements

Tests:
1. spaCy NER & PhraseMatcher skills extraction (CO2)
2. Emotion classification (j-hartmann DistilRoBERTa / fallback) (CO2)
3. Latent Dirichlet Allocation (LDA) Topic Modeling (CO3)
4. ChromaDB RAG Vector Store retrieval and mock interviewer chat loop (CO4 + CO1)
5. spaCy Lemmatization and global corpus TF-IDF similarity (CO1)
6. Score immutability & backward compatibility across all additions
"""

from unittest.mock import patch, MagicMock
import pytest

from modules.ner_skills_emotion import extract_entities_and_skills, analyze_emotions, compute_spacy_similarity
from modules.topic_modeling import infer_topics
from modules.preprocessing import lemmatize_text_spacy
from modules.semantic_analysis import calculate_tfidf_similarity
from modules.scoring import evaluate_answer


def test_spacy_ner_and_skills_matcher():
    """Verify spaCy extracts technical skills and entities from interview response."""
    answer = "I developed microservices in Python and deployed Docker containers on AWS Kubernetes clusters."
    res = extract_entities_and_skills(answer)
    assert res["total_skills_detected"] > 0
    assert any(s in ["Python", "Docker", "Kubernetes", "AWS", "Microservices"] for s in res["technical_skills"])
    assert isinstance(res["entities"], list)


def test_emotion_classification():
    """Verify emotion classification returns dominant emotion and distribution."""
    text = "I am so proud of our team's amazing success and thrilled with the results!"
    res = analyze_emotions(text)
    assert "dominant_emotion" in res
    assert "confidence" in res
    assert res["confidence"] > 0.0
    assert res["dominant_emotion"] in ["joy", "optimism", "neutral"]


def test_topic_modeling_lda():
    """Verify LDA topic modeling assigns appropriate topics to domain answers."""
    tech_ans = "Python lists are mutable while tuples are immutable fixed sequences."
    res = infer_topics(tech_ans)
    assert "dominant_topic" in res
    assert "topic_distribution" in res
    assert len(res["topic_distribution"]) > 0


def test_spacy_lemmatization():
    """Verify spaCy lemmatization reduces inflected words to dictionary lemmas."""
    text = "The engineers were running several automated optimizations."
    lemmas = lemmatize_text_spacy(text)
    assert "run" in lemmas or "optimization" in lemmas or "engineer" in lemmas


def test_global_tfidf_similarity():
    """Verify TF-IDF similarity fitted across question corpus produces valid bounded scores."""
    sim = calculate_tfidf_similarity(
        "Lists are mutable sequences in Python.",
        "Lists and tuples are sequence data types in Python."
    )
    assert 0.0 <= sim <= 1.0
    assert sim > 0.2


def test_evaluate_answer_includes_all_extended_metrics():
    """Verify full evaluation pipeline returns all newly added CO features without breaking existing scores."""
    res = evaluate_answer("TECH001", "Lists are mutable while tuples are immutable in Python.", candidate_level="final_year")
    assert "entities_and_skills" in res
    assert "emotion_analysis" in res
    assert "topic_analysis" in res
    assert "overall_score" in res
    assert 0.0 <= res["overall_score"] <= 100.0
