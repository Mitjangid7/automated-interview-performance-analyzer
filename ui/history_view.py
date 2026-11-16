"""
history_view.py — Interview History & Attempt Comparison View

Provides:
- Score progression visualization across recorded practice sessions
- Structured table and card layout of attempts with date, question, category, score, and tier
- Detailed inspection of past evaluations with option to load into Performance Analysis
- Cross-attempt comparison between two attempts with multi-metric deltas
- Safe data management and reset controls
"""

from typing import Any, Dict, List, Optional
from ui.components import create_trend_chart
from ui.history import clear_history, compare_two_attempts, get_history_summary, load_history


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


def render_history_view(st_module: Any) -> None:
    """
    Render the Interview History and Attempt Comparison page in Streamlit.

    Args:
        st_module: Streamlit module (or mock).
    """
    st_module.markdown("<h1 class='main-title'>Interview Practice History</h1>", unsafe_allow_html=True)
    st_module.markdown(
        "<p class='sub-title'>Review previous practice sessions, inspect evaluation details, and compare your progress across attempts.</p>",
        unsafe_allow_html=True,
    )

    history = load_history()

    if not history:
        st_module.markdown(
            """
            <div class='empty-state-box'>
                <div class='empty-state-icon'>📭</div>
                <div class='empty-state-title'>No Saved Interview Attempts Found</div>
                <div class='empty-state-text'>
                    Practice sessions and detailed score breakdowns are automatically saved here after every evaluation.
                    Head over to <b>Practice Interview</b> to take your first session!
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

    summary = get_history_summary()

    # Three functional tabs
    tab_log, tab_compare, tab_manage = st_module.tabs([
        "📜 Attempt Log & Table",
        "⚖️ Compare Two Attempts",
        "⚙️ Manage Data",
    ])

    # 1. ATTEMPT LOG & TABLE
    with tab_log:
        st_module.markdown(f"### Recorded Attempts: **{len(history)}**")

        # Score Progression Trajectory Visualization
        if len(history) >= 2:
            st_module.caption("📈 Score Progression Trajectory across consecutive sessions")
            trend_fig = create_trend_chart(summary["scores_trend"])
            st_module.plotly_chart(trend_fig, use_container_width=True)

        # Overview Table
        table_rows = []
        for idx, r in enumerate(history):
            c_scores = r.get("component_scores", {})
            lvl = r.get("candidate_level", "final_year").replace("_", " ").title()
            table_rows.append({
                "#": idx + 1,
                "Date": r.get("timestamp", "").split(" ")[0],
                "Category": r.get("category", "General"),
                "Level": lvl,
                "Prompt ID": r.get("question_id", "Q"),
                "Overall Score": f"{r.get('overall_score', 0):.1f} / 100",
                "Tier": r.get("performance_category", "Needs Improvement"),
                "Semantic": f"{c_scores.get('semantic', 0):.1f}",
                "Structure": f"{c_scores.get('structure', 0):.1f}",
                "Comm.": f"{c_scores.get('communication', 0):.1f}",
                "Delivery": f"{c_scores.get('delivery', 0):.1f}",
            })

        with st_module.expander("📊 View History Summary Table", expanded=True):
            if table_rows:
                md_table = [
                    "| # | Date | Category | Level | Prompt ID | Overall Score | Tier | Semantic | Structure | Comm. | Delivery |",
                    "| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
                ]
                for row in table_rows:
                    md_table.append(
                        f"| {row['#']} | {row['Date']} | {row['Category']} | {row['Level']} | `{row['Prompt ID']}` | **{row['Overall Score']}** | {row['Tier']} | {row['Semantic']} | {row['Structure']} | {row['Comm.']} | {row['Delivery']} |"
                    )
                st_module.markdown("\n".join(md_table), unsafe_allow_html=True)
            else:
                st_module.caption("No historical records available to display.")

        st_module.markdown("#### Detailed Attempt Cards")
        st_module.caption("Inspect individual responses, component breakdowns, or reopen any attempt in the Performance Analysis view.")

        # Display attempts in reverse chronological order
        for idx, record in enumerate(reversed(history)):
            score = record.get("overall_score", 0.0)
            tier = record.get("performance_category", "Needs Improvement")
            qid = record.get("question_id", "Q")
            cat = record.get("category", "General")
            ts = record.get("timestamp", "")
            att_id = record.get("attempt_id", "")
            badge = _get_badge_html(tier)

            lvl_badge = record.get("candidate_level", "final_year").replace("_", " ").title()
            with st_module.expander(
                f"[{cat}] {qid} — Score: {score:.1f}/100 ({tier}) — {lvl_badge} — {ts}",
                expanded=(idx == 0),
            ):
                st_module.markdown(
                    f"<div style='margin-bottom: 0.5rem;'><b>Attempt ID:</b> <code>{att_id}</code> &nbsp;|&nbsp; "
                    f"<b>Category:</b> <code>{cat}</code> &nbsp;|&nbsp; <b>Level:</b> <code>{lvl_badge}</code> &nbsp;|&nbsp; <b>Status:</b> {badge}</div>",
                    unsafe_allow_html=True,
                )
                st_module.markdown(f"**Question:** {record.get('question', '')}")
                st_module.markdown(f"**Candidate Response:** *\"{record.get('candidate_answer', '')}\"*")

                # Four Component Scores
                c_scores = record.get("component_scores", {})
                w_contribs = record.get("weighted_contributions", {})
                sc1, sc2, sc3, sc4 = st_module.columns(4)
                sc1.metric("🎯 Semantic (40%)", f"{c_scores.get('semantic', 0):.1f}", f"{w_contribs.get('semantic', 0):.1f} pts")
                sc2.metric("🏗️ Structure (25%)", f"{c_scores.get('structure', 0):.1f}", f"{w_contribs.get('structure', 0):.1f} pts")
                sc3.metric("💬 Communication (20%)", f"{c_scores.get('communication', 0):.1f}", f"{w_contribs.get('communication', 0):.1f} pts")
                sc4.metric("🗣️ Delivery (15%)", f"{c_scores.get('delivery', 0):.1f}", f"{w_contribs.get('delivery', 0):.1f} pts")

                col_btn, _ = st_module.columns([2, 3])
                with col_btn:
                    if st_module.button(f"🔍 Open in Performance Analysis", key=f"open_eval_{att_id}", use_container_width=True):
                        # Re-construct evaluation format for results view
                        st_module.session_state["last_evaluation"] = {
                            "question_id": qid,
                            "question": record.get("question", ""),
                            "candidate_answer": record.get("candidate_answer", ""),
                            "overall_score": score,
                            "performance_category": tier,
                            "component_scores": c_scores,
                            "weighted_contributions": w_contribs,
                            "semantic_analysis": {
                                "keypoint_coverage": {"coverage_percentage": record.get("keypoint_coverage_pct", 0)},
                                "semantic_similarity": {"similarity_percentage": 0},
                            },
                            "technical_correctness": {
                                "detected_misconceptions": [],
                                "correctness_observations": [],
                            },
                            "communication_analysis": {
                                "filler_frequency": record.get("filler_frequency", 0),
                                "communication_observations": [],
                            },
                            "delivery_analysis": {},
                            "structure_analysis": {"framework": "General", "structure_score": c_scores.get("structure", 0)},
                            "feedback": {
                                "summary": record.get("feedback_summary", {}),
                                "strengths": record.get("strengths", []),
                                "areas_for_improvement": record.get("areas_for_improvement", []),
                                "actionable_suggestions": record.get("actionable_suggestions", []),
                                "suggested_improved_answer": record.get("suggested_improved_answer", ""),
                            },
                        }
                        st_module.session_state["active_nav"] = "Performance Analysis"
                        st_module.rerun()

                st_module.markdown("##### 🌟 Strengths Recorded:")
                for s in record.get("strengths", []):
                    st_module.markdown(f"- ✅ {s}")

                st_module.markdown("##### 🎯 Improvement Focus:")
                for imp in record.get("areas_for_improvement", []):
                    st_module.markdown(f"- ⚠️ {imp}")

                if record.get("suggested_improved_answer"):
                    with st_module.expander("📝 View Suggested Model Answer"):
                        st_module.code(record.get("suggested_improved_answer"), language="markdown")

    # 2. COMPARE TWO ATTEMPTS
    with tab_compare:
        st_module.markdown("### Compare Two Practice Attempts")
        st_module.caption(
            "Select two attempts to measure score progression, component changes, and conceptual coverage growth."
        )

        if len(history) < 2:
            st_module.info("ℹ️ You need at least two recorded interview attempts to perform a comparative analysis.")
        else:
            attempt_options = {
                h["attempt_id"]: f"{h['attempt_id']} — [{h['category']}] {h['question_id']} ({h['overall_score']:.1f} pts, {h['timestamp']})"
                for h in history
            }
            att_keys = list(attempt_options.keys())

            c_sel1, c_sel2 = st_module.columns(2)
            with c_sel1:
                att_earlier_id = st_module.selectbox(
                    "Baseline Attempt (Earlier)",
                    att_keys,
                    index=0,
                    format_func=lambda k: attempt_options[k],
                )
            with c_sel2:
                att_later_id = st_module.selectbox(
                    "Comparison Attempt (Later)",
                    att_keys,
                    index=len(att_keys) - 1,
                    format_func=lambda k: attempt_options[k],
                )

            att_map = {h["attempt_id"]: h for h in history}
            earlier = att_map[att_earlier_id]
            later = att_map[att_later_id]

            delta_result = compare_two_attempts(earlier, later)

            st_module.markdown("---")
            st_module.markdown(f"### Comparative Verdict: **{delta_result['verdict']}**")

            m1, m2, m3, m4 = st_module.columns(4)
            with m1:
                st_module.metric(
                    "Overall Score",
                    f"{delta_result['later_score']:.1f}",
                    delta=f"{delta_result['score_delta']:+.1f} pts",
                )
            with m2:
                st_module.metric(
                    "Semantic Delta",
                    f"{later['component_scores'].get('semantic', 0):.1f}",
                    delta=f"{delta_result['component_deltas'].get('semantic', 0):+.1f} pts",
                )
            with m3:
                st_module.metric(
                    "Communication Delta",
                    f"{later['component_scores'].get('communication', 0):.1f}",
                    delta=f"{delta_result['component_deltas'].get('communication', 0):+.1f} pts",
                )
            with m4:
                st_module.metric(
                    "Key-Point Coverage",
                    f"{later.get('keypoint_coverage_pct', 0):.1f}%",
                    delta=f"{delta_result['coverage_delta']:+.1f}%",
                )

            # Detailed comparison breakdown
            with st_module.expander("🔍 View Side-by-Side Answers & Notes"):
                col_e, col_l = st_module.columns(2)
                with col_e:
                    st_module.markdown(f"**Baseline [{earlier['attempt_id']}]:**")
                    st_module.markdown(f"*\"{earlier.get('candidate_answer', '')}\"*")
                with col_l:
                    st_module.markdown(f"**Comparison [{later['attempt_id']}]:**")
                    st_module.markdown(f"*\"{later.get('candidate_answer', '')}\"*")

    # 3. MANAGE DATA
    with tab_manage:
        st_module.markdown("### Manage Saved Interview Data")
        st_module.caption(
            "Persistent history is securely stored locally in `data/interview_history.json`. "
            "You can reset your attempt history below if needed."
        )

        st_module.markdown(
            f"""
            <div class='metric-card'>
                <div class='metric-label'>Storage Statistics</div>
                <div style='color: #CBD5E1; font-size: 0.95rem; line-height: 1.6;'>
                    - Total sessions stored: <b>{len(history)}</b><br>
                    - Storage file: <code>data/interview_history.json</code><br>
                    - Persistence engine: JSON serialization with atomic updates
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        confirm_clear = st_module.checkbox("I confirm that I want to permanently clear all interview history.")
        if st_module.button("Clear History Now 🗑️", type="secondary"):
            if confirm_clear:
                if clear_history():
                    st_module.success("Interview history has been cleared successfully.")
                    st_module.rerun()
                else:
                    st_module.error("Failed to clear interview history.")
            else:
                st_module.warning("Please check the confirmation box before clearing history.")
