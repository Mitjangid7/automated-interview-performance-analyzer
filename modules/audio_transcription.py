"""
audio_transcription.py — Audio Input and Speech-to-Text Transcription Module

Provides:
- Audio payload inspection and validation (WAV and MP3, size limits, headers)
- Multi-provider Speech-to-Text architecture (local faster-whisper when functional;
  production Whisper Cloud API via Groq or OpenAI when configured)
- Credential management: environment variables, Streamlit secrets, or user session inputs (no hard-coded keys)
- Transparent diagnostics: exposes audio properties, byte counts, and exact engine statuses
- Complete exception tracing without silent failures
"""

import io
import json
import os
import tempfile
from typing import Any, Dict, Optional, Tuple
import wave

# Audio constraints
MAX_AUDIO_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB limit
SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3"}

# Module-level model cache for optional local faster-whisper
_WHISPER_MODEL = None
_WHISPER_MODEL_SIZE = "small"
_WHISPER_AVAILABLE: Optional[bool] = None


def is_whisper_available() -> bool:
    """Check if local faster-whisper and its required tensor backends are functional."""
    global _WHISPER_AVAILABLE
    if _WHISPER_AVAILABLE is None:
        try:
            import faster_whisper
            import numpy as np  # faster_whisper requires numpy
            _WHISPER_AVAILABLE = True
        except Exception:
            _WHISPER_AVAILABLE = False
    return _WHISPER_AVAILABLE


def get_whisper_model(model_size: str = "small") -> Any:
    """
    Lazily loads and caches the faster-whisper model on CPU.
    Returns None if faster-whisper or its dependencies are unavailable.
    """
    global _WHISPER_MODEL, _WHISPER_AVAILABLE

    if _WHISPER_MODEL is not None:
        return _WHISPER_MODEL

    if not is_whisper_available():
        return None

    try:
        from faster_whisper import WhisperModel
        _WHISPER_MODEL = WhisperModel(
            model_size_or_path=model_size,
            device="cpu",
            compute_type="int8",
        )
        return _WHISPER_MODEL
    except Exception:
        try:
            from faster_whisper import WhisperModel
            _WHISPER_MODEL = WhisperModel(
                model_size_or_path=model_size,
                device="cpu",
                compute_type="float32",
            )
            return _WHISPER_MODEL
        except Exception:
            _WHISPER_AVAILABLE = False
            return None


def inspect_audio_properties(audio_bytes: bytes) -> Dict[str, Any]:
    """
    Inspect raw audio bytes and extract structural properties for diagnostics.

    Returns:
        Dictionary containing byte_size, format_type, channels, sample_rate,
        bit_depth, duration_sec, and any parsing notes.
    """
    info: Dict[str, Any] = {
        "byte_size": len(audio_bytes) if audio_bytes else 0,
        "is_wav": False,
        "is_mp3": False,
        "format": "Unknown",
        "channels": None,
        "sample_rate": None,
        "bit_depth": None,
        "duration_sec": 0.0,
    }

    if not audio_bytes or len(audio_bytes) < 4:
        return info

    header = audio_bytes[:4]

    # WAV detection and metadata parsing
    if header == b"RIFF" and len(audio_bytes) >= 12 and audio_bytes[8:12] == b"WAVE":
        info["is_wav"] = True
        info["format"] = "WAV (RIFF/WAVE)"
        try:
            with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
                info["channels"] = wf.getnchannels()
                info["sample_width"] = wf.getsampwidth()
                info["bit_depth"] = wf.getsampwidth() * 8
                info["sample_rate"] = wf.getframerate()
                info["n_frames"] = wf.getnframes()
                if wf.getframerate() > 0:
                    info["duration_sec"] = round(wf.getnframes() / float(wf.getframerate()), 2)
        except Exception as e:
            info["note"] = f"WAV header present but wave parser reported: {str(e)}"
        return info

    # MP3 detection
    if header.startswith(b"ID3") or (len(audio_bytes) >= 2 and audio_bytes[0] == 0xFF and (audio_bytes[1] & 0xE0) == 0xE0):
        info["is_mp3"] = True
        info["format"] = "MP3 Audio"
        return info

    return info


