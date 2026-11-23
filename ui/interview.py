"""
interview.py — Practice Interview Page

Provides an interactive interview workspace:
- Category selection (HR, Behavioral, Technical)
- Dynamic question loading with structural answering guidance and expected key points
- Clear, modern question presentation card
- Answer text area with live word counter, character counter, and estimated speaking duration
- Optional response stopwatch / timer feature
- Optional audio file transcript workflow
- Input validation (prevent empty submissions, warnings for brief responses)
- Seamless execution of evaluate_answer() with loading state and history persistence
"""

import time
from typing import Any, Callable, Dict, List, Optional

from config.candidate_levels import (
    CANDIDATE_LEVELS,
    DEFAULT_CANDIDATE_LEVEL,
    LEVEL_DISPLAY_OPTIONS,
    LEVEL_FINAL_YEAR,
    LEVEL_TY_STUDENT,
    get_candidate_level_info,
)
from modules.audio_transcription import (
    transcribe_audio_payload,
    validate_audio_data,
    inspect_audio_properties,
)
from modules.preprocessing import clean_text
from modules.scoring import evaluate_answer, load_questions_map
from ui.history import save_evaluation_to_history


def get_approach_guidance(question_data: Dict[str, Any], candidate_level: str = "final_year") -> str:
    """Generate strategic guidance based on category, STAR flag, question ID, and candidate level."""
    qid = question_data.get("question_id", "")
    cat = question_data.get("category", "")
    uses_star = question_data.get("uses_star_method", False)

    if qid == "HR005":
        if candidate_level == LEVEL_FINAL_YEAR:
            ev_tip = "Cite your **capstone engineering project, industry internship, and core tech stack**."
        elif candidate_level == LEVEL_TY_STUDENT:
            ev_tip = "Highlight your **academic mini-projects, hackathons, rapid learning curve, and coursework**."
        else:
            ev_tip = "Demonstrate your **track record of production delivery, cross-functional impact, and technical ownership**."

        return (
            f"🎯 **Approach Strategy (Skills → Evidence → Strengths → Alignment — {candidate_level.replace('_', ' ').title()} Track):**\n"
            "- **Skills:** State your core technical foundation and key programming / engineering tools.\n"
            f"- **Evidence:** Back your claims with concrete projects or accomplishments. *{ev_tip}*\n"
            "- **Strengths:** Emphasize critical differentiating traits (e.g. debugging under pressure, fast learner, system design rigor).\n"
            "- **Role Alignment:** Explicitly connect your skills and passion with the team's mission and technical goals."
        )

    if qid == "TECH005":
        if candidate_level == LEVEL_FINAL_YEAR:
            alg_tip = "Contrast algorithms requiring scaling (**KNN, SVM, Gradient Descent**) with scale-invariant models (**Decision Trees, Random Forests**)."
        elif candidate_level == LEVEL_TY_STUDENT:
            alg_tip = "Explain why large numeric values dominate distance calculations in **KNN and K-Means**."
        else:
            alg_tip = "Discuss data leakage prevention during train/test split, handling outliers with **RobustScaler**, and computational stability."

        return (
            f"🎯 **Approach Strategy (Definition → Need → Normalization → Standardization → Example — {candidate_level.replace('_', ' ').title()} Track):**\n"
            "- **Definition:** Define feature scaling as transforming numerical features onto a uniform comparable scale.\n"
            "- **Need:** Explain why unscaled features distort distance metrics and cause oscillating/slow gradient descent convergence.\n"
            "- **Normalization (Min-Max):** Explain scaling to [0, 1], formula (X - X_min)/(X_max - X_min), and sensitivity to outliers.\n"
            "- **Standardization (Z-Score):** Explain transformation to zero mean and unit variance, formula (X - μ)/σ, and robustness to outliers.\n"
            f"- **Practical Examples:** {alg_tip}"
        )

    if uses_star or cat.lower() == "behavioral":
        if candidate_level == LEVEL_FINAL_YEAR:
            context_tip = "Anchor your situation in your **major capstone project, college hackathon, or internship**."
        elif candidate_level == LEVEL_TY_STUDENT:
            context_tip = "Draw from **academic mini-projects, coursework lab assignments, or student club activities**."
        else:
            context_tip = "Draw from **production engineering systems, architectural initiatives, or commercial deployments**."

        return (
            f"🎯 **Approach Strategy (STAR Method — {candidate_level.replace('_', ' ').title()} Track):**\n"
            f"- **Situation:** Briefly describe the specific challenge. *{context_tip}*\n"
            "- **Task:** Define your individual role and what needed to be achieved.\n"
            "- **Action:** Explain concrete technical decisions, code implementations, or teamwork steps.\n"
            "- **Result:** Quantify the final outcome (grade, latency reduction, test accuracy %, on-time delivery)."
        )
    elif cat.lower() == "technical":
        return (
            "🎯 **Approach Strategy (Technical Concept):**\n"
            "- **Definition:** Start with a concise, technically precise definition.\n"
            "- **Mechanics / Trade-offs:** Explain internal behavior, memory, or performance implications.\n"
            "- **Practical Application:** State realistic use cases or project scenarios where you would choose this approach."
        )
    else:
        if candidate_level == LEVEL_FINAL_YEAR:
            hr_tip = "Highlight your degree, core technical stack, capstone project, and eagerness to contribute as a placement recruit."
        elif candidate_level == LEVEL_TY_STUDENT:
            hr_tip = "Highlight your academic coursework, passion for technology, and eagerness to secure an internship."
        else:
            hr_tip = "Highlight your professional trajectory, architectural achievements, and reasons for this career transition."

        return (
            f"🎯 **Approach Strategy (Professional Overview — {candidate_level.replace('_', ' ').title()} Track):**\n"
            "- **Clarity:** Provide a focused, professional narrative.\n"
            f"- **Evidence:** {hr_tip}\n"
            "- **Alignment:** Connect your past accomplishments with the target opportunity."
        )


