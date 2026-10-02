import json
from datetime import datetime, date, timedelta, timezone
from typing import List, Dict, Any, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

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
    LearningActivity,
)


def record_learning_activity(
    user_id: int,
    activity_type: str,
    db: Session,
    metadata: Optional[Dict[str, Any]] = None,
) -> LearningActivity:
    """
    Records a qualifying learning activity for the user.
    Uses UTC date to maintain a consistent timezone policy across the platform.
    """
    now = datetime.now(timezone.utc)
    today = now.date()

    activity = LearningActivity(
        user_id=user_id,
        activity_type=activity_type,
        activity_date=today,
        created_at=now,
        metadata_json=json.dumps(metadata or {}),
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


def calculate_user_streak(user_id: int, db: Session) -> Dict[str, Any]:
    """
    Calculates current and longest streaks from consecutive calendar dates in UTC.
    Multiple activities on one date count as exactly one active day.
    Correctly handles:
    - active streaks maintained today or yesterday (pending today's activity)
    - missed days resetting current streak
    - historical longest streak tracking
    """
    # 1. Collect all distinct activity dates for this user
    activity_dates: Set[date] = set()

    # From learning_activities table
    rows = db.query(LearningActivity.activity_date).filter(LearningActivity.user_id == user_id).distinct().all()
    for (act_date,) in rows:
        if act_date:
            activity_dates.add(act_date)

    # Backwards-compatibility: also check historical LessonProgress, QuizAttempt, CourseEnrollment, ResumeAnalysis
    lp_rows = db.query(LessonProgress.completed_at).filter(
        LessonProgress.user_id == user_id,
        LessonProgress.completed.is_(True),
        LessonProgress.completed_at.isnot(None),
    ).all()
    for (cat,) in lp_rows:
        if cat:
            activity_dates.add(cat.date() if isinstance(cat, datetime) else cat)

    qa_rows = db.query(QuizAttempt.created_at).filter(
        QuizAttempt.user_id == user_id,
        QuizAttempt.created_at.isnot(None),
    ).all()
    for (qat,) in qa_rows:
        if qat:
            activity_dates.add(qat.date() if isinstance(qat, datetime) else qat)

    ce_rows = db.query(CourseEnrollment.enrolled_at).filter(
        CourseEnrollment.user_id == user_id,
        CourseEnrollment.enrolled_at.isnot(None),
    ).all()
    for (eat,) in ce_rows:
        if eat:
            activity_dates.add(eat.date() if isinstance(eat, datetime) else eat)

    ra_rows = db.query(ResumeAnalysis.created_at).filter(
        ResumeAnalysis.user_id == user_id,
        ResumeAnalysis.created_at.isnot(None),
    ).all()
    for (rat,) in ra_rows:
        if rat:
            activity_dates.add(rat.date() if isinstance(rat, datetime) else rat)

    if not activity_dates:
        return {
            "current_streak": 0,
            "longest_streak": 0,
            "active_days": 0,
            "today_active": False,
        }

    sorted_dates = sorted(activity_dates)
    today = datetime.now(timezone.utc).date()
    yesterday = today - timedelta(days=1)
    today_active = today in activity_dates

    # Calculate Current Streak
    # If active today, count backwards from today.
    # If not active today, but active yesterday, streak is still alive from yesterday.
    # If neither today nor yesterday, streak is 0.
    current_streak = 0
    if today in activity_dates:
        check_date = today
        while check_date in activity_dates:
            current_streak += 1
            check_date -= timedelta(days=1)
    elif yesterday in activity_dates:
        check_date = yesterday
        while check_date in activity_dates:
            current_streak += 1
            check_date -= timedelta(days=1)

    # Calculate Longest Streak
    longest_streak = 1
    cur_run = 1
    for i in range(1, len(sorted_dates)):
        if sorted_dates[i] == sorted_dates[i - 1] + timedelta(days=1):
            cur_run += 1
            if cur_run > longest_streak:
                longest_streak = cur_run
        elif sorted_dates[i] > sorted_dates[i - 1] + timedelta(days=1):
            cur_run = 1

    longest_streak = max(current_streak, longest_streak)

    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "active_days": len(sorted_dates),
        "today_active": today_active,
    }


