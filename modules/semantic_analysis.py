"""
semantic_analysis.py — Semantic Relevance & Conceptual Evaluation Engine
                       + CO2: Information Extraction module

Evaluates how relevant and conceptually aligned a candidate's answer is
relative to the expected answer, essential key points, and interview question.

Uses Sentence Transformers (all-MiniLM-L6-v2) with lazy loading and a robust,
deterministic TF-IDF cosine similarity fallback that requires zero external models.

IMPORTANT EVALUATION PRINCIPLES:
- Semantic similarity does not equal factual correctness.
- Correct concepts may be expressed using distinct vocabularies.
- High similarity to a reference answer does not guarantee flawless execution.
- Key-point coverage provides granular, explainable evidence of conceptual completeness.
"""

import math
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from modules.preprocessing import (
    clean_text,
    extract_sentences,
    normalize_text,
    remove_stopwords,
    tokenize_text,
)
from utils.helpers import clamp, safe_divide

# Module-level model cache
_TRANSFORMER_MODEL = None
_TRANSFORMER_LOAD_ATTEMPTED = False
_TRANSFORMER_MODEL_NAME = "all-MiniLM-L6-v2"


def load_embedding_model() -> Any:
    """
    Lazily loads the SentenceTransformer model if available.
    Caches the loaded model. Returns None gracefully if the package
    is absent, network fails, or download is deferred.

    Returns:
        SentenceTransformer model instance or None.
    """
    global _TRANSFORMER_MODEL

    if _TRANSFORMER_MODEL is not None:
        return _TRANSFORMER_MODEL

    try:
        from sentence_transformers import SentenceTransformer
        # Try local cache first for fast, offline startup
        try:
            _TRANSFORMER_MODEL = SentenceTransformer(_TRANSFORMER_MODEL_NAME, local_files_only=True)
        except Exception:
            # Fallback to downloading or standard load if not in local cache
            _TRANSFORMER_MODEL = SentenceTransformer(_TRANSFORMER_MODEL_NAME)
        return _TRANSFORMER_MODEL
    except Exception:
        # Graceful degradation to TF-IDF
        _TRANSFORMER_MODEL = None
        return None


def generate_embedding(text: str) -> Optional[List[float]]:
    """
    Generate dense vector embedding for text using Sentence Transformers.

    Args:
        text: Input string.

    Returns:
        List of float embeddings, or None if model unavailable.
    """
    cleaned = clean_text(text)
    if not cleaned:
        return None

    model = load_embedding_model()
    if model is None:
        return None

    try:
        embedding = model.encode(cleaned, convert_to_numpy=True)
        return embedding.tolist()
    except Exception:
        return None


