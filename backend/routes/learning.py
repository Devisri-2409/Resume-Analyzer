from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from auth import get_current_user
from database import get_db
from models import (
    User,
    Course,
    Lesson,
    QuizAttempt,
    LessonProgress,
    CourseEnrollment,
    UserSkill,
)
from services.learning_service import (
    find_skill_recommendations,
    get_learning_dashboard_data,
    calculate_user_streak,
    calculate_and_update_course_progress,
)

router = APIRouter(prefix="/api/learning", tags=["Learning"])


@router.get("/recommendations")
def get_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    recommendations = find_skill_recommendations(current_user.id, db, limit=6)
    return {"recommendations": recommendations}


@router.get("/dashboard")
def get_learning_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = get_learning_dashboard_data(current_user.id, db)
    return data


@router.get("/streak")
def get_streak(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    streak_info = calculate_user_streak(current_user.id, db)
    return streak_info


@router.get("/progress")
def get_learning_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    enrollments = (
        db.query(CourseEnrollment, Course)
        .join(Course, CourseEnrollment.course_id == Course.id)
        .filter(CourseEnrollment.user_id == current_user.id)
        .all()
    )

    courses_progress = []
    for enr, c in enrollments:
        # Keep synced
        progress_val = calculate_and_update_course_progress(current_user.id, c.id, db)
        total = db.query(Lesson).filter(Lesson.course_id == c.id).count()
        completed = (
            db.query(LessonProgress)
            .filter(
                LessonProgress.user_id == current_user.id,
                LessonProgress.course_id == c.id,
                LessonProgress.completed.is_(True),
            )
            .count()
        )
        courses_progress.append({
            "course_id": c.id,
            "title": c.title,
            "progress_percentage": progress_val,
            "completed_lessons": completed,
            "total_lessons": total,
            "is_completed": progress_val >= 100,
        })

    return {"courses": courses_progress}


@router.get("/statistics")
def get_learning_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    enrolled_count = db.query(CourseEnrollment).filter(CourseEnrollment.user_id == current_user.id).count()
    completed_count = (
        db.query(CourseEnrollment)
        .filter(CourseEnrollment.user_id == current_user.id, CourseEnrollment.progress_percentage >= 100)
        .count()
    )
    quizzes_count = (
        db.query(QuizAttempt.quiz_id)
        .filter(QuizAttempt.user_id == current_user.id, QuizAttempt.passed.is_(True))
        .distinct()
        .count()
    )
    avg_score_res = (
        db.query(func.avg(QuizAttempt.percentage))
        .filter(QuizAttempt.user_id == current_user.id)
        .scalar()
    )
    avg_score = round(float(avg_score_res), 1) if avg_score_res is not None else 0.0
    skills_count = db.query(UserSkill).filter(UserSkill.user_id == current_user.id).count()

    streak_info = calculate_user_streak(current_user.id, db)

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

