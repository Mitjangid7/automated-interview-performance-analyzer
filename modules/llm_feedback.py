"""
llm_feedback.py — CO4: Generative AI / LLM Integration

Provides:
- LLM-powered personalized interview feedback using Groq LLaMA.
- Structured prompt engineering tailored to candidate level, question category,
  evaluation scores, missing concepts, sentiment, and STAR structure.
- Reuses existing get_stt_api_credentials() for Groq key resolution.
- Never hardcodes API keys.
- Never fabricates candidate achievements or modifies existing scores.
- Graceful degradation on API failure, timeout, or missing key.

Output schema (all keys always present):
{
    "summary":              str,
    "strengths":            List[str],
    "weaknesses":           List[str],
    "missing_concepts":     List[str],
    "improved_answer":      str,
    "recommendations":      List[str],  # exactly 3
    "model_used":           str,
    "provider":             str,
    "status":               str,        # "success" | "no_api_key" | "api_error" | "parse_error"
    "error":                Optional[str],
}
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GROQ_LLM_MODEL = "llama-3.1-8b-instant"
GROQ_CANDIDATE_MODELS = [
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
    "qwen/qwen3.8-27b",
]
GROQ_CHAT_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
GROQ_TIMEOUT_SECONDS = 30
PROVIDER_NAME = "Groq"

_EMPTY_RESULT_TEMPLATE: Dict[str, Any] = {
    "summary": "",
    "strengths": [],
    "weaknesses": [],
    "missing_concepts": [],
    "improved_answer": "",
    "recommendations": [],
    "model_used": GROQ_LLM_MODEL,
    "provider": PROVIDER_NAME,
    "status": "no_api_key",
    "error": None,
}


# ---------------------------------------------------------------------------
# Prompt Construction
# ---------------------------------------------------------------------------

def build_llm_prompt(eval_data: Dict[str, Any], question_data: Dict[str, Any]) -> str:
    """
    Build a structured system+user prompt from evaluation data.

    Uses real runtime data only — never invents candidate context.
    """
    # ── Extract evaluation data ──────────────────────────────────────────────
    question_text   = eval_data.get("question", question_data.get("question", "N/A"))
    category        = question_data.get("category", eval_data.get("category", "General"))
    cand_level      = eval_data.get("candidate_level", "final_year")
    level_label     = cand_level.replace("_", " ").title()
    candidate_ans   = eval_data.get("candidate_answer", "")
    overall_score   = eval_data.get("overall_score", 0.0)
    comp_scores     = eval_data.get("component_scores", {})
    perf_category   = eval_data.get("performance_category", "")

    # Multilingual — show translated answer if used
    ml_data             = eval_data.get("multilingual_analysis", {})
    translation_used    = ml_data.get("translation_used", False)
    translated_ans      = ml_data.get("translated_text", "")
    detected_lang       = ml_data.get("detected_language", "English")

    # Semantic
    semantic_data   = eval_data.get("semantic_analysis", {})
    cov_data        = semantic_data.get("keypoint_coverage", {})
    covered_pts     = cov_data.get("covered_points", [])
    missing_pts     = cov_data.get("missing_points", [])
    sim_data        = semantic_data.get("semantic_similarity", {})
    similarity_pct  = sim_data.get("similarity_percentage", 0.0)

    # Sentiment
    sentiment_data  = eval_data.get("sentiment_analysis", {})
    sent_label      = sentiment_data.get("sentiment_label", "Neutral")
    sent_compound   = sentiment_data.get("compound", 0.0)

    # Information extraction
    info_data       = eval_data.get("information_extraction", {})
    keywords        = info_data.get("keywords", [])[:8]   # top 8
    concepts        = info_data.get("concepts", [])[:6]

    # Structure
    struct_data     = eval_data.get("structure_analysis", {})
    struct_score    = comp_scores.get("structure", 0.0)
    struct_type     = struct_data.get("structure_type", "general")
    star_data       = struct_data.get("star_analysis", {})
    star_present    = star_data.get("star_present", False) if star_data else False

    # Misconceptions
    tech_data       = eval_data.get("technical_correctness", {})
    misconceptions  = tech_data.get("detected_misconceptions", [])
    misc_texts      = [m.get("misconception", "") for m in misconceptions if m.get("misconception")]

    # ── Compose answer block ─────────────────────────────────────────────────
    answer_block = f'"""\n{candidate_ans}\n"""'
    if translation_used and translated_ans:
        answer_block += (
            f"\n\n[Note: Answer was originally in {detected_lang}. "
            f"English translation used for evaluation:]\n"
            f'"""\n{translated_ans}\n"""'
        )

    # ── Compose score block ───────────────────────────────────────────────────
    score_block = (
        f"- Overall: {overall_score:.1f}/100 ({perf_category})\n"
        f"- Semantic Relevance (40%): {comp_scores.get('semantic', 0):.1f}/100\n"
        f"- Answer Structure (25%):   {comp_scores.get('structure', 0):.1f}/100\n"
        f"- Communication (20%):      {comp_scores.get('communication', 0):.1f}/100\n"
        f"- Delivery (15%):           {comp_scores.get('delivery', 0):.1f}/100\n"
        f"- Semantic Similarity:      {similarity_pct:.1f}%"
    )

    # ── Compose NLP findings block ────────────────────────────────────────────
    covered_str   = "\n".join(f"  ✓ {p}" for p in covered_pts) if covered_pts else "  (none detected)"
    missing_str   = "\n".join(f"  ✗ {p}" for p in missing_pts) if missing_pts else "  (none)"
    keywords_str  = ", ".join(keywords) if keywords else "none detected"
    concepts_str  = ", ".join(concepts) if concepts else "none detected"
    misc_str      = "\n".join(f"  ⚠ {m}" for m in misc_texts) if misc_texts else "  (none)"
    struct_info   = (
        f"STAR Framework ({', '.join(k for k, v in star_data.items() if v and k != 'star_present')})"
        if star_present else f"General Organization (score: {struct_score:.1f}/100)"
    )

    # ── System prompt ─────────────────────────────────────────────────────────
    system_prompt = (
        "You are an experienced technical interview coach and hiring expert. "
        "Your role is to give honest, constructive, and actionable feedback. "
        "\n\nSTRICT RULES:"
        "\n1. Base feedback ONLY on the candidate's actual answer and the provided NLP analysis."
        "\n2. Do NOT invent projects, achievements, company names, or personal experiences."
        "\n3. Do NOT modify, inflate or deflate any scores — scores are fixed by the system."
        "\n4. Do NOT claim the AI verified technical correctness — the system already did that."
        "\n5. Keep feedback appropriate to the candidate's experience level."
        "\n6. Be specific: reference actual phrases or concepts from the answer when possible."
        "\n7. Respond ONLY with valid JSON matching the exact schema provided."
    )

    # ── User prompt ───────────────────────────────────────────────────────────
    user_prompt = f"""
