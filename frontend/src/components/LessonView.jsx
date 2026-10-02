import React, { useEffect, useState } from "react";
import axios from "axios";
import { ArrowLeftIcon, ArrowRightIcon, CheckCircleIcon, ClockIcon } from "./Icons";

export function LessonView({ courseId, lessonId, apiUrl, token, onNavigate, showToast, onActivityCompleted }) {
  const [lesson, setLesson] = useState(null);
  const [loading, setLoading] = useState(true);
  const [marking, setMarking] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchLesson();
  }, [lessonId]);

  const fetchLesson = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${apiUrl}/api/lessons/${lessonId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setLesson(res.data);
    } catch (err) {
      console.error("Lesson fetch error:", err);
      if (showToast) {
        showToast("Could not load lesson.", "error");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleComplete = async () => {
    setMarking(true);
    try {
      const res = await axios.post(
        `${apiUrl}/api/lessons/${lessonId}/complete`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setLesson((prev) => ({ ...prev, is_completed: true }));
      if (showToast) {
        showToast(`Lesson completed! Course progress: ${res.data.course_progress}%`, "success");
      }
      if (onActivityCompleted) {
        onActivityCompleted(res.data);
      }
    } catch (err) {
      console.error("Complete lesson error:", err);
      if (showToast) {
        showToast("Error updating lesson progress.", "error");
      }
    } finally {
      setMarking(false);
    }
  };

  const copyCode = (code) => {
    if (!code) return;
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) {
    return (
      <div className="view-loading-state">
        <div className="spinner" />
        <p>Loading lesson...</p>
      </div>
    );
  }

  if (!lesson) {
    return (
      <div className="empty-card-prompt">
        <h3>Lesson not found</h3>
        <button
          type="button"
          className="primary-button"
          onClick={() => onNavigate(`/courses/${courseId}`)}
        >
          ← Return to Course
        </button>
      </div>
    );
  }

  return (
    <div className="lesson-view-content">
      {/* Navigation Breadcrumbs */}
      <div className="lesson-top-nav">
        <button
          type="button"
          className="back-link-btn"
          onClick={() => onNavigate(`/courses/${courseId}`)}
        >
          <ArrowLeftIcon size={14} />
          <span>Back to {lesson.course_title || "Course"}</span>
        </button>

        <span className="module-badge-tag">{lesson.module_title}</span>
      </div>

      {/* Main Lesson Card */}
      <article className="lesson-card">
        <header className="lesson-header">
          <div className="lesson-meta-bar">
            <span className="lesson-step">Lesson {lesson.order}</span>
            <span className="lesson-time">
              <ClockIcon size={13} />
              {lesson.duration}
            </span>
            {lesson.is_completed && (
              <span className="lesson-done-pill">✓ Completed</span>
            )}
          </div>
          <h1>{lesson.title}</h1>
        </header>

        {/* Section 1: Explanation */}
        <div className="lesson-section">
          <h3>Core Concept & Explanation</h3>
          <p className="lesson-explanation-text">{lesson.explanation}</p>
        </div>

        {/* Section 2: Code / Examples */}
        {lesson.examples && (
          <div className="lesson-section">
            <div className="code-header">
              <span>Code Example</span>
              <button
                type="button"
                className="copy-btn"
                onClick={() => copyCode(lesson.examples)}
              >
                {copied ? "Copied! ✓" : "Copy Code"}
              </button>
            </div>
            <pre className="code-block">
              <code>{lesson.examples}</code>
            </pre>
          </div>
        )}

        {/* Section 3: Important Points */}
        {lesson.important_points && lesson.important_points.length > 0 && (
          <div className="lesson-section takeaways-section">
            <h3>Key Takeaways & Best Practices</h3>
            <ul className="takeaways-list">
              {lesson.important_points.map((point, index) => (
                <li key={index}>
                  <span className="bullet-check">✓</span>
                  <span>{point}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Lesson Actions Footer */}
        <footer className="lesson-footer">
          <div className="footer-left">
            {lesson.prev_lesson_id ? (
              <button
                type="button"
                className="secondary-button"
                onClick={() => onNavigate(`/courses/${courseId}/lessons/${lesson.prev_lesson_id}`)}
              >
                <ArrowLeftIcon size={14} />
                <span>Previous Lesson</span>
              </button>
            ) : (
              <button
                type="button"
                className="secondary-button"
                onClick={() => onNavigate(`/courses/${courseId}`)}
              >
                ← Course Overview
              </button>
            )}
          </div>

          <div className="footer-right">
            <button
              type="button"
              className={`complete-lesson-btn ${lesson.is_completed ? "completed" : "primary-button"}`}
              onClick={handleComplete}
              disabled={marking || lesson.is_completed}
            >
              {lesson.is_completed ? (
                <>
                  <CheckCircleIcon size={16} />
                  <span>Completed ✓</span>
                </>
              ) : marking ? (
                "Saving..."
              ) : (
                "Mark as Complete ✓"
              )}
            </button>

            {lesson.next_lesson_id ? (
              <button
                type="button"
                className="primary-button"
                onClick={() => onNavigate(`/courses/${courseId}/lessons/${lesson.next_lesson_id}`)}
              >
                <span>Next Lesson</span>
                <ArrowRightIcon size={14} />
              </button>
            ) : (
              <button
                type="button"
                className="primary-button finish-course-btn"
                onClick={() => onNavigate(`/courses/${courseId}`)}
              >
                <span>Go to Quizzes →</span>
              </button>
            )}
          </div>
        </footer>
      </article>
    </div>
  );
}

