"""
test_ui.py — Unit Tests for UI Components, Visualizations, and History Persistence
"""

import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from modules.scoring import evaluate_answer, load_questions_map
from ui.components import (
    create_score_gauge,
    create_radar_chart,
    create_component_bar_chart,
    create_trend_chart,
    create_category_pie_chart,
    CUSTOM_CSS,
    get_sidebar_mode_css,
)
from ui.history import (
    load_history,
    save_evaluation_to_history,
    get_history_summary,
    compare_two_attempts,
    clear_history,
)
from ui.interview import get_approach_guidance


class TestPlotlyVisualizations:
    """Verify that Plotly figures are created with valid schemas without runtime errors."""

    def test_create_score_gauge(self):
        fig = create_score_gauge(85.5, "Excellent")
        assert fig is not None
        assert fig.data[0].value == 85.5

    def test_create_radar_chart(self):
        scores = {
            "semantic": 80.0,
            "communication": 90.0,
            "delivery": 85.0,
            "structure": 75.0,
        }
        fig = create_radar_chart(scores)
        assert fig is not None
        assert len(fig.data) == 1

    def test_create_component_bar_chart(self):
        scores = {"semantic": 80.0, "communication": 70.0, "delivery": 90.0, "structure": 85.0}
        contribs = {"semantic": 32.0, "communication": 14.0, "delivery": 13.5, "structure": 21.25}
        fig = create_component_bar_chart(scores, contribs)
        assert fig is not None
        assert len(fig.data) == 2

    def test_create_trend_chart(self):
        records = [
            {"attempt_num": 1, "score": 65.0, "timestamp": "2026-11-01", "question_id": "TECH001", "category": "Technical"},
            {"attempt_num": 2, "score": 85.0, "timestamp": "2026-11-02", "question_id": "TECH001", "category": "Technical"},
        ]
        fig = create_trend_chart(records)
        assert fig is not None
        assert len(fig.data) == 1

    def test_create_trend_chart_empty(self):
        fig = create_trend_chart([])
        assert fig is not None

    def test_create_category_pie_chart(self):
        dist = {"HR": 3, "Behavioral": 5, "Technical": 8}
        fig = create_category_pie_chart(dist)
        assert fig is not None
        assert len(fig.data) == 1


class TestInterviewHistoryPersistence:
    """Verify JSON persistence, recovery, and clearing of interview history."""

    @pytest.fixture(autouse=True)
    def clean_slate_history(self):
        """Ensure clean history before and after tests."""
        clear_history()
        yield
        clear_history()

    def test_save_and_load_history(self):
        eval_result = evaluate_answer("TECH001", "Lists are mutable and tuples are immutable in Python.")
        q_map = load_questions_map()
        q_data = q_map.get("TECH001", {})

        record = save_evaluation_to_history(eval_result, q_data)
        assert "attempt_id" in record
        assert record["question_id"] == "TECH001"
        assert record["overall_score"] > 0.0

        loaded = load_history()
        assert len(loaded) == 1
        assert loaded[0]["attempt_id"] == record["attempt_id"]

    def test_get_history_summary_empty(self):
        summary = get_history_summary()
        assert summary["total_attempts"] == 0
        assert summary["average_score"] == 0.0
        assert summary["highest_score"] == 0.0

    def test_get_history_summary_with_records(self):
        q_map = load_questions_map()
        q_data = q_map.get("TECH001", {})

        eval1 = evaluate_answer("TECH001", "Basic answer.")
        eval2 = evaluate_answer("TECH001", "Much better explanation of mutability and immutability.")

        save_evaluation_to_history(eval1, q_data)
        save_evaluation_to_history(eval2, q_data)

        summary = get_history_summary()
        assert summary["total_attempts"] == 2
        assert summary["average_score"] > 0.0
        assert len(summary["scores_trend"]) == 2

    def test_clear_history(self):
        eval_res = evaluate_answer("TECH001", "Some test text.")
        save_evaluation_to_history(eval_res)
        assert len(load_history()) == 1

        assert clear_history() is True
        assert len(load_history()) == 0


