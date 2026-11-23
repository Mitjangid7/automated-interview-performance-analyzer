"""
test_co2_sentiment_extraction.py — CO2 Test Suite
Sentiment Analysis & Information Extraction

Covers:
  1.  Positive sentiment
  2.  Negative sentiment
  3.  Neutral sentiment
  4.  Mixed sentiment
  5.  Empty / very short response
  6.  Technical answer with neutral wording
  7.  Keyword extraction
  8.  Evidence extraction
  9.  Missing-concept identification
  10. No fabricated information
"""

import pytest
from modules.preprocessing import analyze_sentiment
from modules.semantic_analysis import extract_information


# ── Sentinel question stub (TECH001-like) for extraction tests ────────────────
_TECH001_STUB = {
    "question_id": "TECH001",
    "question": "What is the difference between a list and a tuple in Python?",
    "reference_answer": (
        "Lists are mutable sequences while tuples are immutable. "
        "Lists use square brackets and tuples use parentheses. "
        "Tuples are hashable and can be used as dictionary keys."
    ),
    "essential_key_points": [
        "Lists are mutable; tuples are immutable",
        "Syntax differences: square brackets for lists and parentheses for tuples",
        "Tuples are hashable (can be dictionary keys or set elements); lists are unhashable",
    ],
    "supporting_key_points": [],
    "optional_key_points": [],
    "expected_keywords": ["mutable", "immutable", "hashable", "tuple", "list"],
    "concept_synonyms": {
        "Lists are mutable; tuples are immutable": ["mutable", "immutable", "can be modified", "cannot be modified"],
        "Syntax differences: square brackets for lists and parentheses for tuples": ["square brackets", "parentheses", "[]", "()"],
        "Tuples are hashable (can be dictionary keys or set elements); lists are unhashable": [
            "hashable", "unhashable", "dictionary keys", "dict keys", "set elements", "hash",
        ],
    },
}


# ── 1. Positive Sentiment ─────────────────────────────────────────────────────
class TestPositiveSentiment:
    def test_positive_label(self):
        text = "I am extremely proud of our excellent project outcome and successful delivery."
        res = analyze_sentiment(text)
        assert res["sentiment_label"] == "Positive"
        assert res["compound"] >= 0.05
        assert res["positive"] > res["negative"]

    def test_positive_scores_in_range(self):
        text = "I love building scalable, high-impact software systems."
        res = analyze_sentiment(text)
        assert 0.0 <= res["positive"] <= 1.0
        assert 0.0 <= res["negative"] <= 1.0
        assert 0.0 <= res["neutral"] <= 1.0
        assert -1.0 <= res["compound"] <= 1.0


# ── 2. Negative Sentiment ─────────────────────────────────────────────────────
class TestNegativeSentiment:
    def test_negative_label(self):
        text = "The catastrophic outage caused severe data loss and complete failure."
        res = analyze_sentiment(text)
        assert res["sentiment_label"] == "Negative"
        assert res["compound"] <= -0.05

    def test_negative_does_not_indicate_poor_performance(self):
        """IMPORTANT: negative sentiment must carry an interview-context note, not alter score."""
        text = "Our database crashed badly, causing major production downtime and angry users."
        res = analyze_sentiment(text)
        assert res["sentiment_label"] == "Negative"
        # The note must remind users sentiment is NOT a scoring metric
        assert "not used directly" in res.get("note", "").lower()


# ── 3. Neutral Sentiment ─────────────────────────────────────────────────────
class TestNeutralSentiment:
    def test_neutral_label_on_empty(self):
        res = analyze_sentiment("")
        assert res["sentiment_label"] == "Neutral"
        assert res["compound"] == 0.0

    def test_neutral_on_factual_definition(self):
        text = "A list is a mutable sequence. A tuple is an immutable sequence."
        res = analyze_sentiment(text)
        # Factual technical language should be neutral or near-neutral
        assert res["compound"] < 0.5  # not strongly positive
        assert "sentiment_label" in res


# ── 4. Mixed Sentiment ───────────────────────────────────────────────────────
class TestMixedSentiment:
    def test_mixed_response(self):
        text = (
            "The project was initially a disaster with terrible bugs. "
            "However, we fixed everything and delivered an excellent product."
        )
        res = analyze_sentiment(text)
        # Mixed — compound should be between extremes
        assert -1.0 <= res["compound"] <= 1.0
        assert res["positive"] > 0.0
        assert res["negative"] > 0.0
        assert res["sentiment_label"] in ("Positive", "Negative", "Neutral")

    def test_mixed_all_scores_present(self):
        text = "The deadline was stressful but the final result was outstanding."
        res = analyze_sentiment(text)
        for key in ("positive", "negative", "neutral", "compound", "sentiment_label", "status"):
            assert key in res


# ── 5. Empty / Very Short Response ───────────────────────────────────────────
class TestEdgeCases:
    def test_empty_string(self):
        res = analyze_sentiment("")
        assert res["sentiment_label"] == "Neutral"
        assert res["compound"] == 0.0
        assert res["positive"] == 0.0

    def test_single_word(self):
        res = analyze_sentiment("okay")
        assert "sentiment_label" in res
        assert res["status"] in ("success", "ok", "vader_unavailable")

    def test_very_short_technical(self):
        res = analyze_sentiment("Mutable list.")
        assert "compound" in res


