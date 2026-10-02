from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc
import json
import os
import shutil
from uuid import uuid4

from auth import get_current_user
from database import get_db
from models import ResumeAnalysis, User, Course
from services.ai_service import generate_ai_suggestions
from services.ats_score import calculate_ats_score
from services.job_matcher import match_job
from services.pdf_parser import extract_text_from_pdf
from services.skill_extraction import extract_skills
from services.pdf_report_generator import generate_pdf_report

router = APIRouter(prefix="/api/resume", tags=["Resume Analysis"])


def find_courses_for_missing_skills(missing_skills: list, db: Session, limit: int = 4) -> list:
    if not missing_skills:
        # Default to starter courses
        courses = db.query(Course).order_by(Course.order.asc()).limit(limit).all()
        return [
            {
                "id": c.id,
                "title": c.title,
                "slug": c.slug,
                "description": c.description,
                "difficulty": c.difficulty,
                "estimated_duration": c.estimated_duration,
                "skills_covered": json.loads(c.skills_covered) if c.skills_covered else [],
                "matched_gap": [],
            }
            for c in courses
        ]

    courses = db.query(Course).all()
    matched_courses = []

    for c in courses:
        skills = json.loads(c.skills_covered) if c.skills_covered else []
        gaps = []
        for ms in missing_skills:
            if any(ms.lower() in s.lower() or s.lower() in ms.lower() for s in skills):
                gaps.append(ms)

        if gaps:
            matched_courses.append({
                "id": c.id,
                "title": c.title,
                "slug": c.slug,
                "description": c.description,
                "difficulty": c.difficulty,
                "estimated_duration": c.estimated_duration,
                "skills_covered": skills,
                "matched_gap": list(set(gaps)),
                "gap_count": len(gaps),
            })

    matched_courses.sort(key=lambda x: x["gap_count"], reverse=True)
    return matched_courses[:limit]


@router.post("/analyze")
async def analyze_resume(
    file: UploadFile = File(...),
    job_description: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    if not job_description.strip():
        raise HTTPException(status_code=400, detail="Job description is required.")

    upload_folder = "uploads"
    os.makedirs(upload_folder, exist_ok=True)

    safe_name = f"{uuid4().hex}_{os.path.basename(file.filename)}"
    file_path = os.path.join(upload_folder, safe_name)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        extracted_text, pages = extract_text_from_pdf(file_path)

        if not extracted_text.strip():
            raise HTTPException(
                status_code=400,
                detail="No readable text was found in this PDF. Try a text-based PDF.",
            )

        detected_skills = extract_skills(extracted_text)
        ats_score = calculate_ats_score(detected_skills, extracted_text)
        job_match_result = match_job(extracted_text, job_description)

        ai_suggestions = generate_ai_suggestions(
            resume_text=extracted_text,
            job_description=job_description,
            ats_score=ats_score,
            matched_skills=job_match_result["matched_skills"],
            missing_skills=job_match_result["missing_skills"],
        )

        analysis = ResumeAnalysis(
            user_id=current_user.id,
            filename=file.filename,
            pages=pages,
            ats_score=ats_score,
            detected_skills=json.dumps(detected_skills),
            job_match_percentage=job_match_result["job_match_percentage"],
            matched_skills=json.dumps(job_match_result["matched_skills"]),
            missing_skills=json.dumps(job_match_result["missing_skills"]),
            ai_suggestions=ai_suggestions,
            extracted_text=extracted_text,
        )

        db.add(analysis)
        db.commit()
        db.refresh(analysis)

        course_recs = find_courses_for_missing_skills(
            job_match_result["missing_skills"], db, limit=4
        )

        return {
            "analysis_id": analysis.id,
            "filename": file.filename,
            "message": "Resume analyzed successfully!",
            "pages": pages,
            "ats_score": ats_score,
            "detected_skills": detected_skills,
            "job_match": job_match_result,
            "ai_suggestions": ai_suggestions,
            "recommended_courses": course_recs,
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Resume analysis failed: {str(exc)}",
        )
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@router.get("/history")
def get_resume_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    analyses = (
        db.query(ResumeAnalysis)
        .filter(
            (ResumeAnalysis.user_id == current_user.id)
            | (ResumeAnalysis.user_id.is_(None))
        )
        .order_by(desc(ResumeAnalysis.created_at))
        .limit(20)
        .all()
    )

    results = []
    for a in analyses:
        results.append({
            "id": a.id,
            "filename": a.filename,
            "pages": a.pages,
            "ats_score": a.ats_score,
            "job_match_percentage": a.job_match_percentage,
            "detected_skills": json.loads(a.detected_skills) if a.detected_skills else [],
            "matched_skills": json.loads(a.matched_skills) if a.matched_skills else [],
            "missing_skills": json.loads(a.missing_skills) if a.missing_skills else [],
            "created_at": a.created_at.isoformat() if a.created_at else None,
        })

    return {"history": results}


@router.get("/latest")
def get_latest_resume_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    analysis = (
        db.query(ResumeAnalysis)
        .filter(
            (ResumeAnalysis.user_id == current_user.id)
            | (ResumeAnalysis.user_id.is_(None))
        )
        .order_by(desc(ResumeAnalysis.created_at))
        .first()
    )

    if not analysis:
        return {"latest": None}

    missing_skills = json.loads(analysis.missing_skills) if analysis.missing_skills else []
    course_recs = find_courses_for_missing_skills(missing_skills, db, limit=4)

    return {
        "latest": {
            "id": analysis.id,
            "filename": analysis.filename,
            "pages": analysis.pages,
            "ats_score": analysis.ats_score,
            "job_match_percentage": analysis.job_match_percentage,
            "detected_skills": json.loads(analysis.detected_skills) if analysis.detected_skills else [],
            "matched_skills": json.loads(analysis.matched_skills) if analysis.matched_skills else [],
            "missing_skills": missing_skills,
            "ai_suggestions": analysis.ai_suggestions,
            "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
            "recommended_courses": course_recs,
        }
    }


@router.get("/report/{analysis_id}")
def get_resume_report(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    analysis = db.query(ResumeAnalysis).filter(ResumeAnalysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis report not found.")

    missing_skills = json.loads(analysis.missing_skills) if analysis.missing_skills else []
    course_recs = find_courses_for_missing_skills(missing_skills, db, limit=4)

    return {
        "id": analysis.id,
        "filename": analysis.filename,
        "pages": analysis.pages,
        "ats_score": analysis.ats_score,
        "job_match_percentage": analysis.job_match_percentage,
        "detected_skills": json.loads(analysis.detected_skills) if analysis.detected_skills else [],
        "matched_skills": json.loads(analysis.matched_skills) if analysis.matched_skills else [],
        "missing_skills": missing_skills,
        "ai_suggestions": analysis.ai_suggestions,
        "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
        "recommended_courses": course_recs,
    }


@router.get("/report/{analysis_id}/pdf")
def download_pdf_report(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    analysis = db.query(ResumeAnalysis).filter(ResumeAnalysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis report not found.")

    missing_skills = json.loads(analysis.missing_skills) if analysis.missing_skills else []
    recommended_courses = find_courses_for_missing_skills(missing_skills, db, limit=4)

    pdf_bytes = generate_pdf_report(
        analysis=analysis,
        user_name=current_user.full_name,
        recommended_courses=recommended_courses,
    )

    safe_filename = f"ResumeAI_Report_{analysis_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={safe_filename}",
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )

