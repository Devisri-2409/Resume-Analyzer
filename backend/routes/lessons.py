import json
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import (
    User,
    Course,
    CourseModule,
    Lesson,
    LessonProgress,
    CourseEnrollment,
)

router = APIRouter(prefix="/api/lessons", tags=["Lessons"])


@router.get("/{lesson_id}")
def get_lesson(
    lesson_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found.")

    course = db.query(Course).filter(Course.id == lesson.course_id).first()
    module = db.query(CourseModule).filter(CourseModule.id == lesson.module_id).first()

    progress = (
        db.query(LessonProgress)
        .filter(
            LessonProgress.user_id == current_user.id,
            LessonProgress.lesson_id == lesson.id,
        )
        .first()
    )

    # Find next and previous lessons in the course
    all_lessons = (
        db.query(Lesson)
        .join(CourseModule, Lesson.module_id == CourseModule.id)
        .filter(Lesson.course_id == lesson.course_id)
        .order_by(CourseModule.order.asc(), Lesson.order.asc())
        .all()
    )

    prev_id = None
    next_id = None
    current_idx = -1

    for idx, l in enumerate(all_lessons):
        if l.id == lesson.id:
            current_idx = idx
            break

    if current_idx > 0:
        prev_id = all_lessons[current_idx - 1].id
    if current_idx != -1 and current_idx < len(all_lessons) - 1:
        next_id = all_lessons[current_idx + 1].id

    important_points = []
    if lesson.important_points:
        try:
            important_points = json.loads(lesson.important_points)
        except Exception:
            important_points = [lesson.important_points]

    return {
        "id": lesson.id,
        "course_id": lesson.course_id,
        "course_title": course.title if course else "",
        "module_id": lesson.module_id,
        "module_title": module.title if module else "",
        "title": lesson.title,
        "duration": lesson.duration,
        "order": lesson.order,
        "explanation": lesson.explanation,
        "examples": lesson.examples,
        "important_points": important_points,
        "is_completed": progress.completed if progress else False,
        "prev_lesson_id": prev_id,
        "next_lesson_id": next_id,
    }


@router.post("/{lesson_id}/complete")
def complete_lesson(
    lesson_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found.")

    # Record progress without duplicate records
    progress = (
        db.query(LessonProgress)
        .filter(
            LessonProgress.user_id == current_user.id,
            LessonProgress.lesson_id == lesson.id,
        )
        .first()
    )

    if not progress:
        progress = LessonProgress(
            user_id=current_user.id,
            course_id=lesson.course_id,
            lesson_id=lesson.id,
            completed=True,
            completed_at=datetime.now(timezone.utc),
        )
        db.add(progress)
    else:
        progress.completed = True
        progress.completed_at = datetime.now(timezone.utc)

    # Ensure enrollment exists
    enrollment = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.user_id == current_user.id,
            CourseEnrollment.course_id == lesson.course_id,
        )
        .first()
    )
    if not enrollment:
        enrollment = CourseEnrollment(
            user_id=current_user.id,
            course_id=lesson.course_id,
            progress_percentage=0,
        )
        db.add(enrollment)
        db.flush()

    # Recalculate course progress
    total_lessons = db.query(Lesson).filter(Lesson.course_id == lesson.course_id).count()
    completed_lessons = (
        db.query(LessonProgress)
        .filter(
            LessonProgress.user_id == current_user.id,
            LessonProgress.course_id == lesson.course_id,
            LessonProgress.completed.is_(True),
        )
        .count()
    )

    progress_percentage = (
        round((completed_lessons / total_lessons) * 100) if total_lessons > 0 else 0
    )
    enrollment.progress_percentage = min(100, progress_percentage)
    if enrollment.progress_percentage >= 100 and not enrollment.completed_at:
        enrollment.completed_at = datetime.now(timezone.utc)

    db.commit()

    return {
        "message": "Lesson completed successfully!",
        "lesson_id": lesson.id,
        "is_completed": True,
        "course_id": lesson.course_id,
        "course_progress": enrollment.progress_percentage,
        "completed_lessons": completed_lessons,
        "total_lessons": total_lessons,
    }