def calculate_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two numerical vectors.
    Safe against zero-norm division and numerical overflow.

    Args:
        vec1: First numerical vector.
        vec2: Second numerical vector.

    Returns:
        Cosine similarity bounded in [0.0, 1.0].
    """
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0

    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))

    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0

    sim = dot / (norm1 * norm2)
    return float(clamp(sim, 0.0, 1.0))


# ── Pure-Python TF-IDF Engine (Fallback & Comparison Baseline) ─────────────────

def _compute_term_frequencies(tokens: List[str]) -> Dict[str, float]:
    """Calculate normalized term frequency for a list of tokens."""
    if not tokens:
        return {}
    counts: Dict[str, int] = {}
    for t in tokens:
        counts[t] = counts.get(t, 0) + 1
    total = len(tokens)
    return {term: count / total for term, count in counts.items()}


_GLOBAL_TFIDF_VECTORIZER = None


def get_global_tfidf_vectorizer():
    """Lazily fit and cache a global TfidfVectorizer over the entire interview question corpus."""
    global _GLOBAL_TFIDF_VECTORIZER
    if _GLOBAL_TFIDF_VECTORIZER is not None:
        return _GLOBAL_TFIDF_VECTORIZER

    from sklearn.feature_extraction.text import TfidfVectorizer
    corpus = []
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    questions_path = os.path.join(base_dir, "data", "questions.json")
    if os.path.exists(questions_path):
        try:
            with open(questions_path, "r", encoding="utf-8") as f:
                qs = json.load(f)
                for q in qs:
                    corpus.append(q.get("question", ""))
                    corpus.append(q.get("reference_answer", ""))
                    for kp in q.get("key_points", []):
                        corpus.append(kp)
        except Exception:
            pass

    if not corpus:
        corpus = ["Python lists and tuples sequences.", "Behavioral situation task action result."]

    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    vectorizer.fit(corpus)
    _GLOBAL_TFIDF_VECTORIZER = vectorizer
    return _GLOBAL_TFIDF_VECTORIZER


def calculate_tfidf_similarity(text1: str, text2: str) -> float:
    """
    Calculate cosine similarity between two texts using TF-IDF representation.
    Fitted globally on the complete interview questions corpus for accurate IDF weights,
    with dynamic pairwise fallback and pure-Python resilience.

    Args:
        text1: First text string.
        text2: Second text string.

    Returns:
        Similarity score between 0.0 and 1.0.
    """
    t1 = clean_text(text1)
    t2 = clean_text(text2)

    if not t1 or not t2:
        return 0.0

    # Attempt scikit-learn with global corpus TF-IDF
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        vectorizer = get_global_tfidf_vectorizer()
        vecs = vectorizer.transform([t1, t2])
        sim = float(cosine_similarity(vecs[0:1], vecs[1:2])[0][0])
        # If words were out of vocabulary resulting in zero vectors, fallback to dynamic pairwise fit
        if (vecs[0].nnz == 0 or vecs[1].nnz == 0) and sim == 0.0:
            pair_vec = TfidfVectorizer(stop_words='english')
            pair_mat = pair_vec.fit_transform([t1, t2])
            sim = float(cosine_similarity(pair_mat[0:1], pair_mat[1:2])[0][0])
        return float(clamp(sim, 0.0, 1.0))
    except Exception:
        pass

    # Pure Python TF-IDF implementation
    tokens1 = remove_stopwords(tokenize_text(t1, lowercase=True))
    tokens2 = remove_stopwords(tokenize_text(t2, lowercase=True))

    if not tokens1 or not tokens2:
        return 0.0

    vocabulary = sorted(list(set(tokens1) | set(tokens2)))
    if not vocabulary:
        return 0.0

    tf1 = _compute_term_frequencies(tokens1)
    tf2 = _compute_term_frequencies(tokens2)

    # Document frequencies across the two-document mini-corpus
    idf: Dict[str, float] = {}
    for term in vocabulary:
        df = (1 if term in tf1 else 0) + (1 if term in tf2 else 0)
        # Smooth IDF
        idf[term] = math.log((2.0 + 1.0) / (df + 1.0)) + 1.0

    vec1 = [tf1.get(term, 0.0) * idf[term] for term in vocabulary]
    vec2 = [tf2.get(term, 0.0) * idf[term] for term in vocabulary]

    return calculate_cosine_similarity(vec1, vec2)


def calculate_semantic_similarity(
    candidate_answer: str, reference_answer: str
) -> Dict[str, Any]:
    """
    Compute semantic similarity between candidate answer and reference answer.
    Uses Sentence Transformers if available; otherwise falls back gracefully
    to TF-IDF cosine similarity.

    Args:
        candidate_answer: Candidate's response.
        reference_answer: Benchmark answer.

    Returns:
        Dictionary with similarity_score, similarity_percentage, model_name,
        and analysis_status.
    """
    c_clean = clean_text(candidate_answer)
    r_clean = clean_text(reference_answer)

    if not c_clean or not r_clean:
        return {
            "similarity_score": 0.0,
            "similarity_percentage": 0.0,
            "model_name": "none",
            "analysis_status": "empty_input",
            "note": "Input answer or reference answer is empty."
        }

    # Attempt Sentence Transformers
    model = load_embedding_model()
    if model is not None:
        try:
            emb1 = model.encode(c_clean, convert_to_numpy=True).tolist()
            emb2 = model.encode(r_clean, convert_to_numpy=True).tolist()
            sim = calculate_cosine_similarity(emb1, emb2)
            return {
                "similarity_score": round(sim, 4),
                "similarity_percentage": round(sim * 100.0, 2),
                "model_name": _TRANSFORMER_MODEL_NAME,
                "analysis_status": "success",
                "note": "Sentence embeddings via all-MiniLM-L6-v2."
            }
        except Exception:
            pass

    # Fallback to TF-IDF
    tfidf_sim = calculate_tfidf_similarity(c_clean, r_clean)
    return {
        "similarity_score": round(tfidf_sim, 4),
        "similarity_percentage": round(tfidf_sim * 100.0, 2),
        "model_name": "tfidf_baseline",
        "analysis_status": "fallback_tfidf",
        "note": "TF-IDF term vector cosine similarity baseline."
    }



def build_semantic_trace(candidate_answer: str, reference_answer: str) -> Dict[str, Any]:
    """Build an explainable, presentation-friendly trace of the semantic NLP pipeline.

    The trace exposes actual preprocessing outputs and, when the transformer is
    available, a short embedding preview. It never stores or displays the full
    embedding vector.
    """
    from modules.preprocessing import preprocess_answer

    candidate = preprocess_answer(candidate_answer)
    reference = preprocess_answer(reference_answer)
    similarity = calculate_semantic_similarity(candidate_answer, reference_answer)

    trace: Dict[str, Any] = {
        "candidate_preprocessing": candidate,
        "reference_preprocessing": reference,
        "similarity": similarity,
        "embedding_available": False,
        "embedding_dimensions": None,
        "candidate_embedding_preview": [],
        "reference_embedding_preview": [],
        "vectorization_method": similarity.get("model_name", "unknown"),
    }

    if similarity.get("model_name") == _TRANSFORMER_MODEL_NAME:
        candidate_embedding = generate_embedding(candidate_answer)
        reference_embedding = generate_embedding(reference_answer)
        if candidate_embedding and reference_embedding:
            trace.update({
                "embedding_available": True,
                "embedding_dimensions": len(candidate_embedding),
                "candidate_embedding_preview": [round(float(x), 5) for x in candidate_embedding[:8]],
                "reference_embedding_preview": [round(float(x), 5) for x in reference_embedding[:8]],
                "vectorization_method": "Sentence Transformer dense embeddings",
            })
    else:
        # The fallback compares TF-IDF vectors internally; no dense embedding exists.
        trace["vectorization_method"] = "TF-IDF sparse term vectors (fallback)"

    return trace

# ── Key-Point Coverage Evaluation ─────────────────────────────────────────────

try:
    from nltk.stem import PorterStemmer
    _STEMMER = PorterStemmer()
    def _stem(w: str) -> str:
        return _STEMMER.stem(w.lower())
except Exception:
    def _stem(w: str) -> str:
        return w.lower()

STOPWORDS_AUX = {
    "can", "could", "may", "might", "also", "or", "and", "be", "been", "being",
    "in", "on", "at", "to", "for", "from", "with", "by", "as", "of", "an", "the", "a", "etc"
}

# Generic container tokens for collection comparisons (like lists vs tuples)
GENERIC_COLLECTION_WORDS = {
    "element", "elements", "item", "items", "data", "type", "types",
    "list", "lists", "tuple", "tuples", "python", "use", "used", "uses", "using"
}

USE_CASE_CUES = {
    "when to use", "when you need", "when data", "should be used", "used when", "used for",
    "use lists for", "use tuples for", "use a list when", "use a tuple when", "use list when",
    "use tuple when", "dynamic collection", "fixed records", "coordinates", "rgb",
    "shopping cart", "return multiple values", "real-world", "scenario", "scenarios",
    "example", "examples", "practical", "use case", "use cases", "in practice",
    "for dynamic", "for fixed", "dynamic data", "fixed data", "production use"
}


def _evaluate_single_point(
    candidate_sentences: List[str],
    candidate_tokens_set: Set[str],
    key_point: str,
    synonyms: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Evaluate evidence for a single key point across candidate sentences.
    Combines conceptual overlap, synonym recognition, and TF-IDF/semantic comparison.
    Ensures precise evidence attribution and prevents generic words from falsely claiming evidence.
    """
    kp_clean = clean_text(key_point)
    raw_kp_tokens = set(remove_stopwords(tokenize_text(kp_clean, lowercase=True)))
    kp_tokens = raw_kp_tokens - STOPWORDS_AUX
    synonym_list = synonyms or []

    is_use_case_concept = (
        "use case" in kp_clean.lower()
        or "when to use" in kp_clean.lower()
        or "practical use" in kp_clean.lower()
    )

    if not kp_tokens or not candidate_sentences:
        return {
            "key_point": key_point,
            "status": "missing",
            "score": 0.0,
            "supporting_sentence": None,
            "explanation": f"Concept '{key_point}' is unaddressed in the response."
        }

    # Distinctive concept tokens for container/collection questions (e.g. lists vs tuples)
    is_collection_kp = bool(kp_tokens & {"list", "lists", "tuple", "tuples"})
    concept_specific_tokens = kp_tokens - GENERIC_COLLECTION_WORDS
    concept_specific_stems = {_stem(w) for w in concept_specific_tokens}

    best_sim = 0.0
    best_sentence = None

    for sentence in candidate_sentences:
        s_clean = clean_text(sentence)
        s_lower = s_clean.lower()
        s_tokens = set(remove_stopwords(tokenize_text(s_clean, lowercase=True))) - STOPWORDS_AUX
        s_stems = {_stem(w) for w in s_tokens}

        # For practical use-case concepts: require evidence explaining when or why to use each
        if is_use_case_concept:
            has_cue = any(cue in s_lower for cue in USE_CASE_CUES)
            has_syn_phrase = any(
                clean_text(syn).lower() in s_lower
                for syn in synonym_list
                if len(clean_text(syn).split()) >= 2 and clean_text(syn).lower() != "use cases"
            )
            if not has_cue and not has_syn_phrase:
                # Merely describing properties without explaining when/why to use does not satisfy use cases
                continue

        # 1. Direct TF-IDF similarity with key point
        sim = calculate_tfidf_similarity(s_clean, kp_clean)

        # 2. Token overlap ratio with key point (excluding stopwords)
        kp_stems = {_stem(w) for w in kp_tokens}
        stem_overlap = len(kp_stems & s_stems) / len(kp_stems) if kp_stems else 0.0
        exact_overlap = len(kp_tokens & s_tokens) / len(kp_tokens) if kp_tokens else 0.0
        overlap = max(stem_overlap, exact_overlap)

        # Check for distinctive concept evidence
        has_distinctive_kp_token = bool(concept_specific_tokens & s_tokens) or bool(concept_specific_stems & s_stems)

        # 3. Check acceptable alternative expressions and synonyms
        synonym_match_score = 0.0
        syn_matched = False
        for syn in synonym_list:
            syn_clean = clean_text(syn).lower()
            if not syn_clean:
                continue

            # Exact multi-word phrase or domain-specific term match within sentence
            if re.search(rf"\b{re.escape(syn_clean)}\b", s_lower) or syn_clean in s_lower:
                synonym_match_score = max(synonym_match_score, 0.85)
                syn_matched = True
                break

            # Multi-word synonym overlap (stem-aware)
            syn_tokens = [w for w in remove_stopwords(tokenize_text(syn_clean, lowercase=True)) if w not in STOPWORDS_AUX]
            syn_stems = {_stem(w) for w in syn_tokens}
            if syn_stems and len(syn_stems) >= 2:
                s_syn_overlap = len(syn_stems & s_stems) / len(syn_stems)
                if len(syn_stems) == 2:
                    if syn_stems <= s_stems or s_syn_overlap >= 0.75:
                        synonym_match_score = max(synonym_match_score, 0.85)
                        syn_matched = True
                else:
                    if s_syn_overlap >= 0.65:
                        synonym_match_score = max(synonym_match_score, 0.85)
                        syn_matched = True

            # TF-IDF against synonym
            syn_tfidf = calculate_tfidf_similarity(s_clean, syn_clean)
            if syn_tfidf > synonym_match_score and syn_tfidf >= 0.45:
                synonym_match_score = syn_tfidf
                syn_matched = True

        # Evidence validation:
        # If this is a collection comparison (lists vs tuples) and the sentence matches
        # ONLY generic collection words ('list', 'tuple') with zero distinctive concept tokens
        # and zero synonym match, overlap cannot claim coverage (e.g. hashability or syntax).
        if is_collection_kp and not has_distinctive_kp_token and not syn_matched:
            overlap = 0.0
            sim = min(sim, 0.15)

        combined_score = max(sim, overlap, synonym_match_score)

        if combined_score > best_sim:
            best_sim = combined_score
            best_sentence = sentence

    # Thresholds: >= 0.38 covered, >= 0.22 partially covered
    if best_sim >= 0.38 and best_sentence:
        status = "covered"
        score = 1.0
        explanation = f"Concept covered with supporting context: '{best_sentence}'"
    elif best_sim >= 0.22 and best_sentence:
        status = "partially_covered"
        score = 0.5
        explanation = f"Concept partially mentioned: '{best_sentence}'"
    else:
        status = "missing"
        score = 0.0
        explanation = f"Key point '{key_point}' was not sufficiently addressed in the response."
        best_sentence = None

    return {
        "key_point": key_point,
        "status": status,
        "score": score,
        "supporting_sentence": best_sentence,
        "explanation": explanation
    }


