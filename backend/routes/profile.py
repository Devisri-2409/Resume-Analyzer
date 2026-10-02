import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from auth import get_current_user
from database import get_db
from models import (
    User,
    Profile,
    UserEducation,
    UserSkill,
    UserProject,
    UserCertification,
    CourseEnrollment,
    QuizAttempt,
    LessonProgress,
)
from schemas import (
    ProfileUpdateRequest,
    EducationCreateRequest,
    ProjectCreateRequest,
    CertificationCreateRequest,
    SkillAddRequest,
)
from services.learning_service import calculate_user_streak

router = APIRouter(prefix="/api/profile", tags=["Profile"])


def get_user_learning_stats(user_id: int, db: Session) -> dict:
    enrolled_count = db.query(CourseEnrollment).filter(CourseEnrollment.user_id == user_id).count()
    completed_count = (
        db.query(CourseEnrollment)
        .filter(CourseEnrollment.user_id == user_id, CourseEnrollment.progress_percentage >= 100)
        .count()
    )
    quizzes_count = (
        db.query(QuizAttempt.quiz_id)
        .filter(QuizAttempt.user_id == user_id, QuizAttempt.passed.is_(True))
        .distinct()
        .count()
    )
    avg_score_res = (
        db.query(func.avg(QuizAttempt.percentage))
        .filter(QuizAttempt.user_id == user_id)
        .scalar()
    )
    avg_score = round(float(avg_score_res), 1) if avg_score_res is not None else 0.0

    skills_count = db.query(UserSkill).filter(UserSkill.user_id == user_id).count()

    # Calculate actual consecutive calendar-day streak
    streak_info = calculate_user_streak(user_id, db)

    return {
        "courses_enrolled": enrolled_count,
        "courses_completed": completed_count,
        "quizzes_completed": quizzes_count,
        "average_quiz_score": avg_score,
        "skills_learned": skills_count,
        "learning_streak": streak_info["current_streak"],
        "longest_streak": streak_info["longest_streak"],
        "active_days": streak_info["active_days"],
    }


@router.get("")
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        profile = Profile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)

    educations = (
        db.query(UserEducation)
        .filter(UserEducation.user_id == current_user.id)
        .order_by(UserEducation.created_at.desc())
        .all()
    )
    skills = (
        db.query(UserSkill)
        .filter(UserSkill.user_id == current_user.id)
        .order_by(UserSkill.skill_name.asc())
        .all()
    )
    projects = (
        db.query(UserProject)
        .filter(UserProject.user_id == current_user.id)
        .order_by(UserProject.created_at.desc())
        .all()
    )
    certifications = (
        db.query(UserCertification)
        .filter(UserCertification.user_id == current_user.id)
        .order_by(UserCertification.created_at.desc())
        .all()
    )
    stats = get_user_learning_stats(current_user.id, db)

    return {
        "personal_info": {
            "id": current_user.id,
            "full_name": current_user.full_name,
            "email": current_user.email,
            "role": current_user.role,
            "is_email_verified": bool(current_user.is_email_verified),
            "is_phone_verified": bool(current_user.is_phone_verified),
            "avatar": profile.avatar or "avatar-1",
            "phone": profile.phone or current_user.phone_number or "",
            "location": profile.location or "",
            "github": profile.github or "",
            "linkedin": profile.linkedin or "",
            "portfolio": profile.portfolio or "",
            "bio": profile.bio or "",
        },
        "educations": [
            {
                "id": edu.id,
                "degree": edu.degree,
                "branch": edu.branch,
                "college": edu.college,
                "graduation_year": edu.graduation_year,
            }
            for edu in educations
        ],
        "skills": [s.skill_name for s in skills],
        "projects": [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "technologies": p.technologies,
                "github_url": p.github_url,
                "live_url": p.live_url,
            }
            for p in projects
        ],
        "certifications": [
            {
                "id": c.id,
                "name": c.name,
                "issuing_organization": c.issuing_organization,
                "issue_date": c.issue_date,
                "credential_url": c.credential_url,
            }
            for c in certifications
        ],
        "learning_statistics": stats,
    }


@router.put("")
def update_profile(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        profile = Profile(user_id=current_user.id)
        db.add(profile)

    if payload.full_name is not None and payload.full_name.strip():
        current_user.full_name = payload.full_name.strip()

    if payload.avatar is not None:
        profile.avatar = payload.avatar
    if payload.phone is not None:
        new_phone = payload.phone.strip()
        # If user changes phone, require re-verification
        if new_phone != (profile.phone or ""):
            profile.phone = new_phone
            current_user.phone_number = new_phone
            current_user.is_phone_verified = False
            current_user.phone_otp_hash = None
            current_user.phone_otp_expires_at = None
    if payload.location is not None:
        profile.location = payload.location.strip()
    if payload.github is not None:
        profile.github = payload.github.strip()
    if payload.linkedin is not None:
        profile.linkedin = payload.linkedin.strip()
    if payload.portfolio is not None:
        profile.portfolio = payload.portfolio.strip()
    if payload.bio is not None:
        profile.bio = payload.bio.strip()

    db.commit()
    return {"message": "Profile updated successfully!"}


@router.get("/skills")
def get_user_skills(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    skills = (
        db.query(UserSkill)
        .filter(UserSkill.user_id == current_user.id)
        .order_by(UserSkill.skill_name.asc())
        .all()
    )
    return {"skills": [s.skill_name for s in skills]}


@router.post("/skills", status_code=status.HTTP_201_CREATED)
def add_user_skill(
    payload: SkillAddRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    skill_clean = payload.skill_name.strip()
    if not skill_clean:
        raise HTTPException(status_code=400, detail="Skill name cannot be empty.")

    existing = (
        db.query(UserSkill)
        .filter(UserSkill.user_id == current_user.id, func.lower(UserSkill.skill_name) == skill_clean.lower())
        .first()
    )
    if existing:
        return {"message": "Skill already added.", "skill": existing.skill_name}

    new_skill = UserSkill(user_id=current_user.id, skill_name=skill_clean)
    db.add(new_skill)
    db.commit()
    return {"message": "Skill added successfully.", "skill": skill_clean}


@router.delete("/skills/{skill_name}")
def delete_user_skill(
    skill_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = (
        db.query(UserSkill)
        .filter(
            UserSkill.user_id == current_user.id,
            func.lower(UserSkill.skill_name) == skill_name.strip().lower(),
        )
        .first()
    )
    if not target:
        raise HTTPException(status_code=404, detail="Skill not found in user profile.")

    db.delete(target)
    db.commit()
    return {"message": "Skill removed successfully."}


# Education Endpoints
@router.post("/education", status_code=status.HTTP_201_CREATED)
def add_education(
    payload: EducationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    edu = UserEducation(
        user_id=current_user.id,
        degree=payload.degree.strip(),
        branch=payload.branch.strip() if payload.branch else "",
        college=payload.college.strip() if payload.college else "",
        graduation_year=payload.graduation_year.strip() if payload.graduation_year else "",
    )
    db.add(edu)
    db.commit()
    db.refresh(edu)
    return {"message": "Education added successfully.", "id": edu.id}


@router.delete("/education/{education_id}")
def delete_education(
    education_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    edu = (
        db.query(UserEducation)
        .filter(UserEducation.id == education_id, UserEducation.user_id == current_user.id)
        .first()
    )
    if not edu:
        raise HTTPException(status_code=404, detail="Education record not found.")
    db.delete(edu)
    db.commit()
    return {"message": "Education deleted successfully."}


# Project Endpoints
@router.post("/projects", status_code=status.HTTP_201_CREATED)
def add_project(
    payload: ProjectCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = UserProject(
        user_id=current_user.id,
        name=payload.name.strip(),
        description=payload.description.strip() if payload.description else "",
        technologies=payload.technologies.strip() if payload.technologies else "",
        github_url=payload.github_url.strip() if payload.github_url else "",
        live_url=payload.live_url.strip() if payload.live_url else "",
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return {"message": "Project added successfully.", "id": project.id}


@router.delete("/projects/{project_id}")
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    proj = (
        db.query(UserProject)
        .filter(UserProject.id == project_id, UserProject.user_id == current_user.id)
        .first()
    )
    if not proj:
        raise HTTPException(status_code=404, detail="Project record not found.")
    db.delete(proj)
    db.commit()
    return {"message": "Project deleted successfully."}


# Certification Endpoints
@router.post("/certifications", status_code=status.HTTP_201_CREATED)
def add_certification(
    payload: CertificationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cert = UserCertification(
        user_id=current_user.id,
        name=payload.name.strip(),
        issuing_organization=payload.issuing_organization.strip() if payload.issuing_organization else "",
        issue_date=payload.issue_date.strip() if payload.issue_date else "",
        credential_url=payload.credential_url.strip() if payload.credential_url else "",
    )
    db.add(cert)
    db.commit()
    db.refresh(cert)
    return {"message": "Certification added successfully.", "id": cert.id}


@router.delete("/certifications/{certification_id}")
def delete_certification(
    certification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cert = (
        db.query(UserCertification)
        .filter(UserCertification.id == certification_id, UserCertification.user_id == current_user.id)
        .first()
    )
    if not cert:
        raise HTTPException(status_code=404, detail="Certification record not found.")
    db.delete(cert)
    db.commit()
    return {"message": "Certification deleted successfully."}

