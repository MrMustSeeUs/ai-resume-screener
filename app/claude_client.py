# =============================================================================
# AI Resume Screener — claude_client.py
# Handles all communication with the Anthropic Claude API.
# Builds the prompt, sends the request, parses and validates the response.
# =============================================================================

import os                      # To read environment variables
import json                    # To parse Claude's JSON response
import logging
import anthropic               # The official Anthropic Python SDK

from app.models import ResumeInput, JobDescriptionInput, ScreeningResult

logger = logging.getLogger(__name__)


def build_screening_prompt(resume_text: str, job_description: str) -> str:
    """
    Constructs the prompt we send to Claude.
    
    Prompt engineering principles used here:
    1. Role assignment — tell Claude exactly what it is
    2. Task clarity — specific instructions, not vague
    3. Output format — demand structured JSON so we can parse reliably
    4. Constraints — tell Claude what NOT to do (no hallucination, no fluff)
    5. Delimiters — use XML-style tags to separate resume from job description
       This prevents prompt injection by making the boundary explicit to Claude.
    """

    prompt = f"""You are an expert technical recruiter and career coach with 15 years of experience.
Your task is to analyze a candidate's resume against a job description and return a structured evaluation.

<resume>
{resume_text}
</resume>

<job_description>
{job_description}
</job_description>

Analyze the resume against the job description and return ONLY a valid JSON object with this exact structure:
{{
    "match_score": <integer from 0 to 100>,
    "matched_skills": [<list of skill strings found in both resume and job description>],
    "missing_skills": [<list of skills required by the job but absent from the resume>],
    "suggestions": [<list of 3-5 specific, actionable improvement recommendations>],
    "summary": "<2-3 sentence overall assessment>"
}}

Rules:
- match_score must be an integer between 0 and 100
- All lists must contain strings only
- Do not include any text before or after the JSON object
- Do not hallucinate skills not present in the documents
- Be specific and honest in your assessment
- suggestions should be concrete actions the candidate can take
"""
    return prompt


def screen_resume(resume_text: str, job_description: str) -> ScreeningResult:
    """
    Main function: validates inputs, calls Claude, returns structured result.
    
    Flow:
        1. Validate inputs with Pydantic (raises ValueError if invalid)
        2. Get API key from environment variable (never hardcode keys!)
        3. Build the prompt
        4. Call Claude API
        5. Parse and validate Claude's JSON response
        6. Return a ScreeningResult object
    
    Args:
        resume_text: Plain text extracted from the resume PDF
        job_description: Job description pasted by the recruiter
    
    Returns:
        ScreeningResult (Pydantic model with all fields validated)
    
    Raises:
        ValueError: If inputs fail validation
        RuntimeError: If API call fails or response is malformed
    """

    # ── Step 1: Validate inputs ──────────────────────────────────────────────
    # Pydantic raises ValueError automatically if rules are broken
    validated_resume = ResumeInput(resume_text=resume_text)
    validated_jd = JobDescriptionInput(job_description=job_description)

    # ── Step 2: Load API key from environment ────────────────────────────────
    # NEVER write your API key directly in code.
    # os.environ reads it from the .env file (loaded by python-dotenv in main.py)
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. "
            "Add it to your .env file and ensure python-dotenv is installed."
        )

    # ── Step 3: Build the prompt ─────────────────────────────────────────────
    prompt = build_screening_prompt(
        validated_resume.resume_text,
        validated_jd.job_description
    )

    # ── Step 4: Call Claude API ───────────────────────────────────────────────
    try:
        client = anthropic.Anthropic(api_key=api_key)

        message = client.messages.create(
            model="claude-opus-4-5",          # Fast, cost-effective model
            max_tokens=1500,                   # Cap response length
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        raw_response = message.content[0].text
        logger.info("Claude API call successful.")

    except anthropic.APIConnectionError:
        raise RuntimeError("Could not connect to Anthropic API. Check your internet connection.")
    except anthropic.AuthenticationError:
        raise RuntimeError("Invalid Anthropic API key. Check your .env file.")
    except anthropic.RateLimitError:
        raise RuntimeError("Anthropic API rate limit reached. Please wait a moment and try again.")
    except anthropic.APIError as e:
        logger.error(f"Anthropic API error: {e}", exc_info=True)
        raise RuntimeError(f"Anthropic API returned an error: {str(e)}")

    # ── Step 5: Parse Claude's JSON response ─────────────────────────────────
    try:
        # Claude should return pure JSON per our prompt instructions
        # But just in case it wraps in ```json ... ```, strip that
        cleaned = raw_response.strip()
        if cleaned.startswith("```"):
            # Remove markdown code fences if present
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()

        result_dict = json.loads(cleaned)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Claude response as JSON: {e}\nRaw: {raw_response}")
        raise RuntimeError(
            "Claude returned an unexpected response format. Please try again."
        )

    # ── Step 6: Validate the parsed result with Pydantic ─────────────────────
    try:
        result = ScreeningResult(**result_dict)
    except Exception as e:
        logger.error(f"Claude response failed Pydantic validation: {e}\nData: {result_dict}")
        raise RuntimeError(
            "Claude's response was missing required fields. Please try again."
        )

    return result
