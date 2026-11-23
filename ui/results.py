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
    ml_data = eval_data.get("multilingual_analysis") or {}

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
        composite_semantic = semantic_data.get("composite_semantic_score", comp_scores.get("semantic", 0))

        st_module.markdown("#### Conceptual & Key-Point Coverage")
        st_module.caption(
            "Multi-dimensional evaluation of candidate subject-matter knowledge. "
            "Combines grounded concept verification, question relevance, and pairwise semantic similarity."
        )

        scol1, scol2, scol3, scol4 = st_module.columns(4)
        with scol1:
            st_module.metric("Semantic Relevance", f"{composite_semantic:.1f} / 100", help="Overall weighted score for the Semantic dimension (40% weight in composite evaluation).")
        with scol2:
            st_module.metric("Key-Point Coverage", f"{cov_data.get('coverage_percentage', 0):.1f}%", help="Percentage of required essential technical concepts evidenced in candidate response.")
        with scol3:
            st_module.metric("Semantic Similarity", f"{sim_data.get('similarity_percentage', 0):.1f}%", help="Pairwise cosine similarity between candidate response and the ideal reference essay.")
        with scol4:
            engine_str = semantic_data.get("model_engine", semantic_data.get("model_used", "Sentence Transformers / TF-IDF"))
            short_engine = "all-MiniLM-L6-v2" if "MiniLM" in engine_str else "TF-IDF Baseline"
            st_module.metric("Model Engine", short_engine)

        st_module.markdown(
            """
            <div style='background: rgba(124, 183, 245, 0.08); border-left: 3px solid #7CB7F5; padding: 0.75rem 1rem; border-radius: 4px; margin: 0.75rem 0 1rem 0; font-size: 0.88rem; color: #CBD5E1;'>
                <b>💡 Understanding Semantic Relevance vs. Semantic Similarity:</b><br/>
                • <b>Semantic Relevance (Dimension Score, 40% weight):</b> Measures overall topic mastery. When you address all required key concepts accurately, you receive a high relevance score even if your answer is concise.<br/>
                • <b>Semantic Similarity (Pairwise Alignment):</b> Measures text vector overlap against the lengthy model answer. Concise or distinct phrasing naturally yields lower pairwise similarity (often 35–60%), but your overall score is not penalized because Key-Point Coverage verifies conceptual completeness.
            </div>
            """,
            unsafe_allow_html=True,
        )

        divergence = semantic_data.get("divergence_explanation")
        if divergence:
            st_module.info(f"ℹ️ **Evaluation Dynamics:** {divergence}")

        disclaimer = semantic_data.get("factual_correctness_disclaimer")
        if disclaimer:
            st_module.caption(f"⚖️ {disclaimer}")

        # Explainable semantic NLP pipeline for academic demonstration.
        with st_module.expander("🧪 View Semantic NLP Pipeline (Preprocessing → Vectorization → Similarity)", expanded=False):
            from modules.semantic_analysis import build_semantic_trace

            reference_text = (q_data or {}).get("reference_answer", "")
            if not reference_text:
                st_module.warning("Reference answer metadata is unavailable for this saved result. Submit a new answer from Practice Interview to view the complete pipeline.")
            else:
                trace_input = ml_data.get("evaluation_text", candidate_answer) if ml_data.get("translation_used") else candidate_answer
                trace = build_semantic_trace(trace_input, reference_text)
                candidate_prep = trace["candidate_preprocessing"]
                reference_prep = trace["reference_preprocessing"]

                st_module.markdown("**Step 1 — Original candidate response**")
                st_module.text_area("Original response", candidate_answer, height=100, disabled=True, key="semantic_trace_original")
                if ml_data.get("translation_used"):
                    st_module.caption(f"🌐 Evaluated via English translation ({ml_data.get('detected_language', 'non-English')} detected):")
                    st_module.text_area("English translation for semantic trace", trace_input, height=90, disabled=True, key="semantic_trace_translated")

                st_module.markdown("**Step 2 — Cleaned and normalized text**")
                st_module.text_area("Cleaned response", candidate_prep["cleaned_text"], height=90, disabled=True, key="semantic_trace_cleaned")
                st_module.text_area("Normalized response", candidate_prep["normalized_text"], height=90, disabled=True, key="semantic_trace_normalized")

                st_module.markdown("**Step 3 — Tokenization and stop-word filtering**")
                token_col1, token_col2 = st_module.columns(2)
                with token_col1:
                    st_module.caption(f"Tokens ({len(candidate_prep['tokens'])})")
                    st_module.code(" | ".join(candidate_prep["tokens"]) or "No tokens", language="text")
                with token_col2:
                    st_module.caption(f"Filtered tokens ({len(candidate_prep['filtered_tokens'])})")
                    st_module.code(" | ".join(candidate_prep["filtered_tokens"]) or "No tokens", language="text")

                st_module.markdown("**Step 4 — Numerical vectorization**")
                st_module.write(f"Vectorization method: **{trace['vectorization_method']}**")
                if trace["embedding_available"]:
                    st_module.write(f"Embedding dimensions: **{trace['embedding_dimensions']}**")
                    emb_col1, emb_col2 = st_module.columns(2)
                    with emb_col1:
                        st_module.caption("Candidate embedding (first 8 values)")
                        st_module.code(str(trace["candidate_embedding_preview"]))
                    with emb_col2:
                        st_module.caption("Reference embedding (first 8 values)")
                        st_module.code(str(trace["reference_embedding_preview"]))
                else:
                    st_module.info("The Sentence Transformer was unavailable for this run. The application used its TF-IDF fallback; dense embedding values are therefore not available.")

                st_module.markdown("**Step 5 — Reference answer comparison**")
                st_module.text_area("Reference answer", reference_text, height=110, disabled=True, key="semantic_trace_reference")
                trace_sim = trace["similarity"]
                st_module.metric("Cosine similarity", f"{trace_sim['similarity_percentage']:.2f}%")
                st_module.caption(f"Engine: {trace_sim['model_name']} · Status: {trace_sim['analysis_status']} · Note: Cosine similarity evaluates stylistic proximity to the benchmark text, not correctness.")

                st_module.markdown("**Step 6 — Concept coverage result**")
                st_module.write(f"Coverage: **{cov_data.get('coverage_percentage', 0):.1f}%**")
                trace_covered = cov_data.get("covered_essential_points", [])
                trace_partial = cov_data.get("partially_covered_essential_points", [])
                trace_missing = cov_data.get("missing_essential_points", [])
                for label, items in (("Covered", trace_covered), ("Partially covered", trace_partial), ("Missing", trace_missing)):
                    with st_module.expander(f"{label} concepts ({len(items)})", expanded=(label == "Missing" and bool(items))):
                        if items:
                            for item in items:
                                st_module.write(f"• {item}")
                        else:
                            st_module.caption("None")

                st_module.caption("Interpretation: Key-Point Coverage verifies actual factual concept presence independently of phrasing length, while embedding similarity measures semantic closeness to the reference text.")

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

        # ------------------------------------------------------------------ #
        # CO3: Multilingual NLP Processing Section                            #
        # ------------------------------------------------------------------ #
        ml_data = eval_data.get("multilingual_analysis") or {}
        if ml_data:
            st_module.markdown("---")
            st_module.markdown("#### 🌐 Multilingual NLP Processing (CO3)")
            st_module.caption(
                "Automatic language detection and cloud-AI translation pipeline. "
                "Non-English answers are translated to English before semantic evaluation, "
                "preserving your original answer for display."
            )

            proc_status = ml_data.get("processing_status", "unknown")
            detected_lang = ml_data.get("detected_language", "Unknown")
            lang_code = ml_data.get("language_code", "?")
            conf = ml_data.get("detection_confidence", 0.0)
            translation_used = ml_data.get("translation_used", False)
            eval_note = ml_data.get("evaluation_note", "")
            cloud_service = ml_data.get("cloud_service_used", "Groq LLaMA (llama-3.1-8b-instant)")

            # Status banner
            if proc_status == "english_passthrough":
                st_module.success(eval_note or "✅ English detected — original pipeline used unchanged.")
            elif proc_status == "translated":
                st_module.info(eval_note or f"🌐 Translated from {detected_lang} to English.")
            elif proc_status in ("translation_failed",):
                st_module.warning(eval_note or "⚠️ Translation failed — original text evaluated.")
            elif proc_status in ("too_short", "low_confidence", "detection_failed"):
                st_module.info(eval_note or "ℹ️ Language detection inconclusive — evaluated as English.")
            elif proc_status == "empty":
                st_module.info("ℹ️ No answer submitted — language processing skipped.")
            else:
                st_module.info(eval_note or f"Processing status: {proc_status}")

            # Detection metrics row
            col_a, col_b, col_c = st_module.columns(3)
            col_a.metric("🔤 Detected Language", f"{detected_lang} ({lang_code})")
            col_b.metric("📊 Detection Confidence", f"{conf:.0%}" if conf > 0 else "N/A")
            col_c.metric("☁️ Cloud AI Service", cloud_service.split("(")[0].strip())

            # Show translation details if translation was applied
            if translation_used:
                original_text = ml_data.get("original_text", "")
                translated_text = ml_data.get("translated_text", "")

                with st_module.expander(
                    f"📄 Original Answer ({detected_lang}) and English Translation",
                    expanded=True,
                ):
                    st_module.markdown(f"**Original ({detected_lang}):**")
                    st_module.text_area(
                        "original_answer_co3",
                        value=original_text,
                        height=100,
                        disabled=True,
                        label_visibility="collapsed",
                    )
                    st_module.markdown("**English Translation (used for evaluation):**")
                    st_module.text_area(
                        "translated_answer_co3",
                        value=translated_text,
                        height=100,
                        disabled=True,
                        label_visibility="collapsed",
                    )
                    st_module.caption(
                        "⚠️ Machine translation may not perfectly capture domain-specific nuances. "
                        "Scores reflect the translated text evaluated against English reference answers."
                    )

            # Pipeline trace (always shown)
            with st_module.expander("🔬 CO3 Multilingual Pipeline Trace"):
                st_module.markdown(
                    f"""
| Step | Detail |
|------|--------|
| **Language Detection** | langdetect (offline, deterministic, seed=42) |
| **Detected Language** | {detected_lang} (`{lang_code}`) |
| **Confidence** | {conf:.4f} |
| **Detection Status** | `{ml_data.get('detection_note', proc_status)}` |
| **Translation Required** | {'Yes' if translation_used else 'No'} |
| **Cloud AI Translation** | {cloud_service} |
| **Processing Status** | `{proc_status}` |
| **Evaluation Text** | {'Translated English text' if translation_used else 'Original text (unchanged)'} |
                    """
                )

        # ------------------------------------------------------------------ #
        # CO3: Latent Topic Modeling (LDA) & Word Vectors (CO1)               #
        # ------------------------------------------------------------------ #
        topic_data = eval_data.get("topic_analysis", {})
        spacy_sim_pct = semantic_data.get("spacy_vector_percentage", 0.0)

        st_module.markdown("---")
        st_module.markdown("#### 📊 Topic Modeling (LDA) & Word Vectors")
        col_t1, col_t2 = st_module.columns(2)
        with col_t1:
            dom_topic = topic_data.get("dominant_topic", "General Software Engineering")
            t_conf = topic_data.get("confidence", 0.0)
            st_module.metric("🏷️ Dominant Interview Topic (LDA)", dom_topic.split("(")[0].strip())
            st_module.caption(f"Topic Model: {topic_data.get('algorithm', 'LDA')} · Theme: {dom_topic}")
        with col_t2:
            if spacy_sim_pct > 0.0:
                st_module.metric("🧬 spaCy 300-d Vector Alignment", f"{spacy_sim_pct:.1f}%")
                st_module.caption("Dense word embedding cosine similarity (`en_core_web_md`).")
            else:
                st_module.metric("🧬 spaCy 300-d Vector Alignment", "Unavailable")
                st_module.caption("Dense word embeddings unavailable or non-overlapping vocabulary.")

        t_dist = topic_data.get("topic_distribution", {})
        if t_dist:
            with st_module.expander("📈 Topic Distribution Breakdown"):
                for t_name, t_val in t_dist.items():
                    st_module.progress(min(1.0, float(t_val)), text=f"{t_name}: {t_val:.1%}")



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

        st_module.markdown("---")

        # ── CO2: Sentiment Analysis ───────────────────────────────────────────
        sentiment_data = eval_data.get("sentiment_analysis", {})
        st_module.markdown("#### 🔵 Sentiment Analysis (CO2)")
        st_module.caption(
            "VADER-based observational sentiment scoring of the candidate's response. "
            "Sentiment is a descriptive indicator only — it does NOT replace semantic relevance "
            "or communication scoring, and is NOT used in the final score calculation."
        )

        if sentiment_data:
            sent_label = sentiment_data.get("sentiment_label", "Neutral")
            sent_compound = sentiment_data.get("compound", 0.0)
            sent_pos = sentiment_data.get("positive", 0.0)
            sent_neg = sentiment_data.get("negative", 0.0)
            sent_neu = sentiment_data.get("neutral", 0.0)

            label_color = {
                "Positive": "#22C55E",
                "Negative": "#F87171",
                "Neutral": "#94A3B8",
            }.get(sent_label, "#94A3B8")

            st_module.markdown(
                f"<div style='background:rgba(0,0,0,0.15);border-left:4px solid {label_color};"
                f"padding:0.6rem 1rem;border-radius:4px;margin:0.5rem 0;'>"
                f"<b>Overall Sentiment:</b> <span style='color:{label_color};font-weight:700;font-size:1.1rem;'>"
                f"{sent_label}</span> &nbsp;·&nbsp; Compound score: <code>{sent_compound:+.3f}</code></div>",
                unsafe_allow_html=True,
            )

            scol1, scol2, scol3 = st_module.columns(3)
            with scol1:
                st_module.metric("Positive", f"{sent_pos:.3f}", help="Proportion of tokens with positive valence (VADER pos score, 0–1).")
            with scol2:
                st_module.metric("Negative", f"{sent_neg:.3f}", help="Proportion of tokens with negative valence (VADER neg score, 0–1).")
            with scol3:
                st_module.metric("Neutral", f"{sent_neu:.3f}", help="Proportion of tokens with neutral valence (VADER neu score, 0–1).")

            # Interview-context interpretation
            if sent_label == "Positive":
                interp = (
                    "The response carries a positive tone — common in answers about achievements, "
                    "eagerness, or describing successful outcomes. Positive tone is natural and "
                    "appropriate in many interview contexts."
                )
            elif sent_label == "Negative":
                interp = (
                    "The response carries a negative tone. This can occur when describing challenges, "
                    "failures, or technical outages — which is contextually valid. It does NOT indicate "
                    "poor performance; negative sentiment is expected when narrating problem-solving scenarios."
                )
            else:
                interp = (
                    "The response carries a neutral tone. This is very common for technical answers "
                    "that focus on factual explanations and definitions. Neutral tone reflects professional, "
                    "precise language and does NOT signal a lack of enthusiasm."
                )

            st_module.info(f"💡 **Interview Context:** {interp}")

            if sentiment_data.get("note"):
                st_module.caption(f"⚖️ {sentiment_data['note']}")
        else:
            st_module.caption("Sentiment data not available for this result. Submit a new answer to generate it.")

        st_module.markdown("---")

        # ── CO2: Information Extraction ───────────────────────────────────────
        info_data = eval_data.get("information_extraction", {})
        st_module.markdown("#### 🟡 Information Extraction (CO2)")
        st_module.caption(
            "Extracted keywords, identified concepts, supporting evidence sentences, "
            "and missing relevant information — all traced to the candidate's actual response."
        )

        if info_data:
            # Keywords
            keywords = info_data.get("extracted_keywords", [])
            if keywords:
                st_module.markdown("**🔑 Extracted Important Keywords & Technical Terms:**")
                kw_html = " ".join(
                    f"<span style='background:rgba(96,165,250,0.15);color:#60A5FA;"
                    f"border:1px solid #60A5FA33;padding:2px 8px;border-radius:12px;"
                    f"font-size:0.85rem;margin:2px;display:inline-block;'>{kw}</span>"
                    for kw in keywords
                )
                st_module.markdown(kw_html, unsafe_allow_html=True)
            else:
                st_module.caption("No domain-relevant keywords detected.")

            st_module.markdown("")  # spacer

            # Identified concepts
            identified = info_data.get("identified_concepts", [])
            if identified:
                st_module.markdown(f"**✅ Key Concepts Identified ({len(identified)}):**")
                for ic in identified:
                    with st_module.expander(f"✅ {ic.get('concept', '')}", expanded=False):
                        st_module.write(f"**Matched via:** {ic.get('matched_via', '')}")
                        ev = ic.get("evidence_sentence", "")
                        if ev:
                            st_module.markdown(f"**Evidence sentence:** *\"{ev}\"*")
            else:
                st_module.caption("No key concepts were identified from this response.")

            # Missing concepts
            missing_concepts = info_data.get("missing_concepts", [])
            if missing_concepts:
                st_module.markdown(f"**❌ Missing Relevant Information ({len(missing_concepts)}):**")
                for mc in missing_concepts:
                    st_module.markdown(
                        f"<div class='checklist-item missing'><span>❌ <b>Missing:</b> {mc}</span></div>",
                        unsafe_allow_html=True,
                    )

            # Supporting evidence
            evidence = info_data.get("supporting_evidence", [])
            if evidence:
                with st_module.expander(f"🔎 Supporting Evidence Sentences ({len(evidence)})", expanded=False):
                    for i, sent in enumerate(evidence, 1):
                        st_module.markdown(f"**{i}.** *\"{sent}\"*")

            if info_data.get("extraction_note"):
                st_module.caption(f"ℹ️ {info_data['extraction_note']}")
        else:
            st_module.caption("Information extraction data not available. Submit a new answer to generate it.")

        # ------------------------------------------------------------------ #
        # CO2: Emotion Classification (j-hartmann DistilRoBERTa)             #
        # ------------------------------------------------------------------ #
        emotion_data = eval_data.get("emotion_analysis", {})
        if emotion_data:
            st_module.markdown("---")
            st_module.markdown("#### 🎭 Emotion Analysis (`j-hartmann DistilRoBERTa`)")
            dom_emotion = emotion_data.get("dominant_emotion", "neutral").title()
            conf = emotion_data.get("confidence", 0.0)
            engine = emotion_data.get("model_engine", "DistilRoBERTa")

            emo_emojis = {
                "Joy": "😊", "Optimism": "🌟", "Neutral": "😐",
                "Surprise": "😲", "Sadness": "😔", "Fear": "😰",
                "Anger": "😠", "Disgust": "😒"
            }
            emoji_icon = emo_emojis.get(dom_emotion, "💬")

            c_e1, c_e2 = st_module.columns([2, 3])
            with c_e1:
                st_module.metric("Dominant Tone / Emotion", f"{emoji_icon} {dom_emotion}", f"{conf:.1%} confidence")
                st_module.caption(f"Engine: `{engine}`")
            with c_e2:
                scores = emotion_data.get("emotion_scores", {})
                if scores:
                    st_module.markdown("**Emotion Distribution:**")
                    for emo, sc in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:4]:
                        st_module.progress(min(1.0, float(sc)), text=f"{emo.title()}: {sc:.1%}")

        # ------------------------------------------------------------------ #
        # CO2: spaCy Named Entity Recognition & Skill Matching               #
        # ------------------------------------------------------------------ #
        ner_skills = eval_data.get("entities_and_skills", {})
        if ner_skills:
            st_module.markdown("---")
            st_module.markdown("#### 🏷️ spaCy Entity & Domain Skills Extraction")
            st_module.caption("Extracts Named Entities (NER) and matches industry technical/behavioral skills using spaCy `PhraseMatcher`.")

            tech_skills = ner_skills.get("technical_skills", [])
            beh_skills = ner_skills.get("behavioral_skills", [])
            entities = ner_skills.get("entities", [])

            col_s1, col_s2 = st_module.columns(2)
            with col_s1:
                st_module.markdown(f"**🛠️ Technical Skills Detected ({len(tech_skills)}):**")
                if tech_skills:
                    chips_html = "".join([f"<span class='keyword-chip' style='background: rgba(16, 185, 129, 0.2); color: #6EE7B7; border: 1px solid rgba(16, 185, 129, 0.4);'>{s}</span>" for s in tech_skills])
                    st_module.markdown(f"<div style='margin-bottom: 0.5rem;'>{chips_html}</div>", unsafe_allow_html=True)
                else:
                    st_module.caption("No technical skill keywords matched from the curriculum database.")

            with col_s2:
                st_module.markdown(f"**🤝 Behavioral / Core Competencies ({len(beh_skills)}):**")
                if beh_skills:
                    chips_html = "".join([f"<span class='keyword-chip' style='background: rgba(99, 102, 241, 0.2); color: #A5B4FC; border: 1px solid rgba(99, 102, 241, 0.4);'>{s}</span>" for s in beh_skills])
                    st_module.markdown(f"<div style='margin-bottom: 0.5rem;'>{chips_html}</div>", unsafe_allow_html=True)
                else:
                    st_module.caption("No specific behavioral competence phrases matched.")

            if entities:
                with st_module.expander(f"🏢 Named Entities Recognized ({len(entities)})", expanded=False):
                    ent_rows = "\n".join([f"| `{e['text']}` | **{e['label']}** |" for e in entities[:10]])
                    st_module.markdown(
                        f"""
| Entity Text | Label (Type) |
|---|---|
{ent_rows}
                        """
                    )

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
            framework_title = struct_data.get("framework_title", "Conceptual Structure: Premise, Elaboration, & Conclusion")
            st_module.markdown(f"#### {framework_title}")
            gen = struct_data.get("general_analysis", {})
            st_module.metric("Structure Score", f"{struct_data.get('structure_score', 0):.1f}/100")

            stages = struct_data.get("framework_stages")
            if stages:
                for stage, ok in stages:
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
            else:
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

            gen_credits = struct_data.get("credits") or gen.get("credits", [])
            gen_deductions = struct_data.get("deductions") or gen.get("deductions", [])
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

        # CO4: LLM-generated personalized coaching feedback. This is separate
        # from the deterministic scoring engine and never changes evaluation scores.
        st_module.markdown("---")
        st_module.markdown("#### 🤖 AI-Powered Personalized Interview Feedback")
        st_module.caption(
            "Uses Groq LLaMA to synthesize the existing evaluation findings into coaching advice. "
            "Your original scores are not recalculated or modified."
        )

        import hashlib
        ans_hash = hashlib.md5(candidate_answer.encode("utf-8", errors="ignore")).hexdigest()[:10]
        llm_state_key = f"llm_feedback_{qid}_{ans_hash}"

        llm_result = st_module.session_state.get(llm_state_key)
        btn_label = "🔄 Regenerate AI Feedback" if llm_result else "✨ Generate AI Feedback"

        if st_module.button(btn_label, type="primary" if not llm_result else "secondary", key=f"generate_{llm_state_key}"):
            with st_module.spinner("Generating personalized feedback with Groq LLaMA..."):
                from modules.llm_feedback import generate_llm_feedback
                st_module.session_state[llm_state_key] = generate_llm_feedback(eval_data, q_data)
                llm_result = st_module.session_state.get(llm_state_key)

        if llm_result:
            status = llm_result.get("status")
            if status == "success":
                st_module.success(
                    f"Generated using {llm_result.get('provider', 'LLM')} · "
                    f"{llm_result.get('model_used', 'model')}"
                )
                st_module.markdown("**Performance Summary**")
                st_module.write(llm_result.get("summary", ""))

                col_strength, col_weakness = st_module.columns(2)
                with col_strength:
                    st_module.markdown("**🌟 Strengths**")
                    for item in llm_result.get("strengths", []):
                        st_module.markdown(f"- {item}")
                with col_weakness:
                    st_module.markdown("**🎯 Areas to Improve**")
                    for item in llm_result.get("weaknesses", []):
                        st_module.markdown(f"- {item}")

                st_module.markdown("**📚 Missing Concepts**")
                concepts = llm_result.get("missing_concepts", [])
                if concepts:
                    for item in concepts:
                        st_module.markdown(f"- {item}")
                else:
                    st_module.caption("No additional missing concepts were identified by the feedback model.")

                st_module.markdown("**📝 Sample Improved Answer (Learning Reference)**")
                st_module.info(llm_result.get("improved_answer", ""))

                st_module.markdown("**🚀 Three Actionable Recommendations**")
                for index, item in enumerate(llm_result.get("recommendations", [])[:3], 1):
                    st_module.markdown(f"{index}. {item}")
            else:
                st_module.warning(
                    f"AI feedback is unavailable ({status}). "
                    f"{llm_result.get('error') or 'Please check your Groq configuration and try again.'} "
                    "Your regular evaluation and scores are unaffected."
                )
