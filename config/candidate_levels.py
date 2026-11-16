"""
candidate_levels.py — Candidate Experience Level Specifications & Adaptation Config

Supports three candidate profiles with primary emphasis on:
- Final-year engineering students preparing for campus placements (Primary Level)
- Third-year (TY) engineering students & early career learners (Secondary Level)
- Experienced candidates with industry background (Optional Level)
"""

from typing import Any, Dict, List, Optional

# Canonical Level Keys
LEVEL_FINAL_YEAR = "final_year"
LEVEL_TY_STUDENT = "ty_student"
LEVEL_EXPERIENCED = "experienced"

DEFAULT_CANDIDATE_LEVEL = LEVEL_FINAL_YEAR

CANDIDATE_LEVELS: Dict[str, Dict[str, Any]] = {
    LEVEL_FINAL_YEAR: {
        "id": LEVEL_FINAL_YEAR,
        "name": "Final-Year / Placement Ready",
        "short_label": "Final-Year",
        "badge_label": "🎓 Final-Year / Placement",
        "badge_color": "#3B82F6",
        "description": (
            "Final-year engineering students preparing for campus placements, "
            "internships, and entry-level software/data roles."
        ),
        "primary_evidence_sources": [
            "Major academic capstone project (BE / B.Tech)",
            "Internship and practical problem-solving",
            "Technical implementation details and stack justification",
            "Individual contribution within project teams",
            "Measurable metrics (performance, accuracy, deadlines, testing)",
            "Career goals and enthusiasm for entry-level professional engineering",
        ],
        "expectations": {
            "hr_focus": "Career readiness, project ownership, technical interests, role alignment",
            "behavioral_focus": "Capstone team collaboration, leadership in college tech events, hackathon sprints, resolving project disagreements",
            "technical_depth": "Firm understanding of mechanics, trade-offs, and practical application",
            "conciseness_tolerance": True,
        },
    },
    LEVEL_TY_STUDENT: {
        "id": LEVEL_TY_STUDENT,
        "name": "Third Year (TY) / Early Career",
        "short_label": "TY Student",
        "badge_label": "📚 Third-Year (TY)",
        "badge_color": "#10B981",
        "description": (
            "Third-year engineering students and early learners seeking internships, "
            "focusing on coursework fundamentals and mini-projects."
        ),
        "primary_evidence_sources": [
            "Academic mini-projects and semester assignments",
            "Core computer science coursework and technical fundamentals",
            "Self-learning, online certifications, and coding challenges",
            "Learning agility, curiosity, and growth potential",
            "Internship readiness without assuming prior corporate experience",
        ],
        "expectations": {
            "hr_focus": "Academic interests, passion for technology, eagerness to learn, internship motivation",
            "behavioral_focus": "Coursework lab group work, mini-project challenges, adapting to feedback from professors/mentors",
            "technical_depth": "Clear conceptual understanding of core principles and definitions",
            "conciseness_tolerance": True,
        },
    },
    LEVEL_EXPERIENCED: {
        "id": LEVEL_EXPERIENCED,
        "name": "Experienced Candidate",
        "short_label": "Experienced",
        "badge_label": "💼 Experienced Professional",
        "badge_color": "#8B5CF6",
        "description": (
            "Candidates with prior industry experience, full-time engineering roles, "
            "or professional system ownership."
        ),
        "primary_evidence_sources": [
            "Production systems and commercial deployments",
            "Cross-functional collaboration and business stakeholder management",
            "Architecture design and system scalability",
            "Mentoring junior developers and technical leadership",
            "Measurable business and operational impact",
        ],
        "expectations": {
            "hr_focus": "Strategic career trajectory, reasons for transition, organizational impact",
            "behavioral_focus": "Production incident handling, cross-team conflict resolution, strategic prioritization under tight deadlines",
            "technical_depth": "Deep production trade-offs, concurrency, memory optimization, architectural patterns",
            "conciseness_tolerance": False,
        },
    },
}

LEVEL_DISPLAY_OPTIONS = [
    (LEVEL_FINAL_YEAR, "🎓 Final-Year / Placement Ready (Recommended)"),
    (LEVEL_TY_STUDENT, "📚 Third-Year (TY) / Early Career"),
    (LEVEL_EXPERIENCED, "💼 Experienced Candidate"),
]


def validate_candidate_level(level: Optional[str]) -> str:
    """
    Ensure candidate level is valid, falling back to LEVEL_FINAL_YEAR.

    Args:
        level: Candidate level string or None.

    Returns:
        Validated level key.
    """
    if not level:
        return DEFAULT_CANDIDATE_LEVEL

    cleaned = str(level).strip().lower()
    # Match by key
    if cleaned in CANDIDATE_LEVELS:
        return cleaned

    # Match by common aliases
    if "final" in cleaned or "placement" in cleaned or "be" in cleaned or "b.tech" in cleaned or "4th" in cleaned:
        return LEVEL_FINAL_YEAR
    if "ty" in cleaned or "third" in cleaned or "early" in cleaned or "3rd" in cleaned:
        return LEVEL_TY_STUDENT
    if "exp" in cleaned or "senior" in cleaned or "professional" in cleaned:
        return LEVEL_EXPERIENCED

    return DEFAULT_CANDIDATE_LEVEL


def get_candidate_level_info(level: Optional[str]) -> Dict[str, Any]:
    """Retrieve full configuration dictionary for a candidate level."""
    valid_key = validate_candidate_level(level)
    return CANDIDATE_LEVELS[valid_key]