You are evaluating a {level_label} candidate's answer to a {category} interview question.

=== INTERVIEW QUESTION ===
{question_text}

=== CANDIDATE'S ANSWER ===
{answer_block}

=== SYSTEM EVALUATION SCORES (DO NOT CHANGE THESE) ===
{score_block}

=== NLP ANALYSIS FINDINGS ===
Sentiment: {sent_label} (compound: {sent_compound:.3f})
Key Terms Extracted: {keywords_str}
Concepts Identified: {concepts_str}
Structure Type: {struct_info}

Covered Key Points:
{covered_str}

Missing Key Points:
{missing_str}

Technical Misconceptions Detected:
{misc_str}

=== YOUR TASK ===
Generate personalized interview coaching feedback for this {level_label} candidate.

Respond with ONLY a valid JSON object using exactly this schema:
{{
  "summary": "2-3 sentence executive performance summary referencing the actual answer and score",
  "strengths": ["strength 1 grounded in answer", "strength 2", "strength 3"],
  "weaknesses": ["specific weakness 1 referencing what is missing/wrong", "weakness 2"],
  "missing_concepts": ["concept 1 — brief explanation of why it matters", "concept 2"],
  "improved_answer": "A sample improved answer for this question at {level_label} standard. Must preserve the candidate's core points and style. Must NOT invent personal experiences. Must integrate the missing concepts naturally.",
  "recommendations": [
    "Actionable recommendation 1 for future interviews",
    "Actionable recommendation 2",
    "Actionable recommendation 3"
  ]
}}

Rules for the improved answer:
- Keep it under 150 words.
- Build on what the candidate already said.
- Add the missing concepts naturally.
- Do NOT use phrases like "In my experience at [company]" unless the candidate mentioned a company.
- Label it clearly as a learning reference, not a fabricated personal story.

