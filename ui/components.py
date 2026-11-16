"""
components.py — Reusable UI Components, Plotly Visualizations & Visual Layouts

Provides:
- Responsive Plotly interactive charts (Gauge, Radar, Bar, Trend, Pie)
- Zoom-resilient Modern SaaS Slate theme CSS (75% to 150% zoom support)
- Dynamic custom collapsible sidebar (Expanded vs Icon-Only Rail)
- Reusable UI layout helpers: render_page_header, render_empty_state
"""

from typing import Any, Dict, List, Optional
import plotly.graph_objects as go


# ── CSS Theme Styling (Slate Theme + Zoom-Resilient Responsive Design) ────────

CUSTOM_CSS = """
<style>
/* 1. Global Reset & Box-Sizing */
*, *::before, *::after {
    box-sizing: border-box;
}

/* Hide Streamlit default Deploy button, header chrome, and default collapse controls */
.stDeployButton, [data-testid="stToolbarActions"], footer,
[data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"] {
    display: none !important;
}

/* Typography & Smooth Font */
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', Roboto, sans-serif;
    color: #F8FAFC;
    background-color: #0B0F17;
}

/* Prevent horizontal overflow across all zoom levels (75% to 150%) */
[data-testid="stAppViewContainer"] {
    overflow-x: hidden !important;
    max-width: 100vw !important;
    background-color: #0B0F17 !important;
}

[data-testid="stMain"] {
    overflow-x: hidden !important;
    min-width: 0 !important;
}

[data-testid="stMain"] > div {
    padding-top: 1.25rem !important;
    padding-bottom: 2.5rem !important;
    padding-left: clamp(0.75rem, 2.5vw, 2.25rem) !important;
    padding-right: clamp(0.75rem, 2.5vw, 2.25rem) !important;
    max-width: 100% !important;
}

/* Column wrapping & zero min-width to avoid flex blowout at high zoom */
[data-testid="column"] {
    min-width: 0 !important;
    flex-shrink: 1 !important;
}

/* Responsive Column Wrapping & Stack on Tablet / Mobile / High Zoom (125%-150%) */
@media screen and (max-width: 992px) {
    [data-testid="stMain"] [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
        gap: 0.75rem !important;
    }
    [data-testid="stMain"] [data-testid="stHorizontalBlock"] > [data-testid="column"] {
        flex: 1 1 calc(50% - 0.75rem) !important;
        min-width: calc(50% - 0.75rem) !important;
    }
}

@media screen and (max-width: 640px) {
    [data-testid="stMain"] [data-testid="stHorizontalBlock"] > [data-testid="column"] {
        flex: 1 1 100% !important;
        min-width: 100% !important;
    }
}

/* Text Wrapping throughout UI */
.stMarkdown, p, div, span, h1, h2, h3, h4, h5, h6 {
    word-break: break-word;
    overflow-wrap: break-word;
}

/* 2. Responsive Page Headers */
.main-title {
    font-size: clamp(1.4rem, 2.4vw, 2rem) !important;
    font-weight: 800;
    color: #F8FAFC;
    letter-spacing: -0.02em;
    line-height: 1.25;
    margin-bottom: 0.25rem;
}
.sub-title {
    font-size: clamp(0.85rem, 1.2vw, 1rem) !important;
    color: #94A3B8;
    line-height: 1.45;
    margin-bottom: 1.25rem;
}

/* 3. Slate Cards & Surface Containers */
.kpi-card, .metric-card {
    background: #161F2E;
    border: 1px solid #2A3649;
    border-radius: 10px;
    padding: clamp(0.85rem, 1.5vw, 1.15rem);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.25);
    margin-bottom: 0.85rem;
    transition: all 0.15s ease-in-out;
    min-width: 0;
    max-width: 100%;
}
.kpi-card:hover, .metric-card:hover {
    border-color: #7CB7F5;
    transform: translateY(-2px);
    box-shadow: 0 8px 16px -2px rgba(124, 183, 245, 0.1);
}
.kpi-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.4rem;
}
.kpi-title, .metric-label {
    font-size: clamp(0.7rem, 0.9vw, 0.8rem);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #94A3B8;
}
.kpi-icon {
    font-size: 1.1rem;
}
.kpi-value, .metric-value {
    font-size: clamp(1.35rem, 2.2vw, 1.95rem);
    font-weight: 800;
    color: #F8FAFC;
    line-height: 1.15;
    margin-bottom: 0.25rem;
}
.kpi-subtext, .metric-subtext {
    font-size: clamp(0.72rem, 0.9vw, 0.82rem);
    color: #CBD5E1;
    display: flex;
    align-items: center;
    gap: 0.35rem;
    flex-wrap: wrap;
}

/* KPI Status Badges */
.kpi-badge-positive {
    background: rgba(16, 185, 129, 0.15);
    color: #34D399;
    border: 1px solid rgba(16, 185, 129, 0.35);
    padding: 0.12rem 0.45rem;
    border-radius: 4px;
    font-weight: 600;
    font-size: 0.74rem;
    display: inline-block;
}
.kpi-badge-neutral {
    background: rgba(148, 163, 184, 0.15);
    color: #CBD5E1;
    border: 1px solid rgba(148, 163, 184, 0.3);
    padding: 0.12rem 0.45rem;
    border-radius: 4px;
    font-weight: 600;
    font-size: 0.74rem;
    display: inline-block;
}
.kpi-badge-negative {
    background: rgba(239, 68, 68, 0.15);
    color: #F87171;
    border: 1px solid rgba(239, 68, 68, 0.35);
    padding: 0.12rem 0.45rem;
    border-radius: 4px;
    font-weight: 600;
    font-size: 0.74rem;
    display: inline-block;
}

/* Question Presentation Box */
.question-card {
    background: #161F2E;
    border: 1px solid #2A3649;
    border-left: 4px solid #7CB7F5;
    border-radius: 10px;
    padding: 1.15rem 1.35rem;
    margin-bottom: 1rem;
    max-width: 100%;
}
.question-tag {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    font-size: 0.74rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.4rem;
}
.tag-hr {
    background: rgba(139, 92, 246, 0.18);
    color: #C084FC;
    border: 1px solid rgba(139, 92, 246, 0.35);
}
.tag-behavioral {
    background: rgba(16, 185, 129, 0.18);
    color: #34D399;
    border: 1px solid rgba(16, 185, 129, 0.35);
}
.tag-technical {
    background: rgba(124, 183, 245, 0.18);
    color: #7CB7F5;
    border: 1px solid rgba(124, 183, 245, 0.35);
}
.question-text {
    font-size: clamp(1rem, 1.4vw, 1.12rem);
    font-weight: 600;
    color: #F8FAFC;
    line-height: 1.45;
    margin: 0;
}

/* Performance Badges */
.badge-excellent {
    background-color: rgba(16, 185, 129, 0.18);
    color: #34D399;
    border: 1px solid rgba(16, 185, 129, 0.35);
    padding: 0.2rem 0.65rem;
    border-radius: 9999px;
    font-weight: 600;
    font-size: 0.8rem;
    display: inline-block;
}
.badge-good {
    background-color: rgba(124, 183, 245, 0.18);
    color: #7CB7F5;
    border: 1px solid rgba(124, 183, 245, 0.35);
    padding: 0.2rem 0.65rem;
    border-radius: 9999px;
    font-weight: 600;
    font-size: 0.8rem;
    display: inline-block;
}
.badge-average {
    background-color: rgba(245, 158, 11, 0.18);
    color: #FBBF24;
    border: 1px solid rgba(245, 158, 11, 0.35);
    padding: 0.2rem 0.65rem;
    border-radius: 9999px;
    font-weight: 600;
    font-size: 0.8rem;
    display: inline-block;
}
.badge-needs-improvement {
    background-color: rgba(239, 68, 68, 0.18);
    color: #F87171;
    border: 1px solid rgba(239, 68, 68, 0.35);
    padding: 0.2rem 0.65rem;
    border-radius: 9999px;
    font-weight: 600;
    font-size: 0.8rem;
    display: inline-block;
}

/* Feedback & Diagnostic Callouts */
.card-strength {
    background-color: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.25);
    border-left: 4px solid #10B981;
    border-radius: 6px;
    padding: 0.75rem 0.95rem;
    margin-bottom: 0.65rem;
    color: #E2E8F0;
    font-size: 0.9rem;
}
.card-improvement {
    background-color: rgba(245, 158, 11, 0.1);
    border: 1px solid rgba(245, 158, 11, 0.25);
    border-left: 4px solid #F59E0B;
    border-radius: 6px;
    padding: 0.75rem 0.95rem;
    margin-bottom: 0.65rem;
    color: #E2E8F0;
    font-size: 0.9rem;
}
.card-misconception {
    background-color: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.25);
    border-left: 4px solid #EF4444;
    border-radius: 6px;
    padding: 0.85rem 1rem;
    margin-bottom: 0.75rem;
    color: #E2E8F0;
    font-size: 0.9rem;
}

/* Checklist items */
.checklist-item {
    display: flex;
    align-items: center;
    padding: 0.55rem 0.75rem;
    border-radius: 6px;
    margin-bottom: 0.4rem;
    font-size: 0.9rem;
    border: 1px solid transparent;
}
.checklist-item.detected {
    background-color: rgba(16, 185, 129, 0.1);
    border-color: rgba(16, 185, 129, 0.25);
    color: #34D399;
    font-weight: 600;
}
.checklist-item.partial {
    background-color: rgba(245, 158, 11, 0.1);
    border-color: rgba(245, 158, 11, 0.25);
    color: #FBBF24;
    font-weight: 500;
}
.checklist-item.missing {
    background-color: rgba(239, 68, 68, 0.1);
    border-color: rgba(239, 68, 68, 0.25);
    color: #F87171;
}

/* Counter Bar below answer area */
.counter-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #161F2E;
    border: 1px solid #2A3649;
    border-radius: 6px;
    padding: 0.5rem 0.85rem;
    margin-top: 0.35rem;
    margin-bottom: 0.85rem;
    font-size: 0.82rem;
    color: #94A3B8;
    flex-wrap: wrap;
    gap: 0.4rem;
}
.counter-metric {
    display: flex;
    align-items: center;
    gap: 0.35rem;
}
.counter-metric strong {
    color: #F8FAFC;
}

/* Empty State Container */
.empty-state-box {
    text-align: center;
    padding: clamp(2rem, 5vw, 3.5rem) 1.5rem;
    background: #161F2E;
    border: 1px dashed #354253;
    border-radius: 12px;
    margin: 1.25rem 0;
}
.empty-state-icon {
    font-size: 2.8rem;
    margin-bottom: 0.75rem;
}
.empty-state-title {
    font-size: clamp(1.15rem, 1.8vw, 1.35rem);
    font-weight: 700;
    color: #F8FAFC;
    margin-bottom: 0.4rem;
}
.empty-state-text {
    font-size: 0.92rem;
    color: #94A3B8;
    max-width: 520px;
    margin: 0 auto 1.25rem auto;
    line-height: 1.5;
}

/* 4. Modern SaaS Sidebar (Slate Theme) */
[data-testid="stSidebar"] {
    background-color: #171E2B !important;
    border-right: 1px solid #354253 !important;
    overflow-x: hidden !important;
    transform: none !important;
    visibility: visible !important;
}

[data-testid="stSidebar"] > div:first-child {
    background-color: #171E2B !important;
}

/* Sidebar header & branding */
.sidebar-header {
    display: flex;
    align-items: flex-start;
    gap: 0.65rem;
    padding: 0.15rem 0 0.85rem 0;
    border-bottom: 1px solid #354253;
    margin-bottom: 0.95rem;
}
.sidebar-logo-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 34px;
    height: 34px;
    border-radius: 6px;
    background: #202A38;
    border: 1px solid #354253;
    flex-shrink: 0;
    margin-top: 2px;
}
.sidebar-brand-text {
    display: flex;
    flex-direction: column;
    min-width: 0;
    flex: 1;
}
.sidebar-title {
    font-size: 0.88rem;
    font-weight: 700;
    color: #F1F5F9;
    line-height: 1.3;
    letter-spacing: -0.01em;
    word-break: break-word;
}
.sidebar-subtitle-row {
    display: flex;
    align-items: center;
    gap: 0.35rem;
    margin-top: 0.2rem;
    flex-wrap: wrap;
}
.sidebar-subtitle {
    font-size: 0.72rem;
    color: #A7B2C2;
    line-height: 1.2;
}
.sidebar-version-pill {
    background: #202A38;
    color: #8290A3;
    border: 1px solid #354253;
    border-radius: 4px;
    padding: 0.05rem 0.35rem;
    font-size: 0.68rem;
    font-weight: 600;
    font-family: 'JetBrains Mono', Consolas, monospace;
}

/* Section Label */
.sidebar-nav-label {
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #8290A3;
    margin-bottom: 0.5rem;
    padding-left: 0.2rem;
}

/* Sidebar Button Navigation */
[data-testid="stSidebar"] [data-testid="stButton"] {
    margin-bottom: 0.25rem !important;
}

[data-testid="stSidebar"] [data-testid="stButton"] button {
    display: flex !important;
    align-items: center !important;
    width: 100% !important;
    min-height: 38px !important;
    border-radius: 6px !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    transition: background-color 0.15s ease, color 0.15s ease, border-color 0.15s ease !important;
    user-select: none !important;
    border: 1px solid transparent !important;
    border-left: 3px solid transparent !important;
}

/* Secondary (Inactive) Navigation Button */
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="secondary"],
[data-testid="stSidebar"] [data-testid="stButton"] button[data-testid="baseButton-secondary"],
[data-testid="stSidebar"] [data-testid="stButton"] button:not([kind="primary"]) {
    background-color: transparent !important;
    color: #A7B2C2 !important;
    border-color: transparent !important;
    border-left-color: transparent !important;
    box-shadow: none !important;
}

[data-testid="stSidebar"] [data-testid="stButton"] button[kind="secondary"] p,
[data-testid="stSidebar"] [data-testid="stButton"] button[data-testid="baseButton-secondary"] p,
[data-testid="stSidebar"] [data-testid="stButton"] button:not([kind="primary"]) p {
    color: #A7B2C2 !important;
}

[data-testid="stSidebar"] [data-testid="stButton"] button[kind="secondary"]:hover,
[data-testid="stSidebar"] [data-testid="stButton"] button[data-testid="baseButton-secondary"]:hover,
[data-testid="stSidebar"] [data-testid="stButton"] button:not([kind="primary"]):hover {
    background-color: #202A38 !important;
    color: #F1F5F9 !important;
    border-color: #354253 !important;
    border-left-color: #354253 !important;
}

[data-testid="stSidebar"] [data-testid="stButton"] button[kind="secondary"]:hover p,
[data-testid="stSidebar"] [data-testid="stButton"] button[data-testid="baseButton-secondary"]:hover p,
[data-testid="stSidebar"] [data-testid="stButton"] button:not([kind="primary"]):hover p {
    color: #F1F5F9 !important;
}

/* Primary (Active) Navigation Button */
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"],
[data-testid="stSidebar"] [data-testid="stButton"] button[data-testid="baseButton-primary"] {
    background-color: #29394D !important;
    color: #F1F5F9 !important;
    font-weight: 600 !important;
    border: 1px solid #354253 !important;
    border-left: 3px solid #7CB7F5 !important;
    box-shadow: none !important;
}

[data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] p,
[data-testid="stSidebar"] [data-testid="stButton"] button[data-testid="baseButton-primary"] p {
    color: #F1F5F9 !important;
    font-weight: 600 !important;
}

/* Sidebar Collapse/Expand Toggle Button */
[data-testid="stSidebar"] .st-key-btn_collapse_sidebar button,
[data-testid="stSidebar"] .st-key-btn_expand_sidebar button,
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] [data-testid="column"]:last-child [data-testid="stButton"] button {
    background-color: #24354D !important;
    color: #93C5FD !important;
    border: 1.5px solid #4A6385 !important;
    border-radius: 8px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    min-height: 34px !important;
    padding: 0.2rem 0.5rem !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.25) !important;
}

[data-testid="stSidebar"] .st-key-btn_collapse_sidebar button *,
[data-testid="stSidebar"] .st-key-btn_expand_sidebar button *,
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] [data-testid="column"]:last-child [data-testid="stButton"] button * {
    color: #93C5FD !important;
    font-size: 1.05rem !important;
    font-weight: 800 !important;
    text-align: center !important;
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1 !important;
    visibility: visible !important;
    opacity: 1 !important;
}

[data-testid="stSidebar"] .st-key-btn_collapse_sidebar button:hover,
[data-testid="stSidebar"] .st-key-btn_expand_sidebar button:hover,
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] [data-testid="column"]:last-child [data-testid="stButton"] button:hover {
    background-color: #3B82F6 !important;
    border-color: #93C5FD !important;
    color: #FFFFFF !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4) !important;
}

[data-testid="stSidebar"] .st-key-btn_collapse_sidebar button:hover *,
[data-testid="stSidebar"] .st-key-btn_expand_sidebar button:hover *,
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] [data-testid="column"]:last-child [data-testid="stButton"] button:hover * {
    color: #FFFFFF !important;
}

/* Sidebar Footer */
.sidebar-footer {
    border-top: 1px solid #354253;
    padding-top: 0.75rem;
    margin-top: 1.8rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.sidebar-footer-app {
    font-size: 0.74rem;
    font-weight: 600;
    color: #A7B2C2;
}
.sidebar-footer-ver {
    font-size: 0.68rem;
    color: #8290A3;
    font-family: 'JetBrains Mono', Consolas, monospace;
}
</style>
"""


