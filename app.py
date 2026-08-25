import os
import uuid
from pathlib import Path

import streamlit as st

from main import run_pipeline


# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Vagent | Video Agent",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --------------------------------------------------
# Styling
# --------------------------------------------------

st.markdown(
    """
    <style>
    .stApp {
        background: #0b0d11;
        color: #f5f7fa;
    }

    [data-testid="stSidebar"] {
        background: #101319;
        border-right: 1px solid #22262f;
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 2rem;
    }

    .block-container {
        max-width: 1400px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .vagent-brand {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        margin-bottom: 0.1rem;
    }

    .vagent-subtitle {
        color: #8d95a3;
        font-size: 0.9rem;
        margin-bottom: 2rem;
    }

    .hero {
        padding: 3.5rem 2rem 3rem 2rem;
        border: 1px solid #252a34;
        border-radius: 24px;
        background:
            radial-gradient(
                circle at top right,
                rgba(99, 102, 241, 0.14),
                transparent 35%
            ),
            #101319;
        text-align: center;
        margin-bottom: 2rem;
    }

    .hero-title {
        font-size: 3.2rem;
        font-weight: 800;
        letter-spacing: -0.05em;
        margin-bottom: 0.4rem;
    }

    .hero-title span {
        color: #8b8df8;
    }

    .hero-description {
        max-width: 680px;
        margin: auto;
        color: #9aa2b1;
        font-size: 1.05rem;
        line-height: 1.7;
    }

    .section-title {
        font-size: 1.25rem;
        font-weight: 700;
        margin: 1.5rem 0 0.8rem 0;
    }

    .meeting-header {
        padding: 1.5rem 1.7rem;
        border: 1px solid #252a34;
        border-radius: 18px;
        background: #101319;
        margin-bottom: 1.2rem;
    }

    .meeting-label {
        color: #858d9b;
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.4rem;
    }

    .meeting-title {
        font-size: 1.8rem;
        font-weight: 750;
        line-height: 1.3;
    }

    .stat-card {
        background: #101319;
        border: 1px solid #252a34;
        border-radius: 16px;
        padding: 1.2rem;
        min-height: 105px;
    }

    .stat-value {
        font-size: 1.7rem;
        font-weight: 750;
    }

    .stat-label {
        color: #858d9b;
        font-size: 0.82rem;
        margin-top: 0.25rem;
    }

    .milo-card {
        padding: 1.8rem;
        border: 1px solid #2b3040;
        border-radius: 20px;
        background:
            radial-gradient(
                circle at top right,
                rgba(139, 141, 248, 0.12),
                transparent 38%
            ),
            #101319;
        margin-bottom: 1.5rem;
    }

    .milo-name {
        font-size: 1.35rem;
        font-weight: 750;
    }

    .milo-role {
        color: #858d9b;
        font-size: 0.85rem;
        margin-top: 0.2rem;
    }

    .milo-text {
        color: #c3c8d2;
        margin-top: 1rem;
        line-height: 1.6;
    }

    .suggestion {
        border: 1px solid #252a34;
        border-radius: 12px;
        padding: 0.8rem 1rem;
        background: #0d1015;
        color: #c7ccd5;
        margin-bottom: 0.6rem;
    }

    .empty-state {
        text-align: center;
        padding: 3rem 1rem;
        color: #858d9b;
    }

    .footer {
        text-align: center;
        color: #5f6775;
        font-size: 0.75rem;
        margin-top: 3rem;
    }

    div[data-testid="stMetric"] {
        background: #101319;
        border: 1px solid #252a34;
        border-radius: 14px;
        padding: 1rem;
    }

    div.stButton > button {
        border-radius: 10px;
        font-weight: 600;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# --------------------------------------------------
# Session state
# --------------------------------------------------

if "meeting_result" not in st.session_state:
    st.session_state.meeting_result = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "processing" not in st.session_state:
    st.session_state.processing = False


# --------------------------------------------------
# Helper functions
# --------------------------------------------------

def reset_meeting():
    st.session_state.meeting_result = None
    st.session_state.messages = []
    st.session_state.processing = False


def save_uploaded_file(uploaded_file):
    downloads_dir = Path("downloads")
    downloads_dir.mkdir(exist_ok=True)

    safe_name = Path(uploaded_file.name).name
    unique_name = f"{uuid.uuid4().hex[:8]}_{safe_name}"
    file_path = downloads_dir / unique_name

    with open(file_path, "wb") as file:
        file.write(uploaded_file.getbuffer())

    return str(file_path)


def count_items(text):
    if not text:
        return 0

    lowered = text.lower()

    if "no action items found" in lowered:
        return 0

    if "no decisions found" in lowered:
        return 0

    if "no questions found" in lowered:
        return 0

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    numbered = [
        line for line in lines
        if line[:2].rstrip(".").isdigit()
        or line[:3].rstrip(".").isdigit()
    ]

    return len(numbered) if numbered else len(lines)


def show_analysis():
    result = st.session_state.meeting_result

    if not result:
        return

    title = result.get("title", "Meeting Analysis")
    transcript = result.get("transcript", "")
    summary = result.get("summary", "")
    actions = result.get("action_items", "")
    decisions = result.get("key_decisions", "")
    questions = result.get("open_questions", "")

    st.markdown(
        f"""
        <div class="meeting-header">
            <div class="meeting-label">Vagent Meeting Workspace</div>
            <div class="meeting-title">{title}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    duration = "—"
    transcript_words = len(transcript.split()) if transcript else 0

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            """
            <div class="stat-card">
                <div class="stat-value">✓</div>
                <div class="stat-label">Analysis complete</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-value">{transcript_words:,}</div>
                <div class="stat-label">Transcript words</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-value">{count_items(actions)}</div>
                <div class="stat-label">Action items</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-value">{count_items(questions)}</div>
                <div class="stat-label">Questions</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    overview_tab, insights_tab, transcript_tab, milo_tab = st.tabs(
        ["Overview", "Insights", "Transcript", "✦ Milo"]
    )

    with overview_tab:
        st.markdown("### Executive Summary")
        st.markdown(summary)

        st.markdown("<br>", unsafe_allow_html=True)

        st.info(
            "Milo is ready. Ask questions about this meeting using the transcript as its source."
        )

    with insights_tab:
        action_col, decision_col = st.columns(2)

        with action_col:
            st.markdown("### ✅ Action Items")
            if actions:
                st.markdown(actions)
            else:
                st.caption("No action items available.")

        with decision_col:
            st.markdown("### 🔑 Key Decisions")
            if decisions:
                st.markdown(decisions)
            else:
                st.caption("No decisions available.")

        st.markdown("---")
        st.markdown("### ❓ Open Questions")

        if questions:
            st.markdown(questions)
        else:
            st.caption("No open questions available.")

    with transcript_tab:
        st.markdown("### Meeting Transcript")

        if transcript:
            st.text_area(
                "Transcript",
                value=transcript,
                height=600,
                label_visibility="collapsed"
            )
        else:
            st.markdown(
                '<div class="empty-state">No transcript available.</div>',
                unsafe_allow_html=True
            )

    with milo_tab:
        show_milo_chat()


def show_milo_chat():
    st.markdown(
        """
        <div class="milo-card">
            <div class="milo-name">✦ Milo</div>
            <div class="milo-role">Vagent's AI meeting assistant</div>
            <div class="milo-text">
                Ask me anything about this meeting. I will answer using
                the meeting transcript as my source.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if not st.session_state.messages:
        st.markdown("#### Try asking Milo")

        suggestion_cols = st.columns(2)

        suggestions = [
            "What were the main decisions?",
            "What action items were assigned?",
            "What were the biggest concerns?",
            "What happened with Microsoft?"
        ]

        for index, suggestion in enumerate(suggestions):
            with suggestion_cols[index % 2]:
                if st.button(
                    suggestion,
                    key=f"suggestion_{index}",
                    use_container_width=True
                ):
                    st.session_state.messages.append(
                        {
                            "role": "user",
                            "content": suggestion
                        }
                    )

                    with st.spinner("Milo is thinking..."):
                        try:
                            rag_chain = st.session_state.meeting_result["rag_chain"]
                            answer = rag_chain.invoke(suggestion)

                            st.session_state.messages.append(
                                {
                                    "role": "assistant",
                                    "content": answer
                                }
                            )
                        except Exception as error:
                            st.session_state.messages.append(
                                {
                                    "role": "assistant",
                                    "content": f"I ran into an error: {error}"
                                }
                            )

                    st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
                st.markdown(message["content"])

    question = st.chat_input("Ask Milo about this meeting...")

    if question:
        st.session_state.messages.append(
            {
                "role": "user",
                "content": question
            }
        )

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Milo is thinking..."):
                try:
                    rag_chain = st.session_state.meeting_result["rag_chain"]
                    answer = rag_chain.invoke(question)

                    st.markdown(answer)

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": answer
                        }
                    )
                except Exception as error:
                    error_message = (
                        "I couldn't process that question right now. "
                        "Please try again."
                    )

                    st.error(error_message)

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": error_message
                        }
                    )