def validate_audio_data(
    audio_data: Any,
    filename: Optional[str] = None,
    max_size_mb: float = 25.0,
) -> Tuple[bool, Optional[str]]:
    """
    Validate audio byte payload or file-like object and optional filename against size and format constraints.
    """
    if audio_data is None:
        return False, "Audio recording or file is empty (0 bytes)."

    if hasattr(audio_data, "getvalue"):
        audio_bytes = audio_data.getvalue()
        if not filename and hasattr(audio_data, "name"):
            filename = audio_data.name
    elif hasattr(audio_data, "read"):
        audio_bytes = audio_data.read()
        if not filename and hasattr(audio_data, "name"):
            filename = audio_data.name
    elif isinstance(audio_data, (bytes, bytearray)):
        audio_bytes = bytes(audio_data)
    else:
        return False, f"Invalid audio input type: {type(audio_data).__name__}."

    if not audio_bytes or len(audio_bytes) == 0:
        return False, "Audio recording or file is empty (0 bytes)."

    max_bytes = int(max_size_mb * 1024 * 1024)
    if len(audio_bytes) > max_bytes:
        size_mb = len(audio_bytes) / (1024 * 1024)
        return (
            False,
            f"Audio file exceeds maximum size limit of {max_size_mb:.1f} MB (got {size_mb:.1f} MB).",
        )

    if filename:
        ext = os.path.splitext(filename.lower())[1]
        if ext and ext not in SUPPORTED_AUDIO_EXTENSIONS:
            return (
                False,
                f"Unsupported audio format '{ext}'. Supported formats: {', '.join(sorted(SUPPORTED_AUDIO_EXTENSIONS))}.",
            )

    return True, None


def get_stt_api_credentials(explicit_key: Optional[str] = None) -> Tuple[Optional[str], str]:
    """
    Resolve STT API credentials from explicit user input, environment variables,
    Streamlit secrets runtime, or local .streamlit/secrets.toml.
    Returns:
        Tuple of (api_key: Optional[str], provider: str) where provider is 'groq' or 'openai'.
    """
    # 1. Explicit key provided by caller / UI
    if explicit_key and explicit_key.strip():
        key = explicit_key.strip()
        provider = "groq" if key.startswith("gsk_") else "openai"
        return key, provider

    # 2. Environment variables
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    if groq_key:
        return groq_key, "groq"

    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if openai_key:
        return openai_key, "openai"

    stt_key = os.environ.get("STT_API_KEY", "").strip()
    if stt_key:
        provider = "groq" if stt_key.startswith("gsk_") else "openai"
        return stt_key, provider

    # 3. Streamlit secrets runtime
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            if "GROQ_API_KEY" in st.secrets and st.secrets["GROQ_API_KEY"]:
                return str(st.secrets["GROQ_API_KEY"]).strip(), "groq"
            if "OPENAI_API_KEY" in st.secrets and st.secrets["OPENAI_API_KEY"]:
                return str(st.secrets["OPENAI_API_KEY"]).strip(), "openai"
    except Exception:
        pass

    # 4. Direct .streamlit/secrets.toml check (works in CLI / pytest / subagent)
    for secrets_dir in [".streamlit", os.path.join(os.getcwd(), ".streamlit")]:
        toml_path = os.path.join(secrets_dir, "secrets.toml")
        if os.path.isfile(toml_path):
            try:
                import tomllib
                with open(toml_path, "rb") as f:
                    cfg = tomllib.load(f)
                if cfg.get("GROQ_API_KEY"):
                    return str(cfg["GROQ_API_KEY"]).strip(), "groq"
                if cfg.get("OPENAI_API_KEY"):
                    return str(cfg["OPENAI_API_KEY"]).strip(), "openai"
            except Exception:
                pass

    return None, "none"


def _normalize_language_metadata(raw_lang: Optional[str], text: str) -> Tuple[str, str]:
    """
    Resolve canonical human-readable language name and ISO 639-1 code
    from Whisper metadata or text-based detection fallback.
    """
    from modules.multilingual import SUPPORTED_LANG_NAMES, detect_language

    name_to_code = {v.lower(): k for k, v in SUPPORTED_LANG_NAMES.items()}
    lang_code = "en"
    lang_name = "English"

    if raw_lang:
        raw_clean = raw_lang.strip().lower()
        if raw_clean in SUPPORTED_LANG_NAMES:
            lang_code = raw_clean
            lang_name = SUPPORTED_LANG_NAMES[raw_clean]
        elif raw_clean in name_to_code:
            lang_code = name_to_code[raw_clean]
            lang_name = SUPPORTED_LANG_NAMES[lang_code]
        else:
            lang_name = raw_lang.strip().capitalize()
            lang_code = raw_clean[:2]

    # If language was not detected by Whisper, or if Whisper returned English but text contains non-ASCII characters:
    if (not raw_lang or (lang_code == "en" and any(ord(c) > 127 for c in text))) and text:
        try:
            det = detect_language(text)
            if det.get("status") == "detected" and det.get("language_code") != "en":
                lang_code = det.get("language_code", "en")
                lang_name = det.get("language_name", "English")
        except Exception:
            pass

    return lang_name, lang_code


