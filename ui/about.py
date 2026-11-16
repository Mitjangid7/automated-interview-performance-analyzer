"""
about.py — About Project & Academic Evaluation Methodology Page

Documents:
- Problem statement and AI-assisted interview preparation objective
- Visual system architecture and end-to-end evaluation pipeline
- Categorized technology stack
- Clear distinction between synthetic development data and real-world validation
- Academic psychometric validation protocol for production deployment
- Scientific limitations and ethical disclaimers
"""

from typing import Any
from config.config import SCORING_WEIGHTS


def render_about_page(st_module: Any) -> None:
    """
    Render the About Project and Evaluation Methodology page in Streamlit.

    Args:
        st_module: Streamlit module (or mock).
    """
    st_module.markdown("<h1 class='main-title'>About the Project</h1>", unsafe_allow_html=True)
    st_module.markdown(
        "<p class='sub-title'>Automated Interview Performance Analyzer — AI-assisted evaluation, explainable multi-dimensional scoring, and actionable feedback.</p>",
        unsafe_allow_html=True,
    )

    tab_overview, tab_pipeline, tab_tech, tab_metrics, tab_limits = st_module.tabs([
        "📌 Project Overview",
        "⚙️ System Pipeline & Architecture",
        "💻 Technology Stack",
        "📊 Psychometric Validation Protocol",
        "⚠️ Scientific Limitations & Ethics",
    ])

    # 1. OVERVIEW
    with tab_overview:
        st_module.markdown("### Problem Statement")
        st_module.markdown(
            """
            Interview evaluation is inherently subjective and prone to variability. Different interviewers
            often weigh different aspects of a candidate's response inconsistently, while fatigue, cognitive bias,
            and lack of calibration can lead to unstandardized assessments.

            For candidates, interview practice typically lacks immediate, granular feedback on conceptual correctness,
            linguistic clarity, and structural storytelling.
            """
        )

        st_module.markdown("### Proposed Solution")
        st_module.markdown(
            """
            The **Automated Interview Performance Analyzer** provides an objective, transparent, multi-dimensional
            NLP evaluation framework:
            - **Semantic Relevance:** Evaluates alignment against expert reference answers and measures essential key-point coverage.
            - **Answer Structure:** Verifies behavioral frameworks (STAR: Situation, Task, Action, Result) and conceptual progression (Premise, Elaboration, Conclusion).
            - **Communication Quality:** Assesses vocabulary diversity (Type-Token Ratio) and sentence complexity without penalizing domain-specific terminology.
            - **Linguistic Delivery:** Detects verbal filler frequency, hedging phrases, and conversational habits.
            - **Actionable Guidance:** Synthesizes strengths, growth priorities, and concrete revision blueprints.
            """
        )

        # Configured Evaluation Weights Section
        w_sem = int(round(SCORING_WEIGHTS.get("semantic_relevance", 0.40) * 100))
        w_str = int(round(SCORING_WEIGHTS.get("answer_structure", 0.25) * 100))
        w_comm = int(round(SCORING_WEIGHTS.get("communication", 0.20) * 100))
        w_del = int(round(SCORING_WEIGHTS.get("delivery_indicators", 0.15) * 100))

        st_module.markdown("### ⚖️ Composite Evaluation Weights")
        st_module.caption("The system aggregates four dimensions into a unified 0–100 performance score:")

        st_module.markdown(
            f"""
            <div class='metric-card' style='background: #171E2B; border: 1px solid #354253; padding: 1.15rem 1.35rem; margin-bottom: 1.5rem;'>
                <div style='display: flex; flex-direction: column; gap: 0.95rem;'>
                    <div>
                        <div style='display: flex; justify-content: space-between; font-size: 0.88rem; margin-bottom: 0.35rem;'>
                            <span style='color: #F1F5F9; font-weight: 600;'>🎯 Semantic Relevance</span>
                            <span style='color: #7CB7F5; font-weight: 700; font-family: monospace;'>{w_sem}%</span>
                        </div>
                        <div style='background: #202A38; height: 7px; border-radius: 999px; overflow: hidden; border: 1px solid #354253;'>
                            <div style='background: #7CB7F5; width: {w_sem}%; height: 100%; border-radius: 999px;'></div>
                        </div>
                        <div style='font-size: 0.76rem; color: #8290A3; margin-top: 0.25rem;'>Reference answer semantic similarity, key-point conceptual coverage, and question relevance.</div>
                    </div>
                    <div>
                        <div style='display: flex; justify-content: space-between; font-size: 0.88rem; margin-bottom: 0.35rem;'>
                            <span style='color: #F1F5F9; font-weight: 600;'>🏗️ Answer Structure</span>
                            <span style='color: #7CB7F5; font-weight: 700; font-family: monospace;'>{w_str}%</span>
                        </div>
                        <div style='background: #202A38; height: 7px; border-radius: 999px; overflow: hidden; border: 1px solid #354253;'>
                            <div style='background: #7CB7F5; width: {w_str}%; height: 100%; border-radius: 999px;'></div>
                        </div>
                        <div style='font-size: 0.76rem; color: #8290A3; margin-top: 0.25rem;'>Behavioral STAR method verification (Situation, Task, Action, Result) or conceptual progression.</div>
                    </div>
                    <div>
                        <div style='display: flex; justify-content: space-between; font-size: 0.88rem; margin-bottom: 0.35rem;'>
                            <span style='color: #F1F5F9; font-weight: 600;'>💬 Communication Quality</span>
                            <span style='color: #7CB7F5; font-weight: 700; font-family: monospace;'>{w_comm}%</span>
                        </div>
                        <div style='background: #202A38; height: 7px; border-radius: 999px; overflow: hidden; border: 1px solid #354253;'>
                            <div style='background: #7CB7F5; width: {w_comm}%; height: 100%; border-radius: 999px;'></div>
                        </div>
                        <div style='font-size: 0.76rem; color: #8290A3; margin-top: 0.25rem;'>Vocabulary richness (Type-Token Ratio) and sentence balance without penalizing technical terms.</div>
                    </div>
                    <div>
                        <div style='display: flex; justify-content: space-between; font-size: 0.88rem; margin-bottom: 0.35rem;'>
                            <span style='color: #F1F5F9; font-weight: 600;'>🗣️ Linguistic Delivery</span>
                            <span style='color: #7CB7F5; font-weight: 700; font-family: monospace;'>{w_del}%</span>
                        </div>
                        <div style='background: #202A38; height: 7px; border-radius: 999px; overflow: hidden; border: 1px solid #354253;'>
                            <div style='background: #7CB7F5; width: {w_del}%; height: 100%; border-radius: 999px;'></div>
                        </div>
                        <div style='font-size: 0.76rem; color: #8290A3; margin-top: 0.25rem;'>Observable verbal habits, filler word frequency per 100 words, and repeated hedging phrases.</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Prominent Notice on Synthetic Data
        st_module.markdown(
            """
            <div class='card-improvement' style='margin-top: 1.5rem;'>
                <div style='font-weight: 700; color: #FBBF24; font-size: 1rem; margin-bottom: 0.35rem;'>
                    ⚠️ Notice: Synthetic Development Dataset vs. Real-World Ground Truth
                </div>
                <div style='color: #CBD5E1; font-size: 0.92rem; line-height: 1.6;'>
                    All ratings and sample candidate responses in <code>data/synthetic_answers.csv</code> are 
                    <b>synthetically generated for development, unit testing, and pipeline verification purposes</b>.
                    They are <b>NOT</b> collected from real human candidates and do <b>NOT</b> represent clinical or
                    human-expert ground truth. A production deployment requires calibrated expert panels and empirical human trials.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 2. SYSTEM PIPELINE & ARCHITECTURE
    with tab_pipeline:
        st_module.markdown("### End-to-End Evaluation Pipeline")
        st_module.caption("How an interview answer flows through preprocessing, multi-dimensional NLP evaluation, scoring, and feedback generation.")

        # Visual Pipeline Code block / Diagram
        pipeline_diagram = """
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Candidate Answer + Question Prompt                    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    1. Preprocessing & Text Normalization                    │
│   • Whitespace & Tokenization  • Stopword Cleaning  • VADER Sentiment      │
└──────────────┬───────────────────────┼───────────────────────┬──────────────┘
               │                       │                       │
               ▼                       ▼                       ▼
┌──────────────────────────┐ ┌───────────────────┐ ┌──────────────────────────┐
│  2. Semantic Relevance   │ │ 3. Structure      │ │ 4. Communication Quality │
│  • Sentence Transformers │ │    Analysis       │ │    & Linguistic Delivery │
│  • Key-Point Coverage    │ │ • Behavioral STAR │ │ • Boundary-safe Fillers  │
│  • Technical Concepts    │ │ • Premise/Body/   │ │ • Hedging Patterns       │
│  • Misconception Checks  │ │   Conclusion      │ │ • Diversity (TTR)        │
│  (Weight: 40%)           │ │ (Weight: 25%)     │ │ (Weight: 20% + 15%)      │
└──────────────┬───────────┘ └─────────┬─────────┘ └───────────┬──────────────┘
               │                       │                       │
               └───────────────────────┼───────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     5. Explainable Scoring Engine                           │
│   Composite Score (0 - 100) = (Semantic * 0.40) + (Structure * 0.25)        │
│                             + (Communication * 0.20) + (Delivery * 0.15)    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    6. Intelligent Feedback Generator                        │
│   • Personalized Strengths  • Growth Priorities  • Model Revision Blueprint │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│               7. Interactive Streamlit Dashboard & History                  │
│   • Radar Charts  • Gauges  • Time-Series Trends  • Cross-Attempt Comparison│
└─────────────────────────────────────────────────────────────────────────────┘
        """
        st_module.code(pipeline_diagram, language="text")

        st_module.markdown("#### Core Architecture Modules")
        modules_info = [
            ("Text Preprocessing (`modules/preprocessing.py`)", "Whitespace normalization, tokenization, technical/negation-safe stopword removal, sentence boundary segmentation, and VADER sentiment analysis."),
            ("Communication Analysis (`modules/communication_analysis.py`)", "Boundary-safe regex filler detection (single & multi-word), hedging phrase detection, Type-Token Ratio (TTR) vocabulary diversity, and Coleman-Liau readability metrics."),
            ("Linguistic Delivery (`modules/communication_analysis.py`)", "Observable verbal habit analysis: filler frequency per 100 words, repeated phrases, excessive hedging, and brief response warnings."),
            ("Semantic Analysis & Concepts (`modules/semantic_analysis.py`)", "Sentence embedding similarity, granular essential key-point coverage, optional point tracking, question relevance, and curriculum misconception detection."),
            ("Structure Analysis (`modules/structure_analysis.py`)", "Behavioral STAR method verification (Situation, Task, Action, Result) and Premise/Elaboration/Conclusion analysis for technical/HR questions."),
            ("Weighted Scoring Engine (`modules/scoring.py`)", "Explainable composite scoring (0 - 100) combining Semantic (40%), Structure (25%), Communication (20%), and Delivery (15%). Dynamic weights loaded from config."),
            ("Feedback Generator (`modules/feedback.py`)", "Personalized strengths, pinpointed improvement areas, actionable next steps, and intent-preserving model revision blueprints."),
            ("Interactive UI & Visualizations (`ui/`)", "Modular dashboard, practice workspace, detailed analytical breakdown, Plotly radar/gauge/trend charts, and cross-attempt comparison."),
        ]
        for title, desc in modules_info:
            st_module.markdown(f"- **{title}:** {desc}")

    # 3. TECHNOLOGY STACK
    with tab_tech:
        st_module.markdown("### Technology Stack")
        st_module.caption("Modern, lightweight, and explainable technology stack without unnecessary dependencies.")

        col_t1, col_t2 = st_module.columns(2)
        with col_t1:
            st_module.markdown(
                """
                <div class='metric-card'>
                    <div class='metric-label'>Core Runtime & Data</div>
                    <div style='color: #CBD5E1; font-size: 0.92rem; line-height: 1.6;'>
                        - <b>Language:</b> Python 3.10+ (tested on Python 3.12)<br>
                        - <b>Data Processing:</b> Pandas, NumPy<br>
                        - <b>Data Formats:</b> JSON (atomic persistence), CSV
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st_module.markdown(
                """
                <div class='metric-card'>
                    <div class='metric-label'>Natural Language Processing</div>
                    <div style='color: #CBD5E1; font-size: 0.92rem; line-height: 1.6;'>
                        - <b>Embeddings:</b> Sentence Transformers (<code>all-MiniLM-L6-v2</code>)<br>
                        - <b>Lexical Fallback:</b> Pure-Python TF-IDF Cosine Similarity<br>
                        - <b>Sentiment:</b> VADER Sentiment Intensity Analyzer<br>
                        - <b>Tokenization:</b> NLTK tokenizers & regex boundary matching
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_t2:
            st_module.markdown(
                """
                <div class='metric-card'>
                    <div class='metric-label'>User Interface & Visuals</div>
                    <div style='color: #CBD5E1; font-size: 0.92rem; line-height: 1.6;'>
                        - <b>Web Framework:</b> Streamlit 1.x<br>
                        - <b>Visualizations:</b> Plotly Graph Objects (Radar, Gauge, Bar, Time-Series)<br>
                        - <b>Theme:</b> Dark navy/charcoal responsive CSS architecture
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st_module.markdown(
                """
                <div class='metric-card'>
                    <div class='metric-label'>Quality Assurance & Testing</div>
                    <div style='color: #CBD5E1; font-size: 0.92rem; line-height: 1.6;'>
                        - <b>Testing Framework:</b> pytest test suite (105 passing tests)<br>
                        - <b>Evaluation Engine:</b> Multi-dimensional NLP evaluation pipeline<br>
                        - <b>Explainability:</b> 100% deterministic, inspectable component weights
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # 4. PSYCHOMETRIC VALIDATION PROTOCOL
    with tab_metrics:
        st_module.markdown("### Academic Psychometric Validation Protocol")
        st_module.caption(
            "Rigorous research framework required for calibrating automated interview scoring against human expert panels."
        )

        st_module.markdown(
            """
            For genuine real-world validation and production deployment with human candidates,
            the following academic psychometric protocol must be executed:
            1. **Multi-Rater Expert Panels:** Collect responses from diverse candidate cohorts, scored independently by 3+ calibrated human interviewers.
            2. **Mean Absolute Error (MAE) & RMSE:** Quantify point deviation between automated scores and consensus human ratings.
            3. **Weighted Cohen's Kappa ($k$):** Measure inter-rater agreement between the automated model and expert human raters, penalizing large score discrepancies.
            4. **Intraclass Correlation Coefficient (ICC):** Assess scoring consistency across multi-rater panels.
            5. **Demographic Parity & Accent Neutrality:** Audit evaluation across diverse cultural communication norms and non-native English speakers to avoid algorithmic bias.
            6. **Ablation Testing:** Isolate individual components (semantic vs. communication vs. structure) to quantify feature sensitivity and importance.
            """
        )

    # 5. SCIENTIFIC LIMITATIONS
    with tab_limits:
        st_module.markdown("### Scientific Limitations & Ethical Disclaimers")
        limitations = [
            ("Semantic Similarity ≠ Factual Truth", "High sentence-embedding cosine similarity does not prove factual correctness. A candidate can write semantically similar yet technically inverted statements. Conceptual coverage and rule checks mitigate this, but do not replace expert human judgment."),
            ("Curriculum-Defined Misconceptions", "Rule-based checks identify known interview misconceptions from the curriculum; they do not replace human domain expertise on novel edge cases or emerging technologies."),
            ("Linguistic Indicators ≠ Psychological Traits", "Verbal filler frequencies and hedging indicate observable textual delivery habits only. They do NOT infer candidate confidence, nervousness, honesty, or character."),
            ("Heuristic STAR Detector", "Pattern matching detects structural cues (e.g., 'Situation:', 'In my previous project'); it does not independently verify the authenticity or real-world validity of candidate achievements."),
            ("Synthetic Development Data Notice", "Ratings in `synthetic_answers.csv` are development heuristics created for pipeline testing and must not be cited as real-world human validation."),
            ("Language Support", "The current analysis engine is designed exclusively for English-language interview responses."),
        ]
        for title, desc in limitations:
            st_module.markdown(
                f"""
                <div class='metric-card' style='margin-bottom: 0.75rem;'>
                    <div style='color: #F87171; font-weight: 700; font-size: 0.92rem; margin-bottom: 0.25rem;'>⚠️ {title}</div>
                    <div style='color: #CBD5E1; font-size: 0.88rem; line-height: 1.5;'>{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Subtle credits footer
    st_module.markdown(
        """
        <div style='border-top: 1px solid #354253; padding-top: 1rem; margin-top: 2rem; color: #8290A3; font-size: 0.78rem; display: flex; justify-content: space-between; align-items: center;'>
            <span>Google DeepMind Pair Programming &bull; Antigravity Engine</span>
            <span>Automated Interview Performance Analyzer &bull; v0.1.0</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