def _render_timer_component(st_module: Any) -> None:
    """Render an optional response timer for timed practice with 1-second auto-refresh."""
    if "timer_running" not in st_module.session_state:
        st_module.session_state["timer_running"] = False
    if "timer_start" not in st_module.session_state:
        st_module.session_state["timer_start"] = 0.0
    if "timer_elapsed" not in st_module.session_state:
        st_module.session_state["timer_elapsed"] = 0.0

    is_running = bool(st_module.session_state.get("timer_running", False))

    with st_module.expander("⏱️ Optional Practice Response Timer", expanded=is_running):
        st_module.caption(
            "Time your spoken or typed response. Standard interview benchmarks recommend 90 to 180 seconds per answer."
        )

        def _timer_body():
            elapsed = float(st_module.session_state.get("timer_elapsed", 0.0))
            if st_module.session_state.get("timer_running", False):
                elapsed += time.time() - float(st_module.session_state.get("timer_start", time.time()))

            current_elapsed = int(elapsed)
            mins, secs = divmod(current_elapsed, 60)
            time_str = f"{mins:02d}:{secs:02d}"

            t_col1, t_col2, t_col3, t_col4 = st_module.columns([2, 1, 1, 1])

            with t_col1:
                st_module.markdown(
                    f"""
                    <div class='timer-container'>
                        <span style='color: #94A3B8; font-size: 0.85rem; font-weight: 600;'>ELAPSED TIME</span>
                        <span class='timer-digits'>{time_str}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with t_col2:
                if not st_module.session_state.get("timer_running", False):
                    btn_label = "▶ Resume" if float(st_module.session_state.get("timer_elapsed", 0.0)) > 0 else "▶ Start"
                    if st_module.button(btn_label, key="btn_start_timer", use_container_width=True):
                        st_module.session_state["timer_running"] = True
                        st_module.session_state["timer_start"] = time.time()
                        st_module.rerun()
                else:
                    if st_module.button("⏸ Pause", key="btn_pause_timer", use_container_width=True):
                        st_module.session_state["timer_running"] = False
                        st_module.session_state["timer_elapsed"] += time.time() - st_module.session_state["timer_start"]
                        st_module.rerun()

            with t_col3:
                if st_module.button("🔄 Reset", key="btn_reset_timer", use_container_width=True):
                    st_module.session_state["timer_running"] = False
                    st_module.session_state["timer_elapsed"] = 0.0
                    st_module.session_state["timer_start"] = 0.0
                    st_module.rerun()

            with t_col4:
                if current_elapsed > 180:
                    st_module.caption("⚠️ Exceeds 3 min (consider summarizing)")
                elif current_elapsed >= 60:
                    st_module.caption("🟢 Good answer pace")
                else:
                    st_module.caption("⚪ In progress")

        fragment_fn = getattr(st_module, "fragment", None)
        if fragment_fn is not None and is_running:
            @fragment_fn(run_every=1)
            def _live_timer():
                _timer_body()
            _live_timer()
        else:
            _timer_body()


def _render_transcription_diagnostics(
    st_module: Any,
    tx_info: Dict[str, Any],
    qid: str,
) -> None:
    """Render prominent diagnostic details and API key guidance."""
    props = tx_info.get("debug_info", {})
    status = tx_info.get("status", "unknown")
    engine = tx_info.get("engine", "None")

    badge_color = "#34D399" if status == "success" else "#F87171"
    status_label = "SUCCESS" if status == "success" else "ERROR"

    byte_count = props.get("byte_size", 0)
    rate = props.get("sample_rate", "N/A")
    ch = props.get("channels", "N/A")
    bits = props.get("bit_depth", "N/A")
    dur = props.get("duration_sec", tx_info.get("duration", 0.0))
    fmt = props.get("format", "WAV")

    detected_lang = tx_info.get("language", "English")
    lang_code = tx_info.get("language_code", "en")
    orig_transcript = tx_info.get("original_transcript", tx_info.get("text", ""))
    trans_applied = tx_info.get("translation_applied", False)
    trans_note = (
        "Yes"
        if trans_applied
        else "No (Preserved in original script; translated during evaluation if non-English)"
    )

    st_module.markdown(
        f"""
        <div style='background: #1E293B; border-left: 3px solid {badge_color}; padding: 0.75rem 1rem; border-radius: 6px; margin: 0.6rem 0; font-size: 0.82rem; color: #E2E8F0;'>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;'>
                <strong style='color: #F8FAFC;'>🔍 Transcription Execution Report</strong>
                <span style='background: {badge_color}22; color: {badge_color}; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 0.75rem;'>{status_label}</span>
            </div>
            <div style='font-family: monospace; line-height: 1.6; color: #94A3B8;'>
                • <b>Byte Payload:</b> {byte_count:,} bytes (~{byte_count/1024:.1f} KB)<br/>
                • <b>Detected Properties:</b> {fmt} | {rate} Hz | {ch} channel(s) | {bits}-bit PCM<br/>
                • <b>Duration:</b> ~{dur}s | <b>Engine:</b> <span style='color: #7DB8F5;'>{engine}</span><br/>
                • <b>Detected Language:</b> <span style='color: #38BDF8;'>{detected_lang}</span> (Code: <code>{lang_code}</code>)<br/>
                • <b>Original Transcript:</b> <span style='color: #F8FAFC;'>"{orig_transcript}"</span><br/>
                • <b>Translation Applied:</b> <span style='color: #34D399;'>{trans_note}</span><br/>
                • <b>Handler Status:</b> <code>transcribe_audio_payload()</code> returned <code>{status}</code>.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if status == "success" and tx_info.get("text"):
        st_module.success(f"✅ Transcribed speech loaded into response area: \"{tx_info.get('text')}\"")
    elif status == "success" and tx_info.get("warning"):
        st_module.warning(tx_info.get("warning"))
    elif status == "error":
        st_module.error(f"❌ {tx_info.get('error')}")

        if tx_info.get("error_type") == "CREDENTIALS_REQUIRED":
            st_module.info(
                "💡 **How to proceed:**\n"
                "1. **Option A (Free Groq Whisper)**: Obtain a free API key at [console.groq.com](https://console.groq.com) and enter it below.\n"
                "2. **Option B (OpenAI Whisper)**: Provide your OpenAI API key below.\n"
                "3. **Option C (Direct Text)**: Type or paste your response directly in the text box below (no API key required)."
            )
            new_key = st_module.text_input(
                "Enter Groq or OpenAI API Key",
                type="password",
                value=st_module.session_state.get("user_stt_api_key", ""),
                key=f"inline_key_input_{qid}",
                placeholder="Paste key (e.g. gsk_... or sk-...)",
            )
            if st_module.button("💾 Save Key & Transcribe", key=f"btn_save_key_{qid}", type="secondary"):
                st_module.session_state["user_stt_api_key"] = new_key.strip()
                st_module.rerun()


def render_practice_interview(
    st_module: Any,
    on_evaluation_complete: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> None:
    """
    Render the interactive Practice Interview workspace in Streamlit.

    Args:
        st_module: The streamlit module (or mock).
        on_evaluation_complete: Callback invoked with the evaluation result dict.
    """
    st_module.markdown("<h1 class='main-title'>Practice Interview Workspace</h1>", unsafe_allow_html=True)
    st_module.markdown(
        "<p class='sub-title'>Select an interview prompt, compose your response, and obtain multi-dimensional AI evaluation with instant feedback.</p>",
        unsafe_allow_html=True,
    )

    questions_map = load_questions_map()
    if not questions_map:
        st_module.error("Unable to load interview questions from data/questions.json.")
        return

    # 1. Prompt Selection & Candidate Level Row
    col_sel_cat, col_sel_lvl, col_sel_q = st_module.columns([1, 1, 2])

    with col_sel_cat:
        categories = ["All"] + sorted(list(set(q.get("category", "General") for q in questions_map.values())))
        selected_cat = st_module.selectbox("1. Filter by Category", categories, index=0)

    # Candidate Level Selection (Defaults to Final-Year / Placement Ready)
    if "candidate_level" not in st_module.session_state:
        st_module.session_state["candidate_level"] = DEFAULT_CANDIDATE_LEVEL

    level_keys = [opt[0] for opt in LEVEL_DISPLAY_OPTIONS]
    level_labels = {opt[0]: opt[1] for opt in LEVEL_DISPLAY_OPTIONS}
    current_lvl_idx = level_keys.index(st_module.session_state["candidate_level"]) if st_module.session_state["candidate_level"] in level_keys else 0

    with col_sel_lvl:
        selected_level = st_module.selectbox(
            "2. Candidate Level",
            level_keys,
            index=current_lvl_idx,
            format_func=lambda k: level_labels[k],
            help="Adapts evaluation criteria, structural evidence expectations, and feedback to your career stage.",
        )
        st_module.session_state["candidate_level"] = selected_level

    # Filter questions
    if selected_cat == "All":
        filtered_qids = list(questions_map.keys())
    else:
        filtered_qids = [
            qid for qid, q in questions_map.items() if q.get("category") == selected_cat
        ]

    # 3. Question Selection
    question_labels = {
        qid: f"[{questions_map[qid]['category']}] {questions_map[qid]['question_id']}: {questions_map[qid]['question'][:75]}..."
        for qid in filtered_qids
    }

    with col_sel_q:
        selected_qid = st_module.selectbox(
            "3. Select Interview Question",
            filtered_qids,
            format_func=lambda qid: question_labels[qid],
        )

    current_q = questions_map[selected_qid]
    category_name = current_q.get("category", "General").lower()
    tag_class = f"tag-{category_name}" if category_name in ["hr", "behavioral", "technical"] else "tag-technical"
    lvl_info = get_candidate_level_info(selected_level)
    badge_label = lvl_info.get("badge_label", "🎓 Final-Year / Placement")

    # 4. Question Presentation Card
    st_module.markdown(
        f"""
        <div class='question-card'>
            <div style='display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;'>
                <div>
                    <span class='question-tag {tag_class}'>{current_q.get('category', 'General')} Track</span>
                    <span style='margin-left: 0.5rem; background: rgba(59, 130, 246, 0.15); color: #93C5FD; border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 9999px; padding: 0.2rem 0.65rem; font-size: 0.78rem; font-weight: 600;'>{badge_label}</span>
                </div>
                <span style='color: #94A3B8; font-size: 0.8rem; font-family: monospace;'>ID: {current_q.get('question_id')}</span>
            </div>
            <p class='question-text'>{current_q['question']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Collapsible Strategy Guidance adapted to Candidate Level
    guidance = get_approach_guidance(current_q, candidate_level=selected_level)
    with st_module.expander("💡 Recommended Answering Strategy & Evaluation Focus", expanded=False):
        st_module.markdown(guidance)
        if current_q.get("expected_keywords"):
            keyword_pills = " &bull; ".join(current_q["expected_keywords"][:7])
            st_module.caption(f"**Key Concepts to Touch Upon:** {keyword_pills}")

    # Optional Response Timer
    _render_timer_component(st_module)

    # 4. Input Method Selector (Text Answer, Record Answer, Upload Audio)
    input_modes = ["📝 Text Answer", "🎙️ Record Answer", "📁 Upload Audio"]
    mode_key = f"input_mode_sel_{selected_qid}"
    if mode_key not in st_module.session_state:
        st_module.session_state[mode_key] = "📝 Text Answer"

    selected_mode = st_module.radio(
        "Response Input Method",
        input_modes,
        horizontal=True,
        key=mode_key,
        help="Choose how to enter your response: type directly, record live with microphone, or upload an audio file.",
    )

    input_key = f"answer_input_{selected_qid}"
    text_area_key = f"text_area_{selected_qid}"
    pending_key = f"pending_transcript_{selected_qid}"

    if pending_key not in st_module.session_state:
        st_module.session_state[pending_key] = None
    if input_key not in st_module.session_state:
        st_module.session_state[input_key] = ""

    # Apply any pending transcript or clear BEFORE instantiating the text area widget
    if st_module.session_state[pending_key] is not None:
        st_module.session_state[text_area_key] = st_module.session_state[pending_key]
        st_module.session_state[input_key] = st_module.session_state[pending_key]
        st_module.session_state[pending_key] = None
    elif text_area_key not in st_module.session_state:
        st_module.session_state[text_area_key] = st_module.session_state[input_key]

    if "user_stt_api_key" not in st_module.session_state:
        st_module.session_state["user_stt_api_key"] = ""

    # Mode 2: Record Answer (Browser Microphone)
    if selected_mode == "🎙️ Record Answer":
        st_module.markdown(
            """
            <div class='metric-card' style='margin-bottom: 0.75rem;'>
                <div style='font-size: 0.88rem; font-weight: 600; color: #7CB7F5; margin-bottom: 0.25rem;'>
                    🎙️ Microphone Recording
                </div>
                <div style='font-size: 0.82rem; color: #CBD5E1;'>
                    Click the record button to speak your response. Stop when finished, listen back if desired, and click <b>Transcribe Recording</b>. The converted text will appear in the editable box below for your review.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if hasattr(st_module, "audio_input"):
            rec_audio = st_module.audio_input(
                "Record your answer using your microphone",
                key=f"audio_recorder_{selected_qid}",
            )
            if rec_audio is not None:
                audio_bytes = rec_audio.getvalue()
                col_btn, col_info = st_module.columns([1, 2])
                with col_btn:
                    btn_tx_clicked = st_module.button(
                        "✨ Transcribe Recording",
                        key=f"btn_tx_rec_{selected_qid}",
                        type="primary",
                        use_container_width=True,
                    )
                with col_info:
                    st_module.caption(f"Recording ready ({len(audio_bytes) / 1024:.1f} KB). Click Transcribe to populate the answer box.")

                if btn_tx_clicked:
                    st_module.info("🚀 **Transcription started** — Inspecting WAV payload and executing Speech-to-Text pipeline...")
                    try:
                        tx_res = transcribe_audio_payload(
                            audio_bytes,
                            filename="recording.wav",
                            api_key=st_module.session_state.get("user_stt_api_key"),
                        )
                    except Exception as ex:
                        import traceback
                        props = inspect_audio_properties(audio_bytes)
                        tx_res = {
                            "status": "error",
                            "error_type": "UNCAUGHT_EXCEPTION",
                            "error": f"Unhandled exception during transcription: {ex}",
                            "traceback": traceback.format_exc(),
                            "text": "",
                            "engine": "Exception",
                            "debug_info": props,
                        }

                    st_module.session_state[f"last_tx_info_{selected_qid}"] = tx_res
                    if tx_res.get("status") == "success" and tx_res.get("text"):
                        st_module.session_state[pending_key] = tx_res["text"]
                        st_module.rerun()

                # Persistent diagnostic report
                if f"last_tx_info_{selected_qid}" in st_module.session_state:
                    _render_transcription_diagnostics(
                        st_module,
                        st_module.session_state[f"last_tx_info_{selected_qid}"],
                        selected_qid,
                    )
        else:
            st_module.info("Live microphone recording requires Streamlit 1.35+ (`st.audio_input`). Please use Upload Audio or direct text input.")

    # Mode 3: Upload Audio File
    elif selected_mode == "📁 Upload Audio":
        st_module.markdown(
            """
            <div class='metric-card' style='margin-bottom: 0.75rem;'>
                <div style='font-size: 0.88rem; font-weight: 600; color: #7CB7F5; margin-bottom: 0.25rem;'>
                    📁 Audio File Upload
                </div>
                <div style='font-size: 0.82rem; color: #CBD5E1;'>
                    Upload a pre-recorded response in <b>WAV</b> or <b>MP3</b> format (max 25 MB). Click <b>Transcribe Uploaded Audio</b> to convert it into editable text below.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        audio_file = st_module.file_uploader(
            "Upload Interview Audio Recording",
            type=["wav", "mp3"],
            key=f"audio_uploader_{selected_qid}",
            help="Supported formats: WAV, MP3. File size limit: 25 MB.",
        )

        if audio_file is not None:
            audio_bytes = audio_file.getvalue()
            is_valid, val_err = validate_audio_data(audio_bytes, filename=audio_file.name)
            if not is_valid:
                st_module.error(f"⚠️ {val_err}")
            else:
                st_module.audio(audio_file)
                col_btn, col_info = st_module.columns([1, 2])
                with col_btn:
                    btn_up_clicked = st_module.button(
                        "✨ Transcribe Uploaded Audio",
                        key=f"btn_tx_up_{selected_qid}",
                        type="primary",
                        use_container_width=True,
                    )
                with col_info:
                    st_module.caption(f"Loaded: `{audio_file.name}` ({len(audio_bytes) / 1024:.1f} KB).")

                if btn_up_clicked:
                    st_module.info("🚀 **Transcription started** — Inspecting audio payload and executing Speech-to-Text pipeline...")
                    try:
                        tx_res = transcribe_audio_payload(
                            audio_bytes,
                            filename=audio_file.name,
                            api_key=st_module.session_state.get("user_stt_api_key"),
                        )
                    except Exception as ex:
                        import traceback
                        props = inspect_audio_properties(audio_bytes)
                        tx_res = {
                            "status": "error",
                            "error_type": "UNCAUGHT_EXCEPTION",
                            "error": f"Unhandled exception during transcription: {ex}",
                            "traceback": traceback.format_exc(),
                            "text": "",
                            "engine": "Exception",
                            "debug_info": props,
                        }

                    st_module.session_state[f"last_tx_info_{selected_qid}"] = tx_res
                    if tx_res.get("status") == "success" and tx_res.get("text"):
                        st_module.session_state[pending_key] = tx_res["text"]
                        st_module.rerun()

                # Persistent diagnostic report
                if f"last_tx_info_{selected_qid}" in st_module.session_state:
                    _render_transcription_diagnostics(
                        st_module,
                        st_module.session_state[f"last_tx_info_{selected_qid}"],
                        selected_qid,
                    )

    # 5. Answer Input Area (Always available, editable transcription / direct composition)
    candidate_answer = st_module.text_area(
        "Your Interview Response (Review & Edit)",
        height=240,
        placeholder="Type, dictate, or review your transcribed response here. Provide context, specific actions taken, technical details, and measurable outcomes...",
        key=text_area_key,
    )

    # Sync only candidate answer to input_key (never mutate text_area_key after instantiation)
    st_module.session_state[input_key] = candidate_answer

    # Clean text calculation for counters
    clean_ans = clean_text(candidate_answer)
    words = clean_ans.split() if clean_ans else []
    word_count = len(words)
    char_count = len(clean_ans)
    est_speech_time = round(word_count / 130.0, 1)

    # Word count status indicator
    if word_count == 0:
        len_status = "<span style='color: #94A3B8;'>⚪ Empty</span>"
    elif word_count < 15:
        len_status = "<span style='color: #F87171;'>⚠️ Very brief (<15 words)</span>"
    elif word_count < 80:
        len_status = "<span style='color: #FBBF24;'>🟡 Short (consider expanding)</span>"
    elif word_count <= 250:
        len_status = "<span style='color: #34D399;'>🟢 Optimal length (80-250 words)</span>"
    else:
        len_status = "<span style='color: #60A5FA;'>🔵 Detailed / Comprehensive</span>"

    # Live Word & Character Counter Bar
    st_module.markdown(
        f"""
        <div class='counter-bar'>
            <div class='counter-metric'>
                <span>📝 Word Count:</span>
                <strong>{word_count}</strong>
            </div>
            <div class='counter-metric'>
                <span>🔤 Characters:</span>
                <strong>{char_count}</strong>
            </div>
            <div class='counter-metric'>
                <span>⏱️ Speaking Pace:</span>
                <strong>~{est_speech_time} min</strong>
            </div>
            <div>
                {len_status}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 6. Action Controls: Clear Answer and Submit Answer
    btn_col1, btn_col2 = st_module.columns([1, 2])

    with btn_col1:
        clear_clicked = st_module.button(
            "🗑️ Clear Answer",
            type="secondary",
            use_container_width=True,
            help="Clear current answer text for this question.",
        )
        if clear_clicked:
            st_module.session_state[pending_key] = ""
            st_module.session_state[input_key] = ""
            st_module.rerun()

    with btn_col2:
        evaluate_clicked = st_module.button(
            "🚀 Submit Answer for Evaluation",
            type="primary",
            use_container_width=True,
            help="Run multi-dimensional evaluation across semantic, delivery, and structural dimensions.",
        )

    # 6. Evaluation Results Preview, when available
    last_eval = st_module.session_state.get("last_evaluation")
    if last_eval and last_eval.get("question_id") == selected_qid:
        st_module.markdown(
            f"""
            <div class='metric-card' style='margin-top: 1rem;'>
                <div style='display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;'>
                    <div>
                        <span class='kpi-title'>Latest Evaluation Available for this Prompt</span>
                        <div style='font-size: 1.15rem; font-weight: 700; color: #F8FAFC; margin-top: 0.2rem;'>
                            Overall Score: <span style='color: #7CB7F5;'>{last_eval.get('overall_score', 0):.1f} / 100</span>
                            ({last_eval.get('performance_category', 'Needs Improvement')})
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st_module.button("📊 Inspect Full Breakdown in Performance Analysis", key="btn_view_last_eval", use_container_width=True):
            st_module.session_state["active_nav"] = "Performance Analysis"
            st_module.rerun()

    # 7. Evaluation Handling & Validation
    if evaluate_clicked:
        # Prevent empty submissions
        if not clean_ans or word_count == 0:
            st_module.error("⚠️ Please enter your interview answer before submitting. Empty responses cannot be evaluated.")
            return

        if word_count < 15:
            st_module.warning(
                f"⚠️ Your answer is very brief ({word_count} words). "
                "Answers with limited elaboration typically receive lower semantic and structure scores."
            )

        with st_module.spinner("Analyzing response across semantic, delivery, communication, and structure dimensions..."):
            eval_result = evaluate_answer(selected_qid, clean_ans, candidate_level=selected_level)
            saved_record = save_evaluation_to_history(eval_result, current_q)

            st_module.session_state["last_evaluation"] = eval_result
            st_module.session_state["last_question_data"] = current_q
            st_module.session_state["active_nav"] = "Performance Analysis"

            st_module.success(
                f"Evaluation Complete! Overall Score: **{eval_result['overall_score']:.1f}/100** ({eval_result['performance_category']})."
            )

            if on_evaluation_complete:
                on_evaluation_complete(eval_result)

            st_module.rerun()
