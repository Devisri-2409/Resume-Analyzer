import React, { useEffect, useState } from "react";
import axios from "axios";
import { ScoreRing } from "./ScoreRing";
import { ArrowRightIcon, BookOpenIcon, CheckCircleIcon, ClockIcon, FireIcon, ResumeIcon } from "./Icons";

export function DashboardView({ user, onNavigate, apiUrl, token, showToast, refreshKey, onActivityCompleted }) {
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState(null);
  const [latestResume, setLatestResume] = useState(null);
  const [resumeHistory, setResumeHistory] = useState([]);

  useEffect(() => {
    fetchDashboardData();
  }, [refreshKey]);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const [learningRes, latestRes, historyRes] = await Promise.all([
        axios.get(`${apiUrl}/api/learning/dashboard`, { headers }).catch(() => ({ data: null })),
        axios.get(`${apiUrl}/api/resume/latest`, { headers }).catch(() => ({ data: { latest: null } })),
        axios.get(`${apiUrl}/api/resume/history`, { headers }).catch(() => ({ data: { history: [] } })),
      ]);

      setDashboardData(learningRes.data);
      setLatestResume(latestRes.data?.latest || null);
      setResumeHistory(historyRes.data?.history || []);
    } catch (err) {
      console.error("Dashboard fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="view-loading-state">
        <div className="spinner" />
        <p>Loading your career intelligence dashboard...</p>
      </div>
    );
  }

  const missingSkills = latestResume?.missing_skills || [];
  const currentCourses = dashboardData?.current_courses || [];
  const recommendedCourses = dashboardData?.recommended_courses || [];
  const recentActivity = dashboardData?.recent_activity || [];
  const quizPerf = dashboardData?.quiz_performance || { average_score: 0, quizzes_completed: 0, highest_score: 0 };
  const overallProgress = dashboardData?.overall_progress || 0;

  return (
    <div className="dashboard-view-content">
      {/* Welcome Banner */}
      <section className="welcome-banner">
        <div className="welcome-text">
          <span className="eyebrow">CAREER INTELLIGENCE & ACCELERATION</span>
          <h1>Welcome back, {user?.full_name?.split(" ")[0]}</h1>
          <p>
            Track your ATS resume readiness, bridge identified skill gaps with targeted learning modules,
            and monitor your career progression.
          </p>
        </div>
        <div className="welcome-actions">
          <button
            type="button"
            className="primary-button cta-btn"
            onClick={() => onNavigate("/analyzer")}
          >
            <ResumeIcon size={16} />
            <span>Analyze Resume</span>
          </button>
          <button
            type="button"
            className="secondary-button"
            onClick={() => onNavigate("/courses")}
          >
            <BookOpenIcon size={16} />
            <span>Browse Courses</span>
          </button>
        </div>
      </section>

      {/* Grid: Resume Overview + Learning Overview */}
      <div className="dashboard-grid-two-column">
        {/* LEFT COLUMN: RESUME OVERVIEW */}
        <div className="dashboard-col">
          <div className="section-card-header">
            <div>
              <span className="section-kicker">RESUME INTELLIGENCE</span>
              <h2>Resume Overview</h2>
            </div>
            {latestResume && (
              <button
                type="button"
                className="link-subtle"
                onClick={() => onNavigate("/reports")}
              >
                View History →
              </button>
            )}
          </div>

          {latestResume ? (
            <div className="resume-metrics-panel">
              <div className="metrics-split">
                <div className="metric-box">
                  <ScoreRing
                    value={latestResume.ats_score}
                    label="Latest ATS Score"
                    size={90}
                    color="#0f8a5b"
                  />
                  <div className="metric-detail">
                    <strong>ATS Compatibility</strong>
                    <span>Standard formatting & structure</span>
                  </div>
                </div>

                <div className="metric-box">
                  <ScoreRing
                    value={latestResume.job_match_percentage}
                    label="Job Match Score"
                    size={90}
                    color="#14734e"
                  />
                  <div className="metric-detail">
                    <strong>Role Alignment</strong>
                    <span>Skills aligned with target job</span>
                  </div>
                </div>
              </div>

              {/* Missing Skills Alert */}
              <div className="missing-skills-section">
                <div className="missing-skills-title">
                  <span className="alert-dot" />
                  <strong>Identified Skill Gaps ({missingSkills.length})</strong>
                </div>
                <div className="chips">
                  {missingSkills.length > 0 ? (
                    missingSkills.slice(0, 8).map((sk) => (
                      <span key={sk} className="chip warning">
                        {sk}
                      </span>
                    ))
                  ) : (
                    <span className="empty-state">No skill gaps detected in latest analysis.</span>
                  )}
                </div>
                {missingSkills.length > 0 && (
                  <p className="missing-skills-note">
                    Bridge these gaps with targeted courses recommended below.
                  </p>
                )}
              </div>

              {/* Recent Analyses List */}
              <div className="recent-analyses-mini">
                <strong>Recent Analyses</strong>
                <div className="history-mini-list">
                  {resumeHistory.slice(0, 3).map((item) => (
                    <div key={item.id} className="history-mini-row" onClick={() => onNavigate("/reports")}>
                      <div className="file-col">
                        <ResumeIcon size={14} className="text-muted" />
                        <span className="filename-text">{item.filename}</span>
                      </div>
                      <div className="scores-col">
                        <span className="score-pill">ATS: {item.ats_score}%</span>
                        <span className="score-pill accent">Match: {item.job_match_percentage}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="empty-card-prompt">
              <div className="empty-icon-wrap">
                <ResumeIcon size={32} />
              </div>
              <h3>No Resume Analyzed Yet</h3>
              <p>
                Upload your resume against a target job description to get your ATS score, detected skills,
                and personalized course recommendations.
              </p>
              <button
                type="button"
                className="primary-button"
                onClick={() => onNavigate("/analyzer")}
              >
                Upload & Analyze Resume →
              </button>
            </div>
          )}
        </div>

        {/* RIGHT COLUMN: LEARNING OVERVIEW */}
        <div className="dashboard-col">
          <div className="section-card-header">
            <div>
              <span className="section-kicker">CAREER ACCELERATION</span>
              <h2>Learning Overview</h2>
            </div>
            <button
              type="button"
              className="link-subtle"
              onClick={() => onNavigate("/learning")}
            >
              My Learning →
            </button>
          </div>

          <div className="learning-overview-panel">
            {/* Overall Progress Stat Card */}
            <div className="overall-progress-card">
              <div className="progress-info">
                <span className="mini-label">OVERALL LEARNING PROGRESS</span>
                <div className="progress-number-row">
                  <h3>{overallProgress}%</h3>
                  <span>across enrolled courses</span>
                </div>
                <div className="horizontal-progress-bar">
                  <div className="bar-fill" style={{ width: `${overallProgress}%` }} />
                </div>
              </div>
              <div className="quiz-mini-stats">
                <div className="quiz-mini-stat">
                  <span>Quizzes Passed</span>
                  <strong>{quizPerf.quizzes_completed}</strong>
                </div>
                <div className="quiz-mini-stat">
                  <span>Avg Score</span>
                  <strong>{quizPerf.average_score}%</strong>
                </div>
              </div>
            </div>

            {/* Current Courses Progress Section */}
            <div className="current-courses-section">
              <div className="sub-heading">
                <strong>COURSE PROGRESS</strong>
                <span className="badge-count">{currentCourses.length} in progress</span>
              </div>

              {currentCourses.length > 0 ? (
                <div className="course-progress-list">
                  {currentCourses.map((course) => (
                    <div
                      key={course.id}
                      className="course-progress-row"
                      onClick={() => onNavigate(`/courses/${course.id}`)}
                    >
                      <div className="course-progress-header">
                        <span className="course-name">{course.title}</span>
                        <span className="progress-val">{course.progress_percentage}%</span>
                      </div>
                      <div className="horizontal-progress-bar small">
                        <div
                          className="bar-fill"
                          style={{ width: `${course.progress_percentage}%` }}
                        />
                      </div>
                      <div className="course-progress-sub">
                        <span>
                          {course.completed_lessons} / {course.total_lessons} lessons completed
                        </span>
                        <span className="continue-link">Continue →</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-courses-state">
                  <p>You have not enrolled in any courses yet.</p>
                  <button
                    type="button"
                    className="link-button"
                    onClick={() => onNavigate("/courses")}
                  >
                    Explore Courses Catalog →
                  </button>
                </div>
              )}
            </div>

            {/* Recently Completed Lessons / Activity */}
            {recentActivity.length > 0 && (
              <div className="recent-activity-section">
                <strong>Recent Learning Activity</strong>
                <div className="activity-list">
                  {recentActivity.slice(0, 3).map((act, idx) => (
                    <div key={idx} className="activity-item">
                      <span className="activity-icon">✓</span>
                      <div>
                        <strong>{act.title}</strong>
                        <small>{act.subtitle}</small>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* SKILL-GAP BASED RECOMMENDED COURSES ROW */}
      <section className="recommendations-banner-section">
        <div className="section-card-header">
          <div>
            <span className="section-kicker">BRIDGING IDENTIFIED GAPS</span>
            <h2>Recommended Courses for You</h2>
            <p className="section-desc">
              Tailored learning modules matched to the missing skills detected from your resume analysis.
            </p>
          </div>
          <button
            type="button"
            className="secondary-button"
            onClick={() => onNavigate("/courses")}
          >
            All Courses ({dashboardData?.courses_total || 10}) →
          </button>
        </div>

        <div className="recommendations-cards-grid">
          {recommendedCourses.length > 0 ? (
            recommendedCourses.map((rc) => (
              <div key={rc.id} className="recommended-course-card">
                <div className="card-top-row">
                  <span className="badge-category">{rc.category || "Development"}</span>
                  <span className="badge-difficulty">{rc.difficulty}</span>
                </div>
                <h3>{rc.title}</h3>
                <p className="course-card-desc">{rc.description}</p>

                {rc.matched_missing_skills && rc.matched_missing_skills.length > 0 && (
                  <div className="skills-gap-tags">
                    <span className="gap-tag-label">Bridges:</span>
                    {rc.matched_missing_skills.map((s) => (
                      <span key={s} className="chip success small">
                        {s}
                      </span>
                    ))}
                  </div>
                )}

                <div className="card-footer-action">
                  <div className="meta-info">
                    <ClockIcon size={14} />
                    <span>{rc.estimated_duration}</span>
                  </div>
                  <button
                    type="button"
                    className="primary-button small"
                    onClick={() => onNavigate(`/courses/${rc.id}`)}
                  >
                    Start Course →
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div className="empty-state-banner">
              <p>No specific skill gaps currently detected. Browse our complete catalog.</p>
              <button
                type="button"
                className="primary-button"
                onClick={() => onNavigate("/courses")}
              >
                Browse Course Catalog
              </button>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

