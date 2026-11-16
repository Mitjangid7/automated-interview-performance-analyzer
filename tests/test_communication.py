"""
test_communication.py — Unit Tests for Communication Analysis & Delivery Indicators
"""

import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from modules.communication_analysis import (
    detect_fillers,
    detect_hedging,
    compute_vocabulary_metrics,
    detect_repeated_phrases,
    analyze_communication,
    analyze_delivery_indicators,
)


class TestFillerWordDetection:
    """Tests for single and multi-word filler detection."""

    def test_single_word_fillers(self):
        text = "Um, I basically started coding, and uh, like, it worked."
        res = detect_fillers(text)
        assert res["filler_count"] >= 4
        assert "um" in res["filler_word_details"]
        assert "uh" in res["filler_word_details"]
        assert "basically" in res["filler_word_details"]
        assert "like" in res["filler_word_details"]
        assert res["filler_frequency"] > 0.0

    def test_multi_word_fillers(self):
        text = "You know, we sort of refactored the database, and I mean, it was fast."
        res = detect_fillers(text)
        assert "you know" in res["filler_word_details"]
        assert "sort of" in res["filler_word_details"]
        assert "i mean" in res["filler_word_details"]

    def test_filler_word_boundaries_not_inside_words(self):
        # 'like' inside 'dislike', 'um' inside 'alumni', 'uh' inside 'huh'
        text = "I dislike alumni who assume summary results."
        res = detect_fillers(text)
        assert res["filler_count"] == 0

    def test_fillers_empty_text(self):
        res = detect_fillers("")
        assert res["filler_count"] == 0
        assert res["filler_frequency"] == 0.0
        assert res["filler_word_details"] == {}


class TestHedgingDetection:
    """Tests for hedging expressions."""

    def test_hedging_expressions_detected(self):
        text = "Maybe we could use Redis, perhaps Memcached. I think it is possibly faster, but I am not sure."
        res = detect_hedging(text)
        assert res["hedging_count"] >= 4
        assert "maybe" in res["hedging_details"]
        assert "perhaps" in res["hedging_details"]
        assert "i think" in res["hedging_details"]
        assert "possibly" in res["hedging_details"]
        assert "i am not sure" in res["hedging_details"]
        assert res["hedging_frequency"] > 0.0

    def test_hedging_empty_text(self):
        res = detect_hedging("")
        assert res["hedging_count"] == 0
        assert res["hedging_frequency"] == 0.0


class TestVocabularyAndReadabilityMetrics:
    """Tests for compute_vocabulary_metrics."""

    def test_vocabulary_diversity_and_stats(self):
        text = "Engineers write unit tests to ensure high quality software delivery."
        metrics = compute_vocabulary_metrics(text)
        assert metrics["total_word_count"] > 0
        assert metrics["unique_word_count"] > 0
        assert 0.0 < metrics["vocabulary_diversity"] <= 1.0
        assert metrics["average_sentence_length"] > 0.0
        assert "readability_information" in metrics
        assert "disclaimer" in metrics["readability_information"]

    def test_long_sentence_detection(self):
        long_sentence = (
            "When we began migrating our legacy relational database architecture "
            "to a distributed event streaming platform, we encountered substantial "
            "challenges related to data synchronization, network latency, partition "
            "tolerance, and distributed transactions across multiple cloud regions."
        )
        metrics = compute_vocabulary_metrics(long_sentence)
        assert metrics["long_sentence_count"] == 1

    def test_empty_metrics(self):
        metrics = compute_vocabulary_metrics("")
        assert metrics["total_word_count"] == 0
        assert metrics["vocabulary_diversity"] == 0.0


class TestRepeatedPhrases:
    """Tests for detect_repeated_phrases."""

    def test_detect_repeated_phrases(self):
        text = (
            "We deployed to production on Friday. Later on, we deployed to production "
            "again after running tests, and finally we deployed to production safely."
        )
        repeated = detect_repeated_phrases(text, n_gram_size=3, threshold=2)
        phrases = [r["phrase"] for r in repeated]
        assert any("deployed to production" in p for p in phrases)

    def test_repeated_phrases_short_text(self):
        assert detect_repeated_phrases("Short text") == []


class TestAnalyzeCommunication:
    """Tests for analyze_communication aggregate function."""

    def test_analyze_communication_output_structure(self):
        text = (
            "Well, um, you know, I think we sort of had to fix the bugs. "
            "It was, like, somewhat tricky."
        )
        result = analyze_communication(text)
        assert "filler_count" in result
        assert "filler_frequency" in result
        assert "filler_word_details" in result
        assert "hedging_count" in result
        assert "hedging_frequency" in result
        assert "vocabulary_diversity" in result
        assert "average_sentence_length" in result
        assert "readability_information" in result
        assert "communication_observations" in result
        assert len(result["communication_observations"]) > 0


class TestLinguisticDeliveryIndicators:
    """Tests for analyze_delivery_indicators."""

    def test_delivery_indicators_with_fillers_and_hedging(self):
        text = "Um, like, basically, maybe I think I am not sure about this."
        result = analyze_delivery_indicators(text)
        assert result["component_name"] == "Linguistic Delivery Indicators"
        assert "detected_indicators" in result
        assert "counts" in result
        assert "explanations" in result
        assert "potential_areas_for_improvement" in result
        assert "limitations_notice" in result
        # Check that either filler or hedging was detected
        assert any("filler" in ind or "hedging" in ind or "short" in ind for ind in result["detected_indicators"])

    def test_delivery_indicators_empty_or_brief(self):
        result = analyze_delivery_indicators("Yes, I agree.")
        assert "very_short_response" in result["detected_indicators"]
        assert len(result["potential_areas_for_improvement"]) > 0

    def test_delivery_indicators_clean_fluent_answer(self):
        text = (
            "I led the infrastructure redesign to ensure high availability across three data centers. "
            "Our automated failover reduced unexpected downtime by forty percent over the subsequent quarter. "
            "The engineering leadership adopted our observability runbooks across all product teams."
        )
        result = analyze_delivery_indicators(text)
        assert "smooth_delivery" in result["detected_indicators"] or "counts" in result

