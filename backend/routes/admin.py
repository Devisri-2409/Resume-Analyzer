from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth import require_admin
from database import get_db
from models import (
    Course,
    CourseEnrollment,
    CourseModule,
    LearningActivity,
    Lesson,
    LessonProgress,
    Quiz,
    QuizAttempt,
    QuizOption,
    QuizQuestion,
    ResumeAnalysis,
    User,
)

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
    List all platform users with roles, verification status, and activity counts.
    """
    users = db.query(User).order_by(User.id.asc()).all()
    result = []
    for u in users:
        enroll_count = db.query(CourseEnrollment).filter(CourseEnrollment.user_id == u.id).count()
        analysis_count = db.query(ResumeAnalysis).filter(ResumeAnalysis.user_id == u.id).count()
        result.append({
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "is_email_verified": bool(getattr(u, "is_email_verified", False)),
            "phone_number": u.phone_number or "",
            "is_phone_verified": bool(getattr(u, "is_phone_verified", False)),
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "enrollments_count": enroll_count,
            "analyses_count": analysis_count,
        })
    return result


@router.patch("/users/{user_id}/status")
def toggle_user_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Toggle a user's active/inactive status. Admins cannot deactivate themselves.
    """
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")
    if target.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot deactivate your own administrator account.",
        )
    target.is_active = not target.is_active
    db.commit()
    db.refresh(target)
    return {
        "id": target.id,
        "is_active": target.is_active,
        "message": f"User status set to {'active' if target.is_active else 'deactivated'}.",
    }


