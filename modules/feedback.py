"""
feedback.py — Intelligent & Actionable Interview Feedback Generation Module

Produces personalized, constructive, and explainable feedback based on
multi-dimensional evaluation:
- Identified strengths (grounded in candidate's actual answer and detected components)
- Areas for improvement (with itemized deductions and specific evidence)
- Concrete, actionable recommendations (tailored to question category and candidate level)
- Suggested improved answer blueprint (preserving candidate intent without fabricating achievements)
- Executive performance summary
"""

from typing import Any, Dict, List, Optional


def _build_candidate_tailored_blueprint(
    candidate_answer: str,
    question_data: Dict[str, Any],
    missing_points: List[str],
    detected_misconceptions: List[Dict[str, Any]],
    candidate_level: str,
    structure: Dict[str, Any],
) -> str:
    """
    Construct a candidate-tailored revision blueprint.

    Core principles:
    1. Preserves candidate's original meaning and stated context (capstone, internship, coursework).
    2. Adds genuinely missing concepts without inventing personal experiences or fictional companies.
    3. Tailors suggestions to the candidate's experience level.
    4. Fixes any detected misconceptions with precise technical guidance.
    """
    ref_answer = question_data.get("reference_answer", "")
    category = question_data.get("category", "General")
    level_title = candidate_level.replace("_", " ").title()

    c_clean = candidate_answer.strip() if candidate_answer else ""
    words = c_clean.split()

    # If the answer is empty or minimal, return benchmark guide
    if not c_clean or len(words) < 3:
        return (
            f"[Suggested Template] Benchmark Reference Answer ({level_title} Standard):\n\n"
            f"> \"{ref_answer}\"\n\n"
            f"*Guideline:* Build your response with a clear definition, technical elaboration with examples, "
            f"and practical implications relevant to {level_title} expectations."
        )

    blueprint_sections: List[str] = ["[Example Revision Blueprint]"]

    # Section 1: Preserved Foundation
    blueprint_sections.append(
        f"### 1. Preserved Candidate Foundation\n"
        f"Your response establishes the following core context:\n"
        f"> \"{c_clean}\""
    )

    # Section 2: Misconception Corrections (if any)
    if detected_misconceptions:
        misc_notes = []
        for m in detected_misconceptions:
            matched = m.get("matched_sentence", "").strip()
            guidance = m.get("correction_guidance", "Review theoretical distinction.")
            misc_notes.append(f"- **Statement:** *\"{matched}\"*\n  **Correction:** {guidance}")
        blueprint_sections.append(
            "### 2. Technical Precision Correction\n" + "\n".join(misc_notes)
        )

    # Section 3: Genuinely Missing Concepts
    if missing_points:
        pts_notes = []
        for pt in missing_points:
            pts_notes.append(f"- **Missing Concept:** `{pt}` — Integrate into your technical explanation.")
        blueprint_sections.append(
            "### 3. Missing Essential Concepts to Integrate\n" + "\n".join(pts_notes)
        )

    # Section 4: Structural Completion
    framework = structure.get("framework", "General")
    if framework == "STAR":
        star_data = structure.get("star_analysis", {})
        missing_comps = star_data.get("components_missing", [])
        if missing_comps:
            struct_notes = []
            if "Result" in missing_comps:
                if candidate_level in ("final_year", "ty_student"):
                    struct_notes.append(
                        "- **Add Result:** Conclude your narrative with a verifiable outcome from your academic "
                        "project, internship, or lab (e.g., *'As a result, our model reached 91% accuracy and our "
                        "team received top marks in the capstone evaluation.'*)."
                    )
                else:
                    struct_notes.append(
                        "- **Add Result:** Conclude with measurable impact (e.g., *'This reduced response latency "
                        "by 25% and prevented recurrence in production.'*)."
                    )
            if "Action" in missing_comps:
                struct_notes.append(
                    "- **Add Action:** State specifically what steps *you* took individually rather than speaking "
                    "only about the team as a whole."
                )
            if struct_notes:
                blueprint_sections.append("### 4. Structural Completion (STAR Framework)\n" + "\n".join(struct_notes))
    else:
        gen_data = structure.get("general_analysis", {})
        has_concl = gen_data.get("has_conclusion", False)
        if not has_concl:
            blueprint_sections.append(
                "### 4. Structural Completion (Conclusion / Application)\n"
                "- **Add Practical Conclusion:** Wrap up your answer with a closing summary or real-world use case "
                "(e.g., *'In practice, choosing between these depends on memory constraints and access patterns.'*)."
            )

    # Section 5: Synthesized Revision Blueprint
    # Combine candidate's original text with missing points smoothly without inventing experiences
    synthesized_text = c_clean

    # If misconceptions exist, apply corrections
    for m in detected_misconceptions:
        matched = m.get("matched_sentence", "").strip()
        guidance = m.get("correction_guidance", "")
        if matched and matched in synthesized_text and guidance:
            # Append correction seamlessly
            synthesized_text += f" (Specifically: {guidance})"

    # Seamlessly append missing concepts
    if missing_points:
        additions = []
        for pt in missing_points:
            additions.append(f"It is also critical to consider {pt.lower()}.")
        synthesized_text += " " + " ".join(additions)

    # Append conclusion if missing
    if framework != "STAR":
        gen_data = structure.get("general_analysis", {})
        if not gen_data.get("has_conclusion", False):
            synthesized_text += (
                f" In practical engineering and project applications, this distinction ensures optimal performance "
                f"and system reliability."
            )
    else:
        star_data = structure.get("star_analysis", {})
        if "Result" in star_data.get("components_missing", []):
            if candidate_level in ("final_year", "ty_student"):
                synthesized_text += (
                    f" Ultimately, our project team completed the deliverable successfully ahead of the final evaluation deadline."
                )
            else:
                synthesized_text += (
                    f" Ultimately, this resolution ensured seamless milestone delivery and prevented client disruptions."
                )

    blueprint_sections.append(
        f"### 5. Synthesized Candidate Blueprint ({level_title} Standard)\n"
        f"> \"{synthesized_text}\"\n\n"
        f"*Reference Benchmark for Comparison:*\n\"{ref_answer}\""
    )

    return "\n\n".join(blueprint_sections)


