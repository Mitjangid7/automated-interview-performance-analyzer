"""
multilingual.py — CO3: Multilingual NLP with Cloud AI Integration

Provides:
- Language detection via langdetect (offline, deterministic, 55 languages)
- English translation via Groq LLaMA chat completions (cloud AI)
- Multilingual routing: English unchanged, non-English → translate → existing pipeline
- Preserves original text, exposes translated text for display
- Never exposes or hardcodes API keys
"""

import os
import re
from typing import Any, Dict, Optional, Tuple

# ---------------------------------------------------------------------------
# Language name map (ISO 639-1 → human-readable)
# ---------------------------------------------------------------------------
SUPPORTED_LANG_NAMES: Dict[str, str] = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
    "gu": "Gujarati",
    "ta": "Tamil",
    "te": "Telugu",
    "bn": "Bengali",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi",
    "ur": "Urdu",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "zh-cn": "Chinese (Simplified)",
    "zh-tw": "Chinese (Traditional)",
    "ar": "Arabic",
    "ja": "Japanese",
    "ko": "Korean",
    "pt": "Portuguese",
    "it": "Italian",
    "ru": "Russian",
    "pl": "Polish",
    "nl": "Dutch",
    "sv": "Swedish",
    "da": "Danish",
    "fi": "Finnish",
    "no": "Norwegian",
    "tr": "Turkish",
    "id": "Indonesian",
    "ms": "Malay",
    "th": "Thai",
    "vi": "Vietnamese",
}

# Minimum character length for reliable language detection
MIN_DETECT_LENGTH = 5

# Confidence threshold below which we fall back to English passthrough
MIN_CONFIDENCE_THRESHOLD = 0.50

# Groq model used for translation (fastest, free tier)
GROQ_TRANSLATE_MODEL = "llama-3.1-8b-instant"
GROQ_TRANSLATE_MODELS = [
    "llama-3.1-8b-instant",
    "qwen/qwen3.8-27b",
]

# Request timeout for Groq translation API (seconds)
GROQ_TIMEOUT_SECONDS = 15


# ---------------------------------------------------------------------------
# Language Detection
# ---------------------------------------------------------------------------

def detect_language(text: str) -> Dict[str, Any]:
    """
    Detect the language of *text* using langdetect with confidence scoring.

    Returns a dict with keys:
        language_code  : str  — ISO 639-1 code (e.g. "en", "hi")
        language_name  : str  — Human-readable name (e.g. "English", "Hindi")
        confidence     : float — 0.0–1.0 (probability from langdetect)
        status         : str  — "detected" | "low_confidence" | "too_short" | "failed"
        note           : str  — Human-readable explanation
    """
    stripped = text.strip()

    # Empty / too short
    if len(stripped) < MIN_DETECT_LENGTH:
        return {
            "language_code": "en",
            "language_name": "English",
            "confidence": 0.0,
            "status": "too_short",
            "note": f"Text too short ({len(stripped)} chars) for reliable detection; defaulting to English.",
        }

    try:
        from langdetect import detect_langs
        from langdetect import DetectorFactory
        # Seed for determinism
        DetectorFactory.seed = 42

        results = detect_langs(stripped)
        if not results:
            return _fallback_detection("langdetect returned no results")

        top = results[0]
        lang_code: str = top.lang
        confidence: float = float(top.prob)

        lang_name = SUPPORTED_LANG_NAMES.get(lang_code, lang_code.upper())

        if confidence < MIN_CONFIDENCE_THRESHOLD:
            return {
                "language_code": "en",
                "language_name": "English",
                "confidence": confidence,
                "status": "low_confidence",
                "note": (
                    f"Detected '{lang_name}' with low confidence ({confidence:.2f}); "
                    "defaulting to English passthrough for reliability."
                ),
            }

        return {
            "language_code": lang_code,
            "language_name": lang_name,
            "confidence": confidence,
            "status": "detected",
            "note": f"Detected {lang_name} (code: {lang_code}) with confidence {confidence:.2f}.",
        }

    except ImportError:
        return _fallback_detection("langdetect library not installed")
    except Exception as exc:
        return _fallback_detection(f"Detection error: {exc}")


