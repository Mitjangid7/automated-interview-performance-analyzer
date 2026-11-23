"""
test_audio.py — Unit tests for the audio transcription and validation module.
"""

import io
import wave
import pytest
from modules.audio_transcription import (
    validate_audio_data,
    inspect_audio_properties,
    get_stt_api_credentials,
    transcribe_with_whisper_api,
    transcribe_audio_payload,
    is_whisper_available,
)


class DummyUploadFile:
    """Mock Streamlit UploadedFile object."""

    def __init__(self, name: str, data: bytes):
        self.name = name
        self._data = data
        self.size = len(data)

    def read(self) -> bytes:
        return self._data

    def getvalue(self) -> bytes:
        return self._data


def _make_dummy_wav(duration_sec: float = 0.5, rate: int = 16000, channels: int = 1) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        num_frames = int(duration_sec * rate)
        wf.writeframes(b"\x00\x00" * num_frames * channels)
    return buf.getvalue()


def test_validate_audio_empty_bytes():
    valid, err = validate_audio_data(b"")
    assert not valid
    assert "empty" in err.lower()


def test_validate_audio_unsupported_format():
    valid, err = validate_audio_data(b"test audio content", filename="recording.txt")
    assert not valid
    assert "unsupported" in err.lower()


def test_validate_audio_oversized():
    oversized = b"0" * (26 * 1024 * 1024)
    valid, err = validate_audio_data(oversized, filename="recording.wav")
    assert not valid
    assert "exceeds" in err.lower()


def test_validate_audio_valid_wav_header():
    wav_bytes = _make_dummy_wav(0.1)
    valid, err = validate_audio_data(wav_bytes, filename="voice.wav")
    assert valid
    assert err is None


def test_validate_audio_streamlit_uploaded_file():
    mock_file = DummyUploadFile("interview.mp3", b"\xff\xfb\x90\x64" + b"\x00" * 100)
    valid, err = validate_audio_data(mock_file)
    assert valid
    assert err is None


def test_inspect_audio_properties_wav():
    wav_bytes = _make_dummy_wav(duration_sec=0.4, rate=16000, channels=1)
    props = inspect_audio_properties(wav_bytes)
    assert props["is_wav"] is True
    assert props["channels"] == 1
    assert props["sample_rate"] == 16000
    assert props["bit_depth"] == 16
    assert props["duration_sec"] == 0.4
    assert props["byte_size"] == len(wav_bytes)


def test_inspect_audio_properties_empty():
    props = inspect_audio_properties(b"")
    assert props["byte_size"] == 0
    assert props["is_wav"] is False


def test_get_stt_api_credentials_explicit():
    key, provider = get_stt_api_credentials("gsk_test12345")
    assert key == "gsk_test12345"
    assert provider == "groq"

    key, provider = get_stt_api_credentials("sk-openai12345")
    assert key == "sk-openai12345"
    assert provider == "openai"


def test_transcribe_audio_empty_payload():
    result = transcribe_audio_payload(b"")
    assert result["status"] == "error"
    assert result["text"] == ""
    assert "empty" in result["error"].lower()


def test_transcribe_audio_invalid_extension():
    result = transcribe_audio_payload(b"not audio", filename="test.pdf")
    assert result["status"] == "error"
    assert "unsupported" in result["error"].lower()


def test_transcribe_audio_credentials_required(monkeypatch):
    import modules.audio_transcription as at
    monkeypatch.setattr(at, "get_stt_api_credentials", lambda explicit_key=None: (None, "none"))
    wav_bytes = _make_dummy_wav(0.2)
    # With no key and no local model, should return CREDENTIALS_REQUIRED cleanly
    result = at.transcribe_audio_payload(wav_bytes, filename="test.wav", api_key=None)
    assert result["status"] == "error"
    assert result["error_type"] == "CREDENTIALS_REQUIRED"
    assert "API key" in result["error"]
    assert "debug_info" in result
    assert result["debug_info"]["channels"] == 1


def test_transcribe_whisper_api_automatic_language_detection(monkeypatch):
    """Verify that transcription does not force 'language': 'en', allowing automatic language detection."""
    import modules.audio_transcription as at

    sent_data = {}

    class MockResponse:
        status_code = 200
        def json(self):
            return {"text": "नमस्ते, मैं एक सॉफ्टवेयर इंजीनियर हूँ।", "language": "hindi"}

    def mock_post(url, headers=None, files=None, data=None, verify=True, timeout=30):
        sent_data.update(data or {})
        return MockResponse()

    import requests
    monkeypatch.setattr(requests, "post", mock_post)

    wav_bytes = _make_dummy_wav(0.2)
    res = at.transcribe_with_whisper_api(wav_bytes, api_key="gsk_dummy", provider="groq")
    assert res["status"] == "success"
    assert "नमस्ते" in res["text"]
    assert "language" not in sent_data, "Automatic detection must omit 'language' to avoid forcing English"
    assert sent_data.get("response_format") == "verbose_json", "Must request verbose_json to receive language metadata"
    assert res.get("language").lower() == "hindi"
    assert res.get("language_code") == "hi"
    assert res.get("original_transcript") == res["text"]
    assert res.get("translation_applied") is False


def test_transcribe_whisper_api_explicit_language_override(monkeypatch):
    """Verify that when language is explicitly passed, it is respected in the API request."""
    import modules.audio_transcription as at

    sent_data = {}

    class MockResponse:
        status_code = 200
        def json(self):
            return {"text": "Hello world", "language": "english"}

    def mock_post(url, headers=None, files=None, data=None, verify=True, timeout=30):
        sent_data.update(data or {})
        return MockResponse()

    import requests
    monkeypatch.setattr(requests, "post", mock_post)

    wav_bytes = _make_dummy_wav(0.2)
    res = at.transcribe_with_whisper_api(wav_bytes, api_key="gsk_dummy", provider="groq", language="en")
    assert res["status"] == "success"
    assert sent_data.get("language") == "en"
    assert res.get("language").lower() == "english"
    assert res.get("language_code") == "en"


def test_real_hindi_audio_transcription_live():
    """Live integration test: Transcribe real Hindi speech file and verify native Devanagari script output."""
    import os
    import modules.audio_transcription as at

    key, provider = at.get_stt_api_credentials()
    audio_file = "tests/fixtures/hindi_test.mp3" if os.path.exists("tests/fixtures/hindi_test.mp3") else "hindi_test.mp3"
    if not key or not os.path.exists(audio_file):
        import pytest
        pytest.skip("Groq API key or hindi_test.mp3 not available for live audio test.")

    with open(audio_file, "rb") as f:
        audio_bytes = f.read()

    res = at.transcribe_audio_payload(audio_bytes, filename=os.path.basename(audio_file), api_key=key)
    assert res["status"] == "success"
    assert res["language"] == "Hindi"
    assert res["language_code"] == "hi"
    assert res["translation_applied"] is False
    # Verify transcript is genuinely in Devanagari Hindi script, not English
    text = res["text"]
    assert any("\u0900" <= c <= "\u097F" for c in text), f"Transcript must contain Hindi Devanagari characters: {text}"
    assert "प्रोजेक्ट" in text or "डेटाबेस" in text or "नमस्ते" in text


