# =============================================================================
# AI Resume Screener — app/main.py
# Full Streamlit UI — entry point for the web application.
#
# Resume input methods (user chooses one):
#   1. Upload PDF
#   2. Upload Word (.docx)
#   3. Paste resume text directly
#
# Layout:
#   1. Page config + custom CSS
#   2. Header
#   3. Resume input (tab selector + input area)
#   4. Job description input
#   5. Analyze button
#   6. Results (score, matched skills, missing skills, suggestions)
# =============================================================================

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from app.pdf_utils import validate_uploaded_file, extract_text_from_file
from app.claude_client import screen_resume

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Resume Screener",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');

    .stApp {
        background-color: #0f1117;
        color: #e8e8e8;
        font-family: 'DM Sans', sans-serif;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        max-width: 1100px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .app-header {
        text-align: center;
        padding: 2.5rem 0 2rem 0;
        border-bottom: 1px solid #2a2d3a;
        margin-bottom: 2.5rem;
    }
    .app-title {
        font-family: 'DM Serif Display', serif;
        font-size: 3rem;
        color: #f0f0f0;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .app-subtitle {
        font-size: 1rem;
        color: #8b8fa8;
        margin-top: 0.5rem;
        font-weight: 300;
    }
    .section-label {
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #6c7293;
        margin-bottom: 0.5rem;
    }
    .score-container {
        background: linear-gradient(135deg, #1a1d2e 0%, #16192a 100%);
        border: 1px solid #2a2d3a;
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .score-number {
        font-family: 'DM Serif Display', serif;
        font-size: 5rem;
        line-height: 1;
        margin: 0.5rem 0;
    }
    .score-label {
        font-size: 0.8rem;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #6c7293;
    }
    .score-summary {
        font-size: 0.95rem;
        color: #a0a4bc;
        margin-top: 1rem;
        line-height: 1.6;
        font-style: italic;
    }
    .score-high  { color: #4ade80; }
    .score-mid   { color: #fbbf24; }
    .score-low   { color: #f87171; }
    .results-card {
        background: #1a1d2e;
        border: 1px solid #2a2d3a;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .results-card-title {
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }
    .title-green { color: #4ade80; }
    .title-red   { color: #f87171; }
    .title-blue  { color: #60a5fa; }
    .skill-pills { display: flex; flex-wrap: wrap; gap: 0.5rem; }
    .pill-green {
        background: rgba(74, 222, 128, 0.1);
        border: 1px solid rgba(74, 222, 128, 0.3);
        color: #4ade80;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
    }
    .pill-red {
        background: rgba(248, 113, 113, 0.1);
        border: 1px solid rgba(248, 113, 113, 0.3);
        color: #f87171;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
    }
    .suggestion-item {
        display: flex;
        gap: 0.75rem;
        padding: 0.75rem 0;
        border-bottom: 1px solid #2a2d3a;
        font-size: 0.9rem;
        color: #c0c4d8;
        line-height: 1.5;
    }
    .suggestion-item:last-child { border-bottom: none; }
    .suggestion-number { color: #60a5fa; font-weight: 600; min-width: 1.5rem; }
    .section-divider { border: none; border-top: 1px solid #2a2d3a; margin: 2rem 0; }
    .empty-state { text-align: center; padding: 3rem; color: #4a4d62; font-size: 0.9rem; }
    .stButton > button {
        background: linear-gradient(135deg, #3b5bdb, #5c7cfa);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2.5rem;
        font-family: 'DM Sans', sans-serif;
        font-size: 0.95rem;
        font-weight: 500;
        letter-spacing: 0.5px;
        width: 100%;
    }
    .stTextArea textarea {
        background: #1a1d2e;
        border: 1px solid #2a2d3a;
        border-radius: 12px;
        color: #e8e8e8;
        font-family: 'DM Sans', sans-serif;
        font-size: 0.9rem;
    }
    .error-box {
        background: rgba(248, 113, 113, 0.1);
        border: 1px solid rgba(248, 113, 113, 0.3);
        border-radius: 8px;
        padding: 1rem 1.25rem;
        color: #f87171;
        font-size: 0.9rem;
        margin-top: 1rem;
    }
    /* ── Tab styling ── */
    .stTabs [data-baseweb="tab-list"] {
        background: #1a1d2e;
        border-radius: 8px;
        padding: 4px;
        gap: 4px;
        border: 1px solid #2a2d3a;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: #6c7293;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background: #2a2d3a;
        color: #e8e8e8;
    }
</style>
""", unsafe_allow_html=True)


# ── Helper functions ──────────────────────────────────────────────────────────

def get_score_class(score: int) -> str:
    """Returns CSS class based on score tier: green/amber/red."""
    if score >= 70:
        return "score-high"
    elif score >= 40:
        return "score-mid"
    return "score-low"


def render_pills(skills: list[str], pill_class: str) -> str:
    """Builds HTML pill tags for a list of skills."""
    if not skills:
        return "<span style='color:#4a4d62; font-size:0.85rem;'>None identified</span>"
    pills = "".join(f'<span class="{pill_class}">{s}</span>' for s in skills)
    return f'<div class="skill-pills">{pills}</div>'


def render_suggestions(suggestions: list[str]) -> str:
    """Builds numbered HTML suggestion items."""
    if not suggestions:
        return "<span style='color:#4a4d62; font-size:0.85rem;'>No suggestions available</span>"
    return "".join(
        f'<div class="suggestion-item">'
        f'<span class="suggestion-number">{i+1}.</span>'
        f'<span>{s}</span></div>'
        for i, s in enumerate(suggestions)
    )


# =============================================================================
# MAIN UI
# =============================================================================

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <h1 class="app-title">📄 AI Resume Screener</h1>
    <p class="app-subtitle">Upload or paste your resume and a job description — Claude AI does the rest.</p>
</div>
""", unsafe_allow_html=True)

# ── Two-column layout: Resume input | Job description ─────────────────────────
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown('<p class="section-label">Resume</p>', unsafe_allow_html=True)

    # Tabs let the user choose their preferred input method
    # st.tabs() returns a list of tab context managers
    tab_pdf, tab_docx, tab_paste = st.tabs(["📄 Upload PDF", "📝 Upload Word (.docx)", "✏️ Paste Text"])

    uploaded_file = None
    pasted_text = ""

    with tab_pdf:
        uploaded_file_pdf = st.file_uploader(
            label="Upload PDF resume",
            type=["pdf"],
            help="Max 5 MB · Text-based PDFs only",
            label_visibility="collapsed",
            key="pdf_uploader"
        )
        if uploaded_file_pdf:
            uploaded_file = uploaded_file_pdf

    with tab_docx:
        uploaded_file_docx = st.file_uploader(
            label="Upload Word resume",
            type=["docx"],
            help="Max 5 MB · .docx files only",
            label_visibility="collapsed",
            key="docx_uploader"
        )
        if uploaded_file_docx:
            uploaded_file = uploaded_file_docx

    with tab_paste:
        pasted_text = st.text_area(
            label="Paste resume text",
            placeholder="Paste your full resume text here...",
            height=220,
            label_visibility="collapsed",
            key="resume_paste"
        )

with col2:
    st.markdown('<p class="section-label">Job Description</p>', unsafe_allow_html=True)
    job_description = st.text_area(
        label="Job description",
        placeholder="Paste the full job description here...",
        height=220,
        label_visibility="collapsed",
        key="job_description"
    )

# ── Analyze button ────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
_, btn_col, _ = st.columns([2, 1, 2])
with btn_col:
    analyze_clicked = st.button("Analyze Resume", type="primary")

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# ── Results section ───────────────────────────────────────────────────────────
if analyze_clicked:

    # ── Determine resume text source ─────────────────────────────────────────
    # Priority: file upload > pasted text
    # If the user uploaded a file AND pasted text, the file takes precedence.
    resume_text = ""

    if uploaded_file:
        # Validate the file before reading
        is_valid, error_msg = validate_uploaded_file(uploaded_file)
        if not is_valid:
            st.markdown(f'<div class="error-box">⚠️ {error_msg}</div>',
                        unsafe_allow_html=True)
            st.stop()

        # Extract text using the router function (handles PDF and DOCX)
        with st.spinner("Reading resume..."):
            resume_text, extract_error = extract_text_from_file(uploaded_file)

        if extract_error:
            st.markdown(f'<div class="error-box">⚠️ {extract_error}</div>',
                        unsafe_allow_html=True)
            st.stop()

    elif pasted_text and len(pasted_text.strip()) >= 50:
        # Use pasted text directly — no file processing needed
        resume_text = pasted_text.strip()

    else:
        # No valid resume input provided
        st.markdown(
            '<div class="error-box">⚠️ Please upload a resume (PDF or Word) '
            'or paste your resume text (minimum 50 characters).</div>',
            unsafe_allow_html=True
        )
        st.stop()

    # ── Validate job description ──────────────────────────────────────────────
    if not job_description or len(job_description.strip()) < 30:
        st.markdown(
            '<div class="error-box">⚠️ Please paste a job description (at least 30 characters).</div>',
            unsafe_allow_html=True
        )
        st.stop()

    # ── Call Claude API ───────────────────────────────────────────────────────
    with st.spinner("Analyzing with Claude AI..."):
        try:
            result = screen_resume(resume_text, job_description)
        except ValueError as e:
            st.markdown(f'<div class="error-box">⚠️ Input error: {e}</div>',
                        unsafe_allow_html=True)
            st.stop()
        except RuntimeError as e:
            st.markdown(f'<div class="error-box">⚠️ {e}</div>',
                        unsafe_allow_html=True)
            st.stop()

    # ── Render results ────────────────────────────────────────────────────────
    score_class = get_score_class(result.match_score)

    st.markdown(f"""
    <div class="score-container">
        <div class="score-label">Match Score</div>
        <div class="score-number {score_class}">{result.match_score}</div>
        <div class="score-label">out of 100</div>
        {f'<div class="score-summary">{result.summary}</div>' if result.summary else ''}
    </div>
    """, unsafe_allow_html=True)

    res_col1, res_col2 = st.columns([1, 1], gap="large")

    with res_col1:
        st.markdown(f"""
        <div class="results-card">
            <div class="results-card-title title-green">✓ Matched Skills</div>
            {render_pills(result.matched_skills, "pill-green")}
        </div>
        """, unsafe_allow_html=True)

    with res_col2:
        st.markdown(f"""
        <div class="results-card">
            <div class="results-card-title title-red">✗ Missing Skills</div>
            {render_pills(result.missing_skills, "pill-red")}
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="results-card">
        <div class="results-card-title title-blue">💡 Improvement Suggestions</div>
        {render_suggestions(result.suggestions)}
    </div>
    """, unsafe_allow_html=True)

else:
    st.markdown("""
    <div class="empty-state">
        Upload a resume (PDF or Word), paste your resume text, and add a job description above.<br>
        Then click <strong>Analyze Resume</strong>.
    </div>
    """, unsafe_allow_html=True)