def calculate_and_update_course_progress(user_id: int, course_id: int, db: Session) -> int:
    """
    Calculates accurate course progress reflecting both lesson completion and quiz performance.
    Guarantees CourseEnrollment is created/updated and marks completed_at when 100%.
    """
    total_lessons = db.query(Lesson).filter(Lesson.course_id == course_id).count()
    completed_lessons = (
        db.query(LessonProgress)
        .filter(
            LessonProgress.user_id == user_id,
            LessonProgress.course_id == course_id,
            LessonProgress.completed.is_(True),
        )
        .count()
    )

    total_quizzes = db.query(Quiz).filter(Quiz.course_id == course_id).count()
    passed_quizzes = (
        db.query(QuizAttempt.quiz_id)
        .filter(
            QuizAttempt.user_id == user_id,
            QuizAttempt.course_id == course_id,
            QuizAttempt.passed.is_(True),
        )
        .distinct()
        .count()
    )

    total_items = total_lessons + total_quizzes
    completed_items = completed_lessons + passed_quizzes

    if total_items == 0:
        progress_percentage = 0
    else:
        progress_percentage = min(100, round((completed_items / total_items) * 100))

    enrollment = (
        db.query(CourseEnrollment)
        .filter(CourseEnrollment.user_id == user_id, CourseEnrollment.course_id == course_id)
        .first()
    )

    now = datetime.now(timezone.utc)
    if not enrollment:
        enrollment = CourseEnrollment(
            user_id=user_id,
            course_id=course_id,
            progress_percentage=progress_percentage,
            enrolled_at=now,
            completed_at=now if progress_percentage >= 100 else None,
        )
        db.add(enrollment)
    else:
        enrollment.progress_percentage = progress_percentage
        if progress_percentage >= 100 and not enrollment.completed_at:
            enrollment.completed_at = now

    db.commit()
    db.refresh(enrollment)
    return progress_percentage


