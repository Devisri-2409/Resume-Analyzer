from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth import require_admin
from database import get_db
from models import Course, CourseEnrollment, Quiz, QuizAttempt, ResumeAnalysis, User

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/access-check")
def admin_access_check(current_user: User = Depends(require_admin)):
    """
    Diagnostic endpoint to verify administrator authentication and JWT role resolution.
    Returns 200 OK only if the authenticated user has role == 'admin'.
    Returns 401 if unauthenticated, or 403 if the user is a standard user.
    """
    return {
        "message": "Admin access granted.",
        "user_id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "full_name": current_user.full_name,
    }


@router.get("/metrics")
def get_admin_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Platform analytics and aggregated metrics for the Administrator Dashboard.
    Enforces server-side authorization: requires role == 'admin'.
    """
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active.is_(True)).count()
    admin_users = db.query(User).filter(User.role == "admin").count()
    total_courses = db.query(Course).count()
    total_quizzes = db.query(Quiz).count()
    total_analyses = db.query(ResumeAnalysis).count()
    total_quiz_attempts = db.query(QuizAttempt).count()
    total_enrollments = db.query(CourseEnrollment).count()

    # Calculate average ATS score across all analyses
    avg_ats = db.query(func.avg(ResumeAnalysis.ats_score)).scalar()
    avg_ats_score = round(float(avg_ats), 1) if avg_ats is not None else 0

    # Calculate average quiz score percentage
    avg_quiz = db.query(func.avg(QuizAttempt.percentage)).scalar()
    avg_quiz_score = round(float(avg_quiz), 1) if avg_quiz is not None else 0

    # Calculate course completion rate (if any enrollments exist)
    completed_enrollments = (
        db.query(CourseEnrollment)
        .filter(CourseEnrollment.progress_percentage >= 100)
        .count()
    )
    completion_rate = (
        round((completed_enrollments / total_enrollments) * 100, 1)
        if total_enrollments > 0
        else 0
    )

    # Recent platform activity (last 10 analyses and user registrations)
    recent_analyses = (
        db.query(ResumeAnalysis)
        .order_by(ResumeAnalysis.created_at.desc())
        .limit(5)
        .all()
    )

    recent_users = (
        db.query(User)
        .order_by(User.created_at.desc())
        .limit(5)
        .all()
    )

    recent_activities = []
    for analysis in recent_analyses:
        recent_activities.append({
            "type": "resume_analysis",
            "title": f"Resume Analyzed: {analysis.filename}",
            "description": f"ATS Score: {analysis.ats_score}% - Job Match: {analysis.job_match_percentage or 0}%",
            "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
        })

    for u in recent_users:
        recent_activities.append({
            "type": "user_registration",
            "title": f"User Joined: {u.full_name}",
            "description": f"Email: {u.email} ({u.role.upper()})",
            "created_at": u.created_at.isoformat() if u.created_at else None,
        })

    # Sort combined activities by created_at descending
    recent_activities.sort(key=lambda x: x["created_at"] or "", reverse=True)

    return {
        "stats": {
            "total_users": total_users,
            "active_users": active_users,
            "admin_users": admin_users,
            "total_courses": total_courses,
            "total_tests": total_quizzes,
            "total_analyses": total_analyses,
            "total_attempts": total_quiz_attempts,
            "total_enrollments": total_enrollments,
            "avg_ats_score": avg_ats_score,
            "avg_quiz_score": avg_quiz_score,
            "course_completion_rate": completion_rate,
        },
        "recent_activities": recent_activities[:8],
    }


@router.get("/users")
def get_admin_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    List all platform users with roles and status for admin oversight.
    """
    users = db.query(User).order_by(User.id.asc()).all()
    return [
        {
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]