class TestAttemptComparison:
    """Verify multi-attempt delta calculations and progress feedback."""

    def test_compare_two_attempts_improvement(self):
        earlier = {
            "attempt_id": "ATT-001",
            "overall_score": 60.0,
            "performance_category": "Average",
            "component_scores": {"semantic": 50.0, "communication": 70.0, "delivery": 70.0, "structure": 60.0},
            "keypoint_coverage_pct": 50.0,
        }
        later = {
            "attempt_id": "ATT-002",
            "overall_score": 85.0,
            "performance_category": "Excellent",
            "component_scores": {"semantic": 80.0, "communication": 90.0, "delivery": 90.0, "structure": 80.0},
            "keypoint_coverage_pct": 80.0,
        }
        delta = compare_two_attempts(earlier, later)
        assert delta["score_delta"] == 25.0
        assert delta["component_deltas"]["semantic"] == 30.0
        assert delta["coverage_delta"] == 30.0
        assert "progress" in delta["verdict"].lower()

    def test_compare_two_attempts_regression(self):
        earlier = {
            "attempt_id": "ATT-001",
            "overall_score": 80.0,
            "performance_category": "Good",
            "component_scores": {"semantic": 80.0, "communication": 80.0, "delivery": 80.0, "structure": 80.0},
            "keypoint_coverage_pct": 80.0,
        }
        later = {
            "attempt_id": "ATT-002",
            "overall_score": 50.0,
            "performance_category": "Average",
            "component_scores": {"semantic": 50.0, "communication": 50.0, "delivery": 50.0, "structure": 50.0},
            "keypoint_coverage_pct": 50.0,
        }
        delta = compare_two_attempts(earlier, later)
        assert delta["score_delta"] == -30.0
        assert "decreased" in delta["verdict"].lower()


class TestApproachGuidance:
    """Verify strategic advice generation for different question types."""

    def test_guidance_for_behavioral_star(self):
        q = {"category": "Behavioral", "uses_star_method": True}
        text = get_approach_guidance(q)
        assert "STAR Method" in text
        assert "Situation" in text
        assert "Task" in text
        assert "Action" in text
        assert "Result" in text

    def test_guidance_for_technical(self):
        q = {"category": "Technical", "uses_star_method": False}
        text = get_approach_guidance(q)
        assert "Technical Concept" in text
        assert "Definition" in text


class TestSidebarSlateTheme:
    """Verify Modern SaaS Sidebar (Slate Theme) CSS tokens and structure."""

    def test_sidebar_slate_palette_in_custom_css(self):
        assert "#171E2B" in CUSTOM_CSS  # Main sidebar background
        assert "#202A38" in CUSTOM_CSS  # Secondary background
        assert "#29394D" in CUSTOM_CSS  # Active navigation background
        assert "#7CB7F5" in CUSTOM_CSS  # Primary accent
        assert "#354253" in CUSTOM_CSS  # Dividers
        assert "#A7B2C2" in CUSTOM_CSS  # Secondary text

    def test_sidebar_button_saas_styling_in_custom_css(self):
        assert "stSidebar" in CUSTOM_CSS
        assert "stButton" in CUSTOM_CSS
        assert "sidebar-header" in CUSTOM_CSS
        assert "sidebar-footer" in CUSTOM_CSS

    def test_sidebar_dynamic_collapse_modes(self):
        expanded_css = get_sidebar_mode_css(False)
        assert "260px" in expanded_css
        assert "flex-start" in expanded_css

        collapsed_css = get_sidebar_mode_css(True)
        assert "72px" in collapsed_css
        assert "center" in collapsed_css


