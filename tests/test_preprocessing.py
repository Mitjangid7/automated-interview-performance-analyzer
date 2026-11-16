"""
test_preprocessing.py — Unit Tests for Text Preprocessing Module
"""

import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from modules.preprocessing import (
    clean_text,
    normalize_text,
    tokenize_text,
    remove_stopwords,
    extract_sentences,
    extract_paragraphs,
    extract_basic_statistics,
    analyze_sentiment,
    preprocess_answer,
    PROTECTED_TERMS,
)


class TestTextCleaningAndNormalization:
    """Tests for clean_text and normalize_text."""

    def test_clean_text_normal_string(self):
        raw = "   This is a   clean sentence.   "
        expected = "This is a clean sentence."
        assert clean_text(raw) == expected

    def test_clean_text_empty_and_whitespace(self):
        assert clean_text("") == ""
        assert clean_text("   \n\t  ") == ""

    def test_clean_text_none_input(self):
        assert clean_text(None) == ""

    def test_clean_text_preserves_newlines(self):
        raw = "First paragraph.\n\nSecond paragraph."
        cleaned = clean_text(raw)
        assert "First paragraph." in cleaned
        assert "Second paragraph." in cleaned
        assert "\n\n" in cleaned

    def test_normalize_text_lowercasing(self):
        text = "Python and SQL are GREAT Tools!"
        normalized = normalize_text(text, lowercase=True)
        assert normalized == "python and sql are great tools!"

    def test_normalize_text_without_lowercasing(self):
        text = "Keep CaSe intact."
        normalized = normalize_text(text, lowercase=False)
        assert normalized == "Keep CaSe intact."


class TestTokenizationAndStopwords:
    """Tests for tokenize_text and remove_stopwords."""

    def test_tokenize_normal_text(self):
        tokens = tokenize_text("I developed three microservices in Python.")
        assert "developed" in tokens
        assert "microservices" in tokens
        assert "python" in tokens

    def test_tokenize_empty_and_none(self):
        assert tokenize_text("") == []
        assert tokenize_text(None) == []

    def test_tokenize_contractions_and_hyphens(self):
        tokens = tokenize_text("Don't write low-quality code.")
        assert "don't" in tokens or ("don" in tokens and "t" in tokens)
        assert "low-quality" in tokens or "quality" in tokens

    def test_technical_terms_and_negations_preserved_in_stopwords(self):
        tokens = ["i", "do", "not", "like", "inner", "join", "with", "null", "values"]
        filtered = remove_stopwords(tokens)
        # 'not' must be preserved as negation
        assert "not" in filtered
        # SQL keywords must be preserved
        assert "inner" in filtered
        assert "join" in filtered
        assert "null" in filtered
        # common generic stopwords 'i', 'do' should be removed
        assert "i" not in filtered
        assert "do" not in filtered

    def test_remove_stopwords_empty_list(self):
        assert remove_stopwords([]) == []


class TestSentenceAndParagraphExtraction:
    """Tests for sentence and paragraph splitting."""

    def test_extract_sentences_multiple(self):
        text = "I built an API. It was very fast! Did it scale well? Yes, it did."
        sentences = extract_sentences(text)
        assert len(sentences) == 4
        assert sentences[0] == "I built an API."

    def test_extract_sentences_preserves_decimal_numbers(self):
        text = "Our uptime reached 99.9% in Q3. Python 3.12 was used."
        sentences = extract_sentences(text)
        # Should not split 99.9 or 3.12 into separate sentences
        assert len(sentences) == 2
        assert "99.9%" in sentences[0]
        assert "3.12" in sentences[1]

    def test_extract_sentences_empty(self):
        assert extract_sentences("") == []
        assert extract_sentences(None) == []

    def test_extract_paragraphs(self):
        text = "Paragraph one with detail.\n\nParagraph two with summary."
        paragraphs = extract_paragraphs(text)
        assert len(paragraphs) == 2
        assert paragraphs[0] == "Paragraph one with detail."
        assert paragraphs[1] == "Paragraph two with summary."


class TestBasicStatistics:
    """Tests for extract_basic_statistics."""

    def test_basic_statistics_values(self):
        text = "I love Python programming. It is expressive and clean."
        stats = extract_basic_statistics(text)
        assert stats["word_count"] > 0
        assert stats["sentence_count"] == 2
        assert stats["average_sentence_length"] > 0.0
        assert stats["character_count"] > 0
        assert stats["average_word_length"] > 0.0
        assert stats["paragraph_count"] >= 1

    def test_basic_statistics_empty(self):
        stats = extract_basic_statistics("")
        assert stats["word_count"] == 0
        assert stats["sentence_count"] == 0
        assert stats["average_sentence_length"] == 0.0
        assert stats["character_count"] == 0


class TestSentimentAnalysis:
    """Tests for analyze_sentiment."""

    def test_sentiment_positive(self):
        text = "I am extremely proud of our success and excellent collaboration."
        res = analyze_sentiment(text)
        assert res["sentiment_label"] == "Positive"
        assert res["compound"] > 0.05
        assert "positive" in res

    def test_sentiment_negative(self):
        text = "The catastrophic production outage caused severe failure and anger."
        res = analyze_sentiment(text)
        assert res["sentiment_label"] == "Negative"
        assert res["compound"] < -0.05
        assert "negative" in res

    def test_sentiment_neutral_or_empty(self):
        res = analyze_sentiment("")
        assert res["sentiment_label"] == "Neutral"
        assert res["compound"] == 0.0

    def test_sentiment_does_not_affect_competence(self):
        # Verify the descriptive notice is present
        res = analyze_sentiment("Testing sentiment notice.")
        assert "note" in res
        assert "not used directly" in res["note"]


class TestPreprocessAnswerPipeline:
    """Tests for preprocess_answer full wrapper."""

    def test_preprocess_answer_full_structure(self):
        raw = "I designed a PostgreSQL schema. It supported 500 queries per second."
        result = preprocess_answer(raw)
        assert "original_text" in result
        assert "cleaned_text" in result
        assert "normalized_text" in result
        assert "tokens" in result
        assert "filtered_tokens" in result
        assert "sentences" in result
        assert "statistics" in result
        assert "sentiment" in result
        assert result["original_text"] == raw
        assert len(result["sentences"]) == 2

