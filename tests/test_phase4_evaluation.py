"""
test_phase4_evaluation.py — Comprehensive Test Suite for Phase 4 Evaluation Improvements
and Candidate-Level Adaptation.

Tests:
1. Candidate level configuration and validation.
2. All 15 questions across:
   - Strong placement-ready answers.
   - Average answers.
   - Short but correct answers (fairness check).
   - Incomplete answers.
   - Incorrect / misconception answers.
3. Candidate-level adaptation (Final-Year vs TY vs Experienced).
4. Factual correctness invariance across all candidate levels.
5. Negation safety in technical misconception detection.
"""

import pytest
from typing import Dict, Any

from config.candidate_levels import (
    CANDIDATE_LEVELS,
    DEFAULT_CANDIDATE_LEVEL,
    LEVEL_EXPERIENCED,
    LEVEL_FINAL_YEAR,
    LEVEL_TY_STUDENT,
    get_candidate_level_info,
    validate_candidate_level,
)
from modules.scoring import evaluate_answer, load_questions_map


# ── 1. Candidate Level Configuration & Validation ─────────────────────────────

class TestCandidateLevelConfiguration:
    def test_default_level_is_final_year(self):
        assert DEFAULT_CANDIDATE_LEVEL == LEVEL_FINAL_YEAR

    def test_validate_candidate_level_fallbacks(self):
        assert validate_candidate_level(None) == LEVEL_FINAL_YEAR
        assert validate_candidate_level("") == LEVEL_FINAL_YEAR
        assert validate_candidate_level("invalid_string") == LEVEL_FINAL_YEAR

    def test_validate_candidate_level_aliases(self):
        assert validate_candidate_level("final_year") == LEVEL_FINAL_YEAR
        assert validate_candidate_level("Placement Ready") == LEVEL_FINAL_YEAR
        assert validate_candidate_level("b.tech student") == LEVEL_FINAL_YEAR
        assert validate_candidate_level("ty_student") == LEVEL_TY_STUDENT
        assert validate_candidate_level("third year") == LEVEL_TY_STUDENT
        assert validate_candidate_level("experienced") == LEVEL_EXPERIENCED

    def test_get_candidate_level_info_structure(self):
        info = get_candidate_level_info(LEVEL_FINAL_YEAR)
        assert info["id"] == LEVEL_FINAL_YEAR
        assert "badge_label" in info
        assert len(info["primary_evidence_sources"]) > 0


# ── 2. All 15 Questions Evaluation Testing ─────────────────────────────────────

