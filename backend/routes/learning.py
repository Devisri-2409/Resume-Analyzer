import json
from datetime import datetime, timezone
from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from auth import get_current_user
from database import get_db
from models import (
    User,
    Course,
    Lesson,
    Quiz,
    QuizAttempt,
    LessonProgress,
    CourseEnrollment,
    ResumeAnalysis,
    UserSkill,
)

router = APIRouter(prefix="/api/learning", tags=["Learning"])


def find_skill_recommendations(user_id: int, db: Session, limit: int = 4) -> List[Dict[str, Any]]:
    """
    Finds courses that bridge the user's actual missing skills detected by Resume / JD analysis.
    """
    # 1. Retrieve the user's latest resume analysis (or fallback to any user analysis)
    latest_analysis = (
        db.query(ResumeAnalysis)
        .filter(ResumeAnalysis.user_id == user_id)
        .order_by(ResumeAnalysis.created_at.desc())
        .first()
    )

    if not latest_analysis:
        # Fallback to the most recent overall analysis if user hasn't uploaded yet
        latest_analysis = (
            db.query(ResumeAnalysis)
            .order_by(ResumeAnalysis.created_at.desc())
            .first()
        )

    missing_skills = []
    if latest_analysis and latest_analysis.missing_skills:
        try:
            missing_skills = json.loads(latest_analysis.missing_skills)
        except Exception:
            missing_skills = []

    # If no missing skills from analysis, check skills absent from profile
    user_skills = {
        s.skill_name.lower()
        for s in db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
    }

    # Fetch all courses
    courses = db.query(Course).order_by(Course.order.asc()).all()

    # Get user enrollments
    enrollments = {
        e.course_id: e.progress_percentage
        for e in db.query(CourseEnrollment).filter(CourseEnrollment.user_id == user_id).all()
    }

    scored_courses = []
    for c in courses:
        skills = json.loads(c.skills_covered) if c.skills_covered else []
        matched_gaps = []

        # Check against missing_skills from resume analysis
        for ms in missing_skills:
            if any(ms.lower() in s.lower() or s.lower() in ms.lower() for s in skills):
                matched_gaps.append(ms)

        # Check against profile skills gaps
        if not matched_gaps:
            for s in skills:
                if s.lower() not in user_skills:
                    matched_gaps.append(s)

        score = len(matched_gaps)
        total_lessons = db.query(Lesson).filter(Lesson.course_id == c.id).count()

        scored_courses.append({
            "id": c.id,
            "title": c.title,
            "slug": c.slug,
            "description": c.description,
            "difficulty": c.difficulty,
            "estimated_duration": c.estimated_duration,
            "skills_covered": skills,
            "category": c.category,
            "matched_missing_skills": list(set(matched_gaps)),
            "match_count": score,
            "is_enrolled": c.id in enrollments,
            "progress_percentage": enrollments.get(c.id, 0),
            "total_lessons": total_lessons,
        })

    # Sort courses prioritizing those that bridge detected missing skills
    scored_courses.sort(key=lambda x: (x["match_count"], -x["progress_percentage"]), reverse=True)
    return scored_courses[:limit]


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
    # Enrolled courses
    enrollments = (
        db.query(CourseEnrollment)
        .filter(CourseEnrollment.user_id == current_user.id)
        .order_by(CourseEnrollment.enrolled_at.desc())
        .all()
    )

    current_courses = []
    total_progress_sum = 0

    for enr in enrollments:
        course = db.query(Course).filter(Course.id == enr.course_id).first()
        if not course:
            continue

        total_lessons = db.query(Lesson).filter(Lesson.course_id == course.id).count()
        completed_lessons = (
            db.query(LessonProgress)
            .filter(
                LessonProgress.user_id == current_user.id,
                LessonProgress.course_id == course.id,
                LessonProgress.completed.is_(True),
            )
            .count()
        )

        # Find next uncompleted lesson
        next_lesson = (
            db.query(Lesson)
            .filter(
                Lesson.course_id == course.id,
                ~Lesson.id.in_(
                    db.query(LessonProgress.lesson_id).filter(
                        LessonProgress.user_id == current_user.id,
                        LessonProgress.completed.is_(True),
                    )
                ),
            )
            .order_by(Lesson.order.asc())
            .first()
        )

        current_courses.append({
            "id": course.id,
            "title": course.title,
            "slug": course.slug,
            "difficulty": course.difficulty,
            "progress_percentage": enr.progress_percentage,
            "total_lessons": total_lessons,
            "completed_lessons": completed_lessons,
            "next_lesson_id": next_lesson.id if next_lesson else None,
            "next_lesson_title": next_lesson.title if next_lesson else "Course Complete",
        })
        total_progress_sum += enr.progress_percentage

    overall_progress = (
        round(total_progress_sum / len(current_courses)) if current_courses else 0
    )

    # Recommendations based on actual missing skills
    recommended = find_skill_recommendations(current_user.id, db, limit=4)

    # Recent activity
    recent_activities = []

    # Completed lessons
    recent_lessons = (
        db.query(LessonProgress, Lesson)
        .join(Lesson, LessonProgress.lesson_id == Lesson.id)
        .filter(LessonProgress.user_id == current_user.id, LessonProgress.completed.is_(True))
        .order_by(LessonProgress.completed_at.desc())
        .limit(5)
        .all()
    )
    for prog, les in recent_lessons:
        recent_activities.append({
            "type": "lesson_completed",
            "title": f"Completed: {les.title}",
            "subtitle": f"Duration: {les.duration}",
            "timestamp": prog.completed_at.isoformat() if prog.completed_at else None,
        })

    # Recent quiz attempts
    recent_quizzes = (
        db.query(QuizAttempt, Quiz)
        .join(Quiz, QuizAttempt.quiz_id == Quiz.id)
        .filter(QuizAttempt.user_id == current_user.id)
        .order_by(QuizAttempt.created_at.desc())
        .limit(5)
        .all()
    )
    for att, q in recent_quizzes:
        status_text = "Passed" if att.passed else "Needs Review"
        recent_activities.append({
            "type": "quiz_attempt",
            "title": f"Quiz: {q.title}",
            "subtitle": f"Score: {att.score}/{att.total_questions} ({att.percentage}%) • {status_text}",
            "timestamp": att.created_at.isoformat() if att.created_at else None,
        })

    # Sort recent activity by timestamp
    recent_activities.sort(key=lambda x: x["timestamp"] or "", reverse=True)
    recent_activities = recent_activities[:6]

    # Quiz performance metrics
    total_quizzes_taken = db.query(QuizAttempt).filter(QuizAttempt.user_id == current_user.id).count()
    avg_score_res = (
        db.query(func.avg(QuizAttempt.percentage))
        .filter(QuizAttempt.user_id == current_user.id)
        .scalar()
    )
    avg_score = round(float(avg_score_res), 1) if avg_score_res is not None else 0.0

    highest_score_res = (
        db.query(func.max(QuizAttempt.percentage))
        .filter(QuizAttempt.user_id == current_user.id)
        .scalar()
    )
    highest_score = int(highest_score_res) if highest_score_res is not None else 0

    recent_quiz_scores = [
        {
            "id": att.id,
            "quiz_title": q.title,
            "score": att.score,
            "total": att.total_questions,
            "percentage": att.percentage,
            "passed": att.passed,
            "created_at": att.created_at.isoformat() if att.created_at else None,
        }
        for att, q in recent_quizzes[:5]
    ]

    return {
        "overall_progress": overall_progress,
        "enrolled_count": len(current_courses),
        "current_courses": current_courses,
        "recommended_courses": recommended,
        "recent_activity": recent_activities,
        "quiz_performance": {
            "average_score": avg_score,
            "quizzes_completed": total_quizzes_taken,
            "highest_score": highest_score,
            "recent_scores": recent_quiz_scores,
        },
    }


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
            "progress_percentage": enr.progress_percentage,
            "completed_lessons": completed,
            "total_lessons": total,
            "is_completed": enr.progress_percentage >= 100,
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
    quizzes_count = db.query(QuizAttempt).filter(QuizAttempt.user_id == current_user.id).count()
    avg_score_res = (
        db.query(func.avg(QuizAttempt.percentage))
        .filter(QuizAttempt.user_id == current_user.id)
        .scalar()
    )
    avg_score = round(float(avg_score_res), 1) if avg_score_res is not None else 0.0
    skills_count = db.query(UserSkill).filter(UserSkill.user_id == current_user.id).count()

    return {
        "courses_enrolled": enrolled_count,
        "courses_completed": completed_count,
        "quizzes_completed": quizzes_count,
        "average_quiz_score": avg_score,
        "skills_learned": skills_count,
        "learning_streak": 1 if enrolled_count > 0 else 0,
    }

