import React, { useEffect, useState } from "react";
import axios from "axios";
import { ArrowLeftIcon, ArrowRightIcon, AwardIcon, CheckCircleIcon } from "./Icons";

export function QuizView({ courseId, quizId, apiUrl, token, onNavigate, showToast }) {
  const [quiz, setQuiz] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    fetchQuiz();
  }, [quizId]);

  const fetchQuiz = async () => {
    setLoading(true);
    setResult(null);
    setSelectedAnswers({});
    setCurrentIndex(0);
    try {
      const res = await axios.get(`${apiUrl}/api/quizzes/${quizId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setQuiz(res.data);
    } catch (err) {
      console.error("Quiz fetch error:", err);
      if (showToast) {
        showToast("Could not load quiz questions.", "error");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSelectOption = (questionId, optionId) => {
    if (result) return; // Prevent selection after submission
    setSelectedAnswers((prev) => ({
      ...prev,
      [questionId]: optionId,
    }));
  };

  const handleSubmit = async () => {
    if (!quiz || !quiz.questions) return;
    const answeredCount = Object.keys(selectedAnswers).length;
    if (answeredCount < quiz.questions.length) {
      const proceed = window.confirm(
        `You have answered ${answeredCount} of ${quiz.questions.length} questions. Do you want to submit anyway?`
      );
      if (!proceed) return;
    }

    setSubmitting(true);
    try {
      const res = await axios.post(
        `${apiUrl}/api/quizzes/${quizId}/submit`,
        { answers: selectedAnswers },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setResult(res.data);
      if (showToast) {
        if (res.data.passed) {
          showToast(`Congratulations! You passed with ${res.data.percentage}%!`, "success");
        } else {
          showToast(`Quiz completed: ${res.data.percentage}%. Review answers below.`, "info");
        }
      }
    } catch (err) {
      console.error("Quiz submit error:", err);
      if (showToast) {
        showToast("Error submitting quiz. Please try again.", "error");
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleRetry = () => {
    setResult(null);
    setSelectedAnswers({});
    setCurrentIndex(0);
  };

  if (loading) {
    return (
      <div className="view-loading-state">
        <div className="spinner" />
        <p>Loading assessment quiz...</p>
      </div>
    );
  }

  if (!quiz || !quiz.questions || quiz.questions.length === 0) {
    return (
      <div className="empty-card-prompt">
        <h3>Quiz not available</h3>
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

  const questions = quiz.questions;
  const currentQ = questions[currentIndex];
  const optionLabels = ["A", "B", "C", "D", "E"];

  return (
    <div className="quiz-view-content">
      {/* Top Breadcrumb */}
      <div className="quiz-top-nav">
        <button
          type="button"
          className="back-link-btn"
          onClick={() => onNavigate(`/courses/${courseId}`)}
        >
          <ArrowLeftIcon size={14} />
          <span>Back to {quiz.course_title || "Course"}</span>
        </button>
        <span className="quiz-passing-tag">Passing Score: {quiz.passing_score}%</span>
      </div>

      {/* QUIZ IN-PROGRESS VIEW */}
      {!result ? (
        <div className="quiz-card-main">
          {/* Header & Progress */}
          <div className="quiz-card-header">
            <div>
              <span className="mini-label">ASSESSMENT</span>
              <h2>{quiz.title}</h2>
              <p className="quiz-subtitle">{quiz.description}</p>
            </div>
            <div className="question-counter">
              Question <strong>{currentIndex + 1}</strong> of {questions.length}
            </div>
          </div>

          {/* Progress track */}
          <div className="horizontal-progress-bar">
            <div
              className="bar-fill"
              style={{ width: `${((currentIndex + 1) / questions.length) * 100}%` }}
            />
          </div>

          {/* Question Dots Bar */}
          <div className="question-dots-nav">
            {questions.map((q, idx) => {
              const isAnswered = selectedAnswers[q.id] !== undefined;
              const isCurrent = idx === currentIndex;
              return (
                <button
                  key={q.id}
                  type="button"
                  className={`dot-btn ${isCurrent ? "current" : ""} ${isAnswered ? "answered" : ""}`}
                  onClick={() => setCurrentIndex(idx)}
                  title={`Question ${idx + 1}`}
                >
                  {idx + 1}
                </button>
              );
            })}
          </div>

          {/* Current Question Body */}
          <div className="question-body">
            <h3 className="question-text">{currentQ.question_text}</h3>

            <div className="options-list">
              {currentQ.options.map((opt, optIdx) => {
                const isSelected = selectedAnswers[currentQ.id] === opt.id;
                return (
                  <div
                    key={opt.id}
                    className={`option-item ${isSelected ? "selected" : ""}`}
                    onClick={() => handleSelectOption(currentQ.id, opt.id)}
                  >
                    <span className="option-label-badge">{optionLabels[optIdx] || optIdx + 1}</span>
                    <span className="option-text">{opt.option_text}</span>
                    <span className="radio-circle">{isSelected ? "●" : "○"}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Bottom Actions */}
          <div className="quiz-card-footer">
            <button
              type="button"
              className="secondary-button"
              onClick={() => setCurrentIndex((prev) => Math.max(0, prev - 1))}
              disabled={currentIndex === 0}
            >
              <ArrowLeftIcon size={14} />
              <span>Previous</span>
            </button>

            <div className="footer-right-actions">
              {currentIndex < questions.length - 1 ? (
                <button
                  type="button"
                  className="primary-button"
                  onClick={() => setCurrentIndex((prev) => Math.min(questions.length - 1, prev + 1))}
                >
                  <span>Next Question</span>
                  <ArrowRightIcon size={14} />
                </button>
              ) : (
                <button
                  type="button"
                  className="primary-button submit-quiz-btn"
                  onClick={handleSubmit}
                  disabled={submitting}
                >
                  {submitting ? "Grading..." : "Submit Quiz →"}
                </button>
              )}
            </div>
          </div>
        </div>
      ) : (
        /* QUIZ RESULTS VIEW */
        <div className="quiz-results-container">
          <div className={`quiz-score-hero ${result.passed ? "passed" : "failed"}`}>
            <div className="score-hero-icon">
              {result.passed ? <AwardIcon size={38} /> : "!"}
            </div>
            <h2>{result.passed ? "Quiz Passed Successfully!" : "Needs Improvement"}</h2>
            <p>
              {result.passed
                ? "Outstanding job! You demonstrated mastery of the core concepts."
                : "You did not meet the passing threshold. Review the answer explanations below and retry."}
            </p>

            <div className="score-summary-pills">
              <div className="summary-pill main">
                <span>Score</span>
                <strong>{result.score} / {result.total_questions}</strong>
              </div>
              <div className="summary-pill">
                <span>Percentage</span>
                <strong>{result.percentage}%</strong>
              </div>
              <div className="summary-pill">
                <span>Correct</span>
                <strong className="text-success">{result.correct_count}</strong>
              </div>
              <div className="summary-pill">
                <span>Incorrect</span>
                <strong className="text-danger">{result.incorrect_count}</strong>
              </div>
            </div>

            <div className="score-hero-actions">
              <button type="button" className="secondary-button" onClick={handleRetry}>
                Retry Quiz
              </button>
              <button
                type="button"
                className="primary-button"
                onClick={() => onNavigate(`/courses/${courseId}`)}
              >
                Back to Course →
              </button>
            </div>
          </div>

          {/* Detailed Question Review */}
          <div className="quiz-review-section">
            <div className="review-header">
              <h3>Answer Breakdown & Explanations</h3>
              <span>
                {result.correct_count} of {result.total_questions} correct
              </span>
            </div>

            <div className="review-cards-list">
              {result.breakdown?.map((item, idx) => (
                <div
                  key={idx}
                  className={`review-card ${item.is_correct ? "correct" : "incorrect"}`}
                >
                  <div className="review-card-top">
                    <span className="q-number">Question {idx + 1}</span>
                    <span className={`result-tag ${item.is_correct ? "tag-success" : "tag-danger"}`}>
                      {item.is_correct ? "✓ Correct" : "✕ Incorrect"}
                    </span>
                  </div>

                  <h4>{item.question_text}</h4>

                  <div className="review-answers-grid">
                    <div className="answer-field">
                      <span className="field-label">Your Answer:</span>
                      <strong className={item.is_correct ? "text-success" : "text-danger"}>
                        {item.selected_option_text}
                      </strong>
                    </div>

                    {!item.is_correct && (
                      <div className="answer-field">
                        <span className="field-label">Correct Answer:</span>
                        <strong className="text-success">{item.correct_option_text}</strong>
                      </div>
                    )}
                  </div>

                  {item.explanation && (
                    <div className="explanation-box">
                      <span className="exp-label">Explanation:</span>
                      <p>{item.explanation}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

