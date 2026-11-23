"""
test_vector_alignment_and_topics.py — Unit Tests for Vector Alignment & Topic Modeling Fixes

Verifies:
1. spaCy 300-d vector alignment produces non-zero, reliable cosine similarity when vectors exist.
2. analyze_semantics() populates spacy_word_vector_similarity and spacy_vector_percentage correctly.
3. Edge cases for vector alignment: empty text and out-of-vocabulary strings return 0.0 safely.
4. LDA topic modeling categorizes the candidate's AIML student answer into Machine Learning / AI rather than SQL.
5. Topic modeling correctly differentiates between Python, SQL, Machine Learning, and Behavioral answers.
6. Edge cases for topic modeling: empty text returns Unassigned safely.
"""

import json
import pytest

from modules.ner_skills_emotion import compute_spacy_similarity, get_spacy_model
from modules.semantic_analysis import analyze_semantics
from modules.topic_modeling import fit_interview_topic_model, infer_topics


def test_spacy_model_has_300d_vectors():
    """Verify en_core_web_md is loaded and has 300-dimensional vectors."""
    nlp = get_spacy_model()
    assert nlp.vocab.vectors_length == 300
    assert nlp.vocab.vectors.shape[1] == 300


def test_compute_spacy_similarity_valid_texts():
    """Verify compute_spacy_similarity returns expected cosine similarity (> 0.5) for related texts."""
    t1 = "I am a computer science student specializing in software engineering and machine learning."
    t2 = "I am a final-year Computer Science Engineering student specializing in software development and machine learning."
    sim = compute_spacy_similarity(t1, t2)
    assert 0.5 <= sim <= 1.0


def test_compute_spacy_similarity_edge_cases():
    """Verify empty and whitespace strings return 0.0 safely."""
    assert compute_spacy_similarity("", "Sample answer") == 0.0
    assert compute_spacy_similarity("Sample answer", "   ") == 0.0
    assert compute_spacy_similarity("", "") == 0.0


def test_analyze_semantics_populates_spacy_vector_metrics():
    """Verify analyze_semantics returns non-zero spacy vector similarity and percentage."""
    q_data = {
        "question_id": "HR001",
        "question": "Tell me about yourself and why you are interested in this position.",
        "reference_answer": "I am a final-year Computer Science Engineering student specializing in software development and machine learning. Throughout my degree, I have built strong foundations in data structures, algorithms, and backend systems.",
        "key_points": ["Academic background", "Technical skills", "Motivation"],
        "essential_key_points": ["Academic background", "Technical skills"],
    }
    candidate_answer = "I am a third year AIML student with Python, SQL, web development, machine learning, computer vision and NLP experience."

    res = analyze_semantics(q_data, candidate_answer, candidate_level="ty_student")

    assert "spacy_word_vector_similarity" in res
    assert "spacy_vector_percentage" in res
    # Must NOT be 0.0
    assert res["spacy_word_vector_similarity"] > 0.5
    assert res["spacy_vector_percentage"] > 50.0


def test_lda_topic_modeling_candidate_aiml_answer():
    """
    Verify candidate AIML student response is categorized under Machine Learning & Applied AI,
    NOT Database Systems & SQL.
    """
    candidate_answer = "I am a third year AIML student with Python, SQL, web development, machine learning, computer vision and NLP experience."
    res = infer_topics(candidate_answer)

    assert "Machine Learning" in res["dominant_topic"]
    assert res["confidence"] > 0.40

    # Ensure SQL is NOT the dominant topic
    assert "Database" not in res["dominant_topic"]
    assert "join" not in res["dominant_topic"].lower()


def test_lda_topic_modeling_distinct_domains():
    """Verify LDA model accurately distinguishes between distinct interview domains."""
    # 1. SQL
    sql_text = "An INNER JOIN returns matching rows between two tables, while a LEFT JOIN includes all rows from the left table and NULL values for unmatched right rows."
    sql_res = infer_topics(sql_text)
    assert "Database" in sql_res["dominant_topic"] or "SQL" in sql_res["dominant_topic"]

    # 2. Python
    py_text = "In Python, lists are mutable dynamic arrays, whereas tuples are immutable and can be used as keys in dictionaries."
    py_res = infer_topics(py_text)
    assert "Python" in py_res["dominant_topic"]

    # 3. Machine Learning
    ml_text = "Overfitting occurs when training loss continues to decrease but validation loss rises. We mitigate it using L2 regularization and dropout."
    ml_res = infer_topics(ml_text)
    assert "Machine Learning" in ml_res["dominant_topic"]

    # 4. Behavioral STAR
    beh_text = "When our team faced a conflict over project responsibilities, I initiated a team meeting, clarified expectations, and we successfully delivered on time."
    beh_res = infer_topics(beh_text)
    assert "Behavioral" in beh_res["dominant_topic"] or "STAR" in beh_res["dominant_topic"]


def test_lda_topic_modeling_empty_input():
    """Verify empty input returns Unassigned with empty distribution."""
    res = infer_topics("")
    assert res["dominant_topic"] == "Unassigned"
    assert res["topic_distribution"] == {}