class TestAllFifteenQuestionsEvaluation:
    @classmethod
    def setup_class(cls):
        cls.questions = load_questions_map()
        assert len(cls.questions) == 15

    # ── HR001 ──
    def test_hr001_strong_final_year(self):
        ans = (
            "I am a final-year Computer Science Engineering student specializing in backend systems and applied ML. "
            "For my major capstone project, I developed an automated interview analyzer using Python and FastAPI, which "
            "strengthened my skills in REST APIs and NLP data pipelines. During my summer internship, I collaborated with "
            "engineering teams in daily agile standups to optimize database schemas. I am excited about this software engineering "
            "role because your company builds scalable data products, aligning directly with my career goal of becoming a high-impact SDE."
        )
        res = evaluate_answer("HR001", ans, candidate_level=LEVEL_FINAL_YEAR)
        assert res["overall_score"] >= 80.0
        assert res["performance_category"] in ("Good", "Excellent")
        assert res["component_scores"]["semantic"] >= 75.0
        assert "capstone" in " ".join(res["feedback"]["strengths"]).lower()

    def test_hr001_short_but_correct(self):
        ans = (
            "I am a final year Computer Science student. I have built full stack and machine learning projects, "
            "and I am very excited to join your team to apply my problem solving skills in software engineering."
        )
        res = evaluate_answer("HR001", ans, candidate_level=LEVEL_FINAL_YEAR)
        assert res["overall_score"] >= 65.0
        assert res["component_scores"]["semantic"] >= 70.0

    def test_hr001_irrelevant(self):
        ans = "I enjoy playing video games on weekends and cooking pasta with my family."
        res = evaluate_answer("HR001", ans, candidate_level=LEVEL_FINAL_YEAR)
        assert res["overall_score"] < 50.0

    # ── HR002 ──
    def test_hr002_strong_problem_solving(self):
        ans = (
            "My greatest strength is analytical problem solving. In our capstone project, when our database queries caused "
            "high latency spikes, I analyzed execution bottlenecks and implemented optimized indexing, reducing query time by 40%. "
            "Another strength is adaptability and fast learning; during a 24-hour hackathon, I picked up OAuth2 authentication "
            "and integrated it cleanly into our backend."
        )
        res = evaluate_answer("HR002", ans, candidate_level=LEVEL_FINAL_YEAR)
        assert res["overall_score"] >= 80.0
        assert res["component_scores"]["semantic"] >= 75.0

    def test_hr002_misconception_no_flaws(self):
        ans = "I have no flaws whatsoever and I am perfect at everything I do without any weakness."
        res = evaluate_answer("HR002", ans, candidate_level=LEVEL_FINAL_YEAR)
        assert res["technical_correctness"]["has_misconceptions"] is True

    # ── HR003 ──
    def test_hr003_strong_weakness_improvement(self):
        ans = (
            "My weakness has been spending too much time over-optimizing code before asking for feedback. In earlier projects, "
            "I would delay pull requests trying to make every function flawless. I realized this was slowing down our milestones, "
            "so I adopted time-boxing: I now share work-in-progress code early with teammates to receive constructive reviews."
        )
        res = evaluate_answer("HR003", ans, candidate_level=LEVEL_FINAL_YEAR)
        assert res["overall_score"] >= 80.0
        assert res["component_scores"]["semantic"] >= 75.0

    def test_hr003_fake_weakness_misconception(self):
        ans = "I don't have any weakness. My only weakness is that I work too hard and care too much."
        res = evaluate_answer("HR003", ans, candidate_level=LEVEL_FINAL_YEAR)
        assert res["technical_correctness"]["has_misconceptions"] is True

    # ── HR004 ──
    def test_hr004_strong_career_trajectory(self):
        ans = (
            "In five years, I see myself having grown into a senior software development engineer. In the first two years, "
            "my focus will be mastering your tech stack and taking ownership of backend microservices. Over time, I aim to "
            "deepen my expertise in distributed systems architecture and mentor junior campus recruits."
        )
        res = evaluate_answer("HR004", ans, candidate_level=LEVEL_FINAL_YEAR)
        assert res["overall_score"] >= 80.0
        assert res["component_scores"]["semantic"] >= 75.0

    def test_hr004_aimless(self):
        ans = "I haven't thought about five years, wherever life takes me I will just go along."
        res = evaluate_answer("HR004", ans, candidate_level=LEVEL_FINAL_YEAR)
        assert res["overall_score"] < 55.0

    # ── HR005 ──
    def test_hr005_strong_graduation_transition(self):
        ans = (
            "As a final-year engineering student, I am completing my degree and preparing to transition from academia "
            "into my first full-time software engineering role. While my academic coursework and internship gave me a strong "
            "foundation in data structures and backend development, I am eager to join your company to build scalable production "
            "systems under experienced senior engineers."
        )
        res = evaluate_answer("HR005", ans, candidate_level=LEVEL_FINAL_YEAR)
        assert res["overall_score"] >= 80.0
        assert res["component_scores"]["semantic"] >= 75.0

    def test_hr005_badmouthing_misconception(self):
        ans = "I hate my college and professors were bad so I just want any job that pays me."
        res = evaluate_answer("HR005", ans, candidate_level=LEVEL_FINAL_YEAR)
        assert res["technical_correctness"]["has_misconceptions"] is True

    # ── BEH001 ──
    def test_beh001_strong_capstone_team(self):
        ans = (
            "Situation: During our final-year capstone project, our four-member team built an AI healthcare portal with a tight deadline. "
            "Task: As backend lead, my responsibility was to design REST APIs and integrate the machine learning model. "
            "Action: I organized daily syncs, set up GitHub branch rules, and paired with our frontend teammate to debug asynchronous requests. "
            "Result: We completed the project ahead of schedule, achieved 94% test coverage, and our faculty guide awarded our team an A grade."
        )
        res = evaluate_answer("BEH001", ans, candidate_level=LEVEL_FINAL_YEAR)
        assert res["overall_score"] >= 85.0
        assert res["structure_analysis"]["star_analysis"]["star_completeness_ratio"] == 1.0

    def test_beh001_short_no_star(self):
        ans = "We worked as a team on our college project and everyone did their part."
        res = evaluate_answer("BEH001", ans, candidate_level=LEVEL_FINAL_YEAR)
        assert res["overall_score"] < 65.0
        assert res["structure_analysis"]["star_analysis"]["star_completeness_ratio"] < 0.5

    # ── BEH002 ──
    def test_beh002_strong_hackathon_leadership(self):
        ans = (
            "Situation: In a college hackathon, our database corrupted six hours before final submission, causing panic in our team. "
            "Task: I stepped up to rally the team and re-architect the storage layer to deliver a working demo. "
            "Action: I called a brief timeout, divided tasks into frontend mock APIs and persistence recovery, and rebuilt the SQLite layer. "
            "Result: We restored functionality with two hours to spare, delivered a successful demo, and secured second place in the competition."
        )
        res = evaluate_answer("BEH002", ans, candidate_level=LEVEL_FINAL_YEAR)
        assert res["overall_score"] >= 85.0
        assert res["structure_analysis"]["star_analysis"]["star_completeness_ratio"] == 1.0

    # ── BEH003 ──
    def test_beh003_strong_conflict_resolution(self):
        ans = (
            "Situation: In our final year project, my teammate and I disagreed on whether to use MongoDB or PostgreSQL for our database. "
            "Task: My goal was to resolve the disagreement objectively without harming our teamwork or project timeline. "
            "Action: I suggested we benchmark both against our specific query access patterns and relational integrity needs. I actively listened to their concerns about schema flexibility. "
            "Result: We agreed on a hybrid compromise using PostgreSQL with JSONB columns, delivering the module on schedule with mutual respect."
        )
        res = evaluate_answer("BEH003", ans, candidate_level=LEVEL_FINAL_YEAR)
        assert res["overall_score"] >= 85.0
        assert res["structure_analysis"]["star_analysis"]["star_completeness_ratio"] == 1.0

    # ── BEH004 ──
    def test_beh004_strong_tight_deadline(self):
        ans = (
            "Situation: Our capstone project submission date was advanced by ten days, leaving us only four days to complete model deployment. "
            "Task: I had to prioritize core deliverables, prevent burnout, and ensure a stable demonstration. "
            "Action: I prioritized Must-Have MVP features over animations, broke the work into daily milestones, and automated testing. "
            "Result: We delivered the web application ahead of the deadline, achieving a 150ms inference time and an A+ evaluation grade."
        )
        res = evaluate_answer("BEH004", ans, candidate_level=LEVEL_FINAL_YEAR)
        assert res["overall_score"] >= 85.0

    # ── BEH005 ──
    def test_beh005_strong_constructive_criticism(self):
        ans = (
            "Situation: During my internship, my mentor pointed out that my pull requests lacked edge-case error handling and unit tests. "
            "Task: I needed to take the feedback constructively and improve my professional coding standards. "
            "Action: I asked for clarification on company error-handling patterns, studied production code, and created a personal pre-commit review checklist. "
            "Result: My revised pull request was approved the next day, and my checklist was subsequently shared with other onboarding interns."
        )
        res = evaluate_answer("BEH005", ans, candidate_level=LEVEL_FINAL_YEAR)
        assert res["overall_score"] >= 85.0

    # ── TECH001 ──
    def test_tech001_strong_comprehensive(self):
        ans = (
            "In Python, lists are mutable while tuples are immutable. Lists use square brackets [] and tuples use parentheses (). "
            "Because tuples are immutable, they are hashable and can be used as dictionary keys or set elements, whereas lists cannot. "
            "Tuples have lower memory overhead and faster creation times. Use lists for dynamic collections and tuples for fixed data like coordinates."
        )
        res = evaluate_answer("TECH001", ans, candidate_level=LEVEL_FINAL_YEAR)
        assert res["overall_score"] >= 85.0
        assert res["component_scores"]["semantic"] >= 85.0

    def test_tech001_short_but_correct_fairness(self):
        # 26 words, concise and technically 100% accurate
        ans = (
            "Lists are mutable and use square brackets; tuples are immutable, use parentheses, "
            "and can be used as dictionary keys because they are hashable."
        )
        res = evaluate_answer("TECH001", ans, candidate_level=LEVEL_FINAL_YEAR)
        # Concise accuracy should NOT be capped to 30 or 50
        assert res["component_scores"]["semantic"] >= 80.0
        assert res["overall_score"] >= 70.0

    def test_tech001_misconception_read_only_list(self):
        ans = "Tuples are just read-only lists with no other difference at all."
        res = evaluate_answer("TECH001", ans, candidate_level=LEVEL_FINAL_YEAR)
        assert res["technical_correctness"]["has_misconceptions"] is True

    # ── TECH002 ──
    def test_tech002_strong_joins(self):
        ans = (
            "In SQL, an INNER JOIN returns only matching rows from both tables where the join condition is satisfied. "
            "A LEFT JOIN returns all rows from the left table, plus matched rows from the right table. For non-matching right-table rows, "
            "NULL values are returned. For example, joining Customers to Orders with LEFT JOIN includes customers who have never placed orders."
        )
        res = evaluate_answer("TECH002", ans, candidate_level=LEVEL_FINAL_YEAR)
        assert res["overall_score"] >= 85.0
        assert res["component_scores"]["semantic"] >= 85.0

    def test_tech002_short_but_correct_fairness(self):
        # 23 words, concise and exact
        ans = (
            "INNER JOIN returns only matching rows from both tables. "
            "LEFT JOIN returns all rows from the left table, filling unmatched right columns with NULL."
        )
        res = evaluate_answer("TECH002", ans, candidate_level=LEVEL_FINAL_YEAR)
        assert res["component_scores"]["semantic"] >= 80.0
        assert res["overall_score"] >= 70.0

    def test_tech002_misconception_always_more_rows(self):
        ans = "A LEFT JOIN always returns more rows than an INNER JOIN in every query."
        res = evaluate_answer("TECH002", ans, candidate_level=LEVEL_FINAL_YEAR)
        assert res["technical_correctness"]["has_misconceptions"] is True

    # ── TECH003 ──
    def test_tech003_strong_overfitting(self):
        ans = (
            "Overfitting occurs when a machine learning model memorizes training noise rather than learning generalizable patterns. "
            "It is characterized by high training accuracy but poor validation or test accuracy (high variance). "
            "To prevent overfitting, we use regularization like L1 and L2, k-fold cross-validation, dropout in neural networks, "
            "early stopping, and collecting more data or applying data augmentation."
        )
        res = evaluate_answer("TECH003", ans, candidate_level=LEVEL_FINAL_YEAR)
        assert res["overall_score"] >= 85.0
        assert res["component_scores"]["semantic"] >= 85.0

    def test_tech003_misconception_100_percent_perfect(self):
        ans = "Overfitting is great because 100% training accuracy means a perfect model."
        res = evaluate_answer("TECH003", ans, candidate_level=LEVEL_FINAL_YEAR)
        assert res["technical_correctness"]["has_misconceptions"] is True

    # ── TECH004 ──
    def test_tech004_strong_precision_recall_f1(self):
        ans = (
            "Precision is TP / (TP + FP), measuring the proportion of positive predictions that are correct. "
            "Recall is TP / (TP + FN), measuring the proportion of actual positives detected. "
            "F1-score is the harmonic mean of precision and recall: 2 * (P * R) / (P + R). "
            "Precision is critical when false positives are costly like email spam, whereas recall is vital when false negatives are dangerous like disease diagnosis."
        )
        res = evaluate_answer("TECH004", ans, candidate_level=LEVEL_FINAL_YEAR)
        assert res["overall_score"] >= 85.0
        assert res["component_scores"]["semantic"] >= 85.0

    def test_tech004_misconception_arithmetic_mean(self):
        ans = "F1-score is the arithmetic mean of precision and recall calculated as precision plus recall divided by two."
        res = evaluate_answer("TECH004", ans, candidate_level=LEVEL_FINAL_YEAR)
        assert res["technical_correctness"]["has_misconceptions"] is True

    # ── TECH005 ──
    def test_tech005_strong_decorators(self):
        ans = (
            "In Python, decorators are higher-order functions that modify or extend the behavior of another function without altering its source code. "
            "A decorator takes a function as an argument, defines an inner wrapper function that adds pre- or post-execution logic, and returns the wrapper. "
            "The @ syntax is syntactic sugar for func = decorator(func). Common use cases include logging, execution timing, authentication, and caching with lru_cache."
        )
        res = evaluate_answer("TECH005", ans, candidate_level=LEVEL_FINAL_YEAR)
        assert res["overall_score"] >= 85.0
        assert res["component_scores"]["semantic"] >= 85.0

    def test_tech005_misconception_permanently_alters_code(self):
        ans = "Decorators permanently rewrites the code in the file so the original function is lost."
        res = evaluate_answer("TECH005", ans, candidate_level=LEVEL_FINAL_YEAR)
        assert res["technical_correctness"]["has_misconceptions"] is True