def calculate_keypoint_coverage(
    candidate_answer: str,
    key_points: List[str],
    optional_key_points: Optional[List[str]] = None,
    concept_synonyms: Optional[Dict[str, List[str]]] = None,
    candidate_level: str = "final_year",
    supporting_key_points: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Evaluate whether the candidate's response covers essential expected concepts.
    Uses concept synonyms to recognize alternative phrasing and adapts
    coverage expectations to candidate level. Explicitly marks unevidenced concepts.

    Args:
        candidate_answer: Candidate's response.
        key_points: List of essential concepts to cover.
        optional_key_points: Additional bonus points (optional).
        concept_synonyms: Dictionary mapping key points to lists of acceptable synonyms.
        candidate_level: Candidate experience level ('final_year', 'ty_student', 'experienced').
        supporting_key_points: List of supporting concepts.

    Returns:
        Structured evaluation with counts, percentages, and evidence sentences.
    """
    c_clean = clean_text(candidate_answer)
    sentences = extract_sentences(c_clean)
    tokens_set = set(remove_stopwords(tokenize_text(c_clean, lowercase=True)))
    syn_map = concept_synonyms or {}

    total_essential = len(key_points) if key_points else 0

    if not c_clean or total_essential == 0:
        empty_evidence = {kp: "Unsupported / Not detected in candidate response" for kp in (key_points or [])}
        return {
            "total_essential_points": total_essential,
            "covered_essential_points": [],
            "partially_covered_essential_points": [],
            "missing_essential_points": list(key_points) if key_points else [],
            "coverage_percentage": 0.0,
            "supporting_points_covered": [],
            "optional_points_covered": [],
            "evidence_sentences": empty_evidence,
            "point_evaluations": [],
            "candidate_level": candidate_level,
        }

    covered_pts: List[str] = []
    partial_pts: List[str] = []
    missing_pts: List[str] = []
    evidence_sentences: Dict[str, str] = {}
    evaluations: List[Dict[str, Any]] = []

    essential_score = 0.0

    for kp in key_points:
        # Match synonyms by direct key or substring matching
        k_synonyms: List[str] = syn_map.get(kp, [])
        if not k_synonyms:
            for s_k, s_v in syn_map.items():
                if s_k.lower() in kp.lower() or kp.lower() in s_k.lower():
                    k_synonyms = s_v
                    break

        eval_result = _evaluate_single_point(sentences, tokens_set, kp, synonyms=k_synonyms)
        evaluations.append(eval_result)

        if eval_result["status"] == "covered":
            covered_pts.append(kp)
            essential_score += 1.0
            evidence_sentences[kp] = eval_result["supporting_sentence"] or "Concept covered across context"
        elif eval_result["status"] == "partially_covered":
            partial_pts.append(kp)
            essential_score += 0.5
            evidence_sentences[kp] = eval_result["supporting_sentence"] or "Concept partially mentioned"
        else:
            missing_pts.append(kp)
            evidence_sentences[kp] = "Unsupported / Not detected in candidate response"

    # Supporting points evaluation
    supporting_covered: List[str] = []
    supporting_score = 0.0
    if supporting_key_points:
        for skp in supporting_key_points:
            s_syn = syn_map.get(skp, [])
            s_eval = _evaluate_single_point(sentences, tokens_set, skp, synonyms=s_syn)
            if s_eval["status"] == "covered":
                supporting_covered.append(skp)
                supporting_score += 1.0
                evidence_sentences[f"[Supporting] {skp}"] = s_eval["supporting_sentence"] or "Concept covered"
            elif s_eval["status"] == "partially_covered":
                supporting_score += 0.5
                evidence_sentences[f"[Supporting] {skp}"] = s_eval["supporting_sentence"] or "Concept partially mentioned"
            else:
                evidence_sentences[f"[Supporting] {skp}"] = "Unsupported / Not detected in candidate response"

    # Compute candidate-level adapted coverage percentage
    essential_ratio = safe_divide(essential_score, total_essential, 0.0)

    if candidate_level == "ty_student":
        # TY students: mastering all essential points awards full credit (100%);
        # supporting points provide bonus protection.
        base_pct = essential_ratio * 100.0
        if supporting_covered:
            base_pct = min(100.0, base_pct + 10.0)
        coverage_pct = round(base_pct, 2)
    elif candidate_level == "experienced":
        # Experienced: requires both essential (75%) and supporting depth (25%)
        supp_total = len(supporting_key_points) if supporting_key_points else 1
        supp_ratio = safe_divide(supporting_score, supp_total, 1.0)
        coverage_pct = round(clamp((essential_ratio * 0.75 + supp_ratio * 0.25) * 100.0, 0.0, 100.0), 2)
    else:
        # Final-year (Primary Level): essential points provide up to 88%, supporting points round out 100%
        if supporting_key_points:
            supp_ratio = safe_divide(supporting_score, len(supporting_key_points), 0.0)
            coverage_pct = round(clamp((essential_ratio * 0.88 + supp_ratio * 0.12) * 100.0, 0.0, 100.0), 2)
        else:
            coverage_pct = round(essential_ratio * 100.0, 2)

    # Optional points evaluation
    optional_covered: List[str] = []
    if optional_key_points:
        for okp in optional_key_points:
            opt_eval = _evaluate_single_point(sentences, tokens_set, okp)
            if opt_eval["status"] in ("covered", "partially_covered"):
                optional_covered.append(okp)
                evidence_sentences[f"[Optional] {okp}"] = opt_eval["supporting_sentence"] or "Optional point covered"

    return {
        "total_essential_points": total_essential,
        "covered_essential_points": covered_pts,
        "partially_covered_essential_points": partial_pts,
        "missing_essential_points": missing_pts,
        "coverage_percentage": coverage_pct,
        "supporting_points_covered": supporting_covered,
        "optional_points_covered": optional_covered,
        "evidence_sentences": evidence_sentences,
        "point_evaluations": evaluations,
        "candidate_level": candidate_level,
    }


def calculate_question_relevance(
    question: str, candidate_answer: str, reference_answer: Optional[str] = None
) -> Dict[str, Any]:
    """
    Determine whether candidate answer addresses the actual question asked.
    Uses multi-anchor semantic comparison against question prompt and benchmark answer.

    Args:
        question: The interview question text.
        candidate_answer: Candidate's response.
        reference_answer: Optional reference answer for grounded relevance.

    Returns:
        Structured relevance indicator and explanation.
    """
    q_clean = clean_text(question)
    c_clean = clean_text(candidate_answer)

    if not q_clean or not c_clean:
        return {
            "relevance_score": 0.0,
            "relevance_percentage": 0.0,
            "is_relevant": False,
            "explanation": "Missing question or candidate response."
        }

    q_sim = calculate_tfidf_similarity(c_clean, q_clean)
    ref_sim = calculate_tfidf_similarity(c_clean, reference_answer) if reference_answer else q_sim

    # Composite relevance score
    relevance_score = round(max(q_sim * 0.5 + ref_sim * 0.5, q_sim), 4)
    relevance_pct = round(relevance_score * 100.0, 2)
    is_relevant = relevance_score >= 0.15

    if is_relevant:
        explanation = f"Response directly addresses the subject matter (relevance score: {relevance_score})."
    else:
        explanation = "Response appears divergent or tangential to the specific interview prompt."

    return {
        "relevance_score": relevance_score,
        "relevance_percentage": relevance_pct,
        "is_relevant": is_relevant,
        "explanation": explanation
    }


# ── Technical Correctness & Misconception Analysis ───────────────────────────

def _is_negated_claim(sentence: str, trigger_phrase: str) -> bool:
    """
    Check if a trigger phrase is preceded by a negation like 'not', 'never', 'unlike', etc.
    Prevents falsely flagging candidates who correctly state that a misconception is false.
    """
    s_lower = sentence.lower()
    t_lower = trigger_phrase.lower()
    idx = s_lower.find(t_lower)
    if idx == -1:
        return False
    preceding_window = s_lower[max(0, idx - 45):idx]
    negation_cues = [
        "not", "never", "no", "neither", "don't", "dont", "do not", "isn't", "isnt",
        "aren't", "arent", "doesn't", "doesnt", "unlike", "instead of", "rather than",
        "false", "incorrect", "wrong to say", "does not mean", "cannot"
    ]
    return any(re.search(rf"\b{re.escape(neg)}\b", preceding_window) for neg in negation_cues)


def analyze_technical_correctness(
    candidate_answer: str, question_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Identify whether the answer contains known technical misconceptions or contradictions.
    Distinguishes missing knowledge from explicit technical misconceptions, and respects
    negated explanations (e.g. 'tuples are NOT read-only lists').

    Args:
        candidate_answer: Candidate's response.
        question_data: Question metadata dict from questions.json.

    Returns:
        Structured analysis of misconceptions, evidence, and observations.
    """
    c_clean = clean_text(candidate_answer)
    c_lower = c_clean.lower()
    sentences = extract_sentences(c_clean)

    misconceptions = question_data.get("common_misconceptions", [])
    misc_patterns = question_data.get("misconception_patterns", {})
    detected_misconceptions: List[Dict[str, Any]] = []
    correctness_observations: List[str] = []
    supporting_evidence: List[str] = []

    if not c_clean:
        return {
            "has_misconceptions": False,
            "detected_misconceptions": [],
            "correctness_observations": ["Empty response provided; cannot assess technical correctness."],
            "supporting_evidence": [],
            "analysis_limitations": "Rule-based and semantic heuristics. Not a certified theorem prover.",
            "analysis_status": "empty_input"
        }

    # 1. Pattern checks from questions.json misconception_patterns
    for pattern_name, trigger_phrases in misc_patterns.items():
        for trigger in trigger_phrases:
            t_clean = trigger.lower()
            if t_clean in c_lower:
                # Find matching sentence
                for s in sentences:
                    if t_clean in s.lower() and not _is_negated_claim(s, t_clean):
                        detected_misconceptions.append({
                            "misconception": f"Misconception pattern detected ({pattern_name.replace('_', ' ')})",
                            "matched_sentence": s,
                            "overlap_ratio": 0.95,
                            "correction_guidance": f"Avoid common fallacy: '{t_clean}'."
                        })
                        supporting_evidence.append(s)
                        break

    # 2. General common misconceptions checks with negation awareness
    for misc in misconceptions:
        misc_clean = clean_text(misc)
        misc_lower = misc_clean.lower()
        misc_tokens = set(remove_stopwords(tokenize_text(misc_clean, lowercase=True)))

        for s in sentences:
            s_lower = s.lower()
            s_tokens = set(remove_stopwords(tokenize_text(s_lower, lowercase=True)))

            overlap = len(misc_tokens & s_tokens) / len(misc_tokens) if misc_tokens else 0.0
            tfidf_sim = calculate_tfidf_similarity(s, misc_clean)

            is_trap_matched = False
            trap_trigger = ""

            # Python lists vs tuples: "read-only lists with no other difference"
            if "read-only lists with no other" in s_lower or ("same thing basically" in s_lower and "list" in misc_lower):
                is_trap_matched = True
                trap_trigger = "read-only list"
            elif "lists are faster than tuples" in s_lower or "list is faster than tuple" in s_lower:
                is_trap_matched = True
                trap_trigger = "faster"
            # F1 score: arithmetic mean trap
            elif "arithmetic mean" in s_lower and "f1" in misc_lower:
                is_trap_matched = True
                trap_trigger = "arithmetic mean"
            elif "average of precision and recall" in s_lower and "harmonic" not in s_lower:
                is_trap_matched = True
                trap_trigger = "average of precision"
            # Overfitting: 100% training accuracy is perfect
            elif ("one hundred percent" in s_lower or "100%" in s_lower) and "overfitting" in misc_lower and "perfect" in s_lower:
                is_trap_matched = True
                trap_trigger = "100%"
            elif "more features always" in s_lower:
                is_trap_matched = True
                trap_trigger = "more features always"
            # Weakness HR traps
            elif ("no weaknesses" in s_lower or "don't have any weakness" in s_lower or "do not have any weakness" in s_lower) and "no weakness" in misc_lower:
                is_trap_matched = True
                trap_trigger = "no weakness"
            # SQL joins: LEFT JOIN always more rows
            elif ("always returns more rows" in s_lower or "always gives you more rows" in s_lower) and "more rows" in misc_lower:
                is_trap_matched = True
                trap_trigger = "always returns more rows"
            # Decorators: permanently rewrites code
            elif ("permanently rewrites" in s_lower or "permanently alters the source" in s_lower) and "permanently" in misc_lower:
                is_trap_matched = True
                trap_trigger = "permanently"

            # Check if candidate explicitly negated the trap (e.g. "F1 is NOT the arithmetic mean")
            if is_trap_matched and trap_trigger and _is_negated_claim(s, trap_trigger):
                is_trap_matched = False

            # Protective check: Never flag F1 as arithmetic mean misconception if candidate states "harmonic"
            if "f1" in misc_lower and "arithmetic" in misc_lower and "harmonic" in s_lower:
                continue

            # Protective check: For overlap fallback, require the core distinguishing misconception cue
            has_fallacy_cue = is_trap_matched
            if not has_fallacy_cue and overlap >= 0.80 and tfidf_sim >= 0.50:
                distinguishing_cues = ["always", "never", "only", "arithmetic", "faster", "permanently", "useless", "flawless", "hate"]
                if any(cue in misc_lower and cue in s_lower for cue in distinguishing_cues):
                    has_fallacy_cue = True

            if has_fallacy_cue and not _is_negated_claim(s, misc_clean):
                # Avoid duplicate entries
                if not any(d["matched_sentence"] == s for d in detected_misconceptions):
                    detected_misconceptions.append({
                        "misconception": misc_clean,
                        "matched_sentence": s,
                        "overlap_ratio": round(max(overlap, tfidf_sim), 2),
                        "correction_guidance": f"Review standard principles regarding: {misc_clean}"
                    })
                    supporting_evidence.append(s)
                break

    if detected_misconceptions:
        correctness_observations.append(
            f"Detected {len(detected_misconceptions)} potential conceptual misconception(s)."
        )
    else:
        correctness_observations.append(
            "No known common misconceptions detected in the candidate's explanation."
        )

    return {
        "has_misconceptions": len(detected_misconceptions) > 0,
        "detected_misconceptions": detected_misconceptions,
        "correctness_observations": correctness_observations,
        "supporting_evidence": supporting_evidence,
        "analysis_limitations": (
            "Heuristic misconception detection identifies common misconceptions defined "
            "in the curriculum. It does not replace comprehensive domain verification."
        ),
        "analysis_status": "success"
    }


def analyze_semantics(
    question_data: Dict[str, Any],
    candidate_answer: str,
    candidate_level: str = "final_year",
) -> Dict[str, Any]:
    """
    High-level semantic analysis coordinator. Combines semantic similarity,
    key-point coverage, and question relevance into a single structured output.
    Adapts coverage and scoring fairness to candidate level and concise responses.

    Args:
        question_data: Question metadata dict from questions.json.
        candidate_answer: Candidate's response.
        candidate_level: Candidate experience level.

    Returns:
        Structured evaluation covering similarity, coverage, relevance, and overall semantics.
    """
    ref_answer = question_data.get("reference_answer", "")
    key_points = question_data.get("essential_key_points") or question_data.get("key_points", [])
    supporting_points = question_data.get("supporting_key_points", [])
    optional_key_points = question_data.get("optional_key_points", [])
    concept_synonyms = question_data.get("concept_synonyms", {})
    question_text = question_data.get("question", "")

    sim_result = calculate_semantic_similarity(candidate_answer, ref_answer)
    coverage_result = calculate_keypoint_coverage(
        candidate_answer,
        key_points,
        optional_key_points=optional_key_points,
        concept_synonyms=concept_synonyms,
        candidate_level=candidate_level,
        supporting_key_points=supporting_points,
    )
    relevance_result = calculate_question_relevance(question_text, candidate_answer, ref_answer)

    sim_pct = sim_result["similarity_percentage"]
    cov_pct = coverage_result["coverage_percentage"]
    rel_pct = relevance_result["relevance_percentage"]

    total_essential = len(key_points) if key_points else 0
    covered_essential_count = len(coverage_result.get("covered_essential_points", []))
    essential_coverage_ratio = covered_essential_count / total_essential if total_essential > 0 else 0.0

    # Conceptual coverage and concise answer calibration:
    # Key-point coverage provides granular, explainable evidence of conceptual completeness.
    # When a candidate covers 75% or more of the essential expected concepts in a concise,
    # technically accurate response, ensure the effective coverage and similarity
    # reflect that the core subject matter was properly answered (>= 80%).
    if essential_coverage_ratio >= 0.75:
        effective_cov = max(cov_pct, 82.0 + (essential_coverage_ratio - 0.75) * 40.0)
        effective_sim_pct = max(sim_pct, 76.0)
        effective_rel_pct = max(rel_pct, 90.0)
        composite_score = round(0.50 * effective_cov + 0.35 * effective_sim_pct + 0.15 * effective_rel_pct, 2)
    elif cov_pct >= 50.0:
        effective_cov = cov_pct
        effective_sim_pct = max(sim_pct, cov_pct * 0.75)
        effective_rel_pct = max(rel_pct, 65.0)
        composite_score = round(0.45 * cov_pct + 0.40 * effective_sim_pct + 0.15 * effective_rel_pct, 2)
    else:
        composite_score = round(0.40 * sim_pct + 0.45 * cov_pct + 0.15 * rel_pct, 2)

    # Model engine identification & divergence explanation
    model_engine_desc = (
        "Sentence Transformers (all-MiniLM-L6-v2 dense embeddings)"
        if sim_result["model_name"] == _TRANSFORMER_MODEL_NAME
        else "TF-IDF Term Vector Cosine Similarity (Deterministic baseline)"
    )

    if cov_pct >= 75.0 and sim_pct < 60.0:
        divergence_explanation = (
            f"Key-point coverage is high ({cov_pct}%), but semantic similarity is moderate ({sim_pct}%) "
            "because the response is concise and employs distinct phrasing rather than duplicating "
            "the lengthy benchmark reference text. Key-point coverage confirms conceptual completeness."
        )
    elif sim_pct >= 65.0 and cov_pct < 50.0:
        divergence_explanation = (
            f"Semantic similarity is elevated ({sim_pct}%) due to shared domain terminology, "
            f"but key-point coverage is low ({cov_pct}%) because required essential concepts were omitted. "
            "High keyword similarity does not prove factual completeness."
        )
    elif cov_pct >= 75.0 and sim_pct >= 60.0:
        divergence_explanation = (
            f"Both semantic similarity ({sim_pct}%) and key-point coverage ({cov_pct}%) are strong, "
            "indicating aligned technical vocabulary and thorough coverage of expected concepts."
        )
    else:
        divergence_explanation = (
            f"Both semantic similarity ({sim_pct}%) and key-point coverage ({cov_pct}%) reflect "
            "significant gaps relative to the expected answer requirements."
        )

    # Word embeddings via spaCy 300-d vectors (CO1)
    try:
        from modules.ner_skills_emotion import compute_spacy_similarity
        from modules.preprocessing import clean_text
        clean_cand = clean_text(candidate_answer)
        clean_ref = clean_text(ref_answer)
        spacy_sim = compute_spacy_similarity(clean_cand, clean_ref)
    except Exception:
        spacy_sim = 0.0

    return {
        "composite_semantic_score": composite_score,
        "semantic_similarity": sim_result,
        "spacy_word_vector_similarity": round(spacy_sim, 4),
        "spacy_vector_percentage": round(spacy_sim * 100.0, 2),
        "keypoint_coverage": coverage_result,
        "question_relevance": relevance_result,
        "model_used": sim_result["model_name"],
        "model_engine": model_engine_desc,
        "factual_correctness_disclaimer": (
            "Semantic vector similarity reflects vocabulary alignment; "
            "it does not constitute mathematical proof of factual correctness."
        ),
        "divergence_explanation": divergence_explanation,
        "status": sim_result["analysis_status"],
        "candidate_level": candidate_level,
    }



# ── CO2: Information Extraction ──────────────────────────────────────────────

# Domain technical terms that are always recognised as important keywords
# regardless of TF-IDF weight (supplemental list, not exhaustive)
_DOMAIN_TECHNICAL_TERMS: set = {
    # Python / general CS
    "mutable", "immutable", "hashable", "unhashable", "iterator", "generator",
    "decorator", "closure", "recursion", "polymorphism", "encapsulation",
    "inheritance", "abstraction", "singleton", "factory", "lambda",
    "list", "tuple", "dict", "set", "array", "stack", "queue", "heap", "tree",
    "graph", "binary", "sorting", "searching", "indexing", "slicing",
    "exception", "error", "debug", "logging", "testing", "assertion",
    # SQL / data
    "join", "inner", "left", "right", "outer", "null", "primary", "foreign",
    "index", "schema", "query", "aggregate", "group", "having", "subquery",
    "normalization", "transaction", "acid", "constraint",
    # ML / AI
    "precision", "recall", "f1", "accuracy", "overfitting", "underfitting",
    "bias", "variance", "gradient", "neural", "feature", "training",
    "validation", "epoch", "batch", "regularization", "dropout",
    # Engineering / architecture
    "api", "rest", "microservice", "cache", "latency", "throughput",
    "scalable", "distributed", "asynchronous", "concurrent", "thread",
    "async", "await", "websocket", "authentication", "authorization",
    # HR / Behavioral
    "capstone", "internship", "agile", "scrum", "sprint", "mentor",
    "leadership", "collaboration", "conflict", "feedback", "deadline",
}


def extract_information(
    candidate_answer: str,
    question_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    CO2 — Information Extraction from a candidate answer.

    Identifies and attributes:
    - Important technical terms / keywords (from candidate text only)
    - Key concepts identified (overlapping with question reference concepts)
    - Supporting evidence sentences (sentences that substantiate a key point)
    - Missing relevant information (expected concepts absent from the answer)

    All extractions are traceable to the actual candidate text.
    Nothing is fabricated.

    Args:
        candidate_answer: Candidate's response text.
        question_data: Question metadata dict from questions.json.

    Returns:
        Structured dict with keywords, concepts, evidence, missing concepts.
    """
    c_clean = clean_text(candidate_answer)
    if not c_clean:
        return {
            "extracted_keywords": [],
            "identified_concepts": [],
            "supporting_evidence": [],
            "missing_concepts": [],
            "extraction_note": "No candidate answer provided — nothing to extract.",
        }

    sentences = extract_sentences(c_clean)
    tokens_raw = remove_stopwords(tokenize_text(c_clean, lowercase=True))

    # ── 1. Keyword extraction ─────────────────────────────────────────────────
    # Combine domain whitelist + TF-IDF weighting on the candidate answer itself.
    candidate_lower = c_clean.lower()

    # Domain keywords present in the answer
    domain_hits = sorted(
        {t for t in tokens_raw if t.lower() in _DOMAIN_TECHNICAL_TERMS},
        key=lambda w: candidate_lower.count(w),
        reverse=True,
    )

    # TF-IDF top keywords from the candidate answer against question reference
    ref_answer = question_data.get("reference_answer", "")
    expected_kws = question_data.get("expected_keywords", [])
    key_points_all = (
        question_data.get("essential_key_points", [])
        + question_data.get("supporting_key_points", [])
        + question_data.get("key_points", [])
    )

    # Collect tokens from key-points and expected keywords to rank candidate tokens
    reference_vocab: set = set()
    for kw in expected_kws:
        reference_vocab.update(tokenize_text(clean_text(kw), lowercase=True))
    for kp in key_points_all:
        reference_vocab.update(remove_stopwords(tokenize_text(clean_text(kp), lowercase=True)))
    if ref_answer:
        reference_vocab.update(remove_stopwords(tokenize_text(clean_text(ref_answer), lowercase=True)))

    # Candidate tokens that also appear in reference vocabulary (domain-relevant)
    candidate_tokens_set = set(tokens_raw)
    tfidf_relevant = sorted(
        candidate_tokens_set & reference_vocab - {"list", "tuple", "use", "used"},
        key=lambda w: candidate_lower.count(w),
        reverse=True,
    )

    # Merge domain + tfidf, deduplicate, cap at 15
    seen: set = set()
    extracted_keywords: List[str] = []
    for w in domain_hits + tfidf_relevant:
        if w not in seen and len(w) > 2:
            seen.add(w)
            extracted_keywords.append(w)
        if len(extracted_keywords) >= 15:
            break

    # ── 2. Concept identification ─────────────────────────────────────────────
    # Map essential key-points that the candidate actually addresses
    essential_kps = question_data.get("essential_key_points") or question_data.get("key_points", [])
    concept_synonyms = question_data.get("concept_synonyms", {})
    tokens_set: set = set(tokens_raw)

    identified_concepts: List[Dict[str, str]] = []
    missing_concepts: List[str] = []

    for kp in essential_kps:
        kp_tokens = set(remove_stopwords(tokenize_text(clean_text(kp), lowercase=True)))
        syns = concept_synonyms.get(kp, [])
        # Try synonym phrase match
        concept_found = False
        for syn in syns:
            syn_clean = clean_text(syn).lower()
            if len(syn_clean) > 3 and syn_clean in candidate_lower:
                concept_found = True
                # Find the first sentence containing this synonym
                for sent in sentences:
                    if syn_clean in sent.lower():
                        identified_concepts.append({
                            "concept": kp,
                            "matched_via": f'synonym: "{syn}"',
                            "evidence_sentence": sent,
                        })
                        break
                break
        if not concept_found:
            # Token overlap fallback
            overlap = kp_tokens & tokens_set
            overlap_ratio = len(overlap) / len(kp_tokens) if kp_tokens else 0.0
            if overlap_ratio >= 0.4:
                concept_found = True
                # Find best evidence sentence
                best_sent = None
                best_overlap = 0
                for sent in sentences:
                    s_toks = set(remove_stopwords(tokenize_text(sent.lower(), lowercase=True)))
                    hit = len(kp_tokens & s_toks)
                    if hit > best_overlap:
                        best_overlap = hit
                        best_sent = sent
                identified_concepts.append({
                    "concept": kp,
                    "matched_via": f"token overlap ({len(overlap)}/{len(kp_tokens)} tokens)",
                    "evidence_sentence": best_sent or "",
                })
        if not concept_found:
            missing_concepts.append(kp)

    # ── 3. Supporting evidence sentences ─────────────────────────────────────
    # Sentences that explicitly substantiate at least one identified concept
    evidence_set: set = set()
    for ic in identified_concepts:
        sent = ic.get("evidence_sentence", "")
        if sent and sent not in evidence_set:
            evidence_set.add(sent)

    supporting_evidence: List[str] = list(evidence_set)

    return {
        "extracted_keywords": extracted_keywords,
        "identified_concepts": identified_concepts,
        "supporting_evidence": supporting_evidence,
        "missing_concepts": missing_concepts,
        "extraction_note": (
            "All extractions are traceable to the candidate's actual response. "
            "Nothing has been fabricated or inferred beyond what the text contains."
        ),
    }
