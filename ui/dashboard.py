"""
dashboard.py — Dashboard Overview Page

Renders:
- Executive interview attempt KPI cards (Total Attempts, Average Score, Best Score, Recent Progress)
- Interactive Plotly score progression trajectory chart when multiple attempts exist
- Question category distribution breakdown
- Recent candidate interview practice attempts with expandable diagnostics
- Helpful, inviting empty-state onboarding for new candidates
"""

from typing import Any, Dict, List, Optional
from ui.components import create_trend_chart, create_category_pie_chart
from ui.history import get_history_summary


def _get_score_badge(score: float) -> str:
    """Return an HTML badge for a given numerical score."""
    if score >= 85.0:
        return "<span class='badge-excellent'>Excellent</span>"
    elif score >= 70.0:
        return "<span class='badge-good'>Good</span>"
    elif score >= 50.0:
        return "<span class='badge-average'>Average</span>"
    else:
        return "<span class='badge-needs-improvement'>Needs Work</span>"


def render_dashboard(st_module: Any) -> None:
    """
    Render the main dashboard overview page using Streamlit.

    Args:
        st_module: The streamlit module (or mock).
    """
    st_module.markdown("<h1 class='main-title'>Interview Performance Dashboard</h1>", unsafe_allow_html=True)
    st_module.markdown(
        "<p class='sub-title'>Track your interview preparedness, evaluate linguistic and conceptual scores, and monitor progress over time.</p>",
        unsafe_allow_html=True,
    )

    summary = get_history_summary()
    total = summary["total_attempts"]

    if total == 0:
        # Helpful empty-state onboarding for first-time users
        st_module.markdown(
            """
            <div class='empty-state-box'>
                <div class='empty-state-icon'>🎙️</div>
                <div class='empty-state-title'>Welcome to Your Interview Practice Hub</div>
                <div class='empty-state-text'>
                    You haven't completed any interview sessions yet. Choose a question from HR, Behavioral,
                    or Technical tracks, craft your response, and receive transparent multi-dimensional
                    scoring with actionable feedback blueprints.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_a, col_b, col_c = st_module.columns(3)
        with col_a:
            st_module.markdown(
                """
                <div class='metric-card'>
                    <div class='metric-label'>Step 1: Select Prompt</div>
                    <div style='color: #CBD5E1; font-size: 0.9rem; line-height: 1.5;'>
                        Explore 15 curated questions across Behavioral, Technical, and HR domains.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_b:
            st_module.markdown(
                """
                <div class='metric-card'>
                    <div class='metric-label'>Step 2: Compose Response</div>
                    <div style='color: #CBD5E1; font-size: 0.9rem; line-height: 1.5;'>
                        Draft your answer using built-in STAR frameworks, live word counts, and optional timer.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_c:
            st_module.markdown(
                """
                <div class='metric-card'>
                    <div class='metric-label'>Step 3: Analyze & Grow</div>
                    <div style='color: #CBD5E1; font-size: 0.9rem; line-height: 1.5;'>
                        View radar charts, essential concept coverage, verbal habits, and model answer blueprints.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st_module.write("")
        col_center_1, col_center_2, col_center_3 = st_module.columns([1, 2, 1])
        with col_center_2:
            if st_module.button("🚀 Start Your First Practice Interview", type="primary", use_container_width=True):
                st_module.session_state["active_nav"] = "Practice Interview"
                st_module.rerun()
        return

    # 1. KPI Cards (Total Attempts, Average Score, Best Score, Recent Progress)
    kpi1, kpi2, kpi3, kpi4 = st_module.columns(4)

    with kpi1:
        st_module.markdown(
            f"""
            <div class='kpi-card'>
                <div class='kpi-header'>
                    <span class='kpi-title'>Total Attempts</span>
                    <span class='kpi-icon'>🎯</span>
                </div>
                <div class='kpi-value'>{summary['total_attempts']}</div>
                <div class='kpi-subtext'>
                    <span>Across <b>{summary['unique_questions_attempted']}</b> unique prompt(s)</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi2:
        avg_badge = _get_score_badge(summary["average_score"])
        st_module.markdown(
            f"""
            <div class='kpi-card'>
                <div class='kpi-header'>
                    <span class='kpi-title'>Average Score</span>
                    <span class='kpi-icon'>📊</span>
                </div>
                <div class='kpi-value'>{summary['average_score']:.1f}<span style='font-size: 1.1rem; color: #94A3B8;'>/100</span></div>
                <div class='kpi-subtext'>
                    <span>Overall tier: {avg_badge}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi3:
        best_badge = _get_score_badge(summary["highest_score"])
        st_module.markdown(
            f"""
            <div class='kpi-card'>
                <div class='kpi-header'>
                    <span class='kpi-title'>Best Score</span>
                    <span class='kpi-icon'>🏆</span>
                </div>
                <div class='kpi-value'>{summary['highest_score']:.1f}<span style='font-size: 1.1rem; color: #94A3B8;'>/100</span></div>
                <div class='kpi-subtext'>
                    <span>Personal record: {best_badge}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi4:
        recent_prog = summary.get("recent_progress", 0.0)
        prev_score = summary.get("previous_score")

        if total >= 2:
            if recent_prog > 0:
                delta_html = f"<span class='kpi-badge-positive'>+{recent_prog:.1f} pts</span>"
                sub_label = f"vs attempt #{total - 1} ({prev_score:.1f})"
            elif recent_prog < 0:
                delta_html = f"<span class='kpi-badge-negative'>{recent_prog:.1f} pts</span>"
                sub_label = f"vs attempt #{total - 1} ({prev_score:.1f})"
            else:
                delta_html = "<span class='kpi-badge-neutral'>0.0 pts</span>"
                sub_label = f"Equal to attempt #{total - 1}"

            progress_val_str = f"{summary['latest_score']:.1f}"
        else:
            delta_html = "<span class='kpi-badge-neutral'>Baseline</span>"
            sub_label = "Complete 2nd attempt for delta"
            progress_val_str = f"{summary['latest_score']:.1f}"

        st_module.markdown(
            f"""
            <div class='kpi-card'>
                <div class='kpi-header'>
                    <span class='kpi-title'>Recent Progress</span>
                    <span class='kpi-icon'>📈</span>
                </div>
                <div class='kpi-value'>{progress_val_str}<span style='font-size: 1.1rem; color: #94A3B8;'>/100</span></div>
                <div class='kpi-subtext'>
                    {delta_html} <span style='font-size: 0.78rem;'>{sub_label}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Quick Practice CTA Action
    cta_col1, cta_col2 = st_module.columns([3, 1])
    with cta_col1:
        st_module.caption("💡 Select any interview prompt to start a new practice session and track your progress.")
    with cta_col2:
        if st_module.button("🚀 Start Practice Interview", key="btn_dash_start_practice", type="primary", use_container_width=True):
            st_module.session_state["active_nav"] = "Practice Interview"
            st_module.rerun()

    st_module.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

    # 2. Visualizations: Score Progression Trajectory & Category Distribution
    chart_col1, chart_col2 = st_module.columns([3, 2])

    with chart_col1:
        st_module.markdown("### 📈 Score Progression Trajectory")
        if len(summary["scores_trend"]) >= 2:
            st_module.caption("Chronological progression of overall evaluation scores across consecutive attempts.")
            trend_fig = create_trend_chart(summary["scores_trend"])
            st_module.plotly_chart(trend_fig, use_container_width=True)
        else:
            st_module.caption("Track your growth over multiple interview attempts.")
            st_module.info(
                f"ℹ️ **1 attempt recorded so far** (Score: **{summary['latest_score']:.1f}/100**). "
                "Complete at least one more attempt to view your historical progression trajectory."
            )
            # Render single point trend
            trend_fig = create_trend_chart(summary["scores_trend"])
            st_module.plotly_chart(trend_fig, use_container_width=True)

    with chart_col2:
        st_module.markdown("### 📂 Category Distribution")
        st_module.caption("Breakdown of interview categories practiced.")
        cat_fig = create_category_pie_chart(summary["category_distribution"])
        st_module.plotly_chart(cat_fig, use_container_width=True)

    st_module.markdown("---")

    # 3. Recent Activity Feed
    st_module.markdown("### 🕒 Recent Activity")
    recent = summary["recent_activity"]

    if recent:
        for idx, item in enumerate(recent):
            badge = _get_score_badge(item["overall_score"])
            with st_module.expander(
                f"[{item['category']}] {item['question_id']} — Score: {item['overall_score']:.1f}/100 — {item['timestamp']}",
                expanded=(idx == 0),
            ):
                st_module.markdown(f"**Question:** {item['question']}")
                st_module.markdown(
                    f"**Performance:** {badge} &nbsp;|&nbsp; "
                    f"**Category:** `{item['category']}` &nbsp;|&nbsp; "
                    f"**ID:** `{item.get('attempt_id', 'N/A')}`",
                    unsafe_allow_html=True,
                )

                st_module.markdown(f"**Your Answer:** *\"{item['candidate_answer']}\"*")

                c_scores = item.get("component_scores", {})
                sc1, sc2, sc3, sc4 = st_module.columns(4)
                sc1.caption(f"🎯 Semantic: **{c_scores.get('semantic', 0):.1f}**")
                sc2.caption(f"💬 Communication: **{c_scores.get('communication', 0):.1f}**")
                sc3.caption(f"🗣️ Delivery: **{c_scores.get('delivery', 0):.1f}**")
                sc4.caption(f"🏗️ Structure: **{c_scores.get('structure', 0):.1f}**")

                if item.get("actionable_suggestions"):
                    st_module.markdown(
                        f"💡 **Top Suggestion:** {item['actionable_suggestions'][0]}"
                    )
