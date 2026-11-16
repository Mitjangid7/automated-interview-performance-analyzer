"""
structure_analysis.py — Answer Structure & Organization Analysis Module

Evaluates the organizational structure of interview responses:
- For Behavioral Questions: Heuristic STAR framework detection (Situation, Task, Action, Result).
- For HR & Technical Questions: Conceptual structure (Premise, Technical Elaboration, Conclusion).

HEURISTIC LIMITATIONS:
- This is a heuristic pattern detector using linguistic cues and sentence positioning.
- Presence of an indicator keyword does not guarantee an adequate or truthful explanation.
- Absence of specific indicator phrases does not necessarily imply poor structure.
- STAR analysis is ONLY enforced for behavioral interview questions.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from modules.preprocessing import clean_text, extract_sentences, tokenize_text
from utils.helpers import clamp

# Linguistic indicator patterns for each STAR component (adapted for students, placements & industry)
SITUATION_PATTERNS = [
    r"\bsituation\s*[:\-]",
    r"\bin my (?:previous|former|last|past) (?:role|job|company|team|project|position)\b",
    r"\bat my (?:previous|former|last|past) (?:company|job|role|team)\b",
    r"\bduring my (?:internship|tenure|time|work|training)\b",
    r"\bat that time\b",
    r"\bwhen i was (?:working|at|leading|managing|employed|studying)\b",
    r"\bour team (?:was tasked with|was facing|had to|experienced)\b",
    r"\bwe were (?:tasked with|working on|building|migrating|facing|developing)\b",
    r"\bthere was a (?:time|situation|scenario|problem|incident|challenge)\b",
    r"\bthe context was\b",
    r"\bthe project involved\b",
    # Academic, placement & student project patterns:
    r"\b(?:in|during|for) (?:my|our) (?:final[- ]year|capstone|semester|mini[- ]project|academic|b\.?tech|b\.?e\.?) (?:project|review|submission|portal)\b",
    r"\b(?:during|in|at) (?:a|our|the) (?:college|university|annual)?\s*(?:hackathon|coding competition|tech fest|contest)\b",
    r"\b(?:in|during) (?:my|our) (?:lab|coursework|assignment|internship)\b",
    r"\bwhen (?:our|my) (?:project|hackathon|student|capstone) team\b",
    r"\bfor our (?:degree|college|department) project\b",
]

TASK_PATTERNS = [
    r"\btask\s*[:\-]",
    r"\bmy (?:responsibility|role|goal|objective|assignment|job) was\b",
    r"\bi had to (?:ensure|deliver|manage|coordinate|resolve|build|lead|implement|optimize|design)\b",
    r"\bi was (?:responsible for|tasked with|assigned to|expected to|handling)\b",
    r"\bi needed to (?:scope|deliver|resolve|coordinate|create|handle|address|develop)\b",
    r"\bthe objective was\b",
    r"\bthe challenge was\b",
    r"\bthe goal was to\b",
    r"\bwhat was required of me\b",
    # Student & placement task patterns:
    r"\b(?:my|our) (?:project goal|task|objective|assignment) was\b",
    r"\bi was (?:responsible for|handling|building) (?:the|our)?\s*(?:backend|frontend|model|api|database|integration|testing|pipeline)\b",
    r"\bwe had to (?:complete|deliver|submit|present|build|deploy)\b",
]

ACTION_PATTERNS = [
    r"\baction\s*[:\-]",
    r"\bi (?:implemented|developed|designed|created|built|initiated|organized)\b",
    r"\bi (?:coordinated|led|managed|facilitated|negotiated|proposed)\b",
    r"\bi (?:analyzed|investigated|researched|evaluated|identified|diagnosed)\b",
    r"\bi (?:decided to|started by|took the initiative|set up|conducted|benchmarked)\b",
    r"\bi (?:offered to|scheduled|prepared|wrote|refactored|automated|tested)\b",
    r"\bto address this,? i\b",
    r"\bmy approach was to\b",
    r"\bfirst,? i\b",
    # Technical & engineering action patterns:
    r"\bi (?:used|applied|leveraged|integrated) (?:python|sql|react|fastapi|flask|pytorch|scikit-learn|docker|git|rest|nlp)\b",
    r"\bi (?:set up|configured|structured|divided|paired with)\b",
    r"\b(?:my|our) (?:solution|approach|step) was to\b",
]

RESULT_PATTERNS = [
    r"\bresult\s*[:\-]",
    r"\bas a result\b",
    r"\bthe outcome was\b",
    r"\bthe final result was\b",
    r"\bwe (?:achieved|completed|delivered|launched|succeeded in|reduced|increased)\b",
    r"\bthis (?:improved|reduced|increased|resulted in|led to|saved|enabled)\b",
    r"\b(?:reduced|decreased) by \d+",
    r"\b(?:increased|boosted|grew) by \d+",
    r"\bwithin (?:a few weeks|one month|three months|\d+ days|\d+ weeks|\d+ hours)\b",
    r"\bmy (?:manager|lead|team|client|professor|guide|faculty) (?:praised|commended|thanked|noted|approved)\b",
    r"\bwas (?:successfully|eventually) (?:launched|delivered|resolved|adopted|submitted|deployed)\b",
    # Academic & placement outcome patterns:
    r"\b(?:we|i) (?:achieved|secured|scored|obtained|received) (?:an? )?(?:a\+|a grade|first place|second place|top \d+|prize|\d+%\s*accuracy)\b",
    r"\b(?:faculty|professor|guide|committee|evaluator|judge|mentor) (?:praised|commended|appreciated|approved|accepted)\b",
    r"\b(?:completed|finished) (?:ahead of|before) (?:the )?(?:deadline|schedule|submission)\b",
]


def _match_component_sentences(
    sentences: List[str], patterns: List[str]
) -> List[str]:
    """Find all sentences that match any of the given regex patterns."""
    matched: List[str] = []
    for sentence in sentences:
        s_lower = sentence.lower()
        for pat in patterns:
            if re.search(pat, s_lower):
                matched.append(sentence)
                break
    return matched


def detect_star_structure(
    text: Any,
    is_behavioral: bool = True,
    question: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Detect whether a candidate answer exhibits STAR structure
    (Situation, Task, Action, Result) using heuristic pattern matching.

    Args:
        text: Candidate's interview answer.
        is_behavioral: Whether the question is behavioral. Defaults to True.
        question: Optional dictionary of question metadata. If provided,
                  its 'uses_star_method' field overrides is_behavioral.

    Returns:
        Structured dictionary indicating presence of each component, completeness ratio,
        and matched supporting sentences.
    """
    cleaned = clean_text(text)

    # Determine whether STAR is applicable
    applicable = is_behavioral
    if question is not None:
        applicable = question.get("uses_star_method", is_behavioral)

    if not applicable:
        return {
            "applicable": False,
            "situation_detected": False,
            "task_detected": False,
            "action_detected": False,
            "result_detected": False,
            "components_detected": [],
            "components_missing": [],
            "star_completeness_ratio": 0.0,
            "supporting_sentences": {},
            "observations": [
                "STAR method analysis is not applicable for non-behavioral questions."
            ],
            "limitations_notice": (
                "STAR analysis is reserved for behavioral questions requiring situational narratives."
            )
        }

    if not cleaned:
        return {
            "applicable": True,
            "situation_detected": False,
            "task_detected": False,
            "action_detected": False,
            "result_detected": False,
            "components_detected": [],
            "components_missing": ["Situation", "Task", "Action", "Result"],
            "star_completeness_ratio": 0.0,
            "supporting_sentences": {
                "Situation": [],
                "Task": [],
                "Action": [],
                "Result": [],
            },
            "observations": ["Empty response; no STAR components detected."],
            "limitations_notice": (
                "Heuristic detector identifies indicator patterns only. "
                "Presence does not confirm semantic depth or truthfulness."
            )
        }

    sentences = extract_sentences(cleaned)

    # Match each component
    situation_sentences = _match_component_sentences(sentences, SITUATION_PATTERNS)
    task_sentences = _match_component_sentences(sentences, TASK_PATTERNS)
    action_sentences = _match_component_sentences(sentences, ACTION_PATTERNS)
    result_sentences = _match_component_sentences(sentences, RESULT_PATTERNS)

    situation_detected = len(situation_sentences) > 0
    task_detected = len(task_sentences) > 0
    action_detected = len(action_sentences) > 0
    result_detected = len(result_sentences) > 0

    components_detected: List[str] = []
    components_missing: List[str] = []

    if situation_detected:
        components_detected.append("Situation")
    else:
        components_missing.append("Situation")

    if task_detected:
        components_detected.append("Task")
    else:
        components_missing.append("Task")

    if action_detected:
        components_detected.append("Action")
    else:
        components_missing.append("Action")

    if result_detected:
        components_detected.append("Result")
    else:
        components_missing.append("Result")

    completeness_ratio = round(len(components_detected) / 4.0, 2)
    credits: List[str] = [f"{comp}: Detected (+25 pts)" for comp in components_detected]
    deductions: List[str] = [f"{comp}: Missing (-25 pts)" for comp in components_missing]

    observations: List[str] = []
    if completeness_ratio == 1.0:
        observations.append(
            "Complete STAR structure identified: Situation, Task, Action, and Result are all present."
        )
    elif completeness_ratio >= 0.75:
        observations.append(
            f"Strong STAR structure with 3 of 4 components detected. Missing: {', '.join(components_missing)}."
        )
    elif completeness_ratio >= 0.5:
        observations.append(
            f"Partial STAR structure detected. Missing key stages: {', '.join(components_missing)}."
        )
    else:
        observations.append(
            f"Weak or informal narrative structure. Missing components: {', '.join(components_missing)}."
        )

    if deductions:
        observations.append(f"Structure deductions: {'; '.join(deductions)}")

    return {
        "applicable": True,
        "situation_detected": situation_detected,
        "task_detected": task_detected,
        "action_detected": action_detected,
        "result_detected": result_detected,
        "components_detected": components_detected,
        "components_missing": components_missing,
        "star_completeness_ratio": completeness_ratio,
        "credits": credits,
        "deductions": deductions,
        "supporting_sentences": {
            "Situation": situation_sentences,
            "Task": task_sentences,
            "Action": action_sentences,
            "Result": result_sentences,
        },
        "observations": observations,
        "limitations_notice": (
            "Heuristic detector identifies indicator patterns only. "
            "Presence of keywords does not confirm depth, quality, or authenticity."
        )
    }


def analyze_general_structure(text: str) -> Dict[str, Any]:
    """
    Analyze organization for HR and technical interview responses.
    Evaluates:
    - Definition/Premise introduction
    - Body explanation & depth (multiple coherent sentences)
    - Concluding or practical application remarks

    Args:
        text: Candidate's response.

    Returns:
        Structured organization analysis dictionary with score (0 to 100).
    """
    cleaned = clean_text(text)
    if not cleaned:
        return {
            "structure_score": 0.0,
            "has_introduction": False,
            "has_body": False,
            "has_conclusion": False,
            "sentence_count": 0,
            "observations": ["Empty response; no organizational structure."],
        }

    sentences = extract_sentences(cleaned)
    tokens = tokenize_text(cleaned, lowercase=True)
    sentence_count = len(sentences)
    word_count = len(tokens)

    # 1. Introduction / Premise check
    first_sent = sentences[0].lower() if sentences else ""
    has_intro = any(
        kw in first_sent for kw in [
            "is", "are", "refers to", "means", "i am", "one of", "difference between",
            "in terms of", "my greatest", "when", "occurs when", "a decorator"
        ]
    ) or len(first_sent.split()) >= 6

    # 2. Body / Elaboration check (comparative clauses, contrasting structures, or multi-sentence explanations)
    has_contrast = any(
        kw in cleaned.lower() for kw in [
            "whereas", "while", "in contrast", "on the other hand", "conversely",
            "however", "left join", "tuple", "tuples", "recall", "precision", "regularization", "f1"
        ]
    )
    has_body = (sentence_count >= 2 and word_count >= 16) or (has_contrast and word_count >= 18) or word_count >= 28

    # 3. Conclusion / Practical use case check
    last_sent = sentences[-1].lower() if len(sentences) > 1 else ""
    conclusion_cues = [
        "for example", "in practice", "in summary", "overall", "use case", "use cases",
        "therefore", "useful for", "when you need", "ideal for", "benefit",
        "in conclusion", "to summarize", "as a result", "hence", "consequently",
        "best used for", "practical application", "recommend", "takeaway"
    ]
    has_conclusion = any(kw in last_sent for kw in conclusion_cues) or (sentence_count >= 3 and word_count >= 40)

    # Compute organization score with transparent component weighting
    base_score = 0.0
    credits: List[str] = []
    deductions: List[str] = []

    if has_intro:
        base_score += 35.0
        credits.append("Introductory premise / definition detected (+35 pts).")
    else:
        deductions.append("Missing opening definition or premise (-35 pts).")

    if has_body:
        base_score += 40.0
        credits.append("Body elaboration / technical detail detected (+40 pts).")
    else:
        deductions.append("Insufficient technical elaboration in answer body (-40 pts).")

    if has_conclusion:
        base_score += 25.0
        credits.append("Concluding practical use case or takeaway detected (+25 pts).")
    else:
        deductions.append("Missing practical takeaway, real-world use case, or conclusion (-25 pts).")

    # Length adjustment: allow concise well-formed responses (>= 15 words) to score up to 80-85
    if word_count < 12:
        base_score = min(base_score, 30.0)
        deductions.append("Extreme brevity (<12 words) restricts structural progression.")
    elif word_count < 22:
        if has_intro and (has_body or has_conclusion):
            base_score = min(base_score, 75.0)
        else:
            base_score = min(base_score, 55.0)
            deductions.append("Limited length (<22 words) without full elaboration.")
    elif word_count < 35:
        if has_intro and (has_body or has_conclusion):
            base_score = min(base_score, 88.0)
        else:
            base_score = min(base_score, 70.0)

    score = round(clamp(base_score, 0.0, 100.0), 2)

    obs = []
    if score >= 80:
        obs.append("Well-structured answer with clear premise, elaboration, and practical context.")
    elif score >= 50:
        obs.append("Adequately organized answer; missing either a practical conclusion or deeper body elaboration.")
    else:
        obs.append("Fragmented or brief answer lacking structured progression.")

    if credits:
        obs.append(f"Structure strengths: {'; '.join(credits)}")
    if deductions:
        obs.append(f"Structure deductions: {'; '.join(deductions)}")

    return {
        "structure_score": score,
        "has_introduction": has_intro,
        "has_body": has_body,
        "has_conclusion": has_conclusion,
        "sentence_count": sentence_count,
        "word_count": word_count,
        "observations": obs,
        "credits": credits,
        "deductions": deductions,
    }