def get_sidebar_mode_css(is_collapsed: bool) -> str:
    """
    Generate dynamic scoped CSS for the custom sidebar collapse state:
    - Expanded: 260px comfortable width, left-aligned buttons with labels.
    - Collapsed: 72px narrow icon-only rail, centered icon buttons with hover tooltips.
    """
    if is_collapsed:
        return """
        <style>
        [data-testid="stSidebar"] {
            width: 72px !important;
            min-width: 72px !important;
            max-width: 72px !important;
            transition: width 0.2s ease-in-out !important;
            transform: none !important;
            visibility: visible !important;
        }
        [data-testid="stSidebar"] > div:first-child {
            width: 72px !important;
            min-width: 72px !important;
            padding: 0.75rem 0.35rem !important;
        }
        [data-testid="stSidebar"] [data-testid="stButton"] button {
            justify-content: center !important;
            padding: 0.55rem 0.2rem !important;
            font-size: 1.15rem !important;
        }
        [data-testid="stSidebar"] [data-testid="stButton"] button p {
            text-align: center !important;
            font-size: 1.15rem !important;
        }
        [data-testid="stSidebar"] .st-key-btn_expand_sidebar button {
            background-color: #24354D !important;
            border: 1.5px solid #4A6385 !important;
            color: #93C5FD !important;
            margin-bottom: 0.35rem !important;
            border-radius: 8px !important;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }
        [data-testid="stSidebar"] .st-key-btn_expand_sidebar button:hover {
            background-color: #3B82F6 !important;
            border-color: #93C5FD !important;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4) !important;
        }
        [data-testid="stSidebar"] .st-key-btn_expand_sidebar button * {
            color: #93C5FD !important;
            font-size: 1.05rem !important;
            font-weight: 800 !important;
            visibility: visible !important;
            opacity: 1 !important;
        }
        [data-testid="stSidebar"] .st-key-btn_expand_sidebar button:hover * {
            color: #FFFFFF !important;
        }
        </style>
        """
    else:
        return """
        <style>
        [data-testid="stSidebar"] {
            width: 260px !important;
            min-width: 260px !important;
            max-width: 260px !important;
            transition: width 0.2s ease-in-out !important;
            transform: none !important;
            visibility: visible !important;
        }
        [data-testid="stSidebar"] > div:first-child {
            width: 260px !important;
            min-width: 260px !important;
            padding: 1rem 0.9rem !important;
        }
        [data-testid="stSidebar"] [data-testid="stButton"] button {
            justify-content: flex-start !important;
            padding: 0.55rem 0.85rem !important;
            font-size: 0.89rem !important;
        }
        [data-testid="stSidebar"] [data-testid="stButton"] button p {
            text-align: left !important;
            font-size: 0.89rem !important;
        }
        </style>
        """


