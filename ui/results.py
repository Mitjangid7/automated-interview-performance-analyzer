"""
results.py — Detailed Performance Analysis & Feedback Presentation View

Renders:
- Executive score card with circular gauge chart, performance badge, and calculation explanation
- Clear display of the four core component dimensions:
    1. Semantic Relevance (40%)
    2. Answer Structure (25%)
    3. Communication Quality (20%)
    4. Linguistic Delivery (15%)
- Interactive Plotly radar chart and component comparison bar chart
- Comprehensive deep-dives:
    1. Semantic analysis, key-point coverage (highlighting covered, partial, and missing concepts)
    2. Technical correctness and detected misconception alerts with corrections
    3. Communication metrics and linguistic delivery indicators (fillers, hedging, readability)
    4. Structural analysis (STAR framework or General Organization)
    5. Actionable feedback: strengths, improvements, next steps, and revision blueprint
"""

from typing import Any, Dict, Optional
from config.candidate_levels import get_candidate_level_info
from ui.components import (
    create_score_gauge,
    create_radar_chart,
    create_component_bar_chart,
)


def _get_badge_html(category: str) -> str:
    """Return colored HTML badge corresponding to performance category."""
    cat_lower = category.lower()
    if "excellent" in cat_lower:
        return f"<span class='badge-excellent'>{category}</span>"
    elif "good" in cat_lower:
        return f"<span class='badge-good'>{category}</span>"
    elif "average" in cat_lower:
        return f"<span class='badge-average'>{category}</span>"
    else:
        return f"<span class='badge-needs-improvement'>{category}</span>"


