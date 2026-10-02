import json
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from sqlalchemy import func

from auth import get_current_user, SECRET_KEY, ALGORITHM
from database import get_db
from models import (
    User,
    Course,
    CourseModule,
    Lesson,
    Quiz,
    QuizQuestion,
    QuizOption,
    QuizAttempt,
    LessonProgress,
    CourseEnrollment,
)
from schemas import QuizSubmitRequest

router = APIRouter(prefix="/api/courses", tags=["Courses"])
bearer_scheme_optional = HTTPBearer(auto_error=False)


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme_optional),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
        return db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    except Exception:
        return None


@router.get("")
def list_courses(
    search: Optional[str] = Query(None),
    skill: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    query = db.query(Course)

    if search:
        term = f"%{search.strip().lower()}%"
        query = query.filter(
            func.lower(Course.title).like(term)
            | func.lower(Course.description).like(term)
            | func.lower(Course.skills_covered).like(term)
        )

    if difficulty and difficulty.lower() != "all":
        query = query.filter(func.lower(Course.difficulty) == difficulty.strip().lower())

    courses = query.order_by(Course.order.asc()).all()

    # If skill filter applied, check skills_covered list in Python
    filtered_courses = []
    for c in courses:
        skills_list = json.loads(c.skills_covered) if c.skills_covered else []
        if skill and skill.lower() != "all":
            if not any(skill.lower() in s.lower() for s in skills_list):
                continue
        filtered_courses.append((c, skills_list))

    user_enrollments = {}
    if current_user:
        enrollments = (
            db.query(CourseEnrollment)
            .filter(CourseEnrollment.user_id == current_user.id)
            .all()
        )
        user_enrollments = {e.course_id: e for e in enrollments}

    results = []
    for course, skills_list in filtered_courses:
        enrollment = user_enrollments.get(course.id)
        total_lessons = db.query(Lesson).filter(Lesson.course_id == course.id).count()
        total_quizzes = db.query(Quiz).filter(Quiz.course_id == course.id).count()

        results.append({
            "id": course.id,
            "title": course.title,
            "slug": course.slug,
            "description": course.description,
            "difficulty": course.difficulty,
            "estimated_duration": course.estimated_duration,
            "skills_covered": skills_list,
            "category": course.category,
            "total_lessons": total_lessons,
            "total_quizzes": total_quizzes,
            "is_enrolled": enrollment is not None,
            "progress_percentage": enrollment.progress_percentage if enrollment else 0,
        })

    return {"courses": results}


@router.get("/{course_id}")
def get_course_details(
    course_id: int,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")

    skills_list = json.loads(course.skills_covered) if course.skills_covered else []

    enrollment = None
    completed_lesson_ids = set()
    quiz_attempts_map = {}

    if current_user:
        enrollment = (
            db.query(CourseEnrollment)
            .filter(
                CourseEnrollment.user_id == current_user.id,
                CourseEnrollment.course_id == course.id,
            )
            .first()
        )
        progress_records = (
            db.query(LessonProgress)
            .filter(
                LessonProgress.user_id == current_user.id,
                LessonProgress.course_id == course.id,
                LessonProgress.completed.is_(True),
            )
            .all()
        )
        completed_lesson_ids = {p.lesson_id for p in progress_records}

        attempts = (
            db.query(QuizAttempt)
            .filter(
                QuizAttempt.user_id == current_user.id,
                QuizAttempt.course_id == course.id,
            )
            .all()
        )
        for att in attempts:
            if att.quiz_id not in quiz_attempts_map or att.percentage > quiz_attempts_map[att.quiz_id]["highest_score"]:
                quiz_attempts_map[att.quiz_id] = {
                    "highest_score": att.percentage,
                    "passed": att.passed,
                }

    # Fetch modules and nested lessons
    modules = (
        db.query(CourseModule)
        .filter(CourseModule.course_id == course.id)
        .order_by(CourseModule.order.asc())
        .all()
    )

    modules_data = []
    total_course_lessons = 0
    completed_course_lessons = 0

    for mod in modules:
        lessons = (
            db.query(Lesson)
            .filter(Lesson.module_id == mod.id)
            .order_by(Lesson.order.asc())
            .all()
        )
        lessons_data = []
        mod_completed = 0
        for les in lessons:
            total_course_lessons += 1
            is_comp = les.id in completed_lesson_ids
            if is_comp:
                completed_course_lessons += 1
                mod_completed += 1
            lessons_data.append({
                "id": les.id,
                "title": les.title,
                "order": les.order,
                "duration": les.duration,
                "is_completed": is_comp,
            })

        mod_progress = (
            round((mod_completed / len(lessons)) * 100) if lessons else 0
        )

        modules_data.append({
            "id": mod.id,
            "title": mod.title,
            "order": mod.order,
            "progress_percentage": mod_progress,
            "lessons": lessons_data,
        })

    quizzes = (
        db.query(Quiz)
        .filter(Quiz.course_id == course.id)
        .order_by(Quiz.order.asc())
        .all()
    )
    quizzes_data = []
    for q in quizzes:
        att_info = quiz_attempts_map.get(q.id)
        questions_count = db.query(QuizQuestion).filter(QuizQuestion.quiz_id == q.id).count()
        quizzes_data.append({
            "id": q.id,
            "title": q.title,
            "description": q.description,
            "passing_score": q.passing_score,
            "questions_count": questions_count,
            "is_completed": att_info is not None,
            "highest_score": att_info["highest_score"] if att_info else None,
            "passed": att_info["passed"] if att_info else False,
        })

    computed_progress = (
        round((completed_course_lessons / total_course_lessons) * 100)
        if total_course_lessons > 0
        else 0
    )

    return {
        "id": course.id,
        "title": course.title,
        "slug": course.slug,
        "description": course.description,
        "difficulty": course.difficulty,
        "estimated_duration": course.estimated_duration,
        "skills_covered": skills_list,
        "category": course.category,
        "is_enrolled": enrollment is not None,
        "progress_percentage": enrollment.progress_percentage if enrollment else computed_progress,
        "total_lessons": total_course_lessons,
        "completed_lessons": completed_course_lessons,
        "modules": modules_data,
        "quizzes": quizzes_data,
    }


@router.post("/{course_id}/enroll")
def enroll_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")

    existing = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.user_id == current_user.id,
            CourseEnrollment.course_id == course.id,
        )
        .first()
    )
    if existing:
        return {
            "message": "Already enrolled.",
            "course_id": course.id,
            "progress_percentage": existing.progress_percentage,
        }

    enrollment = CourseEnrollment(
        user_id=current_user.id,
        course_id=course.id,
        progress_percentage=0,
    )
    db.add(enrollment)
    db.commit()

    return {
        "message": f"Successfully enrolled in {course.title}!",
        "course_id": course.id,
        "progress_percentage": 0,
    }

