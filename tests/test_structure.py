"""
test_structure.py — Unit Tests for Answer Structure and STAR Method Detection
"""

import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from modules.structure_analysis import (
    detect_star_structure,
    detect_skills_evidence_strengths_alignment_structure,
    detect_definition_need_norm_std_example_structure,
    analyze_structure,
)


class TestSTARStructureDetection:
    """Tests for detect_star_structure."""

    def test_complete_star_response(self):
        text = (
            "Situation: In my previous role at our analytics company, our database was crashing under peak loads. "
            "Task: My responsibility was to identify bottlenecks and optimize the slow-performing queries. "
            "Action: I analyzed slow query logs, implemented redis caching for repeated joins, and added composite indexes. "
            "Result: We achieved a 65% reduction in query latency, and our uptime improved to 99.9%."
        )
        res = detect_star_structure(text, is_behavioral=True)
        assert res["applicable"] is True
        assert res["situation_detected"] is True
        assert res["task_detected"] is True
        assert res["action_detected"] is True
        assert res["result_detected"] is True
        assert res["star_completeness_ratio"] == 1.0
        assert len(res["components_detected"]) == 4
        assert len(res["components_missing"]) == 0
        assert len(res["supporting_sentences"]["Situation"]) > 0
        assert len(res["supporting_sentences"]["Task"]) > 0
        assert len(res["supporting_sentences"]["Action"]) > 0
        assert len(res["supporting_sentences"]["Result"]) > 0

    def test_missing_result_component(self):
        text = (
            "During my internship at tech corp, our team had to build a dashboard. "
            "My responsibility was to design the REST endpoints. "
            "I developed three endpoints using FastAPI and wrote automated tests."
        )
        res = detect_star_structure(text, is_behavioral=True)
        assert res["applicable"] is True
        assert res["situation_detected"] is True
        assert res["task_detected"] is True
        assert res["action_detected"] is True
        assert res["result_detected"] is False
        assert "Result" in res["components_missing"]
        assert res["star_completeness_ratio"] == 0.75

    def test_missing_action_component(self):
        text = (
            "At my previous job, our payment service stopped processing transactions. "
            "I was assigned to fix the outage and report to the VP. "
            "As a result, we recovered all lost records and our client renewed the contract."
        )
        res = detect_star_structure(text, is_behavioral=True)
        assert res["applicable"] is True
        assert res["situation_detected"] is True
        assert res["task_detected"] is True
        assert res["action_detected"] is False
        assert res["result_detected"] is True
        assert "Action" in res["components_missing"]
        assert res["star_completeness_ratio"] == 0.75

    def test_non_star_technical_answer_when_behavioral_flag_set(self):
        # A purely factual definition (e.g., Python lists vs tuples) evaluated in STAR
        text = "Lists are mutable sequences in Python, while tuples are immutable."
        res = detect_star_structure(text, is_behavioral=True)
        assert res["applicable"] is True
        assert res["star_completeness_ratio"] < 0.5
        assert len(res["components_missing"]) >= 3

    def test_empty_response(self):
        res = detect_star_structure("", is_behavioral=True)
        assert res["applicable"] is True
        assert res["star_completeness_ratio"] == 0.0
        assert len(res["components_missing"]) == 4

    def test_non_behavioral_flag_returns_not_applicable(self):
        text = "Lists and tuples are sequences in Python."
        res = detect_star_structure(text, is_behavioral=False)
        assert res["applicable"] is False
        assert res["star_completeness_ratio"] == 0.0
        assert "not applicable" in res["observations"][0].lower()

    def test_with_question_metadata_behavioral(self):
        question = {
            "question_id": "BEH001",
            "category": "Behavioral",
            "uses_star_method": True
        }
        text = (
            "In my previous project, we were tasked with a data migration. "
            "My responsibility was ETL architecture. "
            "I implemented a distributed worker pool. "
            "We achieved completion two weeks early."
        )
        res = detect_star_structure(text, question=question)
        assert res["applicable"] is True
        assert res["situation_detected"] is True
        assert res["star_completeness_ratio"] == 1.0

    def test_with_question_metadata_technical(self):
        question = {
            "question_id": "TECH001",
            "category": "Technical",
            "uses_star_method": False
        }
        text = "An INNER JOIN returns matching records, whereas LEFT JOIN returns all left rows."
        res = detect_star_structure(text, question=question)
        assert res["applicable"] is False
        assert "not applicable" in res["observations"][0].lower()

    def test_exact_observed_behavioral_answer_detects_all_star_components(self):
        """Regression test for the exact candidate answer that previously reported Situation as Missing."""
        text = (
            "During an academic group project, our team faced a disagreement regarding the technology we should use "
            "for implementation. Some members preferred one approach, while others supported a different solution. "
            "My responsibility was to help the team reach a decision without delaying the project. "
            "I organized a discussion where everyone explained their approach, and we compared the advantages and "
            "disadvantages of each option. We finally selected the approach that best matched our project requirements "
            "and divided the implementation tasks among team members. "
            "As a result, we completed the feature on time and improved our coordination and teamwork."
        )
        res = detect_star_structure(text, is_behavioral=True)
        assert res["applicable"] is True
        assert res["situation_detected"] is True, "Situation must be detected for 'During an academic group project...'"
        assert res["task_detected"] is True, "Task must be detected for 'My responsibility was to...'"
        assert res["action_detected"] is True, "Action must be detected for 'I organized a discussion...'"
        assert res["result_detected"] is True, "Result must be detected for 'As a result, we completed...'"
        assert res["star_completeness_ratio"] == 1.0
        assert len(res["components_missing"]) == 0
        assert "Situation" in res["components_detected"]
        assert any(
            "academic group project" in s.lower()
            for s in res["supporting_sentences"]["Situation"]
        )

    @pytest.mark.parametrize(
        "opening,context_desc",
        [
            ("During an academic project, our database faced severe query latency issues.", "academic project"),
            ("In one of my previous projects, our team had to build a real-time messaging pipeline.", "previous projects"),
            ("While working with my team, we encountered conflicting requirements from different stakeholders.", "while working with team"),
            ("At my internship, the legacy reporting pipeline took several hours to process daily records.", "at my internship"),
            ("We encountered a challenge when our cloud instance ran out of available memory during peak hours.", "encountered challenge"),
        ],
    )
    def test_contextual_situation_openings(self, opening, context_desc):
        """Verify that contextual natural openings are recognized as valid Situations without keyword rigidity."""
        full_text = (
            f"{opening} "
            "My goal was to optimize the processing pipeline. "
            "I implemented redis caching and async worker queues. "
            "As a result, latency dropped by 75% and reliability reached 99.9%."
        )
        res = detect_star_structure(full_text, is_behavioral=True)
        assert res["situation_detected"] is True, f"Failed to detect Situation for opening: {context_desc}"
        assert "Situation" in res["components_detected"]
        assert res["star_completeness_ratio"] == 1.0

    def test_genuinely_incomplete_missing_situation(self):
        """Verify that answers lacking situational context correctly identify Situation as missing."""
        text = (
            "My responsibility was to identify bottlenecks and optimize the slow queries. "
            "I analyzed slow query logs and added composite indexes. "
            "As a result, we achieved a 65% reduction in query latency."
        )
        res = detect_star_structure(text, is_behavioral=True)
        assert res["situation_detected"] is False
        assert "Situation" in res["components_missing"]
        assert res["task_detected"] is True
        assert res["action_detected"] is True
        assert res["result_detected"] is True
        assert res["star_completeness_ratio"] == 0.75

    def test_genuinely_incomplete_missing_situation_and_task(self):
        """Verify that answers with only actions and results correctly flag both Situation and Task as missing."""
        text = (
            "I refactored the database schema and created composite indexes. "
            "As a result, page response times improved by 50%."
        )
        res = detect_star_structure(text, is_behavioral=True)
        assert res["situation_detected"] is False
        assert res["task_detected"] is False
        assert "Situation" in res["components_missing"]
        assert "Task" in res["components_missing"]
        assert res["action_detected"] is True
        assert res["result_detected"] is True
        assert res["star_completeness_ratio"] == 0.5

    def test_technical_definition_does_not_falsely_detect_situation(self):
        """Verify that a purely technical non-behavioral description does not falsely trigger situation."""
        text = "A binary search algorithm operates in O(log n) time complexity by repeatedly dividing the search interval in half."
        res = detect_star_structure(text, is_behavioral=True)
        assert res["situation_detected"] is False
        assert res["star_completeness_ratio"] < 0.5


