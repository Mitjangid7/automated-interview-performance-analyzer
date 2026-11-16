"""
preprocessing.py — Text Preprocessing and Basic Linguistic Analysis Module

Provides reusable, robust text preprocessing functions:
- Cleaning and normalization
- Tokenization (with graceful fallback if NLTK data is absent)
- Stopword removal with preservation of technical terms and negations
- Sentence and paragraph extraction
- Basic text statistics computation
- VADER sentiment analysis with graceful degradation
"""

import math
import re
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

# Try importing NLTK optional resources; define fallbacks if unavailable.
try:
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    # Test if punkt / punkt_tab is downloaded
    _NLTK_TOKENIZE_AVAILABLE = True
except (ImportError, LookupError):
    _NLTK_TOKENIZE_AVAILABLE = False

# Try importing VADER Sentiment
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _VADER_ANALYZER = SentimentIntensityAnalyzer()
    _VADER_AVAILABLE = True
except (ImportError, Exception):
    _VADER_ANALYZER = None
    _VADER_AVAILABLE = False

# Technical terms, SQL/programming keywords, and negations that MUST NOT be removed
# during stopword filtering.
PROTECTED_TERMS: Set[str] = {
    # Negations
    "not", "no", "nor", "neither", "never", "none", "without", "hardly", "barely",
    # Technical & SQL terms that could overlap with common words
    "in", "is", "as", "for", "while", "with", "from", "where", "into", "group", "by",
    "order", "having", "join", "left", "right", "inner", "outer", "all", "and", "or",
    "between", "like", "null", "true", "false", "class", "def", "return", "self", "import"
}

# Standard English stopwords (curated subset without protected terms)
STANDARD_STOPWORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "am", "an", "any", "are",
    "aren't", "at", "be", "because", "been", "before", "being", "below", "between",
    "both", "but", "by", "can't", "cannot", "could", "couldn't", "did", "didn't",
    "do", "does", "doesn't", "doing", "don't", "down", "during", "each", "few",
    "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having", "he",
    "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him",
    "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if",
    "into", "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more",
    "most", "mustn't", "my", "myself", "off", "on", "once", "only", "other",
    "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan't",
    "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
    "while", "who", "who's", "whom", "why", "why's", "won't", "would", "wouldn't",
    "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself",
    "yourselves"
} - PROTECTED_TERMS


def clean_text(text: Any) -> str:
    """
    Remove unnecessary whitespace and standardize formatting while preserving
    sentence boundaries and punctuation.

    Args:
        text: Raw text string (or None/other types safely handled).

    Returns:
        Cleaned string with trimmed whitespace and collapsed inner whitespace.
    """
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)

    # Normalize carriage returns and tabs
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\t", " ")
    # Collapse multiple inline spaces but preserve newlines for paragraph counting
    lines = [re.sub(r"[ ]+", " ", line).strip() for line in text.split("\n")]
    cleaned = "\n".join(lines).strip()
    return cleaned


def normalize_text(text: Any, lowercase: bool = True) -> str:
    """
    Normalize text by cleaning and optionally lowercasing, while keeping
    essential alphanumeric and punctuation intact.

    Args:
        text: Raw input text.
        lowercase: Whether to convert text to lowercase. Defaults to True.

    Returns:
        Normalized text string.
    """
    cleaned = clean_text(text)
    if lowercase:
        cleaned = cleaned.lower()
    return cleaned


def extract_sentences(text: Any) -> List[str]:
    """
    Split text into individual sentences reliably.
    Uses NLTK's sent_tokenize if available and functioning; otherwise falls back
    to regex-based boundary splitting that preserves decimal points, abbreviations,
    and version numbers (e.g., 3.10, Python 3.x).

    Args:
        text: Input text.

    Returns:
        List of non-empty sentence strings.
    """
    cleaned = clean_text(text)
    if not cleaned:
        return []

    # Attempt NLTK tokenizer first
    if _NLTK_TOKENIZE_AVAILABLE:
        try:
            sentences = sent_tokenize(cleaned)
            if sentences:
                return [s.strip() for s in sentences if s.strip()]
        except Exception:
            pass

    # Fallback sentence boundary regex
    # Split on period, exclamation, or question mark followed by whitespace or end of line,
    # or double newlines (paragraphs). Negative lookbehind ensures numbers like 3.10 aren't split.
    pattern = r'(?<!\b[0-9])(?<!\b[A-Za-z])(?<=[.!?])\s+(?=[A-Z0-9"\'])|\n\s*\n'
    raw_sentences = re.split(pattern, cleaned)
    sentences = [s.strip().replace("\n", " ") for s in raw_sentences if s and s.strip()]
    return [re.sub(r"\s+", " ", s) for s in sentences if s]


def tokenize_text(text: Any, lowercase: bool = True, preserve_punct: bool = False) -> List[str]:
    """
    Tokenize text into words/terms. Uses a robust regex-based tokenizer that
    preserves hyphenated words and contractions, falling back seamlessly.

    Args:
        text: Input text string.
        lowercase: Whether to lowercase tokens. Defaults to True.
        preserve_punct: Whether to keep standalone punctuation as tokens.

    Returns:
        List of tokens.
    """
    cleaned = clean_text(text)
    if not cleaned:
        return []

    if lowercase:
        cleaned = cleaned.lower()

    if preserve_punct:
        # Matches words (including contractions/hyphenated words) or individual punctuation
        tokens = re.findall(r"\b[\w'-]+\b|[^\w\s]", cleaned)
    else:
        # Matches alphanumeric words, contractions (e.g. don't), and hyphenated terms
        tokens = re.findall(r"\b[a-zA-Z0-9]+(?:['_-][a-zA-Z0-9]+)*\b", cleaned)

    return tokens


