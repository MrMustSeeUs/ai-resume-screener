# =============================================================================
# AI Resume Screener — models.py
# Pydantic data models for validating all inputs before they reach Claude AI.
# Pydantic = Python library that enforces data types and rules at runtime.
# =============================================================================

from pydantic import BaseModel, field_validator, Field
from typing import Optional


class ResumeInput(BaseModel):
    """
    Validates the resume text extracted from the uploaded PDF.
    
    Why validate? We never trust raw user input. Before sending anything
    to Claude, we confirm the text is a non-empty string within a safe length.
    """

    resume_text: str = Field(
        ...,                        # '...' means this field is required
        min_length=50,              # A real resume has at least 50 characters
        max_length=15000,           # Cap at ~3 pages to prevent abuse
        description="Raw text extracted from the resume PDF"
    )

    @field_validator("resume_text")
    @classmethod
    def no_injection(cls, v: str) -> str:
        """
        Prompt hardening: strip characters often used in prompt injection attacks.
        Prompt injection = someone embeds hidden instructions inside their resume
        to try to trick Claude into ignoring our instructions.
        Example attack: resume contains '### IGNORE ALL PRIOR INSTRUCTIONS ###'
        """
        # List of suspicious patterns we strip from input
        banned_phrases = [
            "ignore previous instructions",
            "ignore all prior",
            "disregard the above",
            "you are now",
            "new instructions:",
        ]
        v_lower = v.lower()
        for phrase in banned_phrases:
            if phrase in v_lower:
                raise ValueError(
                    f"Input contains disallowed content: '{phrase}'"
                )
        return v


class JobDescriptionInput(BaseModel):
    """
    Validates the job description pasted in by the recruiter.
    Same philosophy: validate before use.
    """

    job_description: str = Field(
        ...,
        min_length=30,
        max_length=10000,
        description="Job description pasted by the recruiter"
    )

    @field_validator("job_description")
    @classmethod
    def no_injection(cls, v: str) -> str:
        """Same prompt injection protection as ResumeInput."""
        banned_phrases = [
            "ignore previous instructions",
            "ignore all prior",
            "disregard the above",
            "you are now",
            "new instructions:",
        ]
        v_lower = v.lower()
        for phrase in banned_phrases:
            if phrase in v_lower:
                raise ValueError(
                    f"Input contains disallowed content: '{phrase}'"
                )
        return v


class ScreeningResult(BaseModel):
    """
    The structured result returned by Claude after analyzing the resume.
    
    By defining the expected shape here, we can validate Claude's response
    before showing it to the user — so a malformed AI response never crashes the app.
    """

    match_score: int = Field(
        ...,
        ge=0,   # ge = greater than or equal to 0
        le=100, # le = less than or equal to 100
        description="Overall match score from 0 to 100"
    )
    matched_skills: list[str] = Field(
        default_factory=list,
        description="Skills found in both resume and job description"
    )
    missing_skills: list[str] = Field(
        default_factory=list,
        description="Skills in job description but missing from resume"
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="Actionable improvement recommendations"
    )
    summary: Optional[str] = Field(
        default=None,
        description="Brief overall assessment paragraph"
    )
