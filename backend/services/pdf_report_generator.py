import io
import json
import pymupdf
from datetime import datetime


def generate_pdf_report(analysis, user_name: str, recommended_courses: list = None) -> bytes:
    """
    Generates a clean, professional PDF analysis report using PyMuPDF.
    """
    doc = pymupdf.open()
    page = doc.new_page(width=595.28, height=841.89)  # A4 size

    # Colors
    c_primary = (15 / 255, 107 / 255, 73 / 255)      # #0f6b49 emerald
    c_dark = (24 / 255, 53 / 255, 42 / 255)          # #18352a dark
    c_muted = (113 / 255, 130 / 255, 122 / 255)      # #71827a gray
    c_light = (245 / 255, 248 / 255, 246 / 255)      # #f5f8f6 card bg
    c_line = (220 / 255, 233 / 255, 226 / 255)       # line border
    c_accent = (217 / 255, 119 / 255, 6 / 255)       # warning amber

    y = 40

    # Header Top Bar
    page.draw_rect(pymupdf.Rect(40, y, 555, y + 4), color=c_primary, fill=c_primary)
    y += 20

    # Title
    page.insert_text(
        (40, y + 16),
        "ResumeAI Career Intelligence Report",
        fontsize=18,
        fontname="helv",
        color=c_primary,
    )
    y += 26

    # Subtitle & Meta
    date_str = analysis.created_at.strftime("%B %d, %Y - %I:%M %p") if analysis.created_at else datetime.now().strftime("%B %d, %Y")
    page.insert_text(
        (40, y + 10),
        f"Candidate: {user_name}  |  File: {analysis.filename}  |  Date: {date_str}",
        fontsize=9,
        fontname="helv",
        color=c_muted,
    )
    y += 24

    # Divider
    page.draw_line(pymupdf.Point(40, y), pymupdf.Point(555, y), color=c_line, width=1)
    y += 18

    # Summary Score Cards
    card_width = 245
    card_height = 65

    # Card 1: ATS Score
    r1 = pymupdf.Rect(40, y, 40 + card_width, y + card_height)
    page.draw_rect(r1, color=c_line, fill=c_light, radius=6)
    page.insert_text((55, y + 20), "ATS RESUME SCORE", fontsize=8, fontname="helv", color=c_muted)
    page.insert_text((55, y + 46), f"{analysis.ats_score or 0} / 100", fontsize=20, fontname="helv", color=c_primary)
    page.insert_text((150, y + 42), "Optimized for keyword parsing", fontsize=8, fontname="helv", color=c_muted)

    # Card 2: Job Match
    r2 = pymupdf.Rect(310, y, 310 + card_width, y + card_height)
    page.draw_rect(r2, color=c_line, fill=c_light, radius=6)
    page.insert_text((325, y + 20), "JOB DESCRIPTION MATCH", fontsize=8, fontname="helv", color=c_muted)
    page.insert_text((325, y + 46), f"{analysis.job_match_percentage or 0}%", fontsize=20, fontname="helv", color=c_primary)
    page.insert_text((420, y + 42), "Relevance to requirements", fontsize=8, fontname="helv", color=c_muted)

    y += card_height + 25

    # Skills Section
    detected_skills = json.loads(analysis.detected_skills) if analysis.detected_skills else []
    matched_skills = json.loads(analysis.matched_skills) if analysis.matched_skills else []
    missing_skills = json.loads(analysis.missing_skills) if analysis.missing_skills else []

    # Matched Skills
    page.insert_text((40, y + 10), "MATCHED SKILLS", fontsize=10, fontname="helv", color=c_dark)
    y += 18
    matched_text = ", ".join(matched_skills) if matched_skills else "No direct matches identified in the targeted job description."
    r_matched = pymupdf.Rect(40, y, 555, y + 36)
    page.insert_textbox(r_matched, matched_text, fontsize=9, fontname="helv", color=c_dark)
    y += 42

    # Missing Skills
    page.insert_text((40, y + 10), "SKILL GAPS (MISSING SKILLS)", fontsize=10, fontname="helv", color=c_accent)
    y += 18
    missing_text = ", ".join(missing_skills) if missing_skills else "No critical skill gaps identified."
    r_missing = pymupdf.Rect(40, y, 555, y + 36)
    page.insert_textbox(r_missing, missing_text, fontsize=9, fontname="helv", color=c_dark)
    y += 44

    # Recommended Courses Section
    if recommended_courses:
        page.insert_text((40, y + 10), "RECOMMENDED LEARNING PATHWAY TO BRIDGE GAPS", fontsize=10, fontname="helv", color=c_primary)
        y += 18
        for rc in recommended_courses[:3]:
            course_title = rc.get("title", "")
            duration = rc.get("estimated_duration", "")
            diff = rc.get("difficulty", "")
            skills_str = ", ".join(rc.get("skills_covered", []))
            line = f"• {course_title} ({diff} • {duration}) — Skills: {skills_str}"
            page.insert_text((45, y + 10), line[:95], fontsize=8.5, fontname="helv", color=c_dark)
            y += 15
        y += 15

    # AI Suggestions Section
    page.insert_text((40, y + 10), "AI CAREER RECOMMENDATIONS & ATS FEEDBACK", fontsize=10, fontname="helv", color=c_dark)
    y += 18

    # AI Text
    ai_text = analysis.ai_suggestions or "AI analysis generated successfully."
    # If text is very long, paginate gracefully
    r_ai = pymupdf.Rect(40, y, 555, 800)
    overflow = page.insert_textbox(r_ai, ai_text, fontsize=8.5, fontname="helv", color=c_dark)

    if overflow > 0:
        # Create second page for remaining AI text
        page2 = doc.new_page(width=595.28, height=841.89)
        page2.insert_text((40, 50), "AI CAREER RECOMMENDATIONS (CONTINUED)", fontsize=10, fontname="helv", color=c_dark)
        r_ai2 = pymupdf.Rect(40, 70, 555, 780)
        remaining_text = ai_text[-int(overflow * 4):]
        page2.insert_textbox(r_ai2, remaining_text, fontsize=8.5, fontname="helv", color=c_dark)
        page2.draw_line(pymupdf.Point(40, 800), pymupdf.Point(555, 800), color=c_line, width=1)
        page2.insert_text((40, 815), "ResumeAI Platform • Confidential Career Analysis Report", fontsize=8, fontname="helv", color=c_muted)

    # Footer on first page
    page.draw_line(pymupdf.Point(40, 805), pymupdf.Point(555, 805), color=c_line, width=1)
    page.insert_text(
        (40, 820),
        f"Generated by ResumeAI Platform • Confidentially Prepared for {user_name}",
        fontsize=8,
        fontname="helv",
        color=c_muted,
    )

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes

