import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import (
    User,
    Course,
    Quiz,
    QuizQuestion,
    QuizOption,
    QuizAttempt,
)
from schemas import QuizSubmitRequest

router = APIRouter(prefix="/api/quizzes", tags=["Quizzes"])


@router.get("/course/{course_id}")
def get_course_quizzes(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    quizzes = (
        db.query(Quiz)
        .filter(Quiz.course_id == course_id)
        .order_by(Quiz.order.asc())
        .all()
    )

    results = []
    for q in quizzes:
        attempts = (
            db.query(QuizAttempt)
            .filter(
                QuizAttempt.user_id == current_user.id,
                QuizAttempt.quiz_id == q.id,
            )
            .order_by(QuizAttempt.percentage.desc())
            .all()
        )
        best_score = attempts[0].percentage if attempts else None
        has_passed = any(a.passed for a in attempts)
        q_count = db.query(QuizQuestion).filter(QuizQuestion.quiz_id == q.id).count()

        results.append({
            "id": q.id,
            "course_id": q.course_id,
            "title": q.title,
            "description": q.description,
            "passing_score": q.passing_score,
            "total_questions": q_count,
            "total_attempts": len(attempts),
            "best_score": best_score,
            "passed": has_passed,
        })

    return {"quizzes": results}


@router.get("/{quiz_id}")
def get_quiz(
    quiz_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found.")

    course = db.query(Course).filter(Course.id == quiz.course_id).first()

    questions = (
        db.query(QuizQuestion)
        .filter(QuizQuestion.quiz_id == quiz.id)
        .order_by(QuizQuestion.order.asc())
        .all()
    )

    questions_data = []
    for q in questions:
        options = (
            db.query(QuizOption)
            .filter(QuizOption.question_id == q.id)
            .order_by(QuizOption.id.asc())
            .all()
        )
        questions_data.append({
            "id": q.id,
            "question_text": q.question_text,
            "order": q.order,
            "options": [
                {
                    "id": opt.id,
                    "option_text": opt.option_text,
                }
                for opt in options
            ],
        })

    past_attempts = (
        db.query(QuizAttempt)
        .filter(
            QuizAttempt.user_id == current_user.id,
            QuizAttempt.quiz_id == quiz.id,
        )
        .order_by(QuizAttempt.created_at.desc())
        .limit(5)
        .all()
    )

    attempts_data = [
        {
            "id": a.id,
            "score": a.score,
            "total_questions": a.total_questions,
            "percentage": a.percentage,
            "passed": a.passed,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in past_attempts
    ]

    return {
        "id": quiz.id,
        "course_id": quiz.course_id,
        "course_title": course.title if course else "",
        "title": quiz.title,
        "description": quiz.description,
        "passing_score": quiz.passing_score,
        "questions": questions_data,
        "past_attempts": attempts_data,
    }


@router.post("/{quiz_id}/submit")
def submit_quiz(
    quiz_id: int,
    payload: QuizSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found.")

    questions = (
        db.query(QuizQuestion)
        .filter(QuizQuestion.quiz_id == quiz.id)
        .order_by(QuizQuestion.order.asc())
        .all()
    )

    if not questions:
        raise HTTPException(status_code=400, detail="This quiz has no questions.")

    correct_count = 0
    breakdown = []

    for q in questions:
        options = (
            db.query(QuizOption)
            .filter(QuizOption.question_id == q.id)
            .all()
        )
        selected_option_id = payload.answers.get(q.id) or payload.answers.get(str(q.id))

        correct_opt = next((opt for opt in options if opt.is_correct), None)
        selected_opt = next((opt for opt in options if opt.id == selected_option_id), None)

        is_user_correct = (
            selected_opt is not None and correct_opt is not None and selected_opt.id == correct_opt.id
        )

        if is_user_correct:
            correct_count += 1

        breakdown.append({
            "question_id": q.id,
            "question_text": q.question_text,
            "selected_option_id": selected_option_id,
            "selected_option_text": selected_opt.option_text if selected_opt else "No answer selected",
            "correct_option_id": correct_opt.id if correct_opt else None,
            "correct_option_text": correct_opt.option_text if correct_opt else "",
            "is_correct": is_user_correct,
            "explanation": correct_opt.explanation if correct_opt else "",
        })

    total_questions = len(questions)
    percentage = round((correct_count / total_questions) * 100) if total_questions > 0 else 0
    passed = percentage >= quiz.passing_score
    incorrect_count = total_questions - correct_count

    attempt = QuizAttempt(
        user_id=current_user.id,
        quiz_id=quiz.id,
        course_id=quiz.course_id,
        score=correct_count,
        total_questions=total_questions,
        percentage=percentage,
        passed=passed,
        details_json=json.dumps(breakdown),
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    # Recalculate accurate course progress with the new quiz attempt
    from services.learning_service import (
        calculate_and_update_course_progress,
        award_course_skills_if_passed,
        record_learning_activity,
        calculate_user_streak,
    )
    course_progress = calculate_and_update_course_progress(current_user.id, quiz.course_id, db)

    # If the user passed the quiz, automatically award the skills covered in the course
    awarded_skills = []
    if passed:
        awarded_skills = award_course_skills_if_passed(current_user.id, quiz.course_id, db)

    # Record qualifying learning activity for streak
    record_learning_activity(
        user_id=current_user.id,
        activity_type="quiz_attempt",
        db=db,
        metadata={
            "quiz_id": quiz.id,
            "course_id": quiz.course_id,
            "score": correct_count,
            "percentage": percentage,
            "passed": passed,
        },
    )

    streak_info = calculate_user_streak(current_user.id, db)

    return {
        "attempt_id": attempt.id,
        "score": correct_count,
        "total_questions": total_questions,
        "percentage": percentage,
        "passed": passed,
        "correct_count": correct_count,
        "incorrect_count": incorrect_count,
        "passing_score": quiz.passing_score,
        "course_progress": course_progress,
        "learning_streak": streak_info["current_streak"],
        "awarded_skills": awarded_skills,
        "breakdown": breakdown,
    }