def remove_stopwords(tokens: List[str], custom_protected: Optional[Set[str]] = None) -> List[str]:
    """
    Remove common English stopwords while carefully preserving domain-specific
    technical terms, SQL keywords, and negations.

    Args:
        tokens: List of word tokens.
        custom_protected: Additional terms that should never be removed.

    Returns:
        Filtered list of tokens.
    """
    if not tokens:
        return []

    protected = PROTECTED_TERMS
    if custom_protected:
        protected = protected | {t.lower() for t in custom_protected}

    filtered = [
        token for token in tokens
        if token.lower() not in STANDARD_STOPWORDS or token.lower() in protected
    ]
    return filtered


def extract_paragraphs(text: Any) -> List[str]:
    """
    Extract non-empty paragraphs from text.

    Args:
        text: Input text string.

    Returns:
        List of paragraph strings.
    """
    if text is None:
        return []
    if not isinstance(text, str):
        text = str(text)

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return paragraphs


def extract_basic_statistics(text: Any) -> Dict[str, Any]:
    """
    Extract foundational descriptive statistics from the candidate text:
    - word_count
    - sentence_count
    - average_sentence_length (in words)
    - character_count (excluding external whitespace)
    - average_word_length
    - paragraph_count

    Args:
        text: Input text string.

    Returns:
        Dictionary of computed statistics.
    """
    cleaned = clean_text(text)
    if not cleaned:
        return {
            "word_count": 0,
            "sentence_count": 0,
            "average_sentence_length": 0.0,
            "character_count": 0,
            "average_word_length": 0.0,
            "paragraph_count": 0,
        }

    tokens = tokenize_text(cleaned, lowercase=False, preserve_punct=False)
    sentences = extract_sentences(cleaned)
    paragraphs = extract_paragraphs(cleaned)

    word_count = len(tokens)
    sentence_count = len(sentences)
    paragraph_count = max(1, len(paragraphs)) if cleaned else 0
    character_count = len(re.sub(r"\s", "", cleaned))

    avg_sentence_len = round(word_count / sentence_count, 2) if sentence_count > 0 else 0.0
    total_token_chars = sum(len(t) for t in tokens)
    avg_word_len = round(total_token_chars / word_count, 2) if word_count > 0 else 0.0

    return {
        "word_count": word_count,
        "sentence_count": sentence_count,
        "average_sentence_length": avg_sentence_len,
        "character_count": character_count,
        "average_word_length": avg_word_len,
        "paragraph_count": paragraph_count,
    }


def analyze_sentiment(text: Any) -> Dict[str, Any]:
    """
    Analyze sentiment using VADER sentiment analysis.

    IMPORTANT ARCHITECTURAL NOTE:
    Sentiment is contextual and does NOT indicate interview performance or competence.
    It is computed purely as an observational descriptive feature and does not directly
    contribute to the final interview evaluation score.

    Args:
        text: Input text string.

    Returns:
        Dictionary containing positive, negative, neutral, compound scores and label.
    """
    cleaned = clean_text(text)
    if not cleaned or not _VADER_AVAILABLE or _VADER_ANALYZER is None:
        status_note = "ok" if cleaned else "empty_text"
        if not _VADER_AVAILABLE:
            status_note = "vader_unavailable"

        return {
            "positive": 0.0,
            "negative": 0.0,
            "neutral": 1.0 if cleaned else 0.0,
            "compound": 0.0,
            "sentiment_label": "Neutral",
            "status": status_note,
            "note": "Sentiment is observational and not used directly as a scoring metric."
        }

    try:
        scores = _VADER_ANALYZER.polarity_scores(cleaned)
        compound = scores.get("compound", 0.0)

        if compound >= 0.05:
            label = "Positive"
        elif compound <= -0.05:
            label = "Negative"
        else:
            label = "Neutral"

        return {
            "positive": round(scores.get("pos", 0.0), 3),
            "negative": round(scores.get("neg", 0.0), 3),
            "neutral": round(scores.get("neu", 0.0), 3),
            "compound": round(compound, 3),
            "sentiment_label": label,
            "status": "success",
            "note": "Sentiment is observational and not used directly as a scoring metric."
        }
    except Exception as e:
        return {
            "positive": 0.0,
            "negative": 0.0,
            "neutral": 1.0,
            "compound": 0.0,
            "sentiment_label": "Neutral",
            "status": f"error: {str(e)}",
            "note": "Sentiment computation failed gracefully."
        }


def preprocess_answer(text: Any) -> Dict[str, Any]:
    """
    Full preprocessing pipeline for an interview answer.
    Preserves original text and provides clean tokens, sentences, and statistics.

    Args:
        text: Candidate's raw response.

    Returns:
        Structured dictionary for downstream modules.
    """
    raw_text = "" if text is None else str(text)
    cleaned = clean_text(raw_text)
    normalized = normalize_text(cleaned)
    tokens = tokenize_text(cleaned, lowercase=True)
    filtered_tokens = remove_stopwords(tokens)
    sentences = extract_sentences(cleaned)
    stats = extract_basic_statistics(cleaned)
    sentiment = analyze_sentiment(cleaned)

    return {
        "original_text": raw_text,
        "cleaned_text": cleaned,
        "normalized_text": normalized,
        "tokens": tokens,
        "filtered_tokens": filtered_tokens,
        "sentences": sentences,
        "statistics": stats,
        "sentiment": sentiment,
    }
