"""
communication_analysis.py — Communication & Linguistic Delivery Analysis Module

Analyzes observable communication indicators:
- Filler words (single and multi-word phrases) with frequency per 100 words
- Hedging expressions and their contextual frequency
- Vocabulary metrics: unique word count, vocabulary diversity ratio (TTR)
- Sentence complexity and readability descriptive indicators
- Delivery indicators: repetition, overly long sentences, brief responses

IMPORTANT PHILOSOPHICAL AND SCIENTIFIC LIMITATIONS:
- Linguistic delivery indicators measure observable verbal/textual habits only.
- They DO NOT measure actual candidate confidence, personality, intelligence,
  honesty, or intrinsic subject-matter competence.
- Positive sentiment does NOT automatically mean high performance.
- Modest hedging is frequently healthy and appropriate in nuanced engineering
  and scientific discourse.
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple

from modules.preprocessing import (
    clean_text,
    extract_basic_statistics,
    extract_sentences,
    tokenize_text,
)
from utils.helpers import safe_divide

# Standard filler words and multi-word conversational fillers
FILLER_PATTERNS: List[Tuple[str, str]] = [
    ("you know", r"\byou\s+know\b"),
    ("i mean", r"\bi\s+mean\b"),
    ("sort of", r"\bsort\s+of\b"),
    ("kind of", r"\bkind\s+of\b"),
    ("um", r"\bum+\b"),
    ("uh", r"\buh+\b"),
    ("like", r"\blike\b"),
    ("basically", r"\bbasically\b"),
    ("actually", r"\bactually\b"),
    ("okay", r"\boka?y\b"),
]

# Hedging expressions (indicators of qualification or uncertainty)
HEDGING_PATTERNS: List[Tuple[str, str]] = [
    ("i am not sure", r"\bi\s+am\s+not\s+sure\b|\bi'm\s+not\s+sure\b"),
    ("i guess", r"\bi\s+guess\b"),
    ("i think", r"\bi\s+think\b"),
    ("maybe", r"\bmaybe\b"),
    ("perhaps", r"\bperhaps\b"),
    ("possibly", r"\bpossibly\b"),
    ("probably", r"\bprobably\b"),
    ("somewhat", r"\bsomewhat\b"),
]


def detect_fillers(text: str) -> Dict[str, Any]:
    """
    Detect filler words and phrases using boundary-safe regex patterns.
    Calculates raw counts and frequency per 100 words.

    Args:
        text: Input text string.

    Returns:
        Dictionary with filler details, total count, and frequency per 100 words.
    """
    cleaned = clean_text(text).lower()
    if not cleaned:
        return {
            "filler_count": 0,
            "filler_frequency": 0.0,
            "filler_word_details": {},
        }

    tokens = tokenize_text(cleaned, lowercase=True)
    word_count = len(tokens)

    filler_details: Dict[str, int] = {}
    total_fillers = 0

    for name, pattern in FILLER_PATTERNS:
        matches = re.findall(pattern, cleaned)
        count = len(matches)
        if count > 0:
            filler_details[name] = count
            total_fillers += count

    # Frequency per 100 words
    filler_freq = round(safe_divide(total_fillers * 100.0, word_count, 0.0), 2)

    return {
        "filler_count": total_fillers,
        "filler_frequency": filler_freq,
        "filler_word_details": filler_details,
    }


def detect_hedging(text: str) -> Dict[str, Any]:
    """
    Detect hedging expressions.
    Hedging indicates qualification or cautiousness, which can be normal
    and healthy in engineering tradeoffs.

    Args:
        text: Input text string.

    Returns:
        Dictionary with hedging counts, frequency per 100 words, and item breakdown.
    """
    cleaned = clean_text(text).lower()
    if not cleaned:
        return {
            "hedging_count": 0,
            "hedging_frequency": 0.0,
            "hedging_details": {},
        }

    tokens = tokenize_text(cleaned, lowercase=True)
    word_count = len(tokens)

    hedging_details: Dict[str, int] = {}
    total_hedges = 0

    for name, pattern in HEDGING_PATTERNS:
        matches = re.findall(pattern, cleaned)
        count = len(matches)
        if count > 0:
            hedging_details[name] = count
            total_hedges += count

    hedging_freq = round(safe_divide(total_hedges * 100.0, word_count, 0.0), 2)

    return {
        "hedging_count": total_hedges,
        "hedging_frequency": hedging_freq,
        "hedging_details": hedging_details,
    }


def compute_vocabulary_metrics(text: str) -> Dict[str, Any]:
    """
    Compute descriptive vocabulary and sentence complexity metrics:
    - Unique word count
    - Vocabulary diversity ratio (Type-Token Ratio)
    - Average sentence length
    - Long sentence count (sentences with > 30 words)
    - Readability indicator (Coleman-Liau index as descriptive metric)

    NOTE: Readability and diversity are purely descriptive linguistic indicators,
    not direct measures of intelligence or competence.

    Args:
        text: Input text string.

    Returns:
        Dictionary of vocabulary and sentence complexity statistics.
    """
    cleaned = clean_text(text)
    if not cleaned:
        return {
            "unique_word_count": 0,
            "total_word_count": 0,
            "vocabulary_diversity": 0.0,
            "average_sentence_length": 0.0,
            "long_sentence_count": 0,
            "readability_information": {
                "metric_name": "Coleman-Liau Index",
                "score": 0.0,
                "interpretation": "Insufficient text for evaluation",
                "disclaimer": "Readability metrics are descriptive indicators, not competence scores."
            }
        }

    tokens = tokenize_text(cleaned, lowercase=True)
    sentences = extract_sentences(cleaned)

    word_count = len(tokens)
    unique_words = len(set(tokens))
    sentence_count = len(sentences)

    diversity = round(safe_divide(unique_words, word_count, 0.0), 3)
    avg_sentence_len = round(safe_divide(word_count, sentence_count, 0.0), 2)

    # Count sentences with > 30 words
    long_sentences = 0
    for s in sentences:
        s_tokens = tokenize_text(s, lowercase=True)
        if len(s_tokens) > 30:
            long_sentences += 1

    # Coleman-Liau Readability Index calculation:
    # CLI = 0.0588 * L - 0.296 * S - 15.8
    # L = average number of letters per 100 words
    # S = average number of sentences per 100 words
    if word_count >= 10 and sentence_count >= 1:
        letters_count = sum(len(re.findall(r"[a-zA-Z]", t)) for t in tokens)
        L = (letters_count / word_count) * 100.0
        S = (sentence_count / word_count) * 100.0
        cli_score = round(0.0588 * L - 0.296 * S - 15.8, 1)

        if cli_score < 7.0:
            interpretation = "Basic / conversational reading level"
        elif cli_score <= 12.0:
            interpretation = "Standard professional reading level"
        else:
            interpretation = "Advanced / technical reading level"
    else:
        cli_score = 0.0
        interpretation = "Short text (preliminary sample)"

    return {
        "unique_word_count": unique_words,
        "total_word_count": word_count,
        "vocabulary_diversity": diversity,
        "average_sentence_length": avg_sentence_len,
        "long_sentence_count": long_sentences,
        "readability_information": {
            "metric_name": "Coleman-Liau Index",
            "score": cli_score,
            "interpretation": interpretation,
            "disclaimer": "Readability is a descriptive indicator of text complexity, not a measure of ability."
        }
    }


def detect_repeated_phrases(text: str, n_gram_size: int = 3, threshold: int = 2) -> List[Dict[str, Any]]:
    """
    Detect repeated n-grams of words (phrases repeated multiple times).

    Args:
        text: Input text string.
        n_gram_size: Size of phrase in words (default 3).
        threshold: Minimum occurrences to flag as repeated (default 2).

    Returns:
        List of dicts with phrase and repetition count.
    """
    tokens = tokenize_text(text, lowercase=True)
    if len(tokens) < n_gram_size * 2:
        return []

    phrases: Dict[str, int] = {}
    for i in range(len(tokens) - n_gram_size + 1):
        phrase = " ".join(tokens[i : i + n_gram_size])
        phrases[phrase] = phrases.get(phrase, 0) + 1

    repeated = [
        {"phrase": phrase, "count": count}
        for phrase, count in phrases.items()
        if count >= threshold
    ]
    repeated.sort(key=lambda x: x["count"], reverse=True)
    return repeated


def analyze_communication(text: str) -> Dict[str, Any]:
    """
    Comprehensive communication analysis function.
    Returns structured measurements without arbitrary scoring thresholds.

    Args:
        text: Candidate's response.

    Returns:
        Structured dictionary covering fillers, hedging, vocabulary,
        readability, and qualitative communication observations.
    """
    cleaned = clean_text(text)
    fillers = detect_fillers(cleaned)
    hedging = detect_hedging(cleaned)
    vocab = compute_vocabulary_metrics(cleaned)

    observations: List[str] = []
    if fillers["filler_frequency"] > 5.0:
        observations.append(
            f"Noticeable filler frequency ({fillers['filler_frequency']} per 100 words)."
        )
    elif fillers["filler_count"] == 0 and vocab["total_word_count"] > 20:
        observations.append("Clear delivery with zero common filler words detected.")

    if hedging["hedging_count"] > 3:
        observations.append(
            f"Hedging expressions used {hedging['hedging_count']} times; ensure claims remain decisive where appropriate."
        )

    if vocab["long_sentence_count"] >= 2:
        observations.append(
            f"{vocab['long_sentence_count']} sentences contain over 30 words; consider breaking down complex thoughts."
        )

    if vocab["vocabulary_diversity"] < 0.45 and vocab["total_word_count"] > 40:
        observations.append("Word repetition is elevated; consider broadening descriptive terminology.")

    if not observations:
        observations.append("Communication patterns are well-balanced and fluent.")

    return {
        "filler_count": fillers["filler_count"],
        "filler_frequency": fillers["filler_frequency"],
        "filler_word_details": fillers["filler_word_details"],
        "hedging_count": hedging["hedging_count"],
        "hedging_frequency": hedging["hedging_frequency"],
        "hedging_details": hedging["hedging_details"],
        "vocabulary_diversity": vocab["vocabulary_diversity"],
        "unique_word_count": vocab["unique_word_count"],
        "total_word_count": vocab["total_word_count"],
        "average_sentence_length": vocab["average_sentence_length"],
        "long_sentence_count": vocab["long_sentence_count"],
        "readability_information": vocab["readability_information"],
        "communication_observations": observations,
    }


def analyze_delivery_indicators(text: str) -> Dict[str, Any]:
    """
    Analyze observable linguistic delivery indicators.

    Evaluates:
    - Filler frequency
    - Excessive hedging
    - Overly brief / incomplete answer
    - Overly long sentences
    - Repeated phrases

    LIMITATIONS:
    - This is strictly an analysis of text mechanics and delivery patterns.
    - Does NOT measure personality, true confidence, intelligence, or technical truth.

    Args:
        text: Candidate's response.

    Returns:
        Structured output containing detected indicators, counts, explanations,
        and constructive areas for improvement.
    """
    cleaned = clean_text(text)
    fillers = detect_fillers(cleaned)
    hedging = detect_hedging(cleaned)
    vocab = compute_vocabulary_metrics(cleaned)
    repeated_phrases = detect_repeated_phrases(cleaned, n_gram_size=3, threshold=2)

    word_count = vocab["total_word_count"]
    detected_indicators: List[str] = []
    counts: Dict[str, Any] = {
        "word_count": word_count,
        "filler_count": fillers["filler_count"],
        "filler_frequency": fillers["filler_frequency"],
        "hedging_count": hedging["hedging_count"],
        "hedging_frequency": hedging["hedging_frequency"],
        "long_sentence_count": vocab["long_sentence_count"],
        "repeated_phrases_count": len(repeated_phrases),
    }
    explanations: List[str] = []
    potential_areas_for_improvement: List[str] = []

    # 1. Brief response indicator
    if word_count < 25:
        detected_indicators.append("very_short_response")
        explanations.append(
            f"Response contains only {word_count} words, which may lack sufficient elaboration."
        )
        potential_areas_for_improvement.append(
            "Elaborate on specific actions, rationale, and tangible outcomes."
        )

    # 2. Filler word presence
    if fillers["filler_frequency"] > 4.0:
        detected_indicators.append("elevated_filler_usage")
        explanations.append(
            f"High filler frequency ({fillers['filler_frequency']} per 100 words), primarily '{', '.join(fillers['filler_word_details'].keys())}'."
        )
        potential_areas_for_improvement.append(
            "Practice comfortable pauses instead of verbal placeholders such as 'um' or 'like'."
        )

    # 3. Excessive hedging
    if hedging["hedging_count"] >= 3:
        detected_indicators.append("frequent_hedging")
        explanations.append(
            f"Hedging expressions used {hedging['hedging_count']} times ({hedging['hedging_frequency']} per 100 words)."
        )
        potential_areas_for_improvement.append(
            "Frame known facts and past accomplishments decisively; reserve hedging for uncertain future estimates."
        )

    # 4. Long / convoluted sentences
    if vocab["long_sentence_count"] >= 2:
        detected_indicators.append("excessively_long_sentences")
        explanations.append(
            f"{vocab['long_sentence_count']} sentences exceed 30 words, which can challenge verbal tracking."
        )
        potential_areas_for_improvement.append(
            "Break multi-clause thoughts into concise, separate sentences for clearer delivery."
        )

    # 5. Repeated phrases
    if repeated_phrases:
        detected_indicators.append("phrase_repetition")
        phrases_str = ", ".join(f"'{p['phrase']}'" for p in repeated_phrases[:3])
        explanations.append(f"Multiple repeated phrases detected: {phrases_str}.")
        potential_areas_for_improvement.append(
            "Vary transitional phrasing to keep the narrative engaging and forward-moving."
        )

    if not detected_indicators:
        detected_indicators.append("smooth_delivery")
        explanations.append("No adverse delivery indicators detected; concise and steady flow.")

    return {
        "component_name": "Linguistic Delivery Indicators",
        "evaluation_modality": "text_linguistic_indicators",
        "modality_notice": (
            "This delivery evaluation measures observable text indicators only "
            "(filler frequency, hedging phrases, sentence length balance, phrase repetition). "
            "It does NOT evaluate acoustic vocal tone, pitch, pronunciation, volume, or speaking confidence."
        ),
        "detected_indicators": detected_indicators,
        "counts": counts,
        "explanations": explanations,
        "potential_areas_for_improvement": potential_areas_for_improvement,
        "limitations_notice": (
            "Linguistic Delivery Indicators reflect surface text fluency and verbal habits only. "
            "They do not assess confidence, vocal tone, domain competence, or cognitive capabilities."
        )
    }