class TestHR005SkillsEvidenceStructure:
    """Tests for detect_skills_evidence_strengths_alignment_structure (HR005)."""

    def test_complete_hr005_structure(self):
        text = (
            "You should hire me because I have a strong foundation in Python, SQL, and machine learning. "
            "For example, in my capstone project, I built an end-to-end sentiment classification system that handled 10k reviews. "
            "My primary strength is my analytical mindset and rapid learning ability when picking up new libraries. "
            "I want to contribute directly to your team's mission of building scalable AI solutions."
        )
        res = detect_skills_evidence_strengths_alignment_structure(text, candidate_level="final_year")
        assert res["framework"] == "SkillsEvidenceStrengthsAlignment"
        assert res["structure_score"] >= 90.0
        assert "Skills" in res["components_detected"]
        assert "Evidence" in res["components_detected"]
        assert "Strengths" in res["components_detected"]
        assert "Role Alignment" in res["components_detected"]
        assert len(res["components_missing"]) == 0

    def test_missing_evidence_and_alignment(self):
        text = "I know Python and machine learning. My strength is that I am a hardworking person."
        res = detect_skills_evidence_strengths_alignment_structure(text, candidate_level="final_year")
        assert "Evidence" in res["components_missing"]
        assert "Role Alignment" in res["components_missing"]
        assert res["structure_score"] < 75.0

    def test_empty_answer_handled(self):
        res = detect_skills_evidence_strengths_alignment_structure("", candidate_level="final_year")
        assert res["structure_score"] == 0.0
        assert len(res["components_missing"]) == 4