# ── 6. Technical Answer with Neutral Wording ─────────────────────────────────
class TestTechnicalNeutralSentiment:
    def test_technical_answer_does_not_penalize_neutral(self):
        text = (
            "INNER JOIN returns rows where the join condition is met in both tables. "
            "LEFT JOIN returns all rows from the left table and NULL for unmatched right rows."
        )
        res = analyze_sentiment(text)
        # Technical language should be neutral or mildly positive — NOT force-labelled bad
        assert res["sentiment_label"] in ("Neutral", "Positive")
        assert "not used directly" in res.get("note", "").lower()

    def test_technical_answer_has_all_fields(self):
        text = "Overfitting occurs when the model memorizes training data and fails to generalize."
        res = analyze_sentiment(text)
        for key in ("positive", "negative", "neutral", "compound", "sentiment_label", "note", "status"):
            assert key in res


# ── 7. Keyword Extraction ─────────────────────────────────────────────────────
class TestKeywordExtraction:
    def test_keywords_extracted_from_candidate_text(self):
        answer = "Lists are mutable and tuples are immutable. Tuples are hashable."
        res = extract_information(answer, _TECH001_STUB)
        keywords = res["extracted_keywords"]
        assert isinstance(keywords, list)
        # At least one domain term should be identified
        assert any(kw in ("mutable", "immutable", "hashable", "tuple", "list") for kw in keywords)

    def test_keywords_not_fabricated(self):
        """Keywords must only come from the actual candidate text."""
        answer = "Lists are mutable."
        res = extract_information(answer, _TECH001_STUB)
        keywords = res["extracted_keywords"]
        answer_lower = answer.lower()
        for kw in keywords:
            assert kw.lower() in answer_lower, (
                f"Fabricated keyword '{kw}' not present in candidate answer"
            )

    def test_no_keywords_from_empty_answer(self):
        res = extract_information("", _TECH001_STUB)
        assert res["extracted_keywords"] == []


# ── 8. Evidence Extraction ────────────────────────────────────────────────────
class TestEvidenceExtraction:
    def test_evidence_sentences_are_from_candidate_text(self):
        answer = "Lists are mutable and can be modified. Tuples are immutable and hashable."
        res = extract_information(answer, _TECH001_STUB)
        candidate_sentences = {s.strip() for s in answer.split(".") if s.strip()}
        for ev in res["supporting_evidence"]:
            # Each evidence sentence must be a substring of / present in the answer
            assert any(ev.strip() in answer or answer_sent in ev
                       for answer_sent in candidate_sentences), (
                f"Evidence sentence not from candidate answer: '{ev}'"
            )

    def test_evidence_non_empty_for_good_answer(self):
        answer = (
            "Lists are mutable sequences. Tuples are immutable. "
            "Tuples are hashable and can be used as dictionary keys."
        )
        res = extract_information(answer, _TECH001_STUB)
        assert len(res["supporting_evidence"]) > 0


# ── 9. Missing-Concept Identification ────────────────────────────────────────
class TestMissingConceptIdentification:
    def test_hashability_missing_when_not_mentioned(self):
        answer = "Lists are mutable. Tuples are immutable. Lists use brackets, tuples use parentheses."
        res = extract_information(answer, _TECH001_STUB)
        hash_concept = "Tuples are hashable (can be dictionary keys or set elements); lists are unhashable"
        assert hash_concept in res["missing_concepts"], (
            f"Expected hashability in missing_concepts. Got: {res['missing_concepts']}"
        )

    def test_no_missing_when_all_covered(self):
        answer = (
            "Lists are mutable while tuples are immutable. "
            "Lists use square brackets and tuples use parentheses. "
            "Tuples are hashable and can be used as dictionary keys."
        )
        res = extract_information(answer, _TECH001_STUB)
        assert res["missing_concepts"] == [], (
            f"All concepts covered but missing_concepts = {res['missing_concepts']}"
        )


# ── 10. No Fabricated Information ────────────────────────────────────────────
class TestNoFabricatedInformation:
    def test_extraction_note_states_traceability(self):
        answer = "Lists are mutable. Tuples are immutable."
        res = extract_information(answer, _TECH001_STUB)
        note = res.get("extraction_note", "")
        assert "traceable" in note.lower() or "fabricated" in note.lower()

    def test_identified_concepts_have_evidence_from_answer(self):
        answer = "Lists are mutable and can be changed. Tuples are immutable."
        res = extract_information(answer, _TECH001_STUB)
        answer_lower = answer.lower()
        for ic in res["identified_concepts"]:
            ev = ic.get("evidence_sentence", "")
            if ev:
                assert ev.lower() in answer_lower or any(
                    tok in answer_lower for tok in ev.lower().split()[:3]
                ), f"Evidence sentence not in candidate answer: '{ev}'"

    def test_missing_key_present_in_output(self):
        res = extract_information("Random words here.", _TECH001_STUB)
        assert "missing_concepts" in res
        assert "extracted_keywords" in res
        assert "identified_concepts" in res
        assert "supporting_evidence" in res
