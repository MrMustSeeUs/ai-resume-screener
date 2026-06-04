# =============================================================================
# AI Resume Screener — main.py
# Entry point for the Streamlit web application.
# Recruiter uploads a resume PDF + pastes a job description.
# Claude AI returns: match score, matched skills, missing skills, suggestions.
# =============================================================================

# NOTE: We will fill this file in Step 2 (UI) and Step 3 (Claude integration).
# For now this file confirms the app folder is properly set up.

import streamlit as st

st.set_page_config(
    page_title="AI Resume Screener",
    page_icon="📄",
    layout="centered"
)

st.title("📄 AI Resume Screener")
st.write("Project scaffold is working. Build continues in Step 2.")