def award_course_skills_if_passed(user_id: int, course_id: int, db: Session) -> List[str]:
    """
    When a user demonstrates competency (passing a quiz or completing a course),
    the skills covered by the course are automatically added to the user's verified skills.
    This resolves skill gaps in real-time.
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course or not course.skills_covered:
        return []

    try:
        skills = json.loads(course.skills_covered)
    except Exception:
        skills = []

    awarded = []
    existing_skills = {
        s.skill_name.lower()
        for s in db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
    }

    for skill in skills:
        if skill.strip() and skill.lower() not in existing_skills:
            user_skill = UserSkill(user_id=user_id, skill_name=skill.strip())
            db.add(user_skill)
            existing_skills.add(skill.lower())
            awarded.append(skill.strip())

    if awarded:
        db.commit()

    return awarded


def find_skill_recommendations(user_id: int, db: Session, limit: int = 4) -> List[Dict[str, Any]]:
    """
    Recommends courses that bridge actual missing skills detected from the user's own resume analysis.
    - Strictly user-specific (does NOT leak other users' analyses).
    - Excludes skills the user has already acquired (in UserSkill).
    - Prioritizes courses that bridge active missing skills.
    - Deprioritizes or filters out already completed courses (progress >= 100).
    """
    # 1. Retrieve the user's latest resume analysis (user-specific only)
    latest_analysis = (
        db.query(ResumeAnalysis)
        .filter(ResumeAnalysis.user_id == user_id)
        .order_by(ResumeAnalysis.created_at.desc())
        .first()
    )

    resume_missing_skills = []
    if latest_analysis and latest_analysis.missing_skills:
        try:
            resume_missing_skills = json.loads(latest_analysis.missing_skills)
        except Exception:
            resume_missing_skills = []

    # 2. Get user's verified skills
    user_skills = {
        s.skill_name.lower()
        for s in db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
    }

    # Active missing skills = resume missing skills that user has NOT already acquired
    active_missing_skills = [
        ms for ms in resume_missing_skills if ms.lower() not in user_skills
    ]

    # 3. Get user enrollments
    enrollments_map = {
        e.course_id: e.progress_percentage
        for e in db.query(CourseEnrollment).filter(CourseEnrollment.user_id == user_id).all()
    }

    courses = db.query(Course).order_by(Course.order.asc()).all()
    scored_courses = []

    for c in courses:
        # If the user has already 100% completed the course, do not recommend it as an active gap
        progress = enrollments_map.get(c.id, 0)
        is_completed = progress >= 100

        skills = json.loads(c.skills_covered) if c.skills_covered else []
        matched_gaps = []

        # Check against active_missing_skills from resume analysis
        for ms in active_missing_skills:
            if any(ms.lower() in s.lower() or s.lower() in ms.lower() for s in skills):
                matched_gaps.append(ms)

        # Check against general unacquired profile skills covered in this course
        profile_gaps = []
        for s in skills:
            if s.lower() not in user_skills:
                profile_gaps.append(s)

        # Score calculation:
        # High priority to resume-detected missing skills (weight 10)
        # Moderate priority to profile skills not yet in profile (weight 2)
        # Penalty for already completed courses
        if is_completed:
            score = -100
        else:
            score = (len(matched_gaps) * 10) + len(profile_gaps)
            # Bonus for courses not yet enrolled (encourages new learning pathways)
            if c.id not in enrollments_map:
                score += 1

        total_lessons = db.query(Lesson).filter(Lesson.course_id == c.id).count()

        display_gaps = list(set(matched_gaps if matched_gaps else profile_gaps))

        scored_courses.append({
            "id": c.id,
            "title": c.title,
            "slug": c.slug,
            "description": c.description,
            "difficulty": c.difficulty,
            "estimated_duration": c.estimated_duration,
            "skills_covered": skills,
            "category": c.category,
            "matched_missing_skills": display_gaps,
            "match_count": len(matched_gaps),
            "is_enrolled": c.id in enrollments_map,
            "is_completed": is_completed,
            "progress_percentage": progress,
            "total_lessons": total_lessons,
            "_sort_score": score,
        })

    # Sort descending by score, filtering out fully completed courses from recommendations
    uncompleted_courses = [c for c in scored_courses if not c["is_completed"]]
    uncompleted_courses.sort(key=lambda x: (x["_sort_score"], -x["progress_percentage"]), reverse=True)

    # If all courses are completed or none left, fall back to all courses
    result = uncompleted_courses if uncompleted_courses else scored_courses
    for item in result:
        item.pop("_sort_score", None)

    return result[:limit]


def get_learning_dashboard_data(user_id: int, db: Session) -> Dict[str, Any]:
    """
    Assembles comprehensive learning dashboard data with synchronized progress,
    active streak calculations, and relevant recommendations.
    """
    enrollments = (
        db.query(CourseEnrollment)
        .filter(CourseEnrollment.user_id == user_id)
        .order_by(CourseEnrollment.enrolled_at.desc())
        .all()
    )

    current_courses = []
    total_progress_sum = 0

    for enr in enrollments:
        course = db.query(Course).filter(Course.id == enr.course_id).first()
        if not course:
            continue

        # Keep progress synced with actual lesson and quiz records
        actual_progress = calculate_and_update_course_progress(user_id, course.id, db)

        total_lessons = db.query(Lesson).filter(Lesson.course_id == course.id).count()
        completed_lessons = (
            db.query(LessonProgress)
            .filter(
                LessonProgress.user_id == user_id,
                LessonProgress.course_id == course.id,
                LessonProgress.completed.is_(True),
            )
            .count()
        )

        next_lesson = (
            db.query(Lesson)
            .filter(
                Lesson.course_id == course.id,
                ~Lesson.id.in_(
                    db.query(LessonProgress.lesson_id).filter(
                        LessonProgress.user_id == user_id,
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
            "progress_percentage": actual_progress,
            "total_lessons": total_lessons,
            "completed_lessons": completed_lessons,
            "next_lesson_id": next_lesson.id if next_lesson else None,
            "next_lesson_title": next_lesson.title if next_lesson else "Course Complete",
        })
        total_progress_sum += actual_progress

    overall_progress = (
        round(total_progress_sum / len(current_courses)) if current_courses else 0
    )

    recommended = find_skill_recommendations(user_id, db, limit=4)
    streak_info = calculate_user_streak(user_id, db)

    # Recent activities
    recent_activities = []
    recent_lessons = (
        db.query(LessonProgress, Lesson)
        .join(Lesson, LessonProgress.lesson_id == Lesson.id)
        .filter(LessonProgress.user_id == user_id, LessonProgress.completed.is_(True))
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

    recent_quizzes = (
        db.query(QuizAttempt, Quiz)
        .join(Quiz, QuizAttempt.quiz_id == Quiz.id)
        .filter(QuizAttempt.user_id == user_id)
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

    recent_activities.sort(key=lambda x: x["timestamp"] or "", reverse=True)
    recent_activities = recent_activities[:6]

    # Quiz performance metrics
    passed_quizzes_count = (
        db.query(QuizAttempt.quiz_id)
        .filter(QuizAttempt.user_id == user_id, QuizAttempt.passed.is_(True))
        .distinct()
        .count()
    )
    total_quizzes_taken = db.query(QuizAttempt).filter(QuizAttempt.user_id == user_id).count()
    avg_score_res = (
        db.query(func.avg(QuizAttempt.percentage))
        .filter(QuizAttempt.user_id == user_id)
        .scalar()
    )
    avg_score = round(float(avg_score_res), 1) if avg_score_res is not None else 0.0

    highest_score_res = (
        db.query(func.max(QuizAttempt.percentage))
        .filter(QuizAttempt.user_id == user_id)
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

    total_courses_count = db.query(Course).count()

    return {
        "overall_progress": overall_progress,
        "enrolled_count": len(current_courses),
        "courses_total": total_courses_count,
        "current_courses": current_courses,
        "recommended_courses": recommended,
        "recent_activity": recent_activities,
        "learning_streak": streak_info["current_streak"],
        "longest_streak": streak_info["longest_streak"],
        "active_days": streak_info["active_days"],
        "today_active": streak_info["today_active"],
        "quiz_performance": {
            "average_score": avg_score,
            "quizzes_completed": passed_quizzes_count,
            "total_attempts": total_quizzes_taken,
            "highest_score": highest_score,
            "recent_scores": recent_quiz_scores,
        },
    }

