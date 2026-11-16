"""
app.py — Main Application Entry Point

Automated Interview Performance Analyzer
=========================================
AI-powered interview practice, answer evaluation and personalized feedback.

Launch command:
    streamlit run app.py
"""

import os
import sys

# Ensure project root is in python path
_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

from config.config import PROJECT_NAME, VERSION
from ui.components import CUSTOM_CSS, get_sidebar_mode_css


def run_streamlit_app():
    """Execute the interactive Streamlit web dashboard."""
    import streamlit as st
    import importlib
    import ui.history_view
    importlib.reload(ui.history_view)

    from ui.dashboard import render_dashboard
    from ui.interview import render_practice_interview
    from ui.results import render_results
    from ui.history_view import render_history_view
    from ui.about import render_about_page

    st.set_page_config(
        page_title=f"{PROJECT_NAME}",
        page_icon="🎙️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Initialize sidebar collapse state
    if "sidebar_collapsed" not in st.session_state:
        st.session_state["sidebar_collapsed"] = False

    is_collapsed = st.session_state["sidebar_collapsed"]

    # Inject responsive base CSS + dynamic sidebar collapse mode styling
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    st.markdown(get_sidebar_mode_css(is_collapsed), unsafe_allow_html=True)

    # Manage navigation via session_state
    if "active_nav" not in st.session_state:
        st.session_state["active_nav"] = "Dashboard"

    nav_items = [
        ("Dashboard", "📊", "Dashboard"),
        ("Practice Interview", "🎙️", "Practice Interview"),
        ("Performance Analysis", "📈", "Performance Analysis"),
        ("Interview History", "🕒", "Interview History"),
        ("About Project", "ℹ️", "About Project"),
    ]

    current_nav = st.session_state.get("active_nav", "Dashboard")

    # Sidebar Navigation: Custom Collapsible Sidebar (Expanded vs Icon-Only Rail)
    with st.sidebar:
        if not is_collapsed:
            # ── Expanded State ──────────────────────────────────────────
            col_brand, col_toggle = st.columns([4.2, 1.2])
            with col_brand:
                st.markdown(
                    f"""
                    <div class='sidebar-header' style='border-bottom: none; margin-bottom: 0; padding-bottom: 0;'>
                        <div class='sidebar-logo-icon'>
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#7CB7F5" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
                                <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                                <line x1="12" y1="19" x2="12" y2="22"/>
                            </svg>
                        </div>
                        <div class='sidebar-brand-text'>
                            <div class='sidebar-title'>{PROJECT_NAME}</div>
                            <div class='sidebar-subtitle-row'>
                                <span class='sidebar-subtitle'>AI Practice</span>
                                <span class='sidebar-version-pill'>v{VERSION}</span>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col_toggle:
                if st.button("◀", key="btn_collapse_sidebar", help="Collapse sidebar to icon rail", use_container_width=True):
                    st.session_state["sidebar_collapsed"] = True
                    st.rerun()

            st.markdown("<hr style='border: none; border-top: 1px solid #354253; margin: 0.75rem 0;'>", unsafe_allow_html=True)
            st.markdown("<div class='sidebar-nav-label'>Navigation</div>", unsafe_allow_html=True)

            for page_name, icon, label in nav_items:
                is_active = (current_nav == page_name)
                if st.button(
                    f"{icon}  {label}",
                    key=f"nav_btn_{page_name.lower().replace(' ', '_')}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                ):
                    if st.session_state["active_nav"] != page_name:
                        st.session_state["active_nav"] = page_name
                        st.rerun()

            st.markdown(
                f"""
                <div class='sidebar-footer'>
                    <span class='sidebar-footer-app'>Automated Interview Analyzer</span>
                    <span class='sidebar-footer-ver'>v{VERSION}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            # ── Collapsed State (Icon-Only Rail) ────────────────────────
            if st.button("▶", key="btn_expand_sidebar", help="Expand sidebar", use_container_width=True):
                st.session_state["sidebar_collapsed"] = False
                st.rerun()

            st.markdown(
                """
                <div style='display: flex; justify-content: center; margin: 0.65rem 0 0.85rem 0;'>
                    <div class='sidebar-logo-icon' style='width: 32px; height: 32px;'>
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#7CB7F5" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
                            <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                            <line x1="12" y1="19" x2="12" y2="22"/>
                        </svg>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("<hr style='border: none; border-top: 1px solid #354253; margin: 0.5rem 0 0.75rem 0;'>", unsafe_allow_html=True)

            for page_name, icon, label in nav_items:
                is_active = (current_nav == page_name)
                if st.button(
                    icon,
                    key=f"rail_btn_{page_name.lower().replace(' ', '_')}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                    help=f"Navigate to {label}",
                ):
                    if st.session_state["active_nav"] != page_name:
                        st.session_state["active_nav"] = page_name
                        st.rerun()

            st.markdown(
                f"""
                <div style='margin-top: 2rem; text-align: center;'>
                    <span class='sidebar-version-pill' style='font-size: 0.65rem;'>v{VERSION}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    selected_page = st.session_state.get("active_nav", "Dashboard")

    # Render Active Section
    if selected_page == "Dashboard":
        render_dashboard(st)
    elif selected_page == "Practice Interview":
        render_practice_interview(st)
    elif selected_page == "Performance Analysis":
        render_results(st)
    elif selected_page == "Interview History":
        render_history_view(st)
    elif selected_page == "About Project":
        render_about_page(st)


def run_cli_demo():
    """Fallback interactive CLI demonstration when run directly via python app.py."""
    from modules.scoring import evaluate_answer

    print("=" * 75)
    print(f" {PROJECT_NAME} (v{VERSION})")
    print("=" * 75)
    print("Web Dashboard Mode:")
    print("  To launch the interactive Streamlit dashboard, run:")
    print("    streamlit run app.py")
    print()
    print("CLI Demonstration Mode:")
    print("  Executing candidate evaluation on sample question [TECH001]...")
    print("-" * 75)

    sample_qid = "TECH001"
    sample_answer = (
        "Lists and tuples are both sequence data types in Python. The primary difference is mutability: "
        "lists are mutable, meaning their elements can be modified, added, or removed, while tuples are "
        "immutable. Because tuples are immutable, they are hashable and can be used as dictionary keys. "
        "Tuples also have slight performance and memory advantages due to fixed allocation. Use lists "
        "for dynamic collections and tuples for fixed records."
    )

    result = evaluate_answer(sample_qid, sample_answer)
    print(f"Question:             {result['question']}")
    print(f"Overall Score:        {result['overall_score']} / 100 ({result['performance_category']})")
    print(f"Component Scores:     {result['component_scores']}")
    print(f"Weighted Breakdown:   {result['weighted_contributions']}")
    print()
    print("Personalized Strengths:")
    for s in result["feedback"]["strengths"]:
        print(f"  + {s}")
    print()
    print("Key Actionable Suggestion:")
    for a in result["feedback"]["actionable_suggestions"][:2]:
        print(f"  -> {a}")
    print("=" * 75)


def main():
    """Application entry point."""
    import sys

    # If explicitly requested via command line flag, run the CLI demonstration
    if "--cli" in sys.argv:
        run_cli_demo()
        return

    # Always execute the interactive Streamlit web dashboard
    run_streamlit_app()


if __name__ == "__main__":
    main()