@router.get("/performance")
def get_admin_performance(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Detailed analytics for ATS scores, quiz performance, and skill gaps.
    """
    import json
    from collections import Counter

    analyses = db.query(ResumeAnalysis).all()
    total_analyses = len(analyses)
    ats_scores = [a.ats_score for a in analyses if a.ats_score is not None]

    score_dist = {"0-49": 0, "50-69": 0, "70-84": 0, "85-100": 0}
    for score in ats_scores:
        if score < 50:
            score_dist["0-49"] += 1
        elif score < 70:
            score_dist["50-69"] += 1
        elif score < 85:
            score_dist["70-84"] += 1
        else:
            score_dist["85-100"] += 1

    missing_skills_counter = Counter()
    detected_skills_counter = Counter()

    for a in analyses:
        if a.missing_skills:
            try:
                skills = json.loads(a.missing_skills) if a.missing_skills.startswith("[") else [s.strip() for s in a.missing_skills.split(",")]
                for s in skills:
                    if s:
                        missing_skills_counter[s] += 1
            except Exception:
                pass
        if a.detected_skills:
            try:
                skills = json.loads(a.detected_skills) if a.detected_skills.startswith("[") else [s.strip() for s in a.detected_skills.split(",")]
                for s in skills:
                    if s:
                        detected_skills_counter[s] += 1
            except Exception:
                pass

    top_missing = [{"skill": k, "count": v} for k, v in missing_skills_counter.most_common(8)]
    top_detected = [{"skill": k, "count": v} for k, v in detected_skills_counter.most_common(8)]

    # Quiz stats
    attempts = db.query(QuizAttempt).all()
    total_attempts = len(attempts)
    passed_attempts = sum(1 for att in attempts if att.passed)
    avg_quiz_percentage = (
        round(sum(att.percentage for att in attempts) / total_attempts, 1)
        if total_attempts > 0
        else 0
    )
    pass_rate = (
        round((passed_attempts / total_attempts) * 100, 1)
        if total_attempts > 0
        else 0
    )

    # Course enrollment stats
    enrollments = db.query(CourseEnrollment).all()
    total_enrollments = len(enrollments)
    completed_enrollments = sum(1 for e in enrollments if e.progress_percentage >= 100)
    in_progress_enrollments = sum(1 for e in enrollments if 0 < e.progress_percentage < 100)
    avg_progress = (
        round(sum(e.progress_percentage for e in enrollments) / total_enrollments, 1)
        if total_enrollments > 0
        else 0
    )

    return {
        "ats": {
            "total_analyses": total_analyses,
            "avg_score": round(sum(ats_scores) / len(ats_scores), 1) if ats_scores else 0,
            "distribution": score_dist,
            "top_missing_skills": top_missing,
            "top_detected_skills": top_detected,
        },
        "quizzes": {
            "total_attempts": total_attempts,
            "passed_attempts": passed_attempts,
            "avg_percentage": avg_quiz_percentage,
            "pass_rate": pass_rate,
        },
        "learning": {
            "total_enrollments": total_enrollments,
            "completed_enrollments": completed_enrollments,
            "in_progress_enrollments": in_progress_enrollments,
            "avg_progress": avg_progress,
        },
    }


@router.get("/courses")
def get_admin_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    List all platform courses with module, lesson, and enrollment stats.
    """
    import json

    courses = db.query(Course).order_by(Course.order.asc()).all()
    result = []
    for c in courses:
        lessons_count = db.query(Lesson).filter(Lesson.course_id == c.id).count()
        quizzes_count = db.query(Quiz).filter(Quiz.course_id == c.id).count()
        enrollments = db.query(CourseEnrollment).filter(CourseEnrollment.course_id == c.id).all()
        enrolled_count = len(enrollments)
        completed_count = sum(1 for e in enrollments if e.progress_percentage >= 100)
        skills = []
        if c.skills_covered:
            try:
                skills = json.loads(c.skills_covered)
            except Exception:
                skills = [c.skills_covered]

        result.append({
            "id": c.id,
            "title": c.title,
            "slug": c.slug,
            "category": c.category,
            "difficulty": c.difficulty,
            "estimated_duration": c.estimated_duration,
            "skills_covered": skills,
            "total_lessons": lessons_count,
            "total_quizzes": quizzes_count,
            "enrolled_students": enrolled_count,
            "completed_students": completed_count,
            "completion_rate": round((completed_count / enrolled_count) * 100, 1) if enrolled_count > 0 else 0,
        })
    return result


@router.get("/learning-paths")
def get_admin_learning_paths(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Aggregated career tracks and student journey metrics.
    """
    tracks_definition = [
        {
            "id": "frontend",
            "title": "Frontend Engineering Track",
            "description": "Modern web development from core HTML/CSS to advanced React state management.",
            "target_role": "Frontend Developer / React Specialist",
            "course_ids": [5, 6, 8],  # Web Dev, React, Git
            "skills": ["HTML5", "CSS3", "JavaScript", "React", "Git", "State Management"],
        },
        {
            "id": "backend",
            "title": "Backend Architecture Track",
            "description": "Server-side architecture, RESTful API design, relational databases, and enterprise Java/Python.",
            "target_role": "Backend Engineer / API Developer",
            "course_ids": [1, 2, 3, 7],  # Python, Java, SQL, REST APIs
            "skills": ["Python", "Java", "SQL", "REST APIs", "FastAPI", "Database Indexing"],
        },
        {
            "id": "fullstack",
            "title": "Full-Stack Software Engineering",
            "description": "End-to-end web software lifecycle covering clients, servers, databases, and deployment.",
            "target_role": "Full Stack Engineer",
            "course_ids": [5, 6, 1, 3, 7, 8],
            "skills": ["React", "Python", "SQL", "REST APIs", "Git", "System Design"],
        },
        {
            "id": "devops",
            "title": "DevOps & Cloud Infrastructure",
            "description": "Containerization, cloud architecture, and modern deployment pipelines.",
            "target_role": "DevOps Engineer / Cloud Practitioner",
            "course_ids": [8, 9, 10],  # Git, Docker, AWS
            "skills": ["Git", "Docker", "AWS", "CI/CD", "Cloud Architecture"],
        },
        {
            "id": "datascience",
            "title": "Data Engineering & Algorithms",
            "description": "Algorithmic thinking, data structures, and database query optimization.",
            "target_role": "Data Analyst / Systems Developer",
            "course_ids": [1, 3, 4],  # Python, SQL, DSA
            "skills": ["Python", "SQL", "Algorithms", "Data Structures", "Big-O Analysis"],
        },
    ]

    all_courses = {c.id: c.title for c in db.query(Course).all()}
    enrollments = db.query(CourseEnrollment).all()

    result = []
    for track in tracks_definition:
        track_course_ids = track["course_ids"]
        # Find unique users enrolled in any course of this track
        track_enrollments = [e for e in enrollments if e.course_id in track_course_ids]
        unique_enrolled_users = len(set(e.user_id for e in track_enrollments))
        completed_course_enrollments = sum(1 for e in track_enrollments if e.progress_percentage >= 100)

        course_names = [all_courses.get(cid, f"Course #{cid}") for cid in track_course_ids if cid in all_courses]

        result.append({
            "id": track["id"],
            "title": track["title"],
            "description": track["description"],
            "target_role": track["target_role"],
            "courses": course_names,
            "course_count": len(course_names),
            "skills": track["skills"],
            "active_students": unique_enrolled_users,
            "completions": completed_course_enrollments,
        })
    return result


@router.get("/tests")
def get_admin_tests(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    List all assessment tests/quizzes across courses with attempt stats.
    """
    quizzes = db.query(Quiz).order_by(Quiz.id.asc()).all()
    result = []
    for q in quizzes:
        course = db.query(Course).filter(Course.id == q.course_id).first()
        questions_count = db.query(QuizQuestion).filter(QuizQuestion.quiz_id == q.id).count()
        attempts = db.query(QuizAttempt).filter(QuizAttempt.quiz_id == q.id).all()
        total_attempts = len(attempts)
        passed_attempts = sum(1 for a in attempts if a.passed)
        avg_score = (
            round(sum(a.percentage for a in attempts) / total_attempts, 1)
            if total_attempts > 0
            else 0
        )

        result.append({
            "id": q.id,
            "title": q.title,
            "course_id": q.course_id,
            "course_title": course.title if course else "Independent Assessment",
            "passing_score": q.passing_score,
            "total_questions": questions_count,
            "total_attempts": total_attempts,
            "passed_attempts": passed_attempts,
            "avg_score": avg_score,
            "pass_rate": round((passed_attempts / total_attempts) * 100, 1) if total_attempts > 0 else 0,
        })
    return result


@router.get("/questions")
def get_admin_questions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    List all questions from the question bank with options and explanations.
    """
    questions = db.query(QuizQuestion).order_by(QuizQuestion.quiz_id.asc(), QuizQuestion.order.asc()).all()
    result = []
    for q in questions:
        quiz = db.query(Quiz).filter(Quiz.id == q.quiz_id).first()
        course = db.query(Course).filter(Course.id == quiz.course_id).first() if quiz else None
        options = db.query(QuizOption).filter(QuizOption.question_id == q.id).all()

        result.append({
            "id": q.id,
            "quiz_id": q.quiz_id,
            "quiz_title": quiz.title if quiz else f"Quiz #{q.quiz_id}",
            "course_title": course.title if course else "Assessment",
            "question_text": q.question_text,
            "order": q.order,
            "options": [
                {
                    "id": opt.id,
                    "option_text": opt.option_text,
                    "is_correct": opt.is_correct,
                    "explanation": opt.explanation or "",
                }
                for opt in options
            ],
        })
    return result


@router.get("/badges")
def get_admin_badges(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Platform achievement badge criteria and real unlock counts.
    """
    from models import LessonProgress

    total_users = db.query(User).filter(User.role != "admin").count() or 1

    # Resume Master: ATS score >= 80
    ats_masters = (
        db.query(ResumeAnalysis.user_id)
        .filter(ResumeAnalysis.ats_score >= 80, ResumeAnalysis.user_id.isnot(None))
        .distinct()
        .count()
    )

    # First Steps: Completed at least 1 lesson
    first_step_users = (
        db.query(LessonProgress.user_id)
        .filter(LessonProgress.completed.is_(True))
        .distinct()
        .count()
    )

    # Quiz Ace: Passed quiz with score >= 85%
    quiz_aces = (
        db.query(QuizAttempt.user_id)
        .filter(QuizAttempt.passed.is_(True), QuizAttempt.percentage >= 85)
        .distinct()
        .count()
    )

    # Course Graduate: Completed 100% of any course
    graduates = (
        db.query(CourseEnrollment.user_id)
        .filter(CourseEnrollment.progress_percentage >= 100)
        .distinct()
        .count()
    )

    # Streak Champion: Active on 3+ distinct dates
    streak_champs = (
        db.query(LearningActivity.user_id)
        .group_by(LearningActivity.user_id)
        .having(func.count(func.distinct(LearningActivity.activity_date)) >= 3)
        .count()
    )

    # Verified Identity: Email verified
    verified_users = (
        db.query(User)
        .filter(User.is_email_verified.is_(True))
        .count()
    )

    badges = [
        {
            "id": "resume_master",
            "name": "Resume Master",
            "category": "Resume Intelligence",
            "description": "Achieve an ATS compatibility score of 80% or higher on a verified resume.",
            "unlocked_count": ats_masters,
            "total_eligible": total_users,
            "icon": "award",
            "tier": "Gold",
        },
        {
            "id": "first_steps",
            "name": "Quick Starter",
            "category": "Learning Velocity",
            "description": "Complete your very first technical curriculum lesson.",
            "unlocked_count": first_step_users,
            "total_eligible": total_users,
            "icon": "zap",
            "tier": "Bronze",
        },
        {
            "id": "quiz_ace",
            "name": "Assessment Ace",
            "category": "Assessments",
            "description": "Pass any technical assessment test with an exceptional score of 85% or higher.",
            "unlocked_count": quiz_aces,
            "total_eligible": total_users,
            "icon": "target",
            "tier": "Silver",
        },
        {
            "id": "course_graduate",
            "name": "Curriculum Graduate",
            "category": "Curriculum",
            "description": "Complete 100% of all lessons and quizzes in a full curriculum course.",
            "unlocked_count": graduates,
            "total_eligible": total_users,
            "icon": "book",
            "tier": "Gold",
        },
        {
            "id": "streak_champion",
            "name": "Streak Champion",
            "category": "Consistency",
            "description": "Log qualifying learning activities across at least 3 distinct calendar days.",
            "unlocked_count": streak_champs,
            "total_eligible": total_users,
            "icon": "flame",
            "tier": "Silver",
        },
        {
            "id": "verified_pro",
            "name": "Verified Candidate",
            "category": "Account Security",
            "description": "Verify your email address to validate genuine platform profile identity.",
            "unlocked_count": verified_users,
            "total_eligible": total_users,
            "icon": "shield",
            "tier": "Bronze",
        },
    ]
    return badges


@router.get("/reports")
def get_admin_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    List all resume analysis audits with candidate identity and ATS performance.
    """
    import json

    analyses = (
        db.query(ResumeAnalysis)
        .order_by(ResumeAnalysis.created_at.desc())
        .limit(100)
        .all()
    )
    result = []
    for a in analyses:
        user = db.query(User).filter(User.id == a.user_id).first() if a.user_id else None
        detected = []
        if a.detected_skills:
            try:
                detected = json.loads(a.detected_skills) if a.detected_skills.startswith("[") else [s.strip() for s in a.detected_skills.split(",")]
            except Exception:
                detected = [a.detected_skills]

        missing = []
        if a.missing_skills:
            try:
                missing = json.loads(a.missing_skills) if a.missing_skills.startswith("[") else [s.strip() for s in a.missing_skills.split(",")]
            except Exception:
                missing = [a.missing_skills]

        result.append({
            "id": a.id,
            "filename": a.filename,
            "user_id": a.user_id,
            "candidate_name": user.full_name if user else "Anonymous Candidate",
            "candidate_email": user.email if user else "Not linked",
            "pages": a.pages or 1,
            "ats_score": a.ats_score or 0,
            "job_match_percentage": a.job_match_percentage or 0,
            "detected_skills": detected,
            "missing_skills": missing,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        })
    return result