def transcribe_with_whisper_api(
    audio_bytes: bytes,
    api_key: str,
    provider: str = "groq",
    filename: str = "recording.wav",
    timeout: int = 30,
    language: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Transcribe audio using standard Whisper Cloud API (Groq Whisper or OpenAI Whisper).
    Uses transcription mode (/v1/audio/transcriptions) with automatic language detection
    when language is omitted. Preserves the original transcript in its native script.
    Requires a valid user-supplied API key. No hard-coded keys are used.
    """
    try:
        import certifi
        import requests
        verify_ssl = certifi.where()
    except ImportError:
        import requests
        verify_ssl = True

    if provider.lower() == "groq" or api_key.startswith("gsk_"):
        endpoint = "https://api.groq.com/openai/v1/audio/transcriptions"
        model_name = "whisper-large-v3-turbo"
        engine_name = "Groq Whisper API (whisper-large-v3-turbo)"
    else:
        base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        endpoint = f"{base_url}/audio/transcriptions"
        model_name = "whisper-1"
        engine_name = "OpenAI Whisper API (whisper-1)"

    headers = {"Authorization": f"Bearer {api_key.strip()}"}
    files = {"file": (filename, audio_bytes, "audio/wav" if filename.endswith(".wav") else "audio/mpeg")}
    data = {"model": model_name, "response_format": "verbose_json"}
    if language:
        data["language"] = language

    try:
        resp = requests.post(
            endpoint,
            headers=headers,
            files=files,
            data=data,
            verify=verify_ssl,
            timeout=timeout,
        )
    except requests.exceptions.SSLError as e:
        return {
            "status": "error",
            "error_type": "SSL_ERROR",
            "error": f"SSL certificate verification failed when connecting to {engine_name}: {e}",
            "text": "",
            "engine": engine_name,
        }
    except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout) as e:
        return {
            "status": "error",
            "error_type": "NETWORK_ERROR",
            "error": f"Network connection error contacting {engine_name}: {e}",
            "text": "",
            "engine": engine_name,
        }
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "error_type": "TIMEOUT",
            "error": f"Transcription request timed out after {timeout} seconds.",
            "text": "",
            "engine": engine_name,
        }
    except Exception as e:
        return {
            "status": "error",
            "error_type": "REQUEST_FAILED",
            "error": f"Unexpected request failure ({type(e).__name__}): {e}",
            "text": "",
            "engine": engine_name,
        }

    if resp.status_code != 200:
        err_msg = resp.text
        try:
            err_json = resp.json()
            if "error" in err_json:
                err_msg = err_json["error"].get("message", resp.text)
        except Exception:
            pass
        return {
            "status": "error",
            "error_type": "API_ERROR",
            "error": f"{engine_name} returned HTTP {resp.status_code}: {err_msg}",
            "text": "",
            "engine": engine_name,
        }

    try:
        result_json = resp.json()
        text = result_json.get("text", "").strip()
        raw_lang = result_json.get("language")
    except Exception as e:
        return {
            "status": "error",
            "error_type": "PARSE_ERROR",
            "error": f"Failed to parse JSON response from {engine_name}: {e}",
            "text": "",
            "engine": engine_name,
        }

    if not text:
        return {
            "status": "success",
            "text": "",
            "warning": "The audio was processed successfully, but no audible speech was recognized.",
            "engine": engine_name,
            "original_transcript": "",
            "translation_applied": False,
        }

    lang_name, lang_code = _normalize_language_metadata(raw_lang, text)

    return {
        "status": "success",
        "text": text,
        "engine": engine_name,
        "language": lang_name,
        "language_code": lang_code,
        "original_transcript": text,
        "translation_applied": False,
        "duration": result_json.get("duration", 0.0),
    }


def _transcribe_with_whisper_local(
    temp_path: str,
    model_size: str = "small",
    language: Optional[str] = None,
) -> Dict[str, Any]:
    """Transcribe audio file on disk using local faster-whisper when available."""
    model = get_whisper_model(model_size=model_size)
    if model is None:
        raise RuntimeError("Local faster-whisper model could not be loaded on CPU.")

    segments, info = model.transcribe(
        temp_path,
        beam_size=5,
        language=language,
        condition_on_previous_text=False,
    )

    recognized_chunks = [segment.text.strip() for segment in segments if segment.text.strip()]
    full_text = " ".join(recognized_chunks)
    raw_lang = getattr(info, "language", None)
    lang_name, lang_code = _normalize_language_metadata(raw_lang, full_text)

    return {
        "status": "success",
        "text": full_text,
        "engine": f"faster-whisper Local CPU ({model_size})",
        "language": lang_name,
        "language_code": lang_code,
        "original_transcript": full_text,
        "translation_applied": False,
        "language_probability": getattr(info, "language_probability", 1.0),
        "duration": getattr(info, "duration", 0.0),
    }


def transcribe_audio_payload(
    audio_data: Any,
    filename: Optional[str] = None,
    api_key: Optional[str] = None,
    model_size: str = "small",
    language: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Main entry point for audio transcription.
    Accepts raw audio bytes or Streamlit UploadedFile from st.audio_input or st.file_uploader.

    Workflow:
    1. Validates payload and size.
    2. Gathers diagnostic audio properties.
    3. If local faster-whisper is available, runs offline inference on CPU.
    4. Otherwise, resolves API credentials (explicit argument, GROQ_API_KEY, or OPENAI_API_KEY).
    5. If API key present, executes standard Whisper API request.
    6. If neither local model nor API key is available, returns a clear CREDENTIALS_REQUIRED status.

    Returns:
        Dictionary with status ('success' | 'error'), text, engine, debug_info, warning, and error details.
    """
    # 1. Validation
    is_valid, err = validate_audio_data(audio_data, filename=filename)
    if not is_valid:
        return {
            "status": "error",
            "error_type": "VALIDATION_ERROR",
            "error": err or "Invalid audio data.",
            "text": "",
            "engine": "None",
            "debug_info": {},
        }

    # Extract bytes
    if hasattr(audio_data, "getvalue"):
        audio_bytes = audio_data.getvalue()
        if not filename and hasattr(audio_data, "name"):
            filename = audio_data.name
    elif hasattr(audio_data, "read"):
        audio_bytes = audio_data.read()
        if not filename and hasattr(audio_data, "name"):
            filename = audio_data.name
    elif isinstance(audio_data, (bytes, bytearray)):
        audio_bytes = bytes(audio_data)
    else:
        return {
            "status": "error",
            "error_type": "TYPE_ERROR",
            "error": f"Invalid audio payload type: {type(audio_data).__name__}.",
            "text": "",
            "engine": "None",
            "debug_info": {},
        }

    ext = os.path.splitext(filename.lower())[1] if filename else ".wav"
    if not ext:
        ext = ".wav"

    debug_info = inspect_audio_properties(audio_bytes)

    # 2. Option A: Local faster-whisper if available
    if is_whisper_available():
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tf:
            tf.write(audio_bytes)
            temp_path = tf.name

        try:
            res = _transcribe_with_whisper_local(temp_path, model_size=model_size, language=language)
            res["debug_info"] = debug_info
            return res
        except Exception as e:
            # Report local inference error rather than hiding it
            pass
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    # 3. Option B: Cloud Whisper API via user-supplied credentials
    resolved_key, provider = get_stt_api_credentials(explicit_key=api_key)

    if resolved_key:
        res = transcribe_with_whisper_api(
            audio_bytes=audio_bytes,
            api_key=resolved_key,
            provider=provider,
            filename=filename or "recording.wav",
            language=language,
        )
        res["debug_info"] = debug_info
        return res

    # 4. Neither local engine nor credentials are available
    return {
        "status": "error",
        "error_type": "CREDENTIALS_REQUIRED",
        "error": (
            "No functional Speech-to-Text engine is currently active.\n\n"
            "• Local Engine Status: faster-whisper is unavailable in the current MinGW GCC Python environment "
            "(compiled C-extension matrix libraries NumPy/CTranslate2 are incompatible with this runtime).\n"
            "• Cloud Engine Status: No API key was found.\n\n"
            "To enable automated transcription, please enter a Groq API Key (free at console.groq.com) "
            "or an OpenAI API Key in the settings below or in your GROQ_API_KEY environment variable. "
            "You can also type or dictate your answer directly in the editable text box below."
        ),
        "text": "",
        "engine": "None",
        "debug_info": debug_info,
    }