# ── 3. Candidate Level Adaptation Comparison Tests ────────────────────────────

class TestCandidateLevelAdaptations:
    def test_ty_student_academic_focus_not_penalized(self):
        """Verify TY students drawing from mini-projects/coursework receive appropriate credit."""
        ans = (
            "Situation: In our database lab mini-project, our student team had to build a student management portal. "
            "Task: My assignment was to implement the MySQL database schema and connect it using Python. "
            "Action: I normalized the tables to 3NF, wrote sample queries, and helped my lab partner connect their front-end interface. "
            "Result: We submitted the assignment before the lab deadline and received an A grade from our professor."
        )
        # Evaluated as TY student
        res_ty = evaluate_answer("BEH001", ans, candidate_level=LEVEL_TY_STUDENT)
        assert res_ty["overall_score"] >= 78.0
        assert res_ty["performance_category"] in ("Good", "Excellent")

    def test_factual_correctness_invariance_across_levels(self):
        """Technical misconceptions must be caught regardless of selected candidate level."""
        wrong_ans = "A LEFT JOIN always returns more rows than an INNER JOIN in SQL."
        for lvl in [LEVEL_TY_STUDENT, LEVEL_FINAL_YEAR, LEVEL_EXPERIENCED]:
            res = evaluate_answer("TECH002", wrong_ans, candidate_level=lvl)
            assert res["technical_correctness"]["has_misconceptions"] is True

    def test_negation_safety_not_flagged_as_misconception(self):
        """Candidates stating that a misconception is NOT true should NOT be penalized."""
        safe_ans = (
            "It is incorrect to claim that F1 is the arithmetic mean. "
            "In reality, F1 is the harmonic mean of precision and recall because it penalizes extreme imbalances."
        )
        res = evaluate_answer("TECH004", safe_ans, candidate_level=LEVEL_FINAL_YEAR)
        assert res["technical_correctness"]["has_misconceptions"] is False


