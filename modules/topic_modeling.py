"""
topic_modeling.py — Unsupervised Topic Modeling for Interview Responses (CO3)

Provides:
- Unsupervised Topic Extraction using Latent Dirichlet Allocation (LDA) / NMF
- Discovers latent themes across interview answers (e.g., Python Architecture, Cloud & Microservices, Teamwork/STAR, ML Concepts)
- Assigns topic probabilities and dominant topic to candidate responses
"""

import os
from typing import Any, Dict, List, Optional
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation

_TOPIC_MODEL = None
_VECTORIZER = None
_TOPIC_NAMES = None

# Custom stop words to remove generic conversational verbs and interview meta-tokens
INTERVIEW_STOP_WORDS = list(CountVectorizer(stop_words="english").get_stop_words()) + [
    "think", "know", "like", "just", "really", "also", "good", "well", "want", "said",
    "example", "time", "make", "use", "used", "using", "need", "help", "able", "day",
    "tell", "interview", "answer", "question", "candidate", "sure", "lot", "come", "came",
    "went", "got", "did", "does", "doing", "try", "trying"
]


def _categorize_topic(top_words: List[str]) -> str:
    """Categorize a learned latent topic by analyzing its highest-weight domain keywords."""
    joined = " ".join(top_words).lower()
    words_set = set(joined.split())

    sql_kws = {"join", "left", "inner", "table", "tables", "sql", "database", "databases", "query", "queries", "null", "rows", "columns"}
    py_kws = {"python", "list", "lists", "tuple", "tuples", "mutable", "immutable", "decorator", "decorators", "function", "syntax", "keys"}
    ml_kws = {"learning", "overfitting", "validation", "regularization", "precision", "recall", "f1", "scaling", "standardization", "normalization", "features", "dataset", "classifier", "neural", "aiml", "models", "model", "training", "data"}
    beh_kws = {"team", "conflict", "situation", "action", "result", "leadership", "deadline", "disagreement", "criticism", "collaboration", "guidance"}
    hr_kws = {"student", "background", "career", "goals", "strengths", "weakness", "role", "company", "hire", "education", "position"}

    scores = {
        "Database Systems & SQL": len(words_set & sql_kws) * 2,
        "Python & Core Programming": len(words_set & py_kws) * 2,
        "Machine Learning & Applied AI": len(words_set & ml_kws) * 2,
        "Behavioral & Teamwork (STAR)": len(words_set & beh_kws),
        "Professional Background & Career Goals (HR)": len(words_set & hr_kws),
    }
    best = max(scores, key=scores.get)
    if scores[best] > 0:
        return best
    return "Engineering Systems & Architecture"


def fit_interview_topic_model(num_topics: int = 5):
    """
    Fit an unsupervised LDA topic model across granular interview questions,
    reference answers, evaluation rubrics, and candidate responses.
    """
    global _TOPIC_MODEL, _VECTORIZER, _TOPIC_NAMES

    corpus: List[str] = []
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    questions_path = os.path.join(base_dir, "data", "questions.json")
    answers_path = os.path.join(base_dir, "data", "synthetic_answers.csv")

    if os.path.exists(questions_path):
        import json
        try:
            with open(questions_path, "r", encoding="utf-8") as f:
                qdata = json.load(f)
                for q in qdata:
                    q_text = q.get("question", "")
                    ref_text = q.get("reference_answer", "")
                    corpus.append(f"{q_text} {ref_text}")
                    for kp in q.get("essential_key_points", []) or q.get("key_points", []):
                        corpus.append(f"{q_text} {kp}")
                    keywords = q.get("expected_keywords", [])
                    if keywords:
                        corpus.append(" ".join(keywords))
        except Exception:
            pass

    if os.path.exists(answers_path):
        import pandas as pd
        try:
            df = pd.read_csv(answers_path)
            corpus.extend(df["candidate_answer"].dropna().tolist())
        except Exception:
            pass

    if not corpus:
        corpus = [
            "Python lists are mutable sequences while tuples are immutable fixed records with hashable dictionary keys.",
            "Situation Task Action Result in cross-functional software engineering team conflict resolution.",
            "INNER JOIN matches records while LEFT JOIN retains all left table rows filling NULL for missing records.",
            "Machine learning overfitting regularization cross-validation precision recall bias variance tradeoff.",
            "Computer science student with software engineering internship background career goals alignment."
        ]

    vectorizer = CountVectorizer(
        stop_words=INTERVIEW_STOP_WORDS,
        min_df=2,
        max_df=0.85,
        ngram_range=(1, 2)
    )
    dtm = vectorizer.fit_transform(corpus)

    # Use Dirichlet priors that encourage distinct, sparse topic assignments
    lda = LatentDirichletAllocation(
        n_components=num_topics,
        doc_topic_prior=0.1,
        topic_word_prior=0.05,
        random_state=1,
        max_iter=50,
        learning_method="batch"
    )
    lda.fit(dtm)

    feature_names = vectorizer.get_feature_names_out()
    topic_names = []
    for topic_idx, topic in enumerate(lda.components_):
        top_words = [feature_names[i] for i in topic.argsort()[:-6:-1]]
        label = _categorize_topic(top_words)
        topic_names.append(f"{label} ({top_words[0]}, {top_words[1]}, {top_words[2]})")

    _TOPIC_MODEL = lda
    _VECTORIZER = vectorizer
    _TOPIC_NAMES = topic_names
    return _TOPIC_MODEL, _VECTORIZER, _TOPIC_NAMES


def infer_topics(text: str) -> Dict[str, Any]:
    """
    Infer dominant topic and distribution for a candidate answer.
    """
    global _TOPIC_MODEL, _VECTORIZER, _TOPIC_NAMES
    if _TOPIC_MODEL is None or _VECTORIZER is None:
        fit_interview_topic_model()

    if not text or not text.strip():
        return {
            "dominant_topic": "Unassigned",
            "topic_distribution": {},
            "algorithm": "Latent Dirichlet Allocation (LDA)",
        }

    dtm = _VECTORIZER.transform([text])
    distribution = _TOPIC_MODEL.transform(dtm)[0]

    dominant_idx = int(distribution.argmax())
    dominant_topic = _TOPIC_NAMES[dominant_idx]

    dist_dict = {}
    for idx, prob in enumerate(distribution):
        dist_dict[_TOPIC_NAMES[idx]] = round(float(prob), 4)

    return {
        "dominant_topic": dominant_topic,
        "confidence": round(float(distribution[dominant_idx]), 4),
        "topic_distribution": dist_dict,
        "algorithm": "Latent Dirichlet Allocation (LDA)",
    }
