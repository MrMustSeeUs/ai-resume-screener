# =============================================================================
# AI Resume Screener — app/main.py
# Full Streamlit UI — entry point for the web application.
#
# Layout:
#   1. Page config + custom CSS styling
#   2. Header section
#   3. Two-column input area (PDF upload | Job description)
#   4. Analyze button
#   5. Results section (score gauge, matched skills, missing skills, suggestions)
#   6. Error handling and loading states
# =============================================================================

import streamlit as st          # Web UI framework
from dotenv import load_dotenv  # Loads .env file into environment variables

# Load .env file first — must happen before importing claude_client
# which reads ANTHROPIC_API_KEY from the environment
load_dotenv()

# Import our own modules
from app.pdf_utils import validate_pdf_file, extract_text_from_pdf
from app.claude_client import screen_resume

# ── Page configuration ────────────────────────────────────────────────────────
# Must be the first Streamlit call in the script
st.set_page_config(
    page_title="AI Resume Screener",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
# Streamlit allows injecting CSS via st.markdown with unsafe_allow_html=True
# We use this to override default Streamlit styles and create a polished look
st.markdown("""
<style>
    /* ── Import fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');

    /* ── Global styles ── */
    .stApp {
        background-color: #0f1117;
        color: #e8e8e8;
        font-family: 'DM Sans', sans-serif;
    }

    /* ── Hide Streamlit default header and footer ── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* ── Main container width ── */
    .block-container {
        max-width: 1100px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* ── App header ── */
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

    /* ── Section labels ── */
    .section-label {
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #6c7293;
        margin-bottom: 0.5rem;
    }

    /* ── Score display ── */
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

    /* ── Score color tiers ── */
    .score-high  { color: #4ade80; }   /* green  — 70-100 */
    .score-mid   { color: #fbbf24; }   /* amber  — 40-69  */
    .score-low   { color: #f87171; }   /* red    — 0-39   */

    /* ── Skill cards ── */
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

    /* ── Skill pill tags ── */
    .skill-pills {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
    }
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

    /* ── Suggestion items ── */
    .suggestion-item {
        display: flex;
        gap: 0.75rem;
        padding: 0.75rem 0;
        border-bottom: 1px solid #2a2d3a;
        font-size: 0.9rem;
        color: #c0c4d8;
        line-height: 1.5;
    }
    .suggestion-item:last-child {
        border-bottom: none;
    }
    .suggestion-number {
        color: #60a5fa;
        font-weight: 600;
        min-width: 1.5rem;
    }

    /* ── Divider ── */
    .section-divider {
        border: none;
        border-top: 1px solid #2a2d3a;
        margin: 2rem 0;
    }

    /* ── Empty state ── */
    .empty-state {
        text-align: center;
        padding: 3rem;
        color: #4a4d62;
        font-size: 0.9rem;
    }

    /* ── Analyze button ── */
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
        transition: opacity 0.2s;
        cursor: pointer;
    }
    .stButton > button:hover {
        opacity: 0.9;
    }

    /* ── File uploader ── */
    .stFileUploader {
        background: #1a1d2e;
        border-radius: 12px;
    }

    /* ── Text area ── */
    .stTextArea textarea {
        background: #1a1d2e;
        border: 1px solid #2a2d3a;
        border-radius: 12px;
        color: #e8e8e8;
        font-family: 'DM Sans', sans-serif;
        font-size: 0.9rem;
    }

    /* ── Error box ── */
    .error-box {
        background: rgba(248, 113, 113, 0.1);
        border: 1px solid rgba(248, 113, 113, 0.3);
        border-radius: 8px;
        padding: 1rem 1.25rem;
        color: #f87171;
        font-size: 0.9rem;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# ── Helper: score color class ─────────────────────────────────────────────────
def get_score_class(score: int) -> str:
    """Returns a CSS class name based on the score range."""
    if score >= 70:
        return "score-high"
    elif score >= 40:
        return "score-mid"
    else:
        return "score-low"


# ── Helper: render skill pills ────────────────────────────────────────────────
def render_pills(skills: list[str], pill_class: str) -> str:
    """Builds an HTML string of skill pill tags."""
    if not skills:
        return "<span style='color:#4a4d62; font-size:0.85rem;'>None identified</span>"
    pills = "".join(f'<span class="{pill_class}">{skill}</span>' for skill in skills)
    return f'<div class="skill-pills">{pills}</div>'


# ── Helper: render suggestions ────────────────────────────────────────────────
def render_suggestions(suggestions: list[str]) -> str:
    """Builds an HTML string of numbered suggestion items."""
    if not suggestions:
        return "<span style='color:#4a4d62; font-size:0.85rem;'>No suggestions available</span>"
    items = "".join(
        f'<div class="suggestion-item">'
        f'<span class="suggestion-number">{i+1}.</span>'
        f'<span>{suggestion}</span>'
        f'</div>'
        for i, suggestion in enumerate(suggestions)
    )
    return items


# =============================================================================
# MAIN UI
# =============================================================================

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <h1 class="app-title">📄 AI Resume Screener</h1>
    <p class="app-subtitle">Upload a resume and paste a job description — Claude AI does the rest.</p>
</div>
""", unsafe_allow_html=True)

# ── Input section: two columns ────────────────────────────────────────────────
# st.columns([1, 1]) creates two equal-width columns side by side
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown('<p class="section-label">Resume PDF</p>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        label="Upload resume",          # Required by Streamlit but hidden via CSS
        type=["pdf"],                   # Only show PDF files in the file picker
        help="Max 5 MB · Text-based PDFs only (not scanned images)",
        label_visibility="collapsed"    # Hides the label — we use our own above
    )

with col2:
    st.markdown('<p class="section-label">Job Description</p>', unsafe_allow_html=True)
    job_description = st.text_area(
        label="Job description",
        placeholder="Paste the full job description here...",
        height=220,
        label_visibility="collapsed"
    )

# ── Analyze button ────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
_, btn_col, _ = st.columns([2, 1, 2])   # Center the button using empty columns
with btn_col:
    analyze_clicked = st.button("Analyze Resume", type="primary")

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# ── Results section ───────────────────────────────────────────────────────────
if analyze_clicked:
    # ── Input validation before calling Claude ────────────────────────────────

    # Check 1: Was a file uploaded?
    if not uploaded_file:
        st.markdown('<div class="error-box">⚠️ Please upload a resume PDF.</div>',
                    unsafe_allow_html=True)
        st.stop()   # st.stop() halts execution — nothing below this runs

    # Check 2: Was a job description provided?
    if not job_description or len(job_description.strip()) < 30:
        st.markdown('<div class="error-box">⚠️ Please paste a job description (at least 30 characters).</div>',
                    unsafe_allow_html=True)
        st.stop()

    # Check 3: Validate the PDF file (type, size, not empty)
    is_valid, error_msg = validate_pdf_file(uploaded_file)
    if not is_valid:
        st.markdown(f'<div class="error-box">⚠️ {error_msg}</div>',
                    unsafe_allow_html=True)
        st.stop()

    # ── Extract text from PDF ─────────────────────────────────────────────────
    with st.spinner("Reading resume..."):
        resume_text, extract_error = extract_text_from_pdf(uploaded_file)

    if extract_error:
        st.markdown(f'<div class="error-box">⚠️ {extract_error}</div>',
                    unsafe_allow_html=True)
        st.stop()

    # ── Call Claude API ───────────────────────────────────────────────────────
    with st.spinner("Analyzing with Claude AI..."):
        try:
            result = screen_resume(resume_text, job_description)
        except ValueError as e:
            # Pydantic validation error — bad input
            st.markdown(f'<div class="error-box">⚠️ Input error: {e}</div>',
                        unsafe_allow_html=True)
            st.stop()
        except RuntimeError as e:
            # API error or response parsing error
            st.markdown(f'<div class="error-box">⚠️ {e}</div>',
                        unsafe_allow_html=True)
            st.stop()

    # ── Render results ────────────────────────────────────────────────────────
    # Only reached if everything above succeeded

    score_class = get_score_class(result.match_score)

    # Row 1: Score + Summary
    st.markdown(f"""
    <div class="score-container">
        <div class="score-label">Match Score</div>
        <div class="score-number {score_class}">{result.match_score}</div>
        <div class="score-label">out of 100</div>
        {f'<div class="score-summary">{result.summary}</div>' if result.summary else ''}
    </div>
    """, unsafe_allow_html=True)

    # Row 2: Matched skills | Missing skills
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

    # Row 3: Improvement suggestions (full width)
    st.markdown(f"""
    <div class="results-card">
        <div class="results-card-title title-blue">💡 Improvement Suggestions</div>
        {render_suggestions(result.suggestions)}
    </div>
    """, unsafe_allow_html=True)

else:
    # ── Empty state — shown before the button is clicked ─────────────────────
    st.markdown("""
    <div class="empty-state">
        Upload a resume and paste a job description above, then click <strong>Analyze Resume</strong>.
    </div>
    """, unsafe_allow_html=True)