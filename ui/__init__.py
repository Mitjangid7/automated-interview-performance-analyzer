"""
ui package — Streamlit User Interface & Presentation Layer
"""

from ui.components import (
    create_score_gauge,
    create_radar_chart,
    create_component_bar_chart,
    create_trend_chart,
    create_category_pie_chart,
    CUSTOM_CSS,
)
from ui.history import (
    load_history,
    save_evaluation_to_history,
    get_history_summary,
    compare_two_attempts,
    clear_history,
)

__all__ = [
    "create_score_gauge",
    "create_radar_chart",
    "create_component_bar_chart",
    "create_trend_chart",
    "create_category_pie_chart",
    "CUSTOM_CSS",
    "load_history",
    "save_evaluation_to_history",
    "get_history_summary",
    "compare_two_attempts",
    "clear_history",
]