def _fallback_detection(reason: str) -> Dict[str, Any]:
    """Return a safe English-fallback detection result."""
    return {
        "language_code": "en",
        "language_name": "English",
        "confidence": 0.0,
        "status": "failed",
        "note": f"Language detection failed ({reason}); defaulting to English.",
    }


# ---------------------------------------------------------------------------
# Translation via Groq LLaMA (Cloud AI)
# ---------------------------------------------------------------------------

def translate_to_english_groq(
    text: str,
    source_lang_code: str,
    source_lang_name: str,
) -> Dict[str, Any]:
    """
    Translate *text* to English using Groq LLaMA (cloud AI).

    Reads the Groq API key via get_stt_api_credentials() — never hardcodes it.

    Returns a dict with keys:
        translated_text : str  — English translation (or original on failure)
        status          : str  — "translated" | "no_api_key" | "api_error" | "empty_response"
        model_used      : str  — GROQ_TRANSLATE_MODEL
        cloud_service   : str  — "Groq LLaMA (llama-3.1-8b-instant)"
        error           : Optional[str] — error message if applicable
    """
    cloud_service = f"Groq LLaMA ({GROQ_TRANSLATE_MODEL})"

    # Resolve credentials safely
    api_key: Optional[str] = None
    try:
        from modules.audio_transcription import get_stt_api_credentials
        key, provider = get_stt_api_credentials()
        if key and provider == "groq":
            api_key = key
    except Exception as exc:
        pass  # will be caught below as "no_api_key"

    if not api_key:
        return {
            "translated_text": text,
            "status": "no_api_key",
            "model_used": GROQ_TRANSLATE_MODEL,
            "cloud_service": cloud_service,
            "error": "Groq API key not found; translation skipped.",
        }

    # Build translation prompt
    prompt = (
        f"Translate the following {source_lang_name} text to English. "
        f"Return ONLY the translated text, nothing else:\n\n{text}"
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    import requests
    last_err = None
    for model_name in GROQ_TRANSLATE_MODELS:
        cloud_service = f"Groq ({model_name})"
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 1024,
        }

        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=GROQ_TIMEOUT_SECONDS,
            )
            if response.status_code == 404 and "model" in response.text.lower():
                last_err = response.text
                continue

            response.raise_for_status()
            data = response.json()
            translated = data["choices"][0]["message"]["content"].strip()
            if not translated:
                return {
                    "translated_text": text,
                    "status": "empty_response",
                    "model_used": model_name,
                    "cloud_service": cloud_service,
                    "error": "Groq returned an empty translation.",
                }
            return {
                "translated_text": translated,
                "status": "translated",
                "model_used": model_name,
                "cloud_service": cloud_service,
                "error": None,
            }
        except Exception as exc:
            last_err = str(exc)
            if isinstance(exc, requests.exceptions.HTTPError) and exc.response is not None and exc.response.status_code == 404:
                continue
            return {
                "translated_text": text,
                "status": "api_error",
                "model_used": model_name,
                "cloud_service": cloud_service,
                "error": str(exc),
            }

    return {
        "translated_text": text,
        "status": "api_error",
        "model_used": GROQ_TRANSLATE_MODEL,
        "cloud_service": f"Groq ({GROQ_TRANSLATE_MODEL})",
        "error": last_err or "No translation model responded successfully.",
    }


# ---------------------------------------------------------------------------
# Main CO3 Entry Point
# ---------------------------------------------------------------------------