Respond with ONLY the JSON object. No markdown, no preamble, no explanation outside the JSON.
"""

    return system_prompt, user_prompt


# ---------------------------------------------------------------------------
# API Call
# ---------------------------------------------------------------------------

def _resolve_groq_key() -> Optional[str]:
    """Resolve Groq API key via existing credentials helper."""
    try:
        from modules.audio_transcription import get_stt_api_credentials
        key, provider = get_stt_api_credentials()
        if key and provider == "groq":
            return key
    except Exception:
        pass
    return None


def _call_groq_llm(system_prompt: str, user_prompt: str, api_key: str) -> Tuple[Dict[str, Any], str]:
    """
    Call Groq chat completions API with the given prompts.
    Tries GROQ_CANDIDATE_MODELS starting with LLaMA (llama-3.1-8b-instant).
    Falls back gracefully if Groq reports 404 (model not found / inaccessible).

    Returns (parsed_dict, actual_model_used) or raises an exception.
    """
    import requests

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    last_exc = None
    for model_name in GROQ_CANDIDATE_MODELS:
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            "temperature": 0.4,
            "max_tokens": 1500,
            "response_format": {"type": "json_object"},
        }
        try:
            response = requests.post(
                GROQ_CHAT_ENDPOINT,
                headers=headers,
                json=payload,
                timeout=GROQ_TIMEOUT_SECONDS,
            )
            # If 404 model not found, try next candidate model
            if response.status_code == 404 and "model" in response.text.lower():
                last_exc = requests.exceptions.HTTPError(response.text, response=response)
                continue

            response.raise_for_status()
            data = response.json()
            raw_content = data["choices"][0]["message"]["content"].strip()

            # Strip any accidental markdown code fences
            if raw_content.startswith("```"):
                raw_content = re.sub(r"^```[a-z]*\n?", "", raw_content)
                raw_content = re.sub(r"\n?```$", "", raw_content)
                raw_content = raw_content.strip()

            parsed = json.loads(raw_content)
            return parsed, model_name
        except Exception as exc:
            last_exc = exc
            if isinstance(exc, requests.exceptions.HTTPError) and exc.response is not None and exc.response.status_code == 404:
                continue
            raise exc

    if last_exc:
        raise last_exc
    raise RuntimeError("No candidate Groq model responded successfully.")


# ---------------------------------------------------------------------------
# Response Parsing & Validation
# ---------------------------------------------------------------------------

def _parse_llm_response(raw: Dict[str, Any], model_used: str = GROQ_LLM_MODEL) -> Dict[str, Any]:
    """
    Validate and normalise the LLM JSON response into our output schema.
    Fills missing keys with safe defaults.
    """
    def _as_list(val, max_items: int = 10) -> List[str]:
        if isinstance(val, list):
            return [str(x).strip() for x in val if x][:max_items]
        if isinstance(val, str) and val.strip():
            return [val.strip()]
        return []

    return {
        "summary":          str(raw.get("summary", "")).strip(),
        "strengths":        _as_list(raw.get("strengths", []), 6),
        "weaknesses":       _as_list(raw.get("weaknesses", []), 6),
        "missing_concepts": _as_list(raw.get("missing_concepts", []), 8),
        "improved_answer":  str(raw.get("improved_answer", "")).strip(),
        "recommendations":  _as_list(raw.get("recommendations", []), 3),
        "model_used":       model_used,
        "provider":         PROVIDER_NAME,
        "status":           "success",
        "error":            None,
    }


def _error_result(status: str, error_msg: str) -> Dict[str, Any]:
    result = dict(_EMPTY_RESULT_TEMPLATE)
    result["status"] = status
    result["error"]  = error_msg
    return result


# ---------------------------------------------------------------------------
# Public Entry Point
# ---------------------------------------------------------------------------

def generate_llm_feedback(
    eval_data: Dict[str, Any],
    question_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Main CO4 entry point. Called from the Streamlit UI on button click.

    Parameters
    ----------
    eval_data     : Full output dict from evaluate_answer().
    question_data : Optional question metadata dict (used for category/reference).

    Returns
    -------
    Dict with keys: summary, strengths, weaknesses, missing_concepts,
                    improved_answer, recommendations, model_used, provider,
                    status, error.

    Never raises — all failures return an error_result dict so the rest
    of the application continues working.
    """
    q_data = question_data or {}

    # 1. Check API key
    api_key = _resolve_groq_key()
    if not api_key:
        return _error_result(
            "no_api_key",
            "Groq API key not found. Add GROQ_API_KEY to .streamlit/secrets.toml "
            "or set the GROQ_API_KEY environment variable.",
        )

    # 2. Build prompts
    try:
        system_prompt, user_prompt = build_llm_prompt(eval_data, q_data)
    except Exception as exc:
        return _error_result("prompt_error", f"Prompt construction failed: {exc}")

    # 3. Call LLM
    try:
        raw_call_res = _call_groq_llm(system_prompt, user_prompt, api_key)
        if isinstance(raw_call_res, tuple):
            raw_response, model_used = raw_call_res
        else:
            raw_response, model_used = raw_call_res, GROQ_LLM_MODEL
    except Exception as exc:
        if isinstance(exc, json.JSONDecodeError):
            return _error_result("parse_error", f"Could not parse LLM response: {exc}")
        err = str(exc)
        err_lower = err.lower()
        if isinstance(exc, TimeoutError) or "timeout" in err_lower or "timed out" in err_lower:
            status = "timeout"
        elif "429" in err or "rate" in err_lower:
            status = "rate_limit"
        elif "401" in err or "403" in err or "auth" in err_lower:
            status = "auth_error"
        else:
            status = "api_error"
        return _error_result(status, f"Groq API call failed: {err}")

    # 4. Parse response
    try:
        return _parse_llm_response(raw_response, model_used=model_used)
    except Exception as exc:
        return _error_result("parse_error", f"Could not parse LLM response: {exc}")
