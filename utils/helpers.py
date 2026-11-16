"""
helpers.py — Utility Helper Functions

Provides shared utility functions used across modules, such as
safe text validation, numeric conversion, and consistent result formatting.
"""

from typing import Any


def safe_text(text: Any) -> str:
    """
    Validate and normalize text input. Returns an empty string for
    None or non-string values.

    Args:
        text: The input to validate.

    Returns:
        A stripped string, or empty string if input is None/non-string.
    """
    if text is None:
        return ""
    if not isinstance(text, str):
        return str(text).strip()
    return text.strip()


def is_valid_text(text: Any) -> bool:
    """
    Check whether text is a non-empty string after stripping whitespace.

    Args:
        text: The input to check.

    Returns:
        True if text is a non-empty string.
    """
    return isinstance(text, str) and len(text.strip()) > 0


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning a default when the denominator is zero.

    Args:
        numerator: The dividend.
        denominator: The divisor.
        default: Value to return when denominator is zero.

    Returns:
        The quotient, or the default value.
    """
    if denominator == 0:
        return default
    return numerator / denominator


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert a value to float.

    Args:
        value: The value to convert.
        default: Fallback value if conversion fails.

    Returns:
        The float value, or the default.
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """
    Safely convert a value to int.

    Args:
        value: The value to convert.
        default: Fallback value if conversion fails.

    Returns:
        The int value, or the default.
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    Clamp a numeric value to a given range.

    Args:
        value: The value to clamp.
        min_val: Minimum allowed value.
        max_val: Maximum allowed value.

    Returns:
        The clamped value.
    """
    return max(min_val, min(value, max_val))
