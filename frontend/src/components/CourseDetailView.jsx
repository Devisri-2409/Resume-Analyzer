import React, { useEffect, useState } from "react";
import axios from "axios";
import { ArrowLeftIcon, AwardIcon, BookOpenIcon, CheckCircleIcon, ClockIcon } from "./Icons";

export function CourseDetailView({ courseId, apiUrl, token, onNavigate, showToast }) {
  const [course, setCourse] = useState(null);
  const [loading, setLoading] = useState(true);
  const [enrolling, setEnrolling] = useState(false);

  useEffect(() => {
    fetchCourseDetail();
  }, [courseId]);

  const fetchCourseDetail = async () => {
    setLoading(true);
    try {
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await axios.get(`${apiUrl}/api/courses/${courseId}`, { headers });
      setCourse(res.data);
    } catch (err) {
      console.error("Course detail fetch error:", err);
      if (showToast) {
        showToast("Could not load course details.", "error");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleEnroll = async () => {
    setEnrolling(true);
    try {
      await axios.post(
        `${apiUrl}/api/courses/${courseId}/enroll`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (showToast) {
        showToast(`Enrolled in "${course.title}"!`, "success");
      }
      fetchCourseDetail();
    } catch (err) {
      console.error("Enroll error:", err);
      if (showToast) {
        showToast("Enrollment failed. Please try again.", "error");
      }
    } finally {
      setEnrolling(false);
    }
  };

  if (loading) {
    return (
      <div className="view-loading-state">
        <div className="spinner" />
        <p>Loading course curriculum...</p>
      </div>
    );
  }

  if (!course) {
    return (
      <div className="empty-card-prompt">
        <h3>Course not found</h3>
        <button type="button" className="primary-button" onClick={() => onNavigate("/courses")}>
          ← Back to Catalog
        </button>
      </div>
    );
  }

  const isEnrolled = course.is_enrolled;
  const progress = course.progress_percentage || 0;

  return (
    <div className="course-detail-content">
      {/* Breadcrumb / Back button */}
      <div className="detail-breadcrumb">
        <button type="button" className="back-link-btn" onClick={() => onNavigate("/courses")}>
          <ArrowLeftIcon size={14} />
          <span>Back to Courses</span>
        </button>
      </div>

      {/* Course Hero Banner */}
      <section className="course-hero-card">
        <div className="course-hero-main">
          <div className="course-badges-row">
            <span className="badge-category">{course.category}</span>
            <span className="badge-difficulty">{course.difficulty}</span>
            <span className="badge-duration">
              <ClockIcon size={13} />
              {course.estimated_duration}
            </span>
          </div>

          <h1>{course.title}</h1>
          <p className="course-hero-desc">{course.description}</p>

          <div className="course-skills-row">
            <span className="skills-row-label">Skills Covered:</span>
            {course.skills_covered.map((skill) => (
              <span key={skill} className="chip success small">
                {skill}
              </span>
            ))}
          </div>
        </div>

        {/* Course Progress / Enrollment Action Card */}
        <div className="course-action-card">
          <div className="action-card-header">
            <strong>{isEnrolled ? "Your Course Progress" : "Ready to Start?"}</strong>
          </div>

          {isEnrolled ? (
            <div className="action-progress-body">
              <div className="progress-large-num">
                <strong>{progress}%</strong>
                <span>
                  {course.completed_lessons} of {course.total_lessons} lessons completed
                </span>
              </div>
              <div className="horizontal-progress-bar">
                <div className="bar-fill" style={{ width: `${progress}%` }} />
              </div>
            </div>
          ) : (
            <div className="action-enroll-body">
              <p>Enroll to track your lesson progress, take quizzes, and earn skill badges.</p>
              <button
                type="button"
                className="primary-button full-w"
                onClick={handleEnroll}
                disabled={enrolling}
              >
                {enrolling ? "Enrolling..." : "Enroll in Course Free"}
              </button>
            </div>
          )}
        </div>
      </section>

      {/* Modules and Curriculum */}
      <section className="curriculum-section">
        <div className="curriculum-header">
          <div>
            <span className="section-kicker">SYLLABUS & LESSONS</span>
            <h2>Course Modules & Lessons</h2>
          </div>
          <span className="total-lessons-pill">
            {course.total_lessons} Lessons • {course.quizzes?.length || 1} Quiz
          </span>
        </div>

        <div className="modules-stack">
          {course.modules?.map((mod, modIdx) => (
            <div key={mod.id} className="module-card">
              <div className="module-card-header">
                <div className="module-title-wrap">
                  <span className="module-number">0{modIdx + 1}</span>
                  <div>
                    <h3>{mod.title}</h3>
                    <small>{mod.lessons?.length || 0} Lessons</small>
                  </div>
                </div>
                {isEnrolled && (
                  <span className="module-progress-badge">
                    {mod.progress_percentage}% Complete
                  </span>
                )}
              </div>

              <div className="lessons-list">
                {mod.lessons?.map((les) => {
                  const isDone = les.is_completed;
                  return (
                    <div
                      key={les.id}
                      className={`lesson-row ${isDone ? "completed" : ""}`}
                      onClick={() => onNavigate(`/courses/${course.id}/lessons/${les.id}`)}
                    >
                      <div className="lesson-left">
                        <span className={`status-circle ${isDone ? "done" : ""}`}>
                          {isDone ? "✓" : "○"}
                        </span>
                        <div>
                          <strong>{les.title}</strong>
                          <span className="lesson-duration">{les.duration}</span>
                        </div>
                      </div>

                      <button
                        type="button"
                        className="lesson-action-btn"
                        onClick={(e) => {
                          e.stopPropagation();
                          onNavigate(`/courses/${course.id}/lessons/${les.id}`);
                        }}
                      >
                        {isDone ? "Review" : "Start Lesson →"}
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* Quizzes Section */}
        {course.quizzes && course.quizzes.length > 0 && (
          <div className="course-quizzes-card">
            <div className="quizzes-card-header">
              <div className="quiz-header-icon">
                <AwardIcon size={20} />
              </div>
              <div>
                <span className="section-kicker">KNOWLEDGE ASSESSMENT</span>
                <h3>Course Certification Quiz</h3>
                <p>Pass the quiz to validate your skills and boost your profile stats.</p>
              </div>
            </div>

            <div className="quizzes-list">
              {course.quizzes.map((quiz) => (
                <div key={quiz.id} className="quiz-card-item">
                  <div className="quiz-item-left">
                    <span className="quiz-num-badge">Q</span>
                    <div>
                      <strong>{quiz.title}</strong>
                      <div className="quiz-item-meta">
                        <span>{quiz.questions_count} Questions</span>
                        <span>Passing: {quiz.passing_score}%</span>
                        {quiz.is_completed && (
                          <span className={`quiz-score-pill ${quiz.passed ? "passed" : "retake"}`}>
                            Best: {quiz.highest_score}% {quiz.passed ? "(Passed)" : "(Needs Retake)"}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <button
                    type="button"
                    className="primary-button small"
                    onClick={() => onNavigate(`/courses/${course.id}/quizzes/${quiz.id}`)}
                  >
                    {quiz.is_completed ? "Retake Quiz →" : "Take Quiz →"}
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}