# ── Reusable Layout Helpers ───────────────────────────────────────────────────

def render_page_header(st_module: Any, title: str, subtitle: str) -> None:
    """Render a clean, responsive page header with consistent typography."""
    st_module.markdown(f"<h1 class='main-title'>{title}</h1>", unsafe_allow_html=True)
    st_module.markdown(f"<p class='sub-title'>{subtitle}</p>", unsafe_allow_html=True)


# ── Interactive Plotly Visualizations (Responsive & Slate-Themed) ─────────────

def create_score_gauge(score: float, category: str) -> go.Figure:
    """
    Create a circular gauge chart displaying the candidate's overall score,
    customized for high-contrast visibility on dark slate backgrounds.
    """
    if score >= 85.0:
        bar_color = "#10B981"
    elif score >= 70.0:
        bar_color = "#7CB7F5"
    elif score >= 50.0:
        bar_color = "#F59E0B"
    else:
        bar_color = "#EF4444"

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={
                "suffix": "/100",
                "font": {"size": 32, "family": "Inter, sans-serif", "color": "#F8FAFC"},
            },
            title={
                "text": f"<b>{category}</b>",
                "font": {"size": 17, "color": bar_color, "family": "Inter, sans-serif"},
            },
            gauge={
                "axis": {
                    "range": [0, 100],
                    "tickwidth": 1,
                    "tickcolor": "#94A3B8",
                    "tickfont": {"color": "#94A3B8", "size": 10},
                },
                "bar": {"color": bar_color, "thickness": 0.28},
                "bgcolor": "#1E293B",
                "borderwidth": 1,
                "bordercolor": "#334155",
                "steps": [
                    {"range": [0, 50], "color": "rgba(239, 68, 68, 0.18)"},
                    {"range": [50, 70], "color": "rgba(245, 158, 11, 0.18)"},
                    {"range": [70, 85], "color": "rgba(124, 183, 245, 0.18)"},
                    {"range": [85, 100], "color": "rgba(16, 185, 129, 0.18)"},
                ],
            },
        )
    )
    fig.update_layout(
        autosize=True,
        height=210,
        margin={"l": 20, "r": 20, "t": 30, "b": 10},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, sans-serif", "color": "#F1F5F9"},
    )
    return fig


