import React, { useMemo, useState } from "react";
import axios from "axios";
import { ScoreRing } from "./ScoreRing";
import { ClockIcon, DownloadIcon } from "./Icons";

export function AnalyzerView({ apiUrl, token, onNavigate, showToast, onLogout }) {
  const [resume, setResume] = useState(null);
  const [jobDescription, setJobDescription] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [downloadingPdf, setDownloadingPdf] = useState(false);

  const fileSize = useMemo(() => {
    if (!resume) return "";
    return `${(resume.size / 1024 / 1024).toFixed(2)} MB`;
  }, [resume]);

  const analyzeResume = async () => {
    if (!resume) {
      setError("Please choose a PDF resume.");
      return;
    }

    if (!jobDescription.trim()) {
      setError("Please paste the job description.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    const formData = new FormData();
    formData.append("file", resume);
    formData.append("job_description", jobDescription);

    try {
      const response = await axios.post(`${apiUrl}/api/resume/analyze`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setResult(response.data);
      if (showToast) {
        showToast("Resume analyzed successfully! Skill gaps and course recommendations updated.", "success");
      }
    } catch (err) {
      if (err?.response?.status === 401) {
        onLogout();
        return;
      }
      setError(err?.response?.data?.detail || "Resume analysis failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPdf = async (analysisId) => {
    if (!analysisId) return;
    setDownloadingPdf(true);
    try {
      const response = await axios.get(`${apiUrl}/api/resume/report/${analysisId}/pdf`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: "blob",
      });

      const blob = new Blob([response.data], { type: "application/pdf" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `ResumeAI_Analysis_Report_${analysisId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      if (showToast) {
        showToast("PDF Report downloaded successfully!", "success");
      }
    } catch (err) {
      console.error("PDF download error:", err);
      if (showToast) {
        showToast("Failed to download PDF report. Please try again.", "error");
      }
    } finally {
      setDownloadingPdf(false);
    }
  };

  return (
    <div className="analyzer-view-content">
      <section className="page-heading">
        <div>
          <span className="eyebrow">RESUME INTELLIGENCE & GAP DETECTION</span>
          <h1>Analyze Your Resume</h1>
          <p>
            Upload your resume and compare it against your target job description to reveal ATS compatibility,
            keyword matches, and immediate skill-gap course recommendations.
          </p>
        </div>
      </section>

      <section className="upload-card">
        <div className="upload-grid">
          <div
            className={`drop-zone ${resume ? "has-file" : ""}`}
            onClick={() => document.getElementById("resume-input").click()}
          >
            <input
              id="resume-input"
              type="file"
              accept="application/pdf,.pdf"
              onChange={(e) => setResume(e.target.files?.[0] || null)}
              hidden
            />
            <div className="upload-icon">↑</div>
            <h3>{resume ? resume.name : "Upload your resume"}</h3>
            <p>
              {resume ? `${fileSize} • PDF selected` : "Drag and drop or click to browse"}
            </p>
            <span className="upload-hint">PDF only</span>
          </div>

          <div className="job-input">
            <label htmlFor="job-description">Target job description</label>
            <textarea
              id="job-description"
              placeholder="Paste the target job description or requirements here..."
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
            />
            <div className="textarea-footer">
              <span>{jobDescription.length} characters</span>
              <button
                className="primary-button analyze-button"
                onClick={analyzeResume}
                disabled={loading}
              >
                {loading ? "Analyzing Resume..." : "Analyze Resume →"}
              </button>
            </div>
          </div>
        </div>

        {error && <div className="form-error analysis-error">{error}</div>}
      </section>

      {loading && (
        <div className="loading-card">
          <div className="spinner" />
          <div>
            <strong>Analyzing your resume with Gemini AI...</strong>
            <span>Extracting skills, computing ATS score, and detecting skill gaps.</span>
          </div>
        </div>
      )}

      {result && !loading && (
        <section className="results-section">
          <div className="results-heading">
            <div>
              <span className="eyebrow">ANALYSIS COMPLETE</span>
              <h2>{result.filename}</h2>
            </div>
            <div className="results-heading-actions">
              <span className="page-badge">
                {result.pages} page{result.pages === 1 ? "" : "s"}
              </span>
              <button
                type="button"
                className="download-report-btn"
                onClick={() => handleDownloadPdf(result.analysis_id)}
                disabled={downloadingPdf}
              >
                <DownloadIcon size={15} />
                <span>{downloadingPdf ? "Generating PDF..." : "Download PDF Report"}</span>
              </button>
            </div>
          </div>

          <div className="metrics-grid">
            <div className="metric-card">
              <ScoreRing value={result.ats_score} label="ATS Score" />
              <div className="metric-copy">
                <strong>Resume Quality</strong>
                <span>Calculated based on standard sections, formatting, and keyword density.</span>
              </div>
            </div>

            <div className="metric-card">
              <ScoreRing value={result.job_match.job_match_percentage} label="Job Match" />
              <div className="metric-copy">
                <strong>Skill Alignment</strong>
                <span>Percentage of required skills found directly in your resume.</span>
              </div>
            </div>
          </div>

          <div className="result-grid">
            {/* Matched Skills */}
            <div className="result-card">
              <div className="card-title">
                <div>
                  <span className="section-kicker">SKILL MATCH</span>
                  <h3>Matched Skills</h3>
                </div>
                <span className="count-badge">{result.job_match.matched_skills.length}</span>
              </div>
              <div className="chips">
                {result.job_match.matched_skills.length ? (
                  result.job_match.matched_skills.map((skill) => (
                    <span className="chip success" key={skill}>
                      {skill}
                    </span>
                  ))
                ) : (
                  <span className="empty-state">No matching skills detected.</span>
                )}
              </div>
            </div>

            {/* Missing Skills */}
            <div className="result-card">
              <div className="card-title">
                <div>
                  <span className="section-kicker">SKILL GAP</span>
                  <h3>Missing Skills</h3>
                </div>
                <span className="count-badge">{result.job_match.missing_skills.length}</span>
              </div>
              <div className="chips">
                {result.job_match.missing_skills.length ? (
                  result.job_match.missing_skills.map((skill) => (
                    <span className="chip warning" key={skill}>
                      {skill}
                    </span>
                  ))
                ) : (
                  <span className="empty-state">No missing skills detected! Excellent match.</span>
                )}
              </div>
            </div>

            {/* Resume Profile / Detected Skills */}
            <div className="result-card full">
              <div className="card-title">
                <div>
                  <span className="section-kicker">RESUME PROFILE</span>
                  <h3>All Detected Skills</h3>
                </div>
                <span className="count-badge">{result.detected_skills.length}</span>
              </div>
              <div className="chips">
                {result.detected_skills.map((skill) => (
                  <span className="chip neutral" key={skill}>
                    {skill}
                  </span>
                ))}
              </div>
            </div>

            {/* AI Insights Card */}
            <div className="result-card full ai-card">
              <div className="ai-heading">
                <div className="ai-icon">✦</div>
                <div>
                  <span className="section-kicker">AI INSIGHTS</span>
                  <h3>Gemini Recommendations & Improvement Advice</h3>
                </div>
              </div>
              <div className="ai-result">{result.ai_suggestions}</div>
            </div>

            {/* SKILL-GAP BASED COURSE RECOMMENDATIONS DIRECTLY ON ANALYZER */}
            {result.recommended_courses && result.recommended_courses.length > 0 && (
              <div className="result-card full recommendations-card">
                <div className="card-title">
                  <div>
                    <span className="section-kicker">LEARNING RECOMMENDATIONS</span>
                    <h3>Recommended Courses to Bridge Your Missing Skills</h3>
                  </div>
                </div>
                <p className="card-subtitle">
                  We identified missing skills required for this job description. Start these courses to close the gap:
                </p>

                <div className="results-recs-grid">
                  {result.recommended_courses.map((course) => (
                    <div key={course.id} className="course-rec-mini-card">
                      <div className="rec-mini-top">
                        <span className="badge-difficulty">{course.difficulty}</span>
                        <div className="rec-meta">
                          <ClockIcon size={12} />
                          <span>{course.estimated_duration}</span>
                        </div>
                      </div>
                      <h4>{course.title}</h4>
                      <p>{course.description}</p>
                      {course.matched_gap && course.matched_gap.length > 0 && (
                        <div className="gap-badges">
                          <span className="gap-label">Covers Gap:</span>
                          {course.matched_gap.map((g) => (
                            <span key={g} className="chip success small">
                              {g}
                            </span>
                          ))}
                        </div>
                      )}
                      <button
                        type="button"
                        className="primary-button small full-w"
                        onClick={() => onNavigate(`/courses/${course.id}`)}
                      >
                        Start Course →
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </section>
      )}
    </div>
  );
}