def render_results(
    st_module: Any,
    evaluation_result: Optional[Dict[str, Any]] = None,
    question_data: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Render comprehensive interview evaluation results in Streamlit.

    Args:
        st_module: Streamlit module (or mock).
        evaluation_result: Output from evaluate_answer().
        question_data: Question metadata dict.
    """
    st_module.markdown("<h1 class='main-title'>Performance Analysis</h1>", unsafe_allow_html=True)
    st_module.markdown(
        "<p class='sub-title'>Detailed multi-dimensional diagnosis, conceptual coverage, linguistic delivery indicators, and personalized feedback.</p>",
        unsafe_allow_html=True,
    )

    eval_data = evaluation_result or st_module.session_state.get("last_evaluation")
    q_data = question_data or st_module.session_state.get("last_question_data", {})

    if not eval_data:
        from ui.history import load_history
        hist = load_history()
        if hist:
            eval_data = hist[-1]
            st_module.session_state["last_evaluation"] = eval_data

    if not eval_data:
        st_module.markdown(
            """
            <div class='empty-state-box'>
                <div class='empty-state-icon'>📋</div>
                <div class='empty-state-title'>No Interview Evaluated Yet</div>
                <div class='empty-state-text'>
                    Submit a response in the <b>Practice Interview</b> workspace to view your in-depth score breakdown,
                    four-dimension radar analysis, conceptual coverage, and actionable feedback blueprint.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col_c1, col_c2, col_c3 = st_module.columns([1, 2, 1])
        with col_c2:
            if st_module.button("🚀 Go to Practice Interview", type="primary", use_container_width=True):
                st_module.session_state["active_nav"] = "Practice Interview"
                st_module.rerun()
        return

    overall_score = float(eval_data.get("overall_score", 0.0))
    category = eval_data.get("performance_category", "Needs Improvement")
    question_text = eval_data.get("question", "")
    qid = eval_data.get("question_id", "Q")
    candidate_answer = eval_data.get("candidate_answer", "")
    comp_scores = eval_data.get("component_scores", {})
    weighted_contribs = eval_data.get("weighted_contributions", {})
    feedback = eval_data.get("feedback", {})

    # 1. Top Section: Question Banner Card
    badge_html = _get_badge_html(category)
    cand_level = eval_data.get("candidate_level", "final_year")
    lvl_info = get_candidate_level_info(cand_level)
    level_badge = lvl_info.get("badge_label", "🎓 Final-Year / Placement")

    st_module.markdown(
        f"""
        <div class='question-card'>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem; flex-wrap: wrap; gap: 0.5rem;'>
                <div style='display: flex; align-items: center; gap: 0.6rem;'>
                    <span style='color: #60A5FA; font-weight: 700; font-size: 0.85rem; text-transform: uppercase;'>Question [{qid}]</span>
                    <span style='background: rgba(59, 130, 246, 0.15); color: #93C5FD; border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 9999px; padding: 0.15rem 0.55rem; font-size: 0.75rem; font-weight: 600;'>{level_badge}</span>
                </div>
                <div>{badge_html}</div>
            </div>
            <p class='question-text'>{question_text}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st_module.expander("👁️ View Submitted Candidate Answer", expanded=False):
        st_module.markdown(f"*\"{candidate_answer}\"*")

    # 2. Overall Score Visualization & Executive Summary
    gauge_col, summary_col = st_module.columns([2, 3])

    with gauge_col:
        gauge_fig = create_score_gauge(overall_score, category)
        st_module.plotly_chart(gauge_fig, use_container_width=True)

    with summary_col:
        st_module.markdown("### Executive Summary")
        summary_info = feedback.get("summary", {})
        st_module.markdown(
            f"""
            <div class='kpi-card' style='margin-bottom: 0.5rem;'>
                <div style='color: #E2E8F0; line-height: 1.8;'>
                    <div>🎯 <b>Overall Score:</b> <span style='font-size: 1.25rem; font-weight: 700; color: #60A5FA;'>{overall_score:.1f} / 100</span> ({category})</div>
                    <div>🎓 <b>Candidate Level:</b> <span style='color: #93C5FD; font-weight: 600;'>{level_badge}</span></div>
                    <div>🌟 <b>Strongest Dimension:</b> <span style='color: #34D399; font-weight: 600;'>{summary_info.get('strongest_component', 'N/A').title()}</span></div>
                    <div>🎯 <b>Key Growth Area:</b> <span style='color: #FBBF24; font-weight: 600;'>{summary_info.get('weakest_component', 'N/A').title()}</span></div>
                    <div>💡 <b>Primary Action:</b> <span style='color: #CBD5E1;'>{summary_info.get('main_improvement_priority', 'Practice structured elaboration.')}</span></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st_module.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

    # 3. Four Core Component Scores Display
    st_module.markdown("### 📊 Four Evaluation Dimensions")
    st_module.caption("Transparent component scores evaluated across core subject-matter and delivery standards.")

    c1, c2, c3, c4 = st_module.columns(4)

    with c1:
        st_module.markdown(
            f"""
            <div class='kpi-card'>
                <div class='kpi-header'>
                    <span class='kpi-title'>Semantic Relevance</span>
                    <span class='kpi-icon'>🎯</span>
                </div>
                <div class='kpi-value'>{comp_scores.get('semantic', 0):.1f}</div>
                <div class='kpi-subtext'>
                    <span class='kpi-badge-positive'>{weighted_contribs.get('semantic', 0):.1f} pts</span>
                    <span>(Weight: 40%)</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st_module.markdown(
            f"""
            <div class='kpi-card'>
                <div class='kpi-header'>
                    <span class='kpi-title'>Answer Structure</span>
                    <span class='kpi-icon'>🏗️</span>
                </div>
                <div class='kpi-value'>{comp_scores.get('structure', 0):.1f}</div>
                <div class='kpi-subtext'>
                    <span class='kpi-badge-positive'>{weighted_contribs.get('structure', 0):.1f} pts</span>
                    <span>(Weight: 25%)</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st_module.markdown(
            f"""
            <div class='kpi-card'>
                <div class='kpi-header'>
                    <span class='kpi-title'>Communication Quality</span>
                    <span class='kpi-icon'>💬</span>
                </div>
                <div class='kpi-value'>{comp_scores.get('communication', 0):.1f}</div>
                <div class='kpi-subtext'>
                    <span class='kpi-badge-positive'>{weighted_contribs.get('communication', 0):.1f} pts</span>
                    <span>(Weight: 20%)</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:
        st_module.markdown(
            f"""
            <div class='kpi-card'>
                <div class='kpi-header'>
                    <span class='kpi-title'>Linguistic Delivery</span>
                    <span class='kpi-icon'>🗣️</span>
                </div>
                <div class='kpi-value'>{comp_scores.get('delivery', 0):.1f}</div>
                <div class='kpi-subtext'>
                    <span class='kpi-badge-positive'>{weighted_contribs.get('delivery', 0):.1f} pts</span>
                    <span>(Weight: 15%)</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 4. Score Calculation Explanation
    with st_module.expander("📐 How Your Overall Score is Calculated", expanded=False):
        st_module.markdown(
            """
            The **Automated Interview Performance Analyzer** combines 4 distinct evaluation dimensions into a single
            0–100 overall score using transparent, configurable weights. There is no arbitrary score inflation or hidden grading:
            """
        )
        st_module.latex(
            r"\text{Overall Score} = (\text{Semantic} \times 0.40) + (\text{Structure} \times 0.25) + (\text{Communication} \times 0.20) + (\text{Delivery} \times 0.15)"
        )
        st_module.markdown(
            f"""
            | Evaluation Dimension | Weight | Raw Score (0–100) | Weighted Contribution |
            | :--- | :---: | :---: | :---: |
            | **Semantic Relevance** | 40% | `{comp_scores.get('semantic', 0):.2f}` | **{weighted_contribs.get('semantic', 0):.2f} pts** |
            | **Answer Structure** | 25% | `{comp_scores.get('structure', 0):.2f}` | **{weighted_contribs.get('structure', 0):.2f} pts** |
            | **Communication Quality** | 20% | `{comp_scores.get('communication', 0):.2f}` | **{weighted_contribs.get('communication', 0):.2f} pts** |
            | **Linguistic Delivery** | 15% | `{comp_scores.get('delivery', 0):.2f}` | **{weighted_contribs.get('delivery', 0):.2f} pts** |
            | **Total Composite Score** | **100%** | &mdash; | **{overall_score:.2f} / 100** |
            """
        )

    # 5. Charts: Radar Balance & Component Breakdown
    col_chart1, col_chart2 = st_module.columns(2)
    with col_chart1:
        st_module.markdown("#### Dimensional Balance")
        st_module.caption("Radar polygon showing dimensional symmetry across all 4 evaluation areas.")
        radar_fig = create_radar_chart(comp_scores)
        st_module.plotly_chart(radar_fig, use_container_width=True)

    with col_chart2:
        st_module.markdown("#### Raw vs. Weighted Contribution")
        st_module.caption("Comparison between raw component capability and actual points contributed.")
        bar_fig = create_component_bar_chart(comp_scores, weighted_contribs)
        st_module.plotly_chart(bar_fig, use_container_width=True)

    st_module.markdown("---")

    # 6. In-Depth Diagnostic Tabs
    tab_semantic, tab_correct, tab_comm, tab_struct, tab_feedback = st_module.tabs([
        "🎯 Semantic & Concepts",
        "🔍 Technical Correctness",
        "💬 Communication & Delivery",
        "🏗️ Answer Structure",
        "💡 Actionable Feedback",
    ])

    # TAB 1: Semantic Analysis & Concept Coverage
    with tab_semantic:
        semantic_data = eval_data.get("semantic_analysis", {})
        cov_data = semantic_data.get("keypoint_coverage", {})
        sim_data = semantic_data.get("semantic_similarity", {})

        st_module.markdown("#### Conceptual & Key-Point Coverage")
        st_module.caption(
            "Evaluation of how well your answer addressed essential subject-matter concepts. "
            "Note: High semantic similarity does not prove factual truth; conceptual coverage provides grounded evidence."
        )

        scol1, scol2, scol3 = st_module.columns(3)
        with scol1:
            st_module.metric("Key-Point Coverage", f"{cov_data.get('coverage_percentage', 0):.1f}%")
        with scol2:
            st_module.metric("Semantic Similarity", f"{sim_data.get('similarity_percentage', 0):.1f}%")
        with scol3:
            engine_str = semantic_data.get("model_engine", semantic_data.get("model_used", "Sentence Transformers / TF-IDF"))
            short_engine = "all-MiniLM-L6-v2" if "MiniLM" in engine_str else "TF-IDF Baseline"
            st_module.metric("Model Engine", short_engine)

        divergence = semantic_data.get("divergence_explanation")
        if divergence:
            st_module.info(f"ℹ️ **Evaluation Dynamics:** {divergence}")

        disclaimer = semantic_data.get("factual_correctness_disclaimer")
        if disclaimer:
            st_module.caption(f"⚖️ {disclaimer}")

        st_module.markdown("##### Essential Concepts Status")
        covered = cov_data.get("covered_essential_points", [])
        partial = cov_data.get("partially_covered_essential_points", [])
        missing = cov_data.get("missing_essential_points", [])

        # Covered points
        if covered:
            for pt in covered:
                st_module.markdown(
                    f"""
                    <div class='checklist-item detected'>
                        <span>✅ <b>Covered:</b> {pt}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # Partially covered points
        if partial:
            for pt in partial:
                st_module.markdown(
                    f"""
                    <div class='checklist-item partial'>
                        <span>⚠️ <b>Partially Covered:</b> {pt}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # Missing points (highlighted prominently)
        if missing:
            st_module.markdown("<div style='margin-top: 0.5rem;'><b>⚠️ Missing Essential Concepts (Target for Revision):</b></div>", unsafe_allow_html=True)
            for pt in missing:
                st_module.markdown(
                    f"""
                    <div class='checklist-item missing'>
                        <span>❌ <b>Missing Concept:</b> {pt}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st_module.success("🌟 Outstanding! All essential curriculum concepts were successfully addressed.")

        evidence = cov_data.get("evidence_sentences", {})
        if evidence:
            with st_module.expander("🔎 Supporting Evidence Sentences Extracted from Your Answer"):
                for pt, sent in evidence.items():
                    st_module.markdown(f"- **{pt}:** *\"{sent}\"*")

    # TAB 2: Technical Correctness & Misconceptions
    with tab_correct:
        tech_data = eval_data.get("technical_correctness", {})
        st_module.markdown("#### Technical Correctness & Misconception Analysis")
        st_module.caption(
            "Identifies potential industry misconceptions and checks for factual contradictions against domain benchmarks."
        )

        misconceptions = tech_data.get("detected_misconceptions", [])
        if misconceptions:
            st_module.warning(f"⚠️ Detected {len(misconceptions)} potential technical misconception(s):")
            for m in misconceptions:
                st_module.markdown(
                    f"""
                    <div class='card-misconception'>
                        <div style='font-weight: 700; color: #F87171; font-size: 1rem; margin-bottom: 0.35rem;'>
                            ⚠️ Misconception: {m.get('misconception')}
                        </div>
                        <div style='margin-bottom: 0.35rem;'>
                            <b>Your statement:</b> <i>"{m.get('matched_sentence')}"</i>
                        </div>
                        <div style='color: #60A5FA;'>
                            💡 <b>Correction & Guidance:</b> {m.get('correction_guidance')}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st_module.markdown(
                """
                <div class='card-strength'>
                    <b>✅ Clean Technical Reasoning:</b> No common curriculum misconceptions or contradictory claims were detected.
                </div>
                """,
                unsafe_allow_html=True,
            )

        for obs in tech_data.get("correctness_observations", []):
            st_module.info(obs)

        if tech_data.get("analysis_limitations"):
            st_module.caption(f"ℹ️ Limitation notice: {tech_data.get('analysis_limitations', '')}")

    # TAB 3: Communication & Delivery
    with tab_comm:
        comm_data = eval_data.get("communication_analysis", {})
        delivery_data = eval_data.get("delivery_analysis", {})

        st_module.markdown("#### Verbal Delivery & Linguistic Indicators")
        st_module.caption(
            "Analyzes verbal habits, filler word frequency, and vocabulary diversity. "
            "Note: These indicators measure observable textual patterns only, NOT psychological confidence or nervous traits."
        )

        modality_notice = comm_data.get("modality_notice") or delivery_data.get("modality_notice")
        if modality_notice:
            st_module.info(f"🎙️ **Evaluation Modality Notice:** {modality_notice}")

        dcol1, dcol2, dcol3, dcol4 = st_module.columns(4)
        with dcol1:
            st_module.metric("Filler Frequency", f"{comm_data.get('filler_frequency', 0):.1f} / 100w")
        with dcol2:
            st_module.metric("Total Fillers", comm_data.get("filler_count", 0))
        with dcol3:
            st_module.metric("Hedging Phrases", comm_data.get("hedging_count", 0))
        with dcol4:
            st_module.metric("Vocab Diversity (TTR)", f"{comm_data.get('vocabulary_diversity', 0):.2f}")

        fillers_detail = comm_data.get("filler_word_details", {})
        if fillers_detail:
            with st_module.expander("🗣️ Detected Filler Words Breakdown"):
                for w, cnt in fillers_detail.items():
                    st_module.markdown(f"- **'{w}'**: {cnt} time(s)")

        readability = comm_data.get("readability_information", {})
        if readability:
            st_module.caption(
                f"📖 Reading Complexity ({readability.get('metric_name', '')}): "
                f"**{readability.get('score', 0)}** ({readability.get('interpretation', '')})"
            )

        st_module.markdown("##### Observations:")
        for obs in comm_data.get("communication_observations", []):
            st_module.markdown(f"- {obs}")

    # TAB 4: Answer Structure
    with tab_struct:
        struct_data = eval_data.get("structure_analysis", {})
        framework = struct_data.get("framework", "General")

        if framework == "STAR":
            st_module.markdown("#### Behavioral Answer Structure: STAR Method")
            st_module.caption(
                "Evaluates narrative progression through Situation, Task, Action, and Result."
            )
            star = struct_data.get("star_analysis", {})
            st_module.metric("STAR Completeness", f"{star.get('star_completeness_ratio', 0) * 100:.0f}%")

            comp_status = {
                "Situation": star.get("situation_detected", False),
                "Task": star.get("task_detected", False),
                "Action": star.get("action_detected", False),
                "Result": star.get("result_detected", False),
            }

            for comp_name, is_present in comp_status.items():
                if is_present:
                    st_module.markdown(
                        f"<div class='checklist-item detected'>✅ <b>{comp_name}</b> &mdash; Present and identifiable in response</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st_module.markdown(
                        f"<div class='checklist-item missing'>❌ <b>{comp_name}</b> &mdash; Missing or unstated</div>",
                        unsafe_allow_html=True,
                    )

            sup_sent = star.get("supporting_sentences", {})
            with st_module.expander("🔎 Matched Structural Sentences"):
                for comp, sents in sup_sent.items():
                    if sents:
                        st_module.markdown(f"**{comp}:**")
                        for s in sents:
                            st_module.markdown(f"- *\"{s}\"*")

            star_credits = star.get("credits", [])
            star_deductions = star.get("deductions", [])
            if star_credits or star_deductions:
                with st_module.expander("📊 Score Itemization (Credits & Deductions)", expanded=False):
                    if star_credits:
                        st_module.markdown("**Earned Credits:**")
                        for c in star_credits:
                            st_module.markdown(f"- ✅ {c}")
                    if star_deductions:
                        st_module.markdown("**Deductions:**")
                        for d in star_deductions:
                            st_module.markdown(f"- ⚠️ {d}")
        else:
            st_module.markdown("#### Conceptual Structure: Premise, Elaboration, & Conclusion")
            gen = struct_data.get("general_analysis", {})
            st_module.metric("Structure Score", f"{struct_data.get('structure_score', 0):.1f}/100")

            g_status = [
                ("Introduction / Definition", gen.get("has_introduction", False)),
                ("Technical Elaboration & Body", gen.get("has_body", False)),
                ("Conclusion / Practical Use Cases", gen.get("has_conclusion", False)),
            ]
            for stage, ok in g_status:
                if ok:
                    st_module.markdown(
                        f"<div class='checklist-item detected'>✅ <b>{stage}</b> &mdash; Clear and identified</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st_module.markdown(
                        f"<div class='checklist-item missing'>⚠️ <b>{stage}</b> &mdash; Brief or missing</div>",
                        unsafe_allow_html=True,
                    )

            gen_credits = gen.get("credits", [])
            gen_deductions = gen.get("deductions", [])
            if gen_credits or gen_deductions:
                with st_module.expander("📊 Score Itemization (Credits & Deductions)", expanded=False):
                    if gen_credits:
                        st_module.markdown("**Earned Credits:**")
                        for c in gen_credits:
                            st_module.markdown(f"- ✅ {c}")
                    if gen_deductions:
                        st_module.markdown("**Deductions:**")
                        for d in gen_deductions:
                            st_module.markdown(f"- ⚠️ {d}")

    # TAB 5: Actionable Feedback
    with tab_feedback:
        st_module.markdown("#### Personalized Actionable Feedback")

        # Specific Strengths
        st_module.markdown("##### 🌟 What You Did Well (Strengths)")
        strengths = feedback.get("strengths", [])
        if strengths:
            for str_item in strengths:
                st_module.markdown(
                    f"<div class='card-strength'>✓ {str_item}</div>",
                    unsafe_allow_html=True,
                )
        else:
            st_module.caption("Focus on establishing clear definitions and concrete examples.")

        # Targeted Areas for Improvement
        st_module.markdown("##### 🎯 Targeted Areas for Improvement")
        areas = feedback.get("areas_for_improvement", [])
        if areas:
            for imp_item in areas:
                st_module.markdown(
                    f"<div class='card-improvement'>! {imp_item}</div>",
                    unsafe_allow_html=True,
                )
        else:
            st_module.caption("No critical weaknesses flagged.")

        # Recommended Next Steps
        st_module.markdown("##### 🚀 Recommended Next Steps")
        suggestions = feedback.get("actionable_suggestions", [])
        if suggestions:
            for act in suggestions:
                st_module.info(f"→ {act}")

        # Model Answer Revision Blueprint
        st_module.markdown("---")
        st_module.markdown("##### 📝 Suggested Improved Answer Revision Blueprint")
        st_module.caption(
            "Suggested example answer — use this as a learning reference, not as a fabricated personal experience. "
            "Preserves your original context while integrating missing concepts and fixing misconceptions."
        )
        suggested_ans = feedback.get("suggested_improved_answer", "")
        if suggested_ans:
            st_module.code(suggested_ans, language="markdown")
        else:
            st_module.caption("No revision blueprint available.")
