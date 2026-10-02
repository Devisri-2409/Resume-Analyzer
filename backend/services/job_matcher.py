from services.skill_extraction import extract_skills


def match_job(resume_text: str, job_description: str):
    resume_skill_set = set(extract_skills(resume_text))
    required_skill_set = set(extract_skills(job_description))

    matched_skills = sorted(resume_skill_set.intersection(required_skill_set))
    missing_skills = sorted(required_skill_set.difference(resume_skill_set))

    if not required_skill_set:
        match_percentage = 0
    else:
        match_percentage = round(
            len(matched_skills) / len(required_skill_set) * 100
        )

    return {
        "required_skills": sorted(required_skill_set),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "job_match_percentage": match_percentage,
    }