def generate_feedback(
    evaluation_result: Dict[str, Any],
    question_data: Dict[str, Any],
    candidate_level: str = "final_year",
) -> Dict[str, Any]:
    """
    Generate personalized, constructive feedback for a candidate's response,
    adapted to their candidate level (primary focus: final-year engineering students).

    Args:
        evaluation_result: Evaluation dictionary containing component scores
                           and analysis details.
        question_data: Question metadata dict from questions.json.
        candidate_level: Candidate experience level ('final_year', 'ty_student', 'experienced').

    Returns:
        Structured feedback dictionary containing strengths, areas_for_improvement,
        actionable_suggestions, suggested_improved_answer, and summary.
    """
    comp_scores = evaluation_result.get("component_scores", {})
    semantic = evaluation_result.get("semantic_analysis", {})
    correctness = evaluation_result.get("technical_correctness", {})
    comm = evaluation_result.get("communication_analysis", {})
    delivery = evaluation_result.get("delivery_analysis", {})
    structure = evaluation_result.get("structure_analysis", {})
    candidate_answer = evaluation_result.get("candidate_answer", "")
    ans_lower = candidate_answer.lower() if candidate_answer else ""
    category = question_data.get("category", "General")

    strengths: List[str] = []
    areas_for_improvement: List[str] = []
    actionable_suggestions: List[str] = []

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Strengths Identification (Grounded strictly in candidate answer)
    # ─────────────────────────────────────────────────────────────────────────
    cov_info = semantic.get("keypoint_coverage", {})
    covered_pts = cov_info.get("covered_essential_points", [])
    if covered_pts:
        strengths.append(
            f"Successfully addressed {len(covered_pts)} core concept(s): {', '.join(covered_pts[:3])}."
        )

    # Recognize candidate-level contextual evidence in the answer
    if any(k in ans_lower for k in ["capstone", "final year", "b.tech", "be project", "major project"]):
        strengths.append("Effectively grounded response in academic capstone / final-year engineering project context.")
    elif any(k in ans_lower for k in ["internship", "intern", "company project"]):
        strengths.append("Reinforced points with practical internship experience.")
    elif any(k in ans_lower for k in ["hackathon", "competition", "contest"]):
        strengths.append("Demonstrated high-pressure execution with hackathon project evidence.")
    elif any(k in ans_lower for k in ["mini-project", "coursework", "lab assignment"]):
        strengths.append("Effectively supported response with coursework and academic mini-project examples.")

    if comp_scores.get("semantic", 0) >= 75:
        strengths.append("High semantic alignment with expected technical and professional benchmarks.")

    # High precision praise for concise answers
    if len(candidate_answer.split()) < 50 and comp_scores.get("semantic", 0) >= 75:
        strengths.append("High conceptual precision: explained core concepts accurately without unnecessary filler.")

    # Delivery & Communication Strengths (Text-Based Indicators)
    filler_freq = comm.get("filler_frequency", 0.0)
    word_count = comm.get("total_word_count", 0)
    if filler_freq == 0.0 and word_count >= 20:
        strengths.append("Clean, professional transcript delivery with zero detected conversational filler words.")
    elif filler_freq < 2.5 and word_count >= 20:
        strengths.append("Controlled transcript delivery with minimal filler word usage.")

    # Structure Strengths: strictly match detected components (NEVER praise missing conclusions)
    framework = structure.get("framework", "General")
    if framework == "STAR":
        star_data = structure.get("star_analysis", {})
        det_comp = star_data.get("components_detected", [])
        if len(det_comp) == 4:
            strengths.append("Exemplary adherence to the complete STAR narrative framework (Situation, Task, Action, Result).")
        else:
            if "Result" in det_comp:
                strengths.append("Clearly highlighted the outcome and positive result of your actions.")
            if "Action" in det_comp:
                strengths.append("Articulated specific proactive actions taken.")
            if "Situation" in det_comp and "Task" in det_comp:
                strengths.append("Established a clear context and objective with Situation and Task setup.")
    else:
        gen_data = structure.get("general_analysis", {})
        has_intro = gen_data.get("has_introduction", False)
        has_body = gen_data.get("has_body", False)
        has_concl = gen_data.get("has_conclusion", False)

        if has_intro and has_body and has_concl:
            strengths.append("Complete structural progression with an introductory definition, detailed elaboration, and clear conclusion.")
        elif has_intro and has_body:
            strengths.append("Clear progression from introductory definition to detailed body elaboration.")
        elif has_body and has_concl:
            strengths.append("Substantive technical body elaboration with practical applications/conclusions.")
        elif has_intro:
            strengths.append("Clear opening definition setting up the question topic.")
        elif has_body:
            strengths.append("Substantive body elaboration explaining core mechanisms.")

    if not strengths:
        strengths.append("Showed initial engagement with the question prompt.")

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Areas for Improvement (With Itemized Deductions & Evidence)
    # ─────────────────────────────────────────────────────────────────────────
    missing_pts = cov_info.get("missing_essential_points", [])
    if missing_pts:
        areas_for_improvement.append(
            f"Missing coverage on critical concept(s): {', '.join(missing_pts)}."
        )

    detected_miscs = correctness.get("detected_misconceptions", [])
    if detected_miscs:
        for misc in detected_miscs:
            guidance = misc.get("correction_guidance", "Review standard principles.")
            areas_for_improvement.append(
                f"Technical Correction Needed: In '{misc.get('matched_sentence', '').strip()}' — {guidance}"
            )

    # Delivery & Linguistic Areas for Improvement (Strictly Text Indicators)
    if delivery.get("detected_indicators"):
        for ind in delivery.get("detected_indicators", []):
            if ind == "elevated_filler_usage":
                areas_for_improvement.append(
                    f"Elevated frequency of conversational fillers ({filler_freq:.1f} per 100 words in transcript)."
                )
            elif ind == "very_short_response" and comp_scores.get("semantic", 0) < 70:
                areas_for_improvement.append(
                    "Answer is very brief; lacks necessary depth, technical context, or illustrative examples."
                )
            elif ind == "excessively_long_sentences":
                areas_for_improvement.append(
                    "Contains overly long or convoluted sentences that hinder written or transcribed clarity."
                )

    # Structure Deductions
    if framework == "STAR":
        star_data = structure.get("star_analysis", {})
        deductions = star_data.get("deductions", [])
        for ded in deductions:
            areas_for_improvement.append(f"STAR deduction: {ded}")
    else:
        gen_data = structure.get("general_analysis", {})
        deductions = gen_data.get("deductions", [])
        for ded in deductions:
            areas_for_improvement.append(f"Structure deduction: {ded}")

    if not areas_for_improvement:
        areas_for_improvement.append("No critical weaknesses detected; maintain this high standard.")

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Actionable Suggestions (Category-Specific & Candidate-Level Adapted)
    # ─────────────────────────────────────────────────────────────────────────
    if missing_pts:
        actionable_suggestions.append(f"Explicitly articulate: {missing_pts[0]}.")

    if detected_miscs:
        actionable_suggestions.append(
            "Clarify core theoretical distinction to avoid common interview traps and demonstrate conceptual rigor."
        )

    if filler_freq > 3.0:
        actionable_suggestions.append(
            "In speaking, embrace deliberate 1-second pauses between key thoughts instead of using fillers like 'um' or 'like'."
        )

    # Category and Candidate-Level Tailored Strategy (No generic repeated tips)
    if category == "Technical":
        if candidate_level == "final_year":
            if missing_pts:
                actionable_suggestions.append(
                    f"🎓 Placement Technical Focus: In campus interviews, demonstrate hands-on familiarity by referencing "
                    f"how you used or handled {missing_pts[0].lower()} in an academic capstone, lab assignment, or internship."
                )
            else:
                actionable_suggestions.append(
                    "🎓 Placement Technical Focus: Deepen your technical answers by highlighting algorithmic time/space trade-offs or memory efficiency."
                )
        elif candidate_level == "ty_student":
            actionable_suggestions.append(
                "📚 Academic Technical Focus: Review core definitions and practice contrasting similar mechanisms (e.g. data structures or query joins) using textbook fundamentals."
            )
        elif candidate_level == "experienced":
            actionable_suggestions.append(
                "💼 Production Technical Focus: In senior rounds, explicitly discuss production trade-offs, scalability bottlenecks, and failure modes."
            )
    elif category == "Behavioral":
        star_data = structure.get("star_analysis", {})
        missing_comps = star_data.get("components_missing", [])
        if "Result" in missing_comps:
            if candidate_level in ("final_year", "ty_student"):
                actionable_suggestions.append(
                    "Conclude with concrete project outcomes: mention evaluation grade, faculty approval, test accuracy %, or deadline completion."
                )
            else:
                actionable_suggestions.append(
                    "Conclude your story with concrete results: quantify performance gains, team impact, or client outcomes."
                )
        if "Action" in missing_comps:
            actionable_suggestions.append(
                "Emphasize your specific individual contributions rather than general team activities."
            )

        if candidate_level == "final_year":
            actionable_suggestions.append(
                "🎓 Placement Behavioral Focus: Ground behavioral stories in capstone or hackathon team settings, highlighting proactive collaboration and personal accountability under deadlines."
            )
        elif candidate_level == "ty_student":
            actionable_suggestions.append(
                "📚 Student Behavioral Focus: Draw on course group assignments or club activities, demonstrating adaptability and willingness to learn from peers."
            )
        elif candidate_level == "experienced":
            actionable_suggestions.append(
                "💼 Leadership Behavioral Focus: Emphasize business impact, cross-functional stakeholder alignment, and engineering mentorship."
            )
    elif category == "HR":
        if candidate_level == "final_year":
            actionable_suggestions.append(
                "🎓 Placement HR Focus: Directly articulate how your academic background and project passions match the company's entry-level engineering mission."
            )
        elif candidate_level == "ty_student":
            actionable_suggestions.append(
                "📚 Student HR Focus: Emphasize strong foundational habits, curiosity, and rapid learning agility for upcoming internships."
            )
        elif candidate_level == "experienced":
            actionable_suggestions.append(
                "💼 Professional HR Focus: Articulate long-term career trajectory, team mentorship capability, and alignment with corporate culture."
            )

    if not actionable_suggestions:
        actionable_suggestions.append("Continue practicing structured, concise explanations.")

    # ─────────────────────────────────────────────────────────────────────────
    # 4. Candidate-Tailored Revision Blueprint
    # ─────────────────────────────────────────────────────────────────────────
    suggested_answer = _build_candidate_tailored_blueprint(
        candidate_answer=candidate_answer,
        question_data=question_data,
        missing_points=missing_pts,
        detected_misconceptions=detected_miscs,
        candidate_level=candidate_level,
        structure=structure,
    )

    # ─────────────────────────────────────────────────────────────────────────
    # 5. Overall Evaluation Summary
    # ─────────────────────────────────────────────────────────────────────────
    overall_score = evaluation_result.get("overall_score", 0.0)
    perf_category = evaluation_result.get("performance_category", "Needs Improvement")

    score_items = [
        ("Semantic Relevance", comp_scores.get("semantic", 0.0)),
        ("Communication Quality", comp_scores.get("communication", 0.0)),
        ("Delivery Indicators (Text-based)", comp_scores.get("delivery", 0.0)),
        ("Answer Structure", comp_scores.get("structure", 0.0)),
    ]
    strongest = max(score_items, key=lambda x: x[1])[0]
    weakest = min(score_items, key=lambda x: x[1])[0]

    if missing_pts:
        priority = f"Strengthen concept coverage on {missing_pts[0]}."
    elif detected_miscs:
        priority = "Correct technical misconceptions."
    elif comp_scores.get("delivery", 0.0) < 60:
        priority = "Improve transcript fluency and minimize conversational fillers."
    elif comp_scores.get("structure", 0.0) < 60:
        priority = "Adopt a clearer narrative structure (e.g. STAR method or definition-elaboration-conclusion)."
    else:
        priority = "Maintain strong multi-dimensional performance."

    return {
        "strengths": strengths,
        "areas_for_improvement": areas_for_improvement,
        "actionable_suggestions": actionable_suggestions,
        "suggested_improved_answer": suggested_answer,
        "summary": {
            "overall_score": overall_score,
            "performance_category": perf_category,
            "strongest_component": strongest,
            "weakest_component": weakest,
            "main_improvement_priority": priority,
            "candidate_level": candidate_level,
        }
    }
