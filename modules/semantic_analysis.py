"""
semantic_analysis.py — Semantic Relevance & Conceptual Evaluation Engine

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
    global _TRANSFORMER_MODEL, _TRANSFORMER_LOAD_ATTEMPTED

    if _TRANSFORMER_MODEL is not None:
        return _TRANSFORMER_MODEL

    if _TRANSFORMER_LOAD_ATTEMPTED:
        return None

    _TRANSFORMER_LOAD_ATTEMPTED = True

    try:
        from sentence_transformers import SentenceTransformer
        # Load local or cached model without throwing unhandled exceptions
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


def calculate_tfidf_similarity(text1: str, text2: str) -> float:
    """
    Calculate cosine similarity between two texts using TF-IDF representation.
    Supports scikit-learn when present, with a deterministic pure-Python
    fallback to ensure high availability in any runtime environment.

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

    # Attempt scikit-learn if available
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform([t1, t2])
        sim = float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])
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


# ── Key-Point Coverage Evaluation ─────────────────────────────────────────────

# Generic single-word tokens that should NOT trigger a high-confidence match on their own
GENERIC_SINGLE_WORDS = {
    "role", "roles", "skills", "skill", "project", "projects", "growth",
    "experience", "experiences", "background", "position", "positions",
    "team", "teams", "technologies", "opportunity", "opportunities", "task", "work"
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
    kp_tokens = set(remove_stopwords(tokenize_text(kp_clean, lowercase=True)))
    synonym_list = synonyms or []

    if not kp_tokens or not candidate_sentences:
        return {
            "key_point": key_point,
            "status": "missing",
            "score": 0.0,
            "supporting_sentence": None,
            "explanation": f"Concept '{key_point}' is unaddressed in the response."
        }

    best_sim = 0.0
    best_sentence = None

    for sentence in candidate_sentences:
        s_clean = clean_text(sentence)
        s_lower = s_clean.lower()
        s_tokens = set(remove_stopwords(tokenize_text(s_clean, lowercase=True)))

        # 1. Direct TF-IDF similarity with key point
        sim = calculate_tfidf_similarity(s_clean, kp_clean)

        # 2. Token overlap ratio with key point
        overlap = len(kp_tokens & s_tokens) / len(kp_tokens) if kp_tokens else 0.0

        # 3. Check acceptable alternative expressions and synonyms
        synonym_match_score = 0.0
        for syn in synonym_list:
            syn_clean = clean_text(syn).lower()
            if not syn_clean:
                continue

            # If synonym is a broad generic word, require qualified presence rather than giving full 0.85
            if syn_clean in GENERIC_SINGLE_WORDS:
                if re.search(rf"\b{re.escape(syn_clean)}\b", s_lower):
                    synonym_match_score = max(synonym_match_score, 0.35)
                continue

            # Exact multi-word phrase or domain-specific term match within sentence
            if re.search(rf"\b{re.escape(syn_clean)}\b", s_lower) or syn_clean in s_lower:
                synonym_match_score = max(synonym_match_score, 0.85)
                break

            # Token overlap with multi-word synonym
            syn_tokens = set(remove_stopwords(tokenize_text(syn_clean, lowercase=True)))
            if syn_tokens and len(syn_tokens) >= 2:
                s_syn_overlap = len(syn_tokens & s_tokens) / len(syn_tokens)
                if s_syn_overlap >= 0.70:
                    synonym_match_score = max(synonym_match_score, 0.75)
                elif s_syn_overlap >= 0.50:
                    synonym_match_score = max(synonym_match_score, 0.55)

            # TF-IDF against synonym
            syn_tfidf = calculate_tfidf_similarity(s_clean, syn_clean)
            if syn_tfidf > synonym_match_score and syn_tfidf >= 0.40:
                synonym_match_score = syn_tfidf

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

    # Conceptual coverage and concise answer calibration:
    # Key-point coverage provides granular, explainable evidence of conceptual completeness.
    # When coverage is high (>= 75%), effective similarity and question relevance
    # reflect that the candidate answered the prompt's subject matter accurately.
    if cov_pct >= 75.0:
        effective_sim_pct = max(sim_pct, cov_pct * 0.90)
        effective_rel_pct = max(rel_pct, min(100.0, cov_pct + 10.0))
        composite_score = round(0.50 * cov_pct + 0.35 * effective_sim_pct + 0.15 * effective_rel_pct, 2)
    elif cov_pct >= 50.0:
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

    return {
        "composite_semantic_score": composite_score,
        "semantic_similarity": sim_result,
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