class TestTranscriptPopulationAndWidgetState:
    """Verify safe pending-transcript lifecycle and absence of StreamlitWidgetAlreadyInstantiatedError."""

    def test_pending_transcript_applied_before_widget_instantiation(self):
        """Simulate Streamlit session state and verify pending transcript is applied before widget creation."""
        session_state = {
            "pending_transcript_HR001": "My transcribed answer from audio.",
            "answer_input_HR001": "",
        }

        # Step 1: Pre-widget resolution logic (from ui/interview.py)
        qid = "HR001"
        input_key = f"answer_input_{qid}"
        text_area_key = f"text_area_{qid}"
        pending_key = f"pending_transcript_{qid}"

        if session_state.get(pending_key) is not None:
            session_state[text_area_key] = session_state[pending_key]
            session_state[input_key] = session_state[pending_key]
            session_state[pending_key] = None

        # Assert state before text area is created
        assert session_state[text_area_key] == "My transcribed answer from audio."
        assert session_state[input_key] == "My transcribed answer from audio."
        assert session_state[pending_key] is None

    def test_no_mutation_after_widget_instantiation(self):
        """Simulate strict Streamlit widget environment that disallows mutating widget state post-instantiation."""
        instantiated_widgets = set()

        class MockSessionState(dict):
            def __setitem__(self, key, value):
                if key in instantiated_widgets:
                    raise RuntimeError(f"StreamlitWidgetAlreadyInstantiatedError: {key} modified after instantiation")
                super().__setitem__(key, value)

        mock_state = MockSessionState()
        qid = "HR001"
        text_area_key = f"text_area_{qid}"
        input_key = f"answer_input_{qid}"
        pending_key = f"pending_transcript_{qid}"

        mock_state[pending_key] = "Initial speech transcript"

        # Apply pending transcript before widget creation
        if mock_state.get(pending_key) is not None:
            mock_state[text_area_key] = mock_state[pending_key]
            mock_state[input_key] = mock_state[pending_key]
            mock_state[pending_key] = None

        # Widget instantiation
        instantiated_widgets.add(text_area_key)

        # Simulate user editing answer in text area
        edited_answer = "Initial speech transcript with additional edited points."

        # Syncing only to input_key must NOT raise an error
        mock_state[input_key] = edited_answer
        assert mock_state[input_key] == edited_answer

    def test_clear_answer_via_pending_key(self):
        """Verify clear action stages empty string into pending key without touching instantiated widget."""
        mock_state = {
            "text_area_HR001": "Existing long answer",
            "answer_input_HR001": "Existing long answer",
            "pending_transcript_HR001": None,
        }

        # Clear button sets pending_key
        mock_state["pending_transcript_HR001"] = ""
        mock_state["answer_input_HR001"] = ""

        # On next rerun, pre-widget logic clears text_area_key
        qid = "HR001"
        input_key = f"answer_input_{qid}"
        text_area_key = f"text_area_{qid}"
        pending_key = f"pending_transcript_{qid}"

        if mock_state.get(pending_key) is not None:
            mock_state[text_area_key] = mock_state[pending_key]
            mock_state[input_key] = mock_state[pending_key]
            mock_state[pending_key] = None

        assert mock_state[text_area_key] == ""
        assert mock_state[input_key] == ""
        assert mock_state[pending_key] is None

    def test_streamlit_apptest_interview_workflow(self):
        """End-to-end simulation using Streamlit's official AppTest runtime."""
        import os
        from streamlit.testing.v1 import AppTest

        app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app.py"))
        at = AppTest.from_file(app_path)
        at.session_state["active_nav"] = "Practice Interview"
        at.run()
        assert len(at.exception) == 0

        # Type response
        assert len(at.text_area) > 0
        at.text_area[0].input("Candidate response text.")
        at.run()
        assert len(at.exception) == 0

        # Simulate pending transcript
        active_qid = "HR001"
        for k in at.session_state.keys():
            if k.startswith("text_area_"):
                active_qid = k.replace("text_area_", "")
                break
        at.session_state[f"pending_transcript_{active_qid}"] = "Transcribed speech."
        at.run()
        assert len(at.exception) == 0
        assert at.text_area[0].value == "Transcribed speech."

        # Edit transcribed speech
        at.text_area[0].input("Transcribed speech with additional edits.")
        at.run()
        assert len(at.exception) == 0
        assert at.text_area[0].value == "Transcribed speech with additional edits."