class TestTECH005DefinitionNeedNormStdExampleStructure:
    """Tests for detect_definition_need_norm_std_example_structure (TECH005)."""

    def test_complete_tech005_structure(self):
        text = (
            "Feature scaling transforms numeric features onto a uniform, comparable scale. "
            "Without scaling, features with large numeric ranges dominate distance calculations and slow gradient descent convergence. "
            "Normalization scales features to a bounded range between 0 and 1 using min-max scaling, though it is sensitive to outliers. "
            "Standardization transforms features to zero mean and unit variance using z-score, making it robust to outliers. "
            "For example, algorithms like KNN and SVM require scaling, whereas decision trees are scale-invariant."
        )
        res = detect_definition_need_norm_std_example_structure(text, candidate_level="final_year")
        assert res["framework"] == "DefinitionNeedNormStdExample"
        assert res["structure_score"] == 100.0
        assert "Definition" in res["components_detected"]
        assert "Need" in res["components_detected"]
        assert "Normalization" in res["components_detected"]
        assert "Standardization" in res["components_detected"]
        assert "Example" in res["components_detected"]
        assert len(res["components_missing"]) == 0

    def test_partial_tech005_structure(self):
        text = (
            "Feature scaling is changing feature scales. "
            "Normalization scales values to between 0 and 1. "
            "Standardization centers data around mean zero."
        )
        res = detect_definition_need_norm_std_example_structure(text, candidate_level="final_year")
        assert "Need" in res["components_missing"]
        assert "Example" in res["components_missing"]
        assert res["structure_score"] < 80.0

    def test_dispatch_in_analyze_structure(self):
        q_hr = {"question_id": "HR005", "framework": "Skills_Evidence_Strengths_Alignment", "category": "HR / Behavioral"}
        res_hr = analyze_structure("I know Python and machine learning.", q_hr)
        assert res_hr["framework"] == "SkillsEvidenceStrengthsAlignment"

        q_tech = {"question_id": "TECH005", "framework": "Definition_Need_Norm_Std_Example", "category": "Technical"}
        res_tech = analyze_structure("Feature scaling transforms features.", q_tech)
        assert res_tech["framework"] == "DefinitionNeedNormStdExample"


