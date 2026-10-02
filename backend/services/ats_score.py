def calculate_ats_score(detected_skills, resume_text):
    skill_score = min(len(detected_skills) * 4, 40)

    word_count = len(resume_text.split())
    if word_count >= 400:
        content_score = 20
    elif word_count >= 250:
        content_score = 15
    elif word_count >= 100:
        content_score = 10
    else:
        content_score = 5

    sections = {
        "education": 10,
        "experience": 10,
        "projects": 10,
        "skills": 10,
    }

    text_lower = resume_text.lower()
    section_score = sum(
        points for section, points in sections.items()
        if section in text_lower
    )

    return min(skill_score + content_score + section_score, 100)