def create_radar_chart(component_scores: Dict[str, float]) -> go.Figure:
    """
    Create an interactive 4-axis radar chart showing dimensional performance balance.
    """
    categories = [
        "Semantic (40%)",
        "Communication (20%)",
        "Delivery (15%)",
        "Structure (25%)",
    ]
    values = [
        component_scores.get("semantic", 0.0),
        component_scores.get("communication", 0.0),
        component_scores.get("delivery", 0.0),
        component_scores.get("structure", 0.0),
    ]
    # Close polygon
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=values_closed,
            theta=categories_closed,
            fill="toself",
            fillcolor="rgba(124, 183, 245, 0.22)",
            line={"color": "#7CB7F5", "width": 2.2},
            marker={"size": 6, "color": "#93C5FD"},
            name="Component Score",
        )
    )

    fig.update_layout(
        autosize=True,
        polar={
            "bgcolor": "#161F2E",
            "radialaxis": {
                "visible": True,
                "range": [0, 100],
                "tickfont": {"size": 9, "color": "#94A3B8"},
                "gridcolor": "#2A3649",
                "linecolor": "#354253",
            },
            "angularaxis": {
                "tickfont": {"size": 10, "color": "#CBD5E1", "family": "Inter, sans-serif"},
                "gridcolor": "#2A3649",
                "linecolor": "#354253",
                "rotation": 90,
                "direction": "clockwise",
            },
        },
        height=280,
        margin={"l": 40, "r": 40, "t": 25, "b": 25},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    return fig


def create_component_bar_chart(
    component_scores: Dict[str, float],
    weighted_contributions: Dict[str, float],
) -> go.Figure:
    """
    Create a paired bar chart displaying raw component scores and weighted contribution.
    """
    labels = ["Semantic", "Communication", "Delivery", "Structure"]
    keys = ["semantic", "communication", "delivery", "structure"]

    raw_vals = [component_scores.get(k, 0.0) for k in keys]
    contrib_vals = [weighted_contributions.get(k, 0.0) for k in keys]

    fig = go.Figure(
        data=[
            go.Bar(
                name="Raw Score (0-100)",
                x=labels,
                y=raw_vals,
                marker_color="#7CB7F5",
                text=[f"{v:.0f}" for v in raw_vals],
                textposition="auto",
                textfont={"color": "#FFFFFF", "size": 10},
            ),
            go.Bar(
                name="Weighted Pts",
                x=labels,
                y=contrib_vals,
                marker_color="#10B981",
                text=[f"{v:.1f}" for v in contrib_vals],
                textposition="auto",
                textfont={"color": "#FFFFFF", "size": 10},
            ),
        ]
    )

    fig.update_layout(
        autosize=True,
        barmode="group",
        yaxis={
            "range": [0, 105],
            "title": {"text": "Score / Points", "font": {"color": "#CBD5E1", "size": 11}},
            "gridcolor": "#2A3649",
            "tickfont": {"color": "#94A3B8", "size": 10},
        },
        xaxis={
            "title": "",
            "tickfont": {"color": "#CBD5E1", "size": 10},
        },
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
            "font": {"color": "#CBD5E1", "size": 10},
        },
        height=260,
        margin={"l": 20, "r": 20, "t": 30, "b": 15},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, sans-serif"},
    )
    return fig


def create_trend_chart(scores_trend: List[Dict[str, Any]]) -> go.Figure:
    """
    Plot score trajectory over historical interview attempts.
    """
    if not scores_trend:
        fig = go.Figure()
        fig.update_layout(
            autosize=True,
            title={"text": "No attempt data available", "font": {"color": "#94A3B8", "size": 12}},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=260,
        )
        return fig

    attempts = [f"#{r['attempt_num']}" for r in scores_trend]
    overall_scores = [r["score"] for r in scores_trend]
    hover_texts = [
        f"<b>Attempt #{r['attempt_num']}</b><br>Score: {r['score']:.1f}/100<br>"
        f"Category: {r['category']}<br>Prompt: {r['question_id']}<br>"
        f"Date: {r['timestamp']}"
        for r in scores_trend
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=attempts,
            y=overall_scores,
            mode="lines+markers+text",
            name="Overall Score",
            line={"color": "#7CB7F5", "width": 2.5, "shape": "spline"},
            marker={"size": 8, "color": "#93C5FD", "line": {"width": 1.5, "color": "#1E3A8A"}},
            text=[f"{s:.0f}" for s in overall_scores],
            textposition="top center",
            textfont={"color": "#F8FAFC", "size": 10, "family": "Inter, sans-serif"},
            hoverinfo="text",
            hovertext=hover_texts,
        )
    )

    # Reference benchmark line at 70
    fig.add_hline(
        y=70,
        line_dash="dot",
        line_color="#10B981",
        annotation_text="Benchmark (70)",
        annotation_position="bottom right",
        annotation_font={"color": "#34D399", "size": 9},
    )

    fig.update_layout(
        autosize=True,
        yaxis={
            "range": [0, 105],
            "title": {"text": "Overall Score", "font": {"color": "#CBD5E1", "size": 11}},
            "gridcolor": "#2A3649",
            "tickfont": {"color": "#94A3B8", "size": 10},
        },
        xaxis={
            "gridcolor": "#2A3649",
            "tickfont": {"color": "#CBD5E1", "size": 10},
        },
        height=260,
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, sans-serif"},
    )
    return fig


def create_category_pie_chart(category_distribution: Dict[str, int]) -> go.Figure:
    """
    Donut chart of interview questions practiced by category.
    """
    labels = list(category_distribution.keys())
    values = list(category_distribution.values())

    colors = ["#7CB7F5", "#10B981", "#A78BFA", "#F59E0B"]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.6,
                marker={"colors": colors[: len(labels)], "line": {"color": "#0B0F17", "width": 1.5}},
                textinfo="label+value",
                textfont={"color": "#F8FAFC", "size": 10},
            )
        ]
    )
    fig.update_layout(
        autosize=True,
        height=240,
        margin={"l": 15, "r": 15, "t": 10, "b": 10},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        font={"family": "Inter, sans-serif"},
    )
    return fig