# --------------------------------------------------
# Sidebar
# --------------------------------------------------

with st.sidebar:
    st.markdown(
        """
        <div class="vagent-brand">Vagent</div>
        <div class="vagent-subtitle">Video Agent · Meeting Intelligence</div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### New Meeting")

    source_type = st.radio(
        "Meeting source",
        ["YouTube URL", "Upload file"],
        horizontal=True
    )

    youtube_url = ""
    uploaded_file = None

    if source_type == "YouTube URL":
        youtube_url = st.text_input(
            "YouTube URL",
            placeholder="https://youtube.com/..."
        )

    else:
        uploaded_file = st.file_uploader(
            "Upload meeting audio/video",
            type=[
                "mp3",
                "wav",
                "m4a",
                "mp4",
                "mov",
                "webm",
                "mkv"
            ]
        )

    language = st.selectbox(
        "Meeting language",
        ["english", "hinglish"]
    )

    analyze = st.button(
        "✦ Analyse Meeting",
        type="primary",
        use_container_width=True
    )

    if st.session_state.meeting_result:
        st.markdown("---")

        if st.button(
            "＋ New Meeting",
            use_container_width=True
        ):
            reset_meeting()
            st.rerun()

    st.markdown("---")

    st.caption("Vagent")
    st.caption("AI-powered video and meeting intelligence")


# --------------------------------------------------
# Main application
# --------------------------------------------------

if not st.session_state.meeting_result:
    st.markdown(
        """
        <div class="hero">
            <div class="hero-title">
                Meet <span>Vagent</span>
            </div>
            <div class="hero-description">
                Turn meetings into structured knowledge.
                Vagent transcribes your recording, extracts the important
                information, and lets you ask Milo questions about it.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🎙️ Transcribe")
        st.caption(
            "Convert meeting audio and video into a searchable transcript."
        )

    with col2:
        st.markdown("### 🧠 Understand")
        st.caption(
            "Generate summaries, action items, decisions and questions."
        )

    with col3:
        st.markdown("### ✦ Ask Milo")
        st.caption(
            "Chat with your meeting using retrieval-augmented answers."
        )

    st.markdown("<br>", unsafe_allow_html=True)

    if analyze:
        if source_type == "YouTube URL":
            if not youtube_url.strip():
                st.error("Please enter a YouTube URL.")
                st.stop()

            source = youtube_url.strip()

        else:
            if uploaded_file is None:
                st.error("Please upload an audio or video file.")
                st.stop()

            try:
                source = save_uploaded_file(uploaded_file)
            except Exception:
                st.error("Could not save the uploaded file.")
                st.stop()

        st.session_state.processing = True

        st.markdown("### Analysing your meeting")

        try:
            with st.status(
                "Vagent is processing your meeting...",
                expanded=True
            ) as status:
                st.write("🎙️ Processing audio/video...")
                st.write("📝 Generating transcript...")
                st.write("🧠 Generating meeting insights...")
                st.write("🔎 Building Milo's knowledge base...")

                result = run_pipeline(
                    source,
                    language
                )

                st.session_state.meeting_result = result
                st.session_state.messages = []

                status.update(
                    label="Meeting analysis complete",
                    state="complete",
                    expanded=False
                )

            st.session_state.processing = False
            st.rerun()

        except Exception as error:
            st.session_state.processing = False

            st.error(
                "Vagent could not complete the meeting analysis."
            )

            with st.expander("Technical details"):
                st.exception(error)

else:
    show_analysis()


# --------------------------------------------------
# Footer
# --------------------------------------------------

st.markdown(
    """
    <div class="footer">
        Vagent · Video Agent &nbsp;•&nbsp; Powered by AI
    </div>
    """,
    unsafe_allow_html=True
)