def detect_and_process_multilingual(candidate_answer: str) -> Dict[str, Any]:
    """
    Main CO3 entry point called from scoring.py evaluate_answer().

    Flow:
        1. Detect language of candidate_answer.
        2. If English (or fallback): return passthrough — existing pipeline unchanged.
        3. If non-English: call Groq LLaMA for translation.
           - On success: evaluation_text = translated English text.
           - On failure: evaluation_text = original (preserve, don't fabricate).

    Returns dict with keys:
        original_text        : str  — always equals candidate_answer
        detected_language    : str  — human-readable language name
        language_code        : str  — ISO 639-1 code
        detection_confidence : float
        evaluation_text      : str  — text to pass to analyze_semantics()
        translation_used     : bool
        translated_text      : Optional[str]
        processing_status    : str  — see statuses below
        cloud_service_used   : str
        evaluation_note      : str  — shown in UI
        detection_note       : str  — raw detection note

    Processing statuses:
        "empty"               — blank input
        "too_short"           — < MIN_DETECT_LENGTH chars
        "detection_failed"    — langdetect threw an exception
        "english_passthrough" — detected as English, unchanged
        "translated"          — successfully translated to English
        "translation_failed"  — translation attempted but failed; original preserved
        "low_confidence"      — confidence below threshold, treated as English
    """
    original_text = candidate_answer or ""
    stripped = original_text.strip()

    # Empty input
    if not stripped:
        return {
            "original_text": original_text,
            "detected_language": "Unknown",
            "language_code": "unknown",
            "detection_confidence": 0.0,
            "evaluation_text": original_text,
            "translation_used": False,
            "translated_text": None,
            "processing_status": "empty",
            "cloud_service_used": "None",
            "evaluation_note": "Empty answer — no language processing applied.",
            "detection_note": "Empty input.",
        }

    # Detect language
    detection = detect_language(stripped)
    lang_code = detection["language_code"]
    lang_name = detection["language_name"]
    confidence = detection["confidence"]
    det_status = detection["status"]
    det_note = detection["note"]

    # Map detection status to processing status for edge cases
    if det_status == "too_short":
        return _build_passthrough_result(
            original_text, lang_name, lang_code, confidence, det_note,
            processing_status="too_short",
            evaluation_note="Answer too short for reliable language detection; evaluated as English.",
        )

    if det_status in ("failed", "low_confidence"):
        pstatus = "low_confidence" if det_status == "low_confidence" else "detection_failed"
        return _build_passthrough_result(
            original_text, lang_name, lang_code, confidence, det_note,
            processing_status=pstatus,
            evaluation_note=det_note,
        )

    # English passthrough — existing pipeline unchanged
    if lang_code == "en":
        return _build_passthrough_result(
            original_text, lang_name, lang_code, confidence, det_note,
            processing_status="english_passthrough",
            evaluation_note="✅ English detected — evaluated using original pipeline unchanged.",
        )

    # Non-English: attempt translation
    trans_result = translate_to_english_groq(stripped, lang_code, lang_name)
    trans_status = trans_result["status"]
    cloud_service = trans_result.get("cloud_service", f"Groq LLaMA ({GROQ_TRANSLATE_MODEL})")

    if trans_status == "translated":
        translated_text = trans_result["translated_text"]
        return {
            "original_text": original_text,
            "detected_language": lang_name,
            "language_code": lang_code,
            "detection_confidence": confidence,
            "evaluation_text": translated_text,
            "translation_used": True,
            "translated_text": translated_text,
            "processing_status": "translated",
            "cloud_service_used": cloud_service,
            "evaluation_note": (
                f"🌐 Translated from {lang_name} to English using {cloud_service} "
                f"for semantic evaluation. Original answer preserved for display."
            ),
            "detection_note": det_note,
        }
    else:
        # Translation failed — preserve original, do not fabricate
        error_msg = trans_result.get("error", "Unknown error")
        return {
            "original_text": original_text,
            "detected_language": lang_name,
            "language_code": lang_code,
            "detection_confidence": confidence,
            "evaluation_text": original_text,  # original preserved
            "translation_used": False,
            "translated_text": None,
            "processing_status": "translation_failed",
            "cloud_service_used": cloud_service,
            "evaluation_note": (
                f"⚠️ Detected {lang_name} but translation failed ({error_msg}). "
                f"Evaluated using original text — scores may be lower than expected."
            ),
            "detection_note": det_note,
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_passthrough_result(
    original_text: str,
    lang_name: str,
    lang_code: str,
    confidence: float,
    det_note: str,
    processing_status: str,
    evaluation_note: str,
) -> Dict[str, Any]:
    """Build a passthrough result dict (no translation applied)."""
    return {
        "original_text": original_text,
        "detected_language": lang_name,
        "language_code": lang_code,
        "detection_confidence": confidence,
        "evaluation_text": original_text,
        "translation_used": False,
        "translated_text": None,
        "processing_status": processing_status,
        "cloud_service_used": f"Groq LLaMA ({GROQ_TRANSLATE_MODEL})",
        "evaluation_note": evaluation_note,
        "detection_note": det_note,
    }


def get_supported_languages() -> Dict[str, str]:
    """Return the full supported language map (code → name)."""
    return dict(SUPPORTED_LANG_NAMES)