def analyze_structure(
    candidate_answer: str,
    question_data: Dict[str, Any],
    candidate_level: str = "final_year",
) -> Dict[str, Any]:
    """
    Main entry point for answer structure analysis.
    Dispatches to STAR analysis for behavioral questions, or general organization
    analysis for HR and technical questions. Adapts expectations to candidate level.

    Args:
        candidate_answer: Candidate's response.
        question_data: Question metadata dict from questions.json.
        candidate_level: Candidate experience level ('final_year', 'ty_student', 'experienced').

    Returns:
        Structured dictionary containing structure score (0-100), framework details,
        and observations.
    """
    uses_star = question_data.get("uses_star_method", False)
    category = question_data.get("category", "")

    if uses_star or category.lower() == "behavioral":
        star_res = detect_star_structure(candidate_answer, is_behavioral=True, question=question_data)
        completeness = star_res["star_completeness_ratio"]

        # Level adaptation for behavioral structure:
        # TY students: 3 of 4 components (e.g. S-A-R without heavy T) is scored generously (85)
        if candidate_level == "ty_student" and completeness >= 0.75:
            score = 88.0
        elif candidate_level == "final_year" and completeness >= 0.75:
            score = 85.0
        else:
            score = round(completeness * 100.0, 2)

        return {
            "framework": "STAR",
            "structure_score": score,
            "star_analysis": star_res,
            "observations": star_res["observations"],
            "candidate_level": candidate_level,
        }
    else:
        gen_res = analyze_general_structure(candidate_answer)
        return {
            "framework": "GeneralOrganization",
            "structure_score": gen_res["structure_score"],
            "general_analysis": gen_res,
            "observations": gen_res["observations"],
            "candidate_level": candidate_level,
        }
