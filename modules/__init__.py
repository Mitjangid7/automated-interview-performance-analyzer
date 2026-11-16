"""
Modules package for the Automated Interview Performance Analyzer.

Submodules:
- preprocessing: Text cleaning, tokenization, statistics, sentiment
- communication_analysis: Fillers, hedging, vocabulary, delivery indicators
- structure_analysis: STAR detection & general organization analysis
- semantic_analysis: Embeddings, cosine similarity, key-point coverage, technical correctness
- scoring: Core evaluation pipeline and configurable weighted scoring
- feedback: Intelligent, personalized feedback generation
"""

from modules.preprocessing import clean_text, normalize_text, tokenize_text, preprocess_answer
from modules.communication_analysis import analyze_communication, analyze_delivery_indicators
from modules.structure_analysis import detect_star_structure, analyze_structure
from modules.semantic_analysis import (
    calculate_semantic_similarity,
    calculate_keypoint_coverage,
    calculate_question_relevance,
    analyze_technical_correctness,
    analyze_semantics,
)
from modules.scoring import evaluate_answer
from modules.feedback import generate_feedback
from modules.audio_transcription import (
    transcribe_audio_payload,
    validate_audio_data,
    inspect_audio_properties,
)

__all__ = [
    "clean_text",
    "normalize_text",
    "tokenize_text",
    "preprocess_answer",
    "analyze_communication",
    "analyze_delivery_indicators",
    "detect_star_structure",
    "analyze_structure",
    "calculate_semantic_similarity",
    "calculate_keypoint_coverage",
    "calculate_question_relevance",
    "analyze_technical_correctness",
    "analyze_semantics",
    "evaluate_answer",
    "generate_feedback",
    "transcribe_audio_payload",
    "validate_audio_data",
    "inspect_audio_properties",
]