# ── 4. Engine Refinement & Consistency Verification Tests ─────────────────────

class TestPhase4EvaluationEngineRefinements:
    @classmethod
    def setup_class(cls):
        cls.questions = load_questions_map()

    def test_structure_missing_conclusion_not_praised_in_strengths(self):
        """When an answer lacks a conclusion, feedback must NEVER praise a practical application/conclusion."""
        ans = (
            "In Python, a list is a mutable sequence defined with square brackets. "
            "A tuple is an immutable sequence defined with parentheses where elements cannot be modified."
        )
        res = evaluate_answer("TECH001", ans, candidate_level=LEVEL_FINAL_YEAR)
        gen = res["structure_analysis"]["general_analysis"]
        assert gen["has_conclusion"] is False
        
        # Check that strengths do not falsely praise a conclusion or practical application
        all_strengths = " ".join(res["feedback"]["strengths"]).lower()
        assert "practical application" not in all_strengths
        assert "complete structural progression" not in all_strengths

        # Check that areas for improvement specifically point out the missing conclusion deduction
        all_improvements = " ".join(res["feedback"]["areas_for_improvement"]).lower()
        assert "conclusion" in all_improvements or "structure deduction" in all_improvements

    def test_structure_deductions_itemized_and_explained(self):
        """Structure analysis must provide explicit credits and deductions."""
        ans = "Situation: In our project we had a problem. Task: My task was to fix it."
        res = evaluate_answer("BEH001", ans, candidate_level=LEVEL_FINAL_YEAR)
        star = res["structure_analysis"]["star_analysis"]
        assert len(star["deductions"]) > 0
        assert any("Action" in d for d in star["deductions"])
        assert any("Result" in d for d in star["deductions"])

    def test_evidence_accuracy_mapping_and_unsupported_status(self):
        """Each detected concept must match its actual sentence; missing concepts must be marked unsupported."""
        ans = "In Python, lists are mutable objects that can grow dynamically."
        res = evaluate_answer("TECH001", ans, candidate_level=LEVEL_FINAL_YEAR)
        evidence = res["semantic_analysis"]["keypoint_coverage"]["evidence_sentences"]
        
        # Mutability point must link to the sentence mentioning mutable
        mutability_key = next((k for k in evidence.keys() if "mutable" in k.lower()), None)
        assert mutability_key is not None
        assert "mutable" in evidence[mutability_key].lower()

        # Missing point (e.g. hashability or memory) must explicitly state Unsupported
        missing_key = next((k for k in evidence.keys() if "hashab" in k.lower() or "use case" in k.lower() or "syntax" in k.lower() or "immutab" in k.lower() and evidence[k].startswith("Unsupported")), None)
        assert missing_key is not None
        assert "Unsupported / Not detected in candidate response" == evidence[missing_key]

    def test_delivery_evaluates_only_text_indicators(self):
        """Delivery analysis must evaluate text mechanics only and not claim acoustic voice measurements."""
        ans = (
            "Um, basically, like, lists are mutable, you know, and, um, tuples are immutable, like, for real."
        )
        res = evaluate_answer("TECH001", ans, candidate_level=LEVEL_FINAL_YEAR)
        deliv = res["delivery_analysis"]
        assert deliv["evaluation_modality"] == "text_linguistic_indicators"
        assert "acoustic" in deliv["modality_notice"].lower()
        assert "vocal" in deliv["modality_notice"].lower()

        # Check feedback wording uses text/transcript phrasing
        all_feedback_text = " ".join(res["feedback"]["areas_for_improvement"]).lower()
        assert "transcript" in all_feedback_text or "fillers" in all_feedback_text

    def test_semantic_divergence_and_model_engine(self):
        """Semantic analysis must report model engine, divergence explanation, and disclaimer."""
        ans = "A list is mutable and a tuple is immutable in Python."
        res = evaluate_answer("TECH001", ans, candidate_level=LEVEL_FINAL_YEAR)
        sem = res["semantic_analysis"]
        assert "model_engine" in sem
        assert "divergence_explanation" in sem
        assert "factual_correctness_disclaimer" in sem
        assert len(sem["divergence_explanation"]) > 10

    def test_feedback_category_specific_and_level_adapted(self):
        """Technical questions should receive technical placement advice, not blind generic tips."""
        ans = "Lists are mutable and tuples are immutable in Python."
        res_fy = evaluate_answer("TECH001", ans, candidate_level=LEVEL_FINAL_YEAR)
        fy_suggestions = " ".join(res_fy["feedback"]["actionable_suggestions"])
        assert "Placement Technical Focus" in fy_suggestions

        res_ty = evaluate_answer("TECH001", ans, candidate_level=LEVEL_TY_STUDENT)
        ty_suggestions = " ".join(res_ty["feedback"]["actionable_suggestions"])
        assert "Academic Technical Focus" in ty_suggestions

    def test_candidate_tailored_blueprint_preserves_context(self):
        """Suggested revision blueprint must preserve candidate's original text and avoid fake company stories."""
        ans = (
            "In our final year capstone project on disease prediction using PyTorch, "
            "we encountered high class imbalance in our healthcare dataset."
        )
        res = evaluate_answer("BEH002", ans, candidate_level=LEVEL_FINAL_YEAR)
        blueprint = res["feedback"]["suggested_improved_answer"]

        # Original context must be preserved
        assert "final year capstone project on disease prediction using PyTorch" in blueprint
        # Fictional corporate roles must NOT be invented
        assert "XYZ Corp" not in blueprint
        assert "senior engineering manager" not in blueprint
        # Contains structural completion guidance
        assert "Structural Completion" in blueprint or "Synthesized Candidate Blueprint" in blueprint

    def test_score_consistency_and_weights_across_categories(self):
        """Overall score must strictly equal weighted sum of 4 components (40/25/20/15)."""
        test_qids = ["HR001", "BEH001", "TECH001", "TECH004"]
        test_answers = [
            "I am a final year computer science student with projects in web development and machine learning.",
            "In my capstone project, I led the database design and resolved latency issues before the deadline.",
            "Lists are mutable and tuples are immutable in Python.",
            "Precision is TP/(TP+FP), recall is TP/(TP+FN), and F1 is the harmonic mean of precision and recall.",
        ]
        for qid, ans in zip(test_qids, test_answers):
            res = evaluate_answer(qid, ans, candidate_level=LEVEL_FINAL_YEAR)
            comps = res["component_scores"]
            weighted = res["weighted_contributions"]
            overall = res["overall_score"]

            expected_weighted_sum = round(
                0.40 * comps["semantic"]
                + 0.25 * comps["structure"]
                + 0.20 * comps["communication"]
                + 0.15 * comps["delivery"],
                2,
            )
            assert overall == expected_weighted_sum
            assert round(sum(weighted.values()), 2) == overall


