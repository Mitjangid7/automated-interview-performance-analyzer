"""
ner_skills_emotion.py — Information Extraction, Named Entity Recognition & Emotion Analysis (CO2)

Provides:
1. spaCy Named Entity Recognition (NER) using en_core_web_md (fallback: en_core_web_sm)
2. Domain Skill Extraction via spaCy PhraseMatcher over data/skills.json
3. Multi-class Emotion Classification via j-hartmann/emotion-english-distilroberta-base
4. spaCy 300-d Word Embedding extraction and vector similarity
"""

import json
import os
from typing import Any, Dict, List, Optional, Tuple

_SPACY_NLP = None
_PHRASE_MATCHER = None
_SKILLS_DATA = None
_EMOTION_PIPELINE = None


def get_spacy_model():
    """Lazily load spaCy model with en_core_web_md preferred, en_core_web_sm fallback."""
    global _SPACY_NLP
    if _SPACY_NLP is not None:
        return _SPACY_NLP

    import spacy
    try:
        _SPACY_NLP = spacy.load("en_core_web_md")
    except Exception:
        try:
            _SPACY_NLP = spacy.load("en_core_web_sm")
        except Exception:
            _SPACY_NLP = spacy.blank("en")
    return _SPACY_NLP


def get_skills_matcher():
    """Lazily load skills dictionary and spaCy PhraseMatcher."""
    global _PHRASE_MATCHER, _SKILLS_DATA
    if _PHRASE_MATCHER is not None and _SKILLS_DATA is not None:
        return _PHRASE_MATCHER, _SKILLS_DATA

    nlp = get_spacy_model()
    from spacy.matcher import PhraseMatcher

    skills_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "skills.json"
    )

    tech_skills = []
    beh_skills = []
    if os.path.exists(skills_path):
        try:
            with open(skills_path, "r", encoding="utf-8") as f:
                _SKILLS_DATA = json.load(f)
                tech_skills = _SKILLS_DATA.get("technical_skills", [])
                beh_skills = _SKILLS_DATA.get("behavioral_skills", [])
        except Exception:
            _SKILLS_DATA = {"technical_skills": [], "behavioral_skills": []}
    else:
        _SKILLS_DATA = {"technical_skills": [], "behavioral_skills": []}

    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    if tech_skills:
        tech_patterns = [nlp.make_doc(s) for s in tech_skills]
        matcher.add("TECHNICAL_SKILL", tech_patterns)
    if beh_skills:
        beh_patterns = [nlp.make_doc(s) for s in beh_skills]
        matcher.add("BEHAVIORAL_SKILL", beh_patterns)

    _PHRASE_MATCHER = matcher
    return _PHRASE_MATCHER, _SKILLS_DATA


def extract_entities_and_skills(text: str) -> Dict[str, Any]:
    """
    Extract Named Entities and Skills from candidate response.
    Returns:
        entities: list of {"text": str, "label": str}
        technical_skills: list of unique matched tech skills
        behavioral_skills: list of unique matched behavioral skills
        total_skills_detected: int
    """
    if not text or not text.strip():
        return {
            "entities": [],
            "technical_skills": [],
            "behavioral_skills": [],
            "total_skills_detected": 0,
        }

    nlp = get_spacy_model()
    matcher, _ = get_skills_matcher()
    doc = nlp(text)

    # Named Entities
    entities = []
    seen_ent = set()
    for ent in doc.ents:
        if (ent.text.lower(), ent.label_) not in seen_ent:
            seen_ent.add((ent.text.lower(), ent.label_))
            entities.append({
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
            })

    # PhraseMatcher Skills
    matches = matcher(doc)
    tech_skills = set()
    beh_skills = set()

    for match_id, start, end in matches:
        match_label = nlp.vocab.strings[match_id]
        span_text = doc[start:end].text
        if match_label == "TECHNICAL_SKILL":
            tech_skills.add(span_text)
        elif match_label == "BEHAVIORAL_SKILL":
            beh_skills.add(span_text)

    # Also detect common skills with case-insensitive boundary match for resilience
    text_lower = text.lower()
    for s in _SKILLS_DATA.get("technical_skills", []):
        if f" {s.lower()} " in f" {text_lower} ":
            tech_skills.add(s)
    for s in _SKILLS_DATA.get("behavioral_skills", []):
        if f" {s.lower()} " in f" {text_lower} ":
            beh_skills.add(s)

    sorted_tech = sorted(tech_skills)
    sorted_beh = sorted(beh_skills)

    return {
        "entities": entities,
        "technical_skills": sorted_tech,
        "behavioral_skills": sorted_beh,
        "total_skills_detected": len(sorted_tech) + len(sorted_beh),
        "spacy_model": nlp.meta.get("name", "en_core_web_md"),
    }


def analyze_emotions(text: str) -> Dict[str, Any]:
    """
    Classify interview answer emotions using j-hartmann/emotion-english-distilroberta-base.
    Labels: joy, optimism/neutral, sadness, fear, anger, surprise, disgust.

    Gracefully falls back to heuristic emotion mapping if transformer is loading or unavailable.
    """
    global _EMOTION_PIPELINE
    if not text or not text.strip():
        return {
            "dominant_emotion": "neutral",
            "confidence": 1.0,
            "emotion_scores": {"neutral": 1.0},
            "model_engine": "none",
        }

    try:
        if _EMOTION_PIPELINE is None:
            from transformers import pipeline
            _EMOTION_PIPELINE = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                top_k=None,
            )

        # Truncate text for classifier to 512 tokens
        cleaned = text.strip()[:1000]
        preds = _EMOTION_PIPELINE(cleaned)
        # preds is list of lists: [[{'label': 'joy', 'score': 0.95}, ...]]
        scores_list = preds[0] if isinstance(preds, list) and isinstance(preds[0], list) else preds

        emotion_dict = {}
        for item in scores_list:
            emotion_dict[item["label"]] = round(float(item["score"]), 4)

        dominant = max(emotion_dict.items(), key=lambda x: x[1])

        return {
            "dominant_emotion": dominant[0],
            "confidence": dominant[1],
            "emotion_scores": emotion_dict,
            "model_engine": "j-hartmann/emotion-english-distilroberta-base",
        }
    except Exception as exc:
        # Fallback heuristic emotion classification
        from modules.preprocessing import analyze_sentiment
        sent = analyze_sentiment(text)
        cmp = sent.get("compound", 0.0)
        if cmp >= 0.4:
            dom = "joy"
        elif cmp <= -0.2:
            dom = "fear" if "nervous" in text.lower() or "anxious" in text.lower() else "sadness"
        else:
            dom = "neutral"

        return {
            "dominant_emotion": dom,
            "confidence": round(abs(cmp), 4) if abs(cmp) > 0.5 else 0.75,
            "emotion_scores": {dom: 0.8, "neutral": 0.2},
            "model_engine": "heuristic_sentiment_fallback",
            "fallback_reason": str(exc),
        }


def compute_spacy_similarity(text1: str, text2: str) -> float:
    """
    Compute dense vector similarity using spaCy 300-d word embeddings (en_core_web_md).
    Returns cosine similarity 0.0 - 1.0.
    """
    if not text1.strip() or not text2.strip():
        return 0.0
    nlp = get_spacy_model()
    doc1 = nlp(text1)
    doc2 = nlp(text2)
    if doc1.vector_norm and doc2.vector_norm:
        sim = float(doc1.similarity(doc2))
        return max(0.0, min(1.0, sim))
    return 0.0
