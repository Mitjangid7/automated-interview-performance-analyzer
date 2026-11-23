"""
test_co3_multilingual.py — Tests for CO3: Multilingual NLP with Cloud AI Integration

Covers:
- Language detection (English, Hindi, Marathi, Gujarati, edge cases)
- Translation routing (English passthrough, non-English → Groq translate)
- API failure handling (key missing, timeout, bad response)
- Original answer preservation
- Scoring weights unchanged
- CO1/CO2 output keys intact in full evaluate_answer() result
- All Groq API calls are mocked — no real network traffic

Expected: 15 tests, all pass.
"""

import os
import sys
import unittest
from typing import Any, Dict
from unittest.mock import MagicMock, patch

# Ensure project root is on sys.path for all test environments
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_detect_langs_result(lang_code: str, prob: float = 0.99):
    """Return a mock langdetect.detect_langs() result list."""
    item = MagicMock()
    item.lang = lang_code
    item.prob = prob
    return [item]


def _make_groq_response(translated_text: str, status_code: int = 200):
    """Return a mock requests.Response for a successful Groq translation call."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": translated_text}}]
    }
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


# ---------------------------------------------------------------------------
# Test Suite
# ---------------------------------------------------------------------------

class TestCO3MultilingualDetection(unittest.TestCase):
    """Tests 1–4: Language detection for supported languages."""

    @patch("langdetect.detect_langs")
    def test_01_english_detection(self, mock_detect):
        """English text → language_code 'en', processing_status 'english_passthrough'."""
        mock_detect.return_value = _make_detect_langs_result("en", 0.99)
        from modules.multilingual import detect_and_process_multilingual
        result = detect_and_process_multilingual("Lists are mutable and tuples are immutable.")
        self.assertEqual(result["language_code"], "en")
        self.assertEqual(result["processing_status"], "english_passthrough")
        self.assertFalse(result["translation_used"])

    @patch("langdetect.detect_langs")
    def test_02_hindi_detection(self, mock_detect):
        """Hindi text → language_code 'hi', detected_language 'Hindi'."""
        mock_detect.return_value = _make_detect_langs_result("hi", 0.97)
        from modules.multilingual import detect_and_process_multilingual
        result = detect_and_process_multilingual("यह एक परीक्षण वाक्य है।")
        self.assertEqual(result["language_code"], "hi")
        self.assertEqual(result["detected_language"], "Hindi")

    @patch("langdetect.detect_langs")
    def test_03_marathi_detection(self, mock_detect):
        """Marathi text → language_code 'mr', detected_language 'Marathi'."""
        mock_detect.return_value = _make_detect_langs_result("mr", 0.95)
        from modules.multilingual import detect_and_process_multilingual
        result = detect_and_process_multilingual("हे एक चाचणी वाक्य आहे.")
        self.assertEqual(result["language_code"], "mr")
        self.assertEqual(result["detected_language"], "Marathi")

    @patch("langdetect.detect_langs")
    def test_04_gujarati_detection(self, mock_detect):
        """Gujarati text → language_code 'gu', detected_language 'Gujarati'."""
        mock_detect.return_value = _make_detect_langs_result("gu", 0.96)
        from modules.multilingual import detect_and_process_multilingual
        result = detect_and_process_multilingual("આ એક પ્રશ્ન છે.")
        self.assertEqual(result["language_code"], "gu")
        self.assertEqual(result["detected_language"], "Gujarati")


class TestCO3EdgeCases(unittest.TestCase):
    """Tests 5–7: Edge cases — empty input, too short, unicode."""

    def test_05_empty_input(self):
        """Empty string → processing_status 'empty', no crash."""
        from modules.multilingual import detect_and_process_multilingual
        result = detect_and_process_multilingual("")
        self.assertIn(result["processing_status"], ("empty",))
        self.assertEqual(result["evaluation_text"], "")
        self.assertFalse(result["translation_used"])

    def test_06_very_short_input(self):
        """Input shorter than MIN_DETECT_LENGTH → 'too_short', English fallback."""
        from modules.multilingual import detect_and_process_multilingual
        result = detect_and_process_multilingual("Hi")  # 2 chars < 5
        self.assertIn(result["processing_status"], ("too_short", "english_passthrough"))
        self.assertFalse(result["translation_used"])
        # Must not crash
        self.assertIn("evaluation_text", result)

    @patch("langdetect.detect_langs")
    def test_07_unicode_text_no_crash(self, mock_detect):
        """Unicode / emoji-rich input → no encoding errors, function completes."""
        mock_detect.return_value = _make_detect_langs_result("en", 0.90)
        from modules.multilingual import detect_and_process_multilingual
        result = detect_and_process_multilingual("Résumé café naïve 日本語 🎯")
        self.assertIn("processing_status", result)
        self.assertIn("evaluation_text", result)


class TestCO3Routing(unittest.TestCase):
    """Tests 8–9: Routing logic — passthrough vs translate."""

    @patch("langdetect.detect_langs")
    def test_08_english_passthrough_unmodified(self, mock_detect):
        """English answers → evaluation_text equals original text, translation_used False."""
        mock_detect.return_value = _make_detect_langs_result("en", 0.99)
        from modules.multilingual import detect_and_process_multilingual
        answer = "Lists are mutable collections stored using square brackets."
        result = detect_and_process_multilingual(answer)
        self.assertEqual(result["evaluation_text"], answer)
        self.assertFalse(result["translation_used"])
        self.assertIsNone(result["translated_text"])

    @patch("requests.post")
    @patch("langdetect.detect_langs")
    def test_09_hindi_translates_to_english(self, mock_detect, mock_post):
        """Hindi text → Groq translate called, translated_text populated, translation_used True."""
        mock_detect.return_value = _make_detect_langs_result("hi", 0.97)
        mock_post.return_value = _make_groq_response("This is a test sentence.")
        from modules.multilingual import detect_and_process_multilingual
        result = detect_and_process_multilingual("यह एक परीक्षण वाक्य है।")
        self.assertEqual(result["processing_status"], "translated")
        self.assertTrue(result["translation_used"])
        self.assertEqual(result["translated_text"], "This is a test sentence.")
        self.assertEqual(result["evaluation_text"], "This is a test sentence.")


class TestCO3APIFailureHandling(unittest.TestCase):
    """Tests 10–12: API failures handled gracefully."""

    @patch("requests.post")
    @patch("langdetect.detect_langs")
    def test_10_translation_api_failure_preserves_original(self, mock_detect, mock_post):
        """When Groq API throws exception → translation_failed, evaluation_text = original."""
        mock_detect.return_value = _make_detect_langs_result("hi", 0.97)
        mock_post.side_effect = Exception("Connection timeout")
        from modules.multilingual import detect_and_process_multilingual
        answer = "यह एक परीक्षण वाक्य है।"
        result = detect_and_process_multilingual(answer)
        self.assertEqual(result["processing_status"], "translation_failed")
        self.assertEqual(result["evaluation_text"], answer)
        self.assertFalse(result["translation_used"])
        self.assertIsNone(result["translated_text"])

    @patch("modules.audio_transcription.get_stt_api_credentials")
    @patch("langdetect.detect_langs")
    def test_11_missing_api_key_graceful_fallback(self, mock_detect, mock_creds):
        """When API key missing → translation_failed, evaluation_text = original, no crash."""
        mock_detect.return_value = _make_detect_langs_result("hi", 0.97)
        mock_creds.return_value = (None, "groq")
        from modules.multilingual import detect_and_process_multilingual
        answer = "यह एक परीक्षण वाक्य है।"
        result = detect_and_process_multilingual(answer)
        self.assertIn(result["processing_status"], ("translation_failed", "no_api_key"))
        self.assertFalse(result["translation_used"])
        # original must be preserved
        self.assertEqual(result["original_text"], answer)

    @patch("langdetect.detect_langs")
    def test_12_low_confidence_fallback_to_english(self, mock_detect):
        """Low confidence detection → low_confidence status, treated as English passthrough."""
        mock_detect.return_value = _make_detect_langs_result("fr", 0.30)  # < threshold
        from modules.multilingual import detect_and_process_multilingual
        answer = "Some ambiguous text"
        result = detect_and_process_multilingual(answer)
        self.assertIn(result["processing_status"], ("low_confidence", "english_passthrough"))
        self.assertFalse(result["translation_used"])


class TestCO3OriginalPreservation(unittest.TestCase):
    """Tests 13–14: Invariant — original_text always equals input."""

    @patch("langdetect.detect_langs")
    def test_13_original_text_preserved_english(self, mock_detect):
        """original_text always equals candidate_answer for English input."""
        mock_detect.return_value = _make_detect_langs_result("en", 0.99)
        from modules.multilingual import detect_and_process_multilingual
        answer = "Object-oriented programming uses classes and objects."
        result = detect_and_process_multilingual(answer)
        self.assertEqual(result["original_text"], answer)

    @patch("requests.post")
    @patch("langdetect.detect_langs")
    def test_14_original_text_preserved_after_translation(self, mock_detect, mock_post):
        """original_text always equals candidate_answer even after successful translation."""
        mock_detect.return_value = _make_detect_langs_result("hi", 0.97)
        mock_post.return_value = _make_groq_response("OOP uses classes and objects.")
        from modules.multilingual import detect_and_process_multilingual
        answer = "ऑब्जेक्ट-ओरिएंटेड प्रोग्रामिंग में कक्षाएं और ऑब्जेक्ट होते हैं।"
        result = detect_and_process_multilingual(answer)
        self.assertEqual(result["original_text"], answer)
        self.assertNotEqual(result["evaluation_text"], answer)  # translated version differs


class TestCO3IntegrationContracts(unittest.TestCase):
    """Test 15: Scoring weights unchanged + CO1/CO2 keys present in evaluate_answer()."""

    def test_15_scoring_weights_and_co1_co2_keys_intact(self):
        """
        Scoring weights remain 40/25/20/15.
        evaluate_answer() returns semantic_analysis, sentiment_analysis,
        information_extraction AND multilingual_analysis keys.
        """
        from config.config import SCORING_WEIGHTS
        self.assertAlmostEqual(SCORING_WEIGHTS.get("semantic_relevance", 0), 0.40, places=4)
        self.assertAlmostEqual(SCORING_WEIGHTS.get("answer_structure", 0), 0.25, places=4)
        self.assertAlmostEqual(SCORING_WEIGHTS.get("communication", 0), 0.20, places=4)
        self.assertAlmostEqual(SCORING_WEIGHTS.get("delivery_indicators", 0), 0.15, places=4)

        from modules.scoring import evaluate_answer
        result = evaluate_answer(
            "TECH001",
            "Lists are mutable and use square brackets. Tuples are immutable.",
            candidate_level="final_year",
        )
        self.assertIn("semantic_analysis", result)
        self.assertIn("sentiment_analysis", result)
        self.assertIn("information_extraction", result)
        self.assertIn("multilingual_analysis", result)

        ml = result["multilingual_analysis"]
        self.assertIn("processing_status", ml)
        self.assertIn("evaluation_text", ml)


if __name__ == "__main__":
    unittest.main(verbosity=2)
