import React, { useEffect, useState } from "react";
import axios from "axios";
import { ScoreRing } from "./ScoreRing";
import { AwardIcon, BookOpenIcon, ClockIcon, FireIcon } from "./Icons";

export function LearningView({ apiUrl, token, onNavigate, showToast }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLearningDashboard();
  }, []);

  const fetchLearningDashboard = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${apiUrl}/api/learning/dashboard`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setData(res.data);
    } catch (err) {
      console.error("Learning dashboard error:", err);
      if (showToast) {
        showToast("Error loading learning dashboard.", "error");
      }
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="view-loading-state">
        <div className="spinner" />
        <p>Loading your career learning journey...</p>
      </div>
    );
  }

  const overallProgress = data?.overall_progress || 0;
  const currentCourses = data?.current_courses || [];
  const recommendedCourses = data?.recommended_courses || [];
  const recentActivity = data?.recent_activity || [];
  const quizPerf = data?.quiz_performance || {
    average_score: 0,
    quizzes_completed: 0,
    highest_score: 0,
    recent_scores: [],
  };

  return (
    <div className="learning-view-content">
      <section className="page-heading">
        <div>
          <span className="eyebrow">CAREER ADVANCEMENT DASHBOARD</span>
          <h1>My Learning Journey</h1>
          <p>
            Track your course progress, review recent quiz attempts, and bridge skill gaps detected from
            your resume analysis.
          </p>
        </div>
      </section>

      {/* Top Hero Stats */}
      <div className="learning-hero-grid">
        {/* Large Overall Progress Indicator */}
        <div className="learning-hero-card progress-hero">
          <div className="hero-ring-side">
            <ScoreRing
              value={overallProgress}
              label=""
              size={120}
              color="#0f8a5b"
              sublabel="Complete"
            />
          </div>
          <div className="hero-text-side">
            <span className="mini-label">OVERALL COMPLETION</span>
            <h2>{overallProgress}% Mastered</h2>
            <p>
              Your cumulative progress across all enrolled courses and interactive lesson modules.
            </p>
            <div className="mini-stats-inline">
              <div>
                <strong>{currentCourses.length}</strong>
                <span>Enrolled</span>
              </div>
              <div>
                <strong>
                  {currentCourses.filter((c) => c.progress_percentage >= 100).length}
                </strong>
                <span>Completed</span>
              </div>
              <div>
                <strong>{quizPerf.quizzes_completed}</strong>
                <span>Quizzes Passed</span>
              </div>
            </div>
          </div>
        </div>

        {/* Quiz Performance Summary Card */}
        <div className="learning-hero-card quiz-perf-hero">
          <div className="card-top-icon">
            <AwardIcon size={24} />
          </div>
          <span className="mini-label">QUIZ PERFORMANCE</span>
          <div className="quiz-stats-row">
            <div className="q-stat">
              <span>Average Score</span>
              <strong>{quizPerf.average_score}%</strong>
            </div>
            <div className="q-stat">
              <span>Highest Score</span>
              <strong className="text-success">{quizPerf.highest_score}%</strong>
            </div>
            <div className="q-stat">
              <span>Assessments</span>
              <strong>{quizPerf.quizzes_completed}</strong>
            </div>
          </div>
          <p className="card-hint">
            Quizzes validate your skills and demonstrate competence on your ResumeAI profile.
          </p>
        </div>
      </div>

      {/* Main Two Column Layout */}
      <div className="learning-sections-grid">
        {/* LEFT COLUMN: In-Progress Courses & Recommended */}
        <div className="learning-column">
          {/* Section: Current Courses */}
          <section className="learning-panel">
            <div className="panel-header">
              <div>
                <span className="section-kicker">ACTIVE STUDY</span>
                <h2>Current Courses</h2>
              </div>
              <span className="badge-count">{currentCourses.length} In Progress</span>
            </div>

            {currentCourses.length > 0 ? (
              <div className="active-courses-stack">
                {currentCourses.map((c) => (
                  <div key={c.id} className="active-course-box">
                    <div className="course-box-top">
                      <div>
                        <span className="badge-difficulty small">{c.difficulty}</span>
                        <h3>{c.title}</h3>
                      </div>
                      <span className="progress-percentage-pill">{c.progress_percentage}%</span>
                    </div>

                    <div className="horizontal-progress-bar">
                      <div className="bar-fill" style={{ width: `${c.progress_percentage}%` }} />
                    </div>

                    <div className="course-box-footer">
                      <span className="lessons-tally">
                        {c.completed_lessons} of {c.total_lessons} lessons completed
                      </span>
                      <button
                        type="button"
                        className="primary-button small"
                        onClick={() => onNavigate(`/courses/${c.id}`)}
                      >
                        Continue Learning →
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-card-prompt">
                <BookOpenIcon size={28} />
                <p>You have not enrolled in any courses yet.</p>
                <button
                  type="button"
                  className="primary-button small"
                  onClick={() => onNavigate("/courses")}
                >
                  Browse Course Catalog →
                </button>
              </div>
            )}
          </section>

          {/* Section: Recommended Courses */}
          <section className="learning-panel">
            <div className="panel-header">
              <div>
                <span className="section-kicker">SKILL-GAP RECOMMENDATIONS</span>
                <h2>Recommended For Your Career</h2>
              </div>
            </div>
            <p className="section-subtitle">
              Based on missing skills detected from your target job description analyses:
            </p>

            <div className="recommended-list-compact">
              {recommendedCourses.map((rc) => (
                <div key={rc.id} className="rec-row-item">
                  <div className="rec-row-left">
                    <span className="badge-category">{rc.category}</span>
                    <h4>{rc.title}</h4>
                    {rc.matched_missing_skills && rc.matched_missing_skills.length > 0 && (
                      <div className="chips">
                        {rc.matched_missing_skills.map((s) => (
                          <span key={s} className="chip success small">
                            {s}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  <button
                    type="button"
                    className="secondary-button small"
                    onClick={() => onNavigate(`/courses/${rc.id}`)}
                  >
                    Start Course →
                  </button>
                </div>
              ))}
            </div>
          </section>
        </div>

        {/* RIGHT COLUMN: Recent Activity & Recent Quiz Scores */}
        <div className="learning-column">
          {/* Recent Activity */}
          <section className="learning-panel">
            <div className="panel-header">
              <div>
                <span className="section-kicker">TIMELINE</span>
                <h2>Recent Activity</h2>
              </div>
            </div>

            {recentActivity.length > 0 ? (
              <div className="activity-timeline">
                {recentActivity.map((act, idx) => (
                  <div key={idx} className="timeline-entry">
                    <div className="timeline-dot">✓</div>
                    <div className="timeline-content">
                      <strong>{act.title}</strong>
                      <small>{act.subtitle}</small>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-activity">
                Activity will appear as you complete lessons and quizzes.
              </div>
            )}
          </section>

          {/* Recent Quiz Scores */}
          <section className="learning-panel">
            <div className="panel-header">
              <div>
                <span className="section-kicker">EXAMINATION HISTORY</span>
                <h2>Recent Quiz Scores</h2>
              </div>
            </div>

            {quizPerf.recent_scores && quizPerf.recent_scores.length > 0 ? (
              <div className="recent-scores-table-wrap">
                <table className="custom-table">
                  <thead>
                    <tr>
                      <th>Quiz Name</th>
                      <th>Score</th>
                      <th>Result</th>
                    </tr>
                  </thead>
                  <tbody>
                    {quizPerf.recent_scores.map((s) => (
                      <tr key={s.id}>
                        <td><strong>{s.quiz_title}</strong></td>
                        <td>{s.score}/{s.total} ({s.percentage}%)</td>
                        <td>
                          <span className={`status-badge ${s.passed ? "badge-success" : "badge-warning"}`}>
                            {s.passed ? "Passed" : "Needs Retake"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="empty-activity">
                No quizzes taken yet. Complete course modules to take quizzes.
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}

