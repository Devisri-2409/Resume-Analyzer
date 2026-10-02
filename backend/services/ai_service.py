from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None


def generate_ai_suggestions(
    resume_text: str,
    job_description: str,
    ats_score: int,
    matched_skills: list,
    missing_skills: list,
):
    if not client:
        return (
            "AI suggestions are temporarily unavailable because GEMINI_API_KEY "
            "is not configured. The ATS and job-match analysis is still available."
        )

    prompt = f"""
You are a professional resume analyzer.

Analyze this resume against this job description.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

ATS SCORE: {ats_score}/100
MATCHED SKILLS: {matched_skills}
MISSING SKILLS: {missing_skills}

Return concise, practical advice using exactly these sections:
1. Strengths
2. Missing Skills
3. Resume Improvement Suggestions
4. Important Keywords
5. Overall Recommendation

Use only information present in the resume and job description.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text or "AI returned no text."
    except Exception as exc:
        # Do not make the whole resume analysis fail when Gemini has a temporary outage.
        return (
            "AI suggestions are temporarily unavailable. "
            "Your ATS score, detected skills, and job-match results are still valid. "
            f"AI service status: {type(exc).__name__}."
        )
