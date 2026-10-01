import React, { useEffect, useState } from "react";
import axios from "axios";
import { DownloadIcon, ResumeIcon } from "./Icons";

export function ReportsView({ apiUrl, token, onNavigate, showToast }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [downloadingId, setDownloadingId] = useState(null);
  const [selectedReport, setSelectedReport] = useState(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${apiUrl}/api/resume/history`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setHistory(res.data.history || []);
    } catch (err) {
      console.error("History fetch error:", err);
      if (showToast) showToast("Could not load reports history.", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPdf = async (analysisId) => {
    setDownloadingId(analysisId);
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
      if (showToast) showToast("PDF Report downloaded successfully!", "success");
    } catch (err) {
      console.error("PDF download error:", err);
      if (showToast) showToast("Failed to download PDF report.", "error");
    } finally {
      setDownloadingId(null);
    }
  };

  const openReportDetails = async (id) => {
    try {
      const res = await axios.get(`${apiUrl}/api/resume/report/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setSelectedReport(res.data);
    } catch (err) {
      console.error("Report detail error:", err);
    }
  };

  if (loading) {
    return (
      <div className="view-loading-state">
        <div className="spinner" />
        <p>Loading your resume analysis reports...</p>
      </div>
    );
  }

  return (
    <div className="reports-view-content">
      <section className="page-heading">
        <div>
          <span className="eyebrow">SAVED ASSESSMENTS & AUDITS</span>
          <h1>Resume Analysis Reports</h1>
          <p>
            Access your full audit history, review ATS scores and detected skill gaps, and export
            executive-ready PDF reports for any analysis.
          </p>
        </div>
      </section>

      {history.length > 0 ? (
        <div className="reports-table-card">
          <table className="custom-table reports-table">
            <thead>
              <tr>
                <th>Resume Document</th>
                <th>ATS Score</th>
                <th>Job Match</th>
                <th>Skill Gaps</th>
                <th>Date Generated</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {history.map((item) => {
                const dateFormatted = item.created_at
                  ? new Date(item.created_at).toLocaleDateString(undefined, {
                      year: "numeric",
                      month: "short",
                      day: "numeric",
                    })
                  : "Recent";

                return (
                  <tr key={item.id}>
                    <td>
                      <div className="table-doc-cell">
                        <ResumeIcon size={16} className="text-muted" />
                        <div>
                          <strong>{item.filename}</strong>
                          <small>{item.pages || 1} page(s)</small>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className="table-score-pill ats">{item.ats_score || 0} / 100</span>
                    </td>
                    <td>
                      <span className="table-score-pill match">
                        {item.job_match_percentage || 0}%
                      </span>
                    </td>
                    <td>
                      <span className="badge-count">
                        {item.missing_skills?.length || 0} gaps detected
                      </span>
                    </td>
                    <td>
                      <span className="text-muted">{dateFormatted}</span>
                    </td>
                    <td>
                      <div className="table-actions">
                        <button
                          type="button"
                          className="table-btn secondary"
                          onClick={() => openReportDetails(item.id)}
                        >
                          View Details
                        </button>
                        <button
                          type="button"
                          className="table-btn primary"
                          onClick={() => handleDownloadPdf(item.id)}
                          disabled={downloadingId === item.id}
                        >
                          <DownloadIcon size={13} />
                          <span>{downloadingId === item.id ? "PDF..." : "PDF"}</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="empty-card-prompt">
          <ResumeIcon size={32} />
          <h3>No Analysis Reports Yet</h3>
          <p>
            Upload your resume against a job description in the Resume Analyzer to generate your first ATS
            report.
          </p>
          <button
            type="button"
            className="primary-button"
            onClick={() => onNavigate("/analyzer")}
          >
            Start Resume Analysis →
          </button>
        </div>
      )}

      {/* REPORT DETAIL MODAL */}
      {selectedReport && (
        <div className="modal-backdrop" onClick={() => setSelectedReport(null)}>
          <div className="modal-dialog modal-large" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <span className="eyebrow">ANALYSIS AUDIT REPORT</span>
                <h3>{selectedReport.filename}</h3>
              </div>
              <button type="button" className="close-btn" onClick={() => setSelectedReport(null)}>
                ✕
              </button>
            </div>

            <div className="modal-scroll-body">
              <div className="modal-scores-row">
                <div className="modal-score-box">
                  <span>ATS Resume Score</span>
                  <strong>{selectedReport.ats_score} / 100</strong>
                </div>
                <div className="modal-score-box">
                  <span>Job Match Score</span>
                  <strong>{selectedReport.job_match_percentage}%</strong>
                </div>
              </div>

              <div className="modal-section-block">
                <h4>Matched Skills ({selectedReport.matched_skills?.length || 0})</h4>
                <div className="chips">
                  {selectedReport.matched_skills?.map((s) => (
                    <span key={s} className="chip success">
                      {s}
                    </span>
                  ))}
                </div>
              </div>

              <div className="modal-section-block">
                <h4>Missing Skills / Gaps ({selectedReport.missing_skills?.length || 0})</h4>
                <div className="chips">
                  {selectedReport.missing_skills?.map((s) => (
                    <span key={s} className="chip warning">
                      {s}
                    </span>
                  ))}
                </div>
              </div>

              {selectedReport.ai_suggestions && (
                <div className="modal-section-block">
                  <h4>Gemini AI Recommendations</h4>
                  <div className="ai-result modal-ai">{selectedReport.ai_suggestions}</div>
                </div>
              )}

              {selectedReport.recommended_courses && selectedReport.recommended_courses.length > 0 && (
                <div className="modal-section-block">
                  <h4>Recommended Courses to Bridge Gaps</h4>
                  <div className="modal-recs-grid">
                    {selectedReport.recommended_courses.map((rc) => (
                      <div key={rc.id} className="rec-row-item">
                        <div>
                          <strong>{rc.title}</strong>
                          <small>{rc.estimated_duration} • {rc.difficulty}</small>
                        </div>
                        <button
                          type="button"
                          className="primary-button small"
                          onClick={() => {
                            setSelectedReport(null);
                            onNavigate(`/courses/${rc.id}`);
                          }}
                        >
                          Start Course →
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="modal-actions">
              <button
                type="button"
                className="secondary-button"
                onClick={() => setSelectedReport(null)}
              >
                Close
              </button>
              <button
                type="button"
                className="primary-button"
                onClick={() => handleDownloadPdf(selectedReport.id)}
              >
                <DownloadIcon size={14} />
                <span>Download Official PDF</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

