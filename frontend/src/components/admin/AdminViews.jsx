import React, { useEffect, useState, useMemo } from "react";
import axios from "axios";
import {
  AwardIcon,
  CheckCircleIcon,
  ClockIcon,
  CoursesIcon,
  DashboardIcon,
  FireIcon,
  LearningIcon,
  ProfileIcon,
  ReportsIcon,
  ResumeIcon,
} from "../Icons";

function AuthHeaders(token) {
  return { headers: { Authorization: `Bearer ${token}` } };
}

// ============================================================================
// 1. DASHBOARD OVERVIEW VIEW
// ============================================================================
export function AdminDashboardOverview({ metrics, loading, error, onRetry, onNavigate }) {
  if (loading && !metrics) {
    return (
      <div className="admin-loading-state">
        <div className="spinner" />
        <p>Loading administrator workspace metrics...</p>
      </div>
    );
  }

  const stats = metrics?.stats || {};
  const recentActivities = metrics?.recent_activities || [];

  return (
    <div className="admin-view-container">
      {error && (
        <div className="admin-notice error">
          <strong>Administrator Authorization Notice</strong>
          <p>{error}</p>
          <div className="admin-notice-actions">
            <button className="primary-button" onClick={onRetry} type="button">
              Retry Request
            </button>
            <button className="secondary-button" onClick={() => onNavigate("/dashboard")} type="button">
              Back to User Portal
            </button>
          </div>
        </div>
      )}

      {/* Hero Stat Grid */}
      <section className="admin-stat-grid">
        <div className="admin-stat" onClick={() => onNavigate("/admin/users")} style={{ cursor: "pointer" }}>
          <span>Total users</span>
          <strong>{stats.total_users ?? 0}</strong>
          <small>{stats.active_users ?? 0} Active accounts →</small>
        </div>
        <div className="admin-stat" onClick={() => onNavigate("/admin/courses")} style={{ cursor: "pointer" }}>
          <span>Total courses</span>
          <strong>{stats.total_courses ?? 0}</strong>
          <small>Curriculum modules active →</small>
        </div>
        <div className="admin-stat" onClick={() => onNavigate("/admin/tests")} style={{ cursor: "pointer" }}>
          <span>Total tests</span>
          <strong>{stats.total_tests ?? 0}</strong>
          <small>{stats.total_attempts ?? 0} Quiz attempts taken →</small>
        </div>
        <div className="admin-stat accent" onClick={() => onNavigate("/admin/reports")} style={{ cursor: "pointer" }}>
          <span>Total analyses</span>
          <strong>{stats.total_analyses ?? 0}</strong>
          <small>Candidate resumes analyzed →</small>
        </div>
      </section>

      {/* Main Grid: Platform Health & Latest Platform Events */}
      <section className="admin-overview-grid">
        <div className="admin-panel">
          <div className="panel-heading">
            <div>
              <span className="section-kicker">PERFORMANCE OVERVIEW</span>
              <h2>Platform health</h2>
            </div>
            <button
              className="link-subtle"
              type="button"
              onClick={() => onNavigate("/admin/performance")}
              style={{ fontSize: "0.8rem" }}
            >
              Full Analytics →
            </button>
          </div>
          <div className="health-list">
            <div>
              <span>Average ATS score</span>
              <strong>{stats.avg_ats_score !== undefined ? `${stats.avg_ats_score}%` : "0%"}</strong>
            </div>
            <div>
              <span>Average test score</span>
              <strong>{stats.avg_quiz_score !== undefined ? `${stats.avg_quiz_score}%` : "0%"}</strong>
            </div>
            <div>
              <span>Course completion rate</span>
              <strong>{stats.course_completion_rate !== undefined ? `${stats.course_completion_rate}%` : "0%"}</strong>
            </div>
            <div>
              <span>Active enrollments</span>
              <strong>{stats.total_enrollments ?? 0}</strong>
            </div>
          </div>
        </div>

        <div className="admin-panel activity-panel">
          <div className="panel-heading">
            <div>
              <span className="section-kicker">RECENT ACTIVITY</span>
              <h2>Latest platform events</h2>
            </div>
          </div>
          {recentActivities.length > 0 ? (
            <div className="admin-activity-list">
              {recentActivities.map((act, i) => (
                <div key={i} className="admin-activity-row">
                  <div className="admin-activity-title">{act.title}</div>
                  <div className="admin-activity-desc">{act.description}</div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-activity">
              Platform live and monitoring resume analysis & quiz submissions.
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

// ============================================================================
// 2. USERS VIEW
// ============================================================================
export function AdminUsersView({ apiUrl, token, showToast }) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [roleFilter, setRoleFilter] = useState("all");
  const [updatingId, setUpdatingId] = useState(null);

  const fetchUsers = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await axios.get(`${apiUrl}/api/admin/users`, AuthHeaders(token));
      setUsers(res.data || []);
    } catch (err) {
      console.error("Admin users fetch error:", err);
      setError(err?.response?.data?.detail || "Failed to load platform users.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleToggleStatus = async (user) => {
    setUpdatingId(user.id);
    try {
      const res = await axios.patch(
        `${apiUrl}/api/admin/users/${user.id}/status`,
        {},
        AuthHeaders(token)
      );
      setUsers((prev) =>
        prev.map((u) => (u.id === user.id ? { ...u, is_active: res.data.is_active } : u))
      );
      if (showToast) showToast(res.data.message || "User status updated", "success");
    } catch (err) {
      const msg = err?.response?.data?.detail || "Could not change user status.";
      if (showToast) showToast(msg, "error");
    } finally {
      setUpdatingId(null);
    }
  };

  const filteredUsers = useMemo(() => {
    return users.filter((u) => {
      const matchesSearch =
        u.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        u.email?.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesRole = roleFilter === "all" || u.role === roleFilter;
      return matchesSearch && matchesRole;
    });
  }, [users, searchTerm, roleFilter]);

  if (loading) {
    return (
      <div className="admin-loading-state">
        <div className="spinner" />
        <p>Loading platform user accounts...</p>
      </div>
    );
  }

  return (
    <div className="admin-view-container">
      <div className="admin-section-header">
        <div>
          <h2>User Accounts & Access Management</h2>
          <p>Supervise user profiles, credentials, and authentication statuses across the platform.</p>
        </div>
        <button className="secondary-button" onClick={fetchUsers} type="button">
          Refresh List
        </button>
      </div>

      {error && (
        <div className="admin-notice error">
          <p>{error}</p>
          <button className="primary-button" onClick={fetchUsers} type="button">Retry</button>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="admin-filter-bar">
        <div className="search-wrap">
          <input
            type="text"
            className="admin-search-input"
            placeholder="Search by name or email address..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="admin-pill-group">
          <button
            type="button"
            className={`admin-filter-pill ${roleFilter === "all" ? "active" : ""}`}
            onClick={() => setRoleFilter("all")}
          >
            All Roles ({users.length})
          </button>
          <button
            type="button"
            className={`admin-filter-pill ${roleFilter === "user" ? "active" : ""}`}
            onClick={() => setRoleFilter("user")}
          >
            Learners ({users.filter((u) => u.role === "user").length})
          </button>
          <button
            type="button"
            className={`admin-filter-pill ${roleFilter === "admin" ? "active" : ""}`}
            onClick={() => setRoleFilter("admin")}
          >
            Admins ({users.filter((u) => u.role === "admin").length})
          </button>
        </div>
      </div>

      {/* Users Table */}
      <div className="admin-table-card">
        <table className="admin-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Full Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Account Status</th>
              <th>Email Verified</th>
              <th>Phone Verified</th>
              <th>Activity</th>
              <th>Joined Date</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredUsers.length > 0 ? (
              filteredUsers.map((u) => (
                <tr key={u.id}>
                  <td><strong>#{u.id}</strong></td>
                  <td>
                    <div style={{ fontWeight: 600 }}>{u.full_name}</div>
                  </td>
                  <td><code style={{ fontSize: "0.82rem" }}>{u.email}</code></td>
                  <td>
                    <span className={`admin-badge-role ${u.role}`}>
                      {u.role.toUpperCase()}
                    </span>
                  </td>
                  <td>
                    <span className={`status-indicator-pill ${u.is_active ? "active" : "inactive"}`}>
                      <span className="dot" />
                      {u.is_active ? "Active" : "Deactivated"}
                    </span>
                  </td>
                  <td>
                    {u.is_email_verified ? (
                      <span className="chip-verified">✓ Verified</span>
                    ) : (
                      <span className="chip-unverified">Pending</span>
                    )}
                  </td>
                  <td>
                    {u.is_phone_verified ? (
                      <span className="chip-verified">✓ {u.phone_number || "Verified"}</span>
                    ) : (
                      <span className="chip-unverified">{u.phone_number ? "Unverified" : "None"}</span>
                    )}
                  </td>
                  <td>
                    <small style={{ color: "#64748b" }}>
                      {u.enrollments_count ?? 0} courses · {u.analyses_count ?? 0} resumes
                    </small>
                  </td>
                  <td>
                    <span style={{ fontSize: "0.78rem", color: "#64748b" }}>
                      {u.created_at ? new Date(u.created_at).toLocaleDateString() : "—"}
                    </span>
                  </td>
                  <td>
                    {u.role !== "admin" ? (
                      <button
                        type="button"
                        className={`admin-action-btn ${u.is_active ? "danger" : "primary"}`}
                        onClick={() => handleToggleStatus(u)}
                        disabled={updatingId === u.id}
                      >
                        {updatingId === u.id ? "Updating..." : u.is_active ? "Deactivate" : "Activate"}
                      </button>
                    ) : (
                      <span style={{ fontSize: "0.75rem", color: "#94a3b8" }}>Protected</span>
                    )}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={10} style={{ textAlign: "center", padding: "35px" }}>
                  <p style={{ color: "#64748b", margin: 0 }}>No user accounts matched the filter criteria.</p>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ============================================================================
// 3. PERFORMANCE VIEW
// ============================================================================
export function AdminPerformanceView({ apiUrl, token }) {
  const [perf, setPerf] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchPerf = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await axios.get(`${apiUrl}/api/admin/performance`, AuthHeaders(token));
      setPerf(res.data);
    } catch (err) {
      console.error("Admin performance fetch error:", err);
      setError(err?.response?.data?.detail || "Failed to load platform performance analytics.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPerf();
  }, []);

  if (loading) {
    return (
      <div className="admin-loading-state">
        <div className="spinner" />
        <p>Calculating platform metrics and skill gap analytics...</p>
      </div>
    );
  }

  const ats = perf?.ats || {};
  const dist = ats.distribution || {};
  const quizzes = perf?.quizzes || {};
  const learning = perf?.learning || {};
  const topMissing = ats.top_missing_skills || [];
  const topDetected = ats.top_detected_skills || [];

  return (
    <div className="admin-view-container">
      <div className="admin-section-header">
        <div>
          <h2>Performance & Learning Analytics</h2>
          <p>Real-time insights across candidate resume ATS scores, assessment quiz mastery, and curriculum progress.</p>
        </div>
        <button className="secondary-button" onClick={fetchPerf} type="button">
          Refresh Analytics
        </button>
      </div>

      {error && (
        <div className="admin-notice error">
          <p>{error}</p>
          <button className="primary-button" onClick={fetchPerf} type="button">Retry</button>
        </div>
      )}

      {/* Top 4 Performance Cards */}
      <section className="admin-stat-grid">
        <div className="admin-stat accent">
          <span>Average ATS Compatibility</span>
          <strong>{ats.avg_score !== undefined ? `${ats.avg_score}%` : "0%"}</strong>
          <small>Across {ats.total_analyses ?? 0} candidate resumes</small>
        </div>
        <div className="admin-stat">
          <span>Quiz Pass Rate</span>
          <strong>{quizzes.pass_rate !== undefined ? `${quizzes.pass_rate}%` : "0%"}</strong>
          <small>{quizzes.passed_attempts ?? 0} / {quizzes.total_attempts ?? 0} attempts passed</small>
        </div>
        <div className="admin-stat">
          <span>Average Quiz Score</span>
          <strong>{quizzes.avg_percentage !== undefined ? `${quizzes.avg_percentage}%` : "0%"}</strong>
          <small>Assessment knowledge mastery</small>
        </div>
        <div className="admin-stat">
          <span>Course Completion</span>
          <strong>
            {learning.total_enrollments > 0
              ? `${Math.round((learning.completed_enrollments / learning.total_enrollments) * 100)}%`
              : "0%"}
          </strong>
          <small>{learning.completed_enrollments ?? 0} fully completed courses</small>
        </div>
      </section>

      {/* Performance Grids */}
      <div className="admin-grid-two-column">
        {/* ATS Score Distribution Card */}
        <div className="admin-panel">
          <div className="panel-heading">
            <div>
              <span className="section-kicker">RESUME SCORING SPREAD</span>
              <h2>ATS Score Distribution</h2>
            </div>
            <span className="panel-period">{ats.total_analyses ?? 0} Resumes</span>
          </div>
          <div className="admin-dist-list">
            {[
              { label: "85 - 100% (High Alignment)", key: "85-100", color: "#10b981" },
              { label: "70 - 84% (Good Compatibility)", key: "70-84", color: "#0ea5e9" },
              { label: "50 - 69% (Moderate Gaps)", key: "50-69", color: "#f59e0b" },
              { label: "0 - 49% (Major Gaps)", key: "0-49", color: "#ef4444" },
            ].map(({ label, key, color }) => {
              const count = dist[key] || 0;
              const pct = ats.total_analyses ? Math.round((count / ats.total_analyses) * 100) : 0;
              return (
                <div key={key} className="admin-dist-row">
                  <div className="dist-row-header">
                    <span>{label}</span>
                    <strong>{count} ({pct}%)</strong>
                  </div>
                  <div className="horizontal-progress-bar small">
                    <div className="bar-fill" style={{ width: `${pct}%`, background: color }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Top Missing Skills Card */}
        <div className="admin-panel">
          <div className="panel-heading">
            <div>
              <span className="section-kicker">CAREER GAPS</span>
              <h2>Top Missing Skills Detected</h2>
            </div>
          </div>
          {topMissing.length > 0 ? (
            <div className="admin-skill-frequency-list">
              {topMissing.map((item, idx) => (
                <div key={item.skill} className="admin-skill-freq-row">
                  <span className="skill-rank">#{idx + 1}</span>
                  <span className="skill-name">{item.skill}</span>
                  <span className="skill-count-chip">{item.count} resumes missing</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-activity">No skill gap analyses recorded yet.</div>
          )}
        </div>
      </div>

      {/* Detected Skills + Enrollment Progress */}
      <div className="admin-grid-two-column" style={{ marginTop: "16px" }}>
        <div className="admin-panel">
          <div className="panel-heading">
            <div>
              <span className="section-kicker">TALENT BENCHMARK</span>
              <h2>Top Detected Candidate Skills</h2>
            </div>
          </div>
          {topDetected.length > 0 ? (
            <div className="admin-skill-frequency-list">
              {topDetected.map((item, idx) => (
                <div key={item.skill} className="admin-skill-freq-row">
                  <span className="skill-rank">#{idx + 1}</span>
                  <span className="skill-name">{item.skill}</span>
                  <span className="skill-count-chip green">{item.count} resumes present</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-activity">No candidate skills detected yet.</div>
          )}
        </div>

        <div className="admin-panel">
          <div className="panel-heading">
            <div>
              <span className="section-kicker">LEARNER ENGAGEMENT</span>
              <h2>Curriculum Completion Funnel</h2>
            </div>
          </div>
          <div className="health-list" style={{ marginTop: "16px" }}>
            <div>
              <span>Total Course Enrollments</span>
              <strong>{learning.total_enrollments ?? 0}</strong>
            </div>
            <div>
              <span>Courses In Progress</span>
              <strong>{learning.in_progress_enrollments ?? 0}</strong>
            </div>
            <div>
              <span>Courses Fully Graduated</span>
              <strong>{learning.completed_enrollments ?? 0}</strong>
            </div>
            <div>
              <span>Platform Average Progress</span>
              <strong>{learning.avg_progress !== undefined ? `${learning.avg_progress}%` : "0%"}</strong>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// 4. COURSES VIEW
// ============================================================================
export function AdminCoursesView({ apiUrl, token, onNavigate }) {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");

  const fetchCourses = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await axios.get(`${apiUrl}/api/admin/courses`, AuthHeaders(token));
      setCourses(res.data || []);
    } catch (err) {
      console.error("Admin courses fetch error:", err);
      setError(err?.response?.data?.detail || "Failed to load platform courses.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCourses();
  }, []);

  const categories = useMemo(() => {
    const set = new Set(courses.map((c) => c.category).filter(Boolean));
    return ["all", ...Array.from(set)];
  }, [courses]);

  const filtered = useMemo(() => {
    return courses.filter((c) => {
      const matchSearch =
        c.title.toLowerCase().includes(search.toLowerCase()) ||
        c.skills_covered?.some((s) => s.toLowerCase().includes(search.toLowerCase()));
      const matchCat = categoryFilter === "all" || c.category === categoryFilter;
      return matchSearch && matchCat;
    });
  }, [courses, search, categoryFilter]);

  if (loading) {
    return (
      <div className="admin-loading-state">
        <div className="spinner" />
        <p>Loading course curriculum catalog...</p>
      </div>
    );
  }

  return (
    <div className="admin-view-container">
      <div className="admin-section-header">
        <div>
          <h2>Curriculum & Course Management</h2>
          <p>Review course syllabi, learner enrollment statistics, and curriculum completion metrics.</p>
        </div>
        <button className="secondary-button" onClick={fetchCourses} type="button">
          Refresh Courses
        </button>
      </div>

      {error && (
        <div className="admin-notice error">
          <p>{error}</p>
          <button className="primary-button" onClick={fetchCourses} type="button">Retry</button>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="admin-filter-bar">
        <input
          type="text"
          className="admin-search-input"
          placeholder="Filter courses by title or skill (e.g. Python, React)..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <div className="admin-pill-group">
          {categories.map((cat) => (
            <button
              key={cat}
              type="button"
              className={`admin-filter-pill ${categoryFilter === cat ? "active" : ""}`}
              onClick={() => setCategoryFilter(cat)}
            >
              {cat === "all" ? `All Categories (${courses.length})` : cat}
            </button>
          ))}
        </div>
      </div>

      {/* Courses Cards Grid */}
      <div className="admin-courses-grid">
        {filtered.length > 0 ? (
          filtered.map((c) => (
            <div key={c.id} className="admin-course-card">
              <div className="course-card-top">
                <span className={`difficulty-badge ${c.difficulty.toLowerCase()}`}>
                  {c.difficulty}
                </span>
                <span className="course-category-tag">{c.category}</span>
              </div>
              <h3>{c.title}</h3>
              <div className="course-meta-inline">
                <span>⏱ {c.estimated_duration}</span>
                <span>📚 {c.total_lessons} Lessons</span>
                <span>📝 {c.total_quizzes} Quizzes</span>
              </div>

              {/* Progress / Completion stats */}
              <div className="course-enrollment-stats">
                <div className="stats-row">
                  <span>Enrolled: <strong>{c.enrolled_students} learners</strong></span>
                  <span>Completed: <strong>{c.completed_students}</strong></span>
                </div>
                <div className="horizontal-progress-bar small">
                  <div className="bar-fill" style={{ width: `${c.completion_rate}%` }} />
                </div>
                <small style={{ color: "#64748b", marginTop: "4px", display: "block" }}>
                  Completion rate: {c.completion_rate}%
                </small>
              </div>

              {/* Covered Skills */}
              <div className="course-skills-chips">
                {(c.skills_covered || []).slice(0, 5).map((sk) => (
                  <span key={sk} className="chip">
                    {sk}
                  </span>
                ))}
              </div>
            </div>
          ))
        ) : (
          <div className="empty-state-box" style={{ gridColumn: "1 / -1" }}>
            <p>No courses match your filter criteria.</p>
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// 5. LEARNING PATHS VIEW
// ============================================================================
export function AdminLearningPathsView({ apiUrl, token }) {
  const [paths, setPaths] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchPaths = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await axios.get(`${apiUrl}/api/admin/learning-paths`, AuthHeaders(token));
      setPaths(res.data || []);
    } catch (err) {
      console.error("Admin learning paths fetch error:", err);
      setError(err?.response?.data?.detail || "Failed to load learning paths.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPaths();
  }, []);

  if (loading) {
    return (
      <div className="admin-loading-state">
        <div className="spinner" />
        <p>Loading career learning pathways...</p>
      </div>
    );
  }

  return (
    <div className="admin-view-container">
      <div className="admin-section-header">
        <div>
          <h2>Career Learning Tracks</h2>
          <p>Structured career curriculums mapped to industry roles and candidate skill gap recommendations.</p>
        </div>
        <button className="secondary-button" onClick={fetchPaths} type="button">
          Refresh Tracks
        </button>
      </div>

      {error && (
        <div className="admin-notice error">
          <p>{error}</p>
          <button className="primary-button" onClick={fetchPaths} type="button">Retry</button>
        </div>
      )}

      <div className="admin-tracks-grid">
        {paths.map((p) => (
          <div key={p.id} className="admin-track-card">
            <div className="track-card-header">
              <span className="track-target-role">TARGET ROLE: {p.target_role}</span>
              <h3>{p.title}</h3>
              <p>{p.description}</p>
            </div>

            <div className="track-stats-strip">
              <div>
                <strong>{p.active_students}</strong>
                <span>Active Learners</span>
              </div>
              <div>
                <strong>{p.completions}</strong>
                <span>Course Completions</span>
              </div>
              <div>
                <strong>{p.course_count}</strong>
                <span>Curriculum Modules</span>
              </div>
            </div>

            <div className="track-courses-list">
              <strong>Syllabus Pathway:</strong>
              <ol>
                {p.courses.map((courseTitle, idx) => (
                  <li key={idx}>
                    <span>{courseTitle}</span>
                  </li>
                ))}
              </ol>
            </div>

            <div className="track-skills-wrap">
              <strong>Competencies Acquired:</strong>
              <div className="chips">
                {p.skills.map((sk) => (
                  <span key={sk} className="chip accent">
                    {sk}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================================================
// 6. TESTS VIEW
// ============================================================================
export function AdminTestsView({ apiUrl, token }) {
  const [tests, setTests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");

  const fetchTests = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await axios.get(`${apiUrl}/api/admin/tests`, AuthHeaders(token));
      setTests(res.data || []);
    } catch (err) {
      console.error("Admin tests fetch error:", err);
      setError(err?.response?.data?.detail || "Failed to load assessments.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTests();
  }, []);

  const filtered = useMemo(() => {
    return tests.filter((t) =>
      t.title.toLowerCase().includes(search.toLowerCase()) ||
      t.course_title.toLowerCase().includes(search.toLowerCase())
    );
  }, [tests, search]);

  if (loading) {
    return (
      <div className="admin-loading-state">
        <div className="spinner" />
        <p>Loading assessment tests and pass rate statistics...</p>
      </div>
    );
  }

  return (
    <div className="admin-view-container">
      <div className="admin-section-header">
        <div>
          <h2>Technical Assessments & Quizzes</h2>
          <p>Monitor course evaluation quizzes, passing thresholds, and candidate attempt statistics.</p>
        </div>
        <button className="secondary-button" onClick={fetchTests} type="button">
          Refresh Tests
        </button>
      </div>

      {error && (
        <div className="admin-notice error">
          <p>{error}</p>
          <button className="primary-button" onClick={fetchTests} type="button">Retry</button>
        </div>
      )}

      <div className="admin-filter-bar">
        <input
          type="text"
          className="admin-search-input"
          placeholder="Search assessments by quiz or course title..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div className="admin-table-card">
        <table className="admin-table">
          <thead>
            <tr>
              <th>Quiz ID</th>
              <th>Assessment Title</th>
              <th>Associated Course</th>
              <th>Pass Threshold</th>
              <th>Questions</th>
              <th>Total Attempts</th>
              <th>Passed Attempts</th>
              <th>Pass Rate</th>
              <th>Avg Score</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length > 0 ? (
              filtered.map((t) => (
                <tr key={t.id}>
                  <td><strong>#{t.id}</strong></td>
                  <td><strong>{t.title}</strong></td>
                  <td><span className="course-tag">{t.course_title}</span></td>
                  <td>{t.passing_score}% Score</td>
                  <td>{t.total_questions} Questions</td>
                  <td>{t.total_attempts} attempts</td>
                  <td><strong style={{ color: "#10b981" }}>{t.passed_attempts}</strong></td>
                  <td>
                    <span className={`pass-rate-pill ${t.pass_rate >= 70 ? "good" : "moderate"}`}>
                      {t.pass_rate}%
                    </span>
                  </td>
                  <td><strong>{t.avg_score}%</strong></td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={9} style={{ textAlign: "center", padding: "30px", color: "#64748b" }}>
                  No assessment tests found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ============================================================================
// 7. QUESTIONS VIEW
// ============================================================================
export function AdminQuestionsView({ apiUrl, token }) {
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedQuiz, setSelectedQuiz] = useState("all");

  const fetchQuestions = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await axios.get(`${apiUrl}/api/admin/questions`, AuthHeaders(token));
      setQuestions(res.data || []);
    } catch (err) {
      console.error("Admin questions fetch error:", err);
      setError(err?.response?.data?.detail || "Failed to load question bank.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQuestions();
  }, []);

  const quizzesList = useMemo(() => {
    const map = new Map();
    questions.forEach((q) => {
      if (!map.has(q.quiz_id)) {
        map.set(q.quiz_id, `${q.quiz_title} (${q.course_title})`);
      }
    });
    return Array.from(map.entries());
  }, [questions]);

  const filtered = useMemo(() => {
    if (selectedQuiz === "all") return questions;
    return questions.filter((q) => q.quiz_id === Number(selectedQuiz));
  }, [questions, selectedQuiz]);

  if (loading) {
    return (
      <div className="admin-loading-state">
        <div className="spinner" />
        <p>Loading assessment question bank...</p>
      </div>
    );
  }

  return (
    <div className="admin-view-container">
      <div className="admin-section-header">
        <div>
          <h2>Assessment Question Bank</h2>
          <p>Review questions, multiple choice options, correct answers, and educational explanations.</p>
        </div>
        <button className="secondary-button" onClick={fetchQuestions} type="button">
          Refresh Questions
        </button>
      </div>

      {error && (
        <div className="admin-notice error">
          <p>{error}</p>
          <button className="primary-button" onClick={fetchQuestions} type="button">Retry</button>
        </div>
      )}

      <div className="admin-filter-bar">
        <label style={{ fontSize: "0.85rem", fontWeight: 600, color: "#475569" }}>Filter by Assessment:</label>
        <select
          className="admin-select"
          value={selectedQuiz}
          onChange={(e) => setSelectedQuiz(e.target.value)}
        >
          <option value="all">All Quizzes ({questions.length} total questions)</option>
          {quizzesList.map(([id, title]) => (
            <option key={id} value={id}>
              {title}
            </option>
          ))}
        </select>
      </div>

      <div className="admin-questions-list">
        {filtered.length > 0 ? (
          filtered.map((q, idx) => (
            <div key={q.id} className="admin-question-card">
              <div className="question-header">
                <span className="question-num">Q{idx + 1}</span>
                <span className="question-quiz-badge">{q.quiz_title}</span>
                <span className="question-course-badge">{q.course_title}</span>
              </div>
              <h4 className="question-prompt">{q.question_text}</h4>

              <div className="options-grid">
                {q.options.map((opt) => (
                  <div key={opt.id} className={`admin-option-item ${opt.is_correct ? "correct" : ""}`}>
                    <span className="option-indicator">{opt.is_correct ? "✓" : "○"}</span>
                    <span className="option-text">{opt.option_text}</span>
                    {opt.is_correct && <span className="correct-tag">Correct Answer</span>}
                  </div>
                ))}
              </div>

              {q.options.some((o) => o.explanation) && (
                <div className="question-explanation-box">
                  <strong>Explanation:</strong>{" "}
                  {q.options.find((o) => o.is_correct)?.explanation ||
                    q.options.find((o) => o.explanation)?.explanation}
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="empty-state-box">
            <p>No questions found for the selected assessment.</p>
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// 8. BADGES VIEW
// ============================================================================
export function AdminBadgesView({ apiUrl, token }) {
  const [badges, setBadges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchBadges = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await axios.get(`${apiUrl}/api/admin/badges`, AuthHeaders(token));
      setBadges(res.data || []);
    } catch (err) {
      console.error("Admin badges fetch error:", err);
      setError(err?.response?.data?.detail || "Failed to load achievement badges.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBadges();
  }, []);

  if (loading) {
    return (
      <div className="admin-loading-state">
        <div className="spinner" />
        <p>Loading achievement badges and platform unlock criteria...</p>
      </div>
    );
  }

  const getBadgeIcon = (iconName) => {
    switch (iconName) {
      case "award":
        return <AwardIcon size={28} />;
      case "flame":
        return <FireIcon size={28} />;
      case "book":
        return <CoursesIcon size={28} />;
      default:
        return <CheckCircleIcon size={28} />;
    }
  };

  return (
    <div className="admin-view-container">
      <div className="admin-section-header">
        <div>
          <h2>Platform Achievement Badges & Milestones</h2>
          <p>Gamification milestones awarded to candidates for resume improvements, quiz excellence, and daily streaks.</p>
        </div>
        <button className="secondary-button" onClick={fetchBadges} type="button">
          Refresh Badges
        </button>
      </div>

      {error && (
        <div className="admin-notice error">
          <p>{error}</p>
          <button className="primary-button" onClick={fetchBadges} type="button">Retry</button>
        </div>
      )}

      <div className="admin-badges-grid">
        {badges.map((b) => {
          const pct = b.total_eligible ? Math.round((b.unlocked_count / b.total_eligible) * 100) : 0;
          return (
            <div key={b.id} className="admin-badge-card">
              <div className="badge-card-top">
                <div className={`badge-icon-wrap tier-${b.tier.toLowerCase()}`}>
                  {getBadgeIcon(b.icon)}
                </div>
                <div>
                  <span className={`badge-tier-tag ${b.tier.toLowerCase()}`}>{b.tier} Tier</span>
                  <span className="badge-category">{b.category}</span>
                </div>
              </div>

              <h3>{b.name}</h3>
              <p className="badge-desc">{b.description}</p>

              <div className="badge-unlock-stats">
                <div className="stats-row">
                  <span>Earned by:</span>
                  <strong>{b.unlocked_count} of {b.total_eligible} learners ({pct}%)</strong>
                </div>
                <div className="horizontal-progress-bar small">
                  <div className="bar-fill" style={{ width: `${pct}%` }} />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ============================================================================
// 9. REPORTS VIEW
// ============================================================================
export function AdminReportsView({ apiUrl, token }) {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [selectedReport, setSelectedReport] = useState(null);

  const fetchReports = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await axios.get(`${apiUrl}/api/admin/reports`, AuthHeaders(token));
      setReports(res.data || []);
    } catch (err) {
      console.error("Admin reports fetch error:", err);
      setError(err?.response?.data?.detail || "Failed to load resume analysis audits.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const filtered = useMemo(() => {
    return reports.filter((r) =>
      r.candidate_name.toLowerCase().includes(search.toLowerCase()) ||
      r.filename.toLowerCase().includes(search.toLowerCase()) ||
      r.candidate_email.toLowerCase().includes(search.toLowerCase())
    );
  }, [reports, search]);

  if (loading) {
    return (
      <div className="admin-loading-state">
        <div className="spinner" />
        <p>Loading candidate resume analysis audits...</p>
      </div>
    );
  }

  return (
    <div className="admin-view-container">
      <div className="admin-section-header">
        <div>
          <h2>Candidate Resume Analysis Audits</h2>
          <p>Comprehensive audit log of candidate resume uploads, ATS compatibility scores, and detected skill gaps.</p>
        </div>
        <button className="secondary-button" onClick={fetchReports} type="button">
          Refresh Logs
        </button>
      </div>

      {error && (
        <div className="admin-notice error">
          <p>{error}</p>
          <button className="primary-button" onClick={fetchReports} type="button">Retry</button>
        </div>
      )}

      <div className="admin-filter-bar">
        <input
          type="text"
          className="admin-search-input"
          placeholder="Search by candidate name, email, or filename..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div className="admin-table-card">
        <table className="admin-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Candidate</th>
              <th>Resume File</th>
              <th>Pages</th>
              <th>ATS Score</th>
              <th>Role Match</th>
              <th>Detected Skills</th>
              <th>Missing Skills</th>
              <th>Analyzed Date</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length > 0 ? (
              filtered.map((r) => (
                <tr key={r.id}>
                  <td><strong>#{r.id}</strong></td>
                  <td>
                    <strong>{r.candidate_name}</strong>
                    <div style={{ fontSize: "0.78rem", color: "#64748b" }}>{r.candidate_email}</div>
                  </td>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                      <ResumeIcon size={14} />
                      <span style={{ fontSize: "0.82rem" }}>{r.filename}</span>
                    </div>
                  </td>
                  <td>{r.pages} p.</td>
                  <td>
                    <span className={`score-badge ${r.ats_score >= 70 ? "high" : r.ats_score >= 50 ? "mid" : "low"}`}>
                      {r.ats_score}%
                    </span>
                  </td>
                  <td>
                    <span className="score-badge mid">
                      {r.job_match_percentage}%
                    </span>
                  </td>
                  <td>
                    <div className="chips-mini">
                      {(r.detected_skills || []).slice(0, 3).map((s) => (
                        <span key={s} className="chip mini">{s}</span>
                      ))}
                      {(r.detected_skills || []).length > 3 && (
                        <span className="chip mini muted">+{r.detected_skills.length - 3}</span>
                      )}
                    </div>
                  </td>
                  <td>
                    <div className="chips-mini">
                      {(r.missing_skills || []).slice(0, 2).map((s) => (
                        <span key={s} className="chip mini warning">{s}</span>
                      ))}
                      {(r.missing_skills || []).length > 2 && (
                        <span className="chip mini muted">+{r.missing_skills.length - 2}</span>
                      )}
                    </div>
                  </td>
                  <td>
                    <span style={{ fontSize: "0.78rem", color: "#64748b" }}>
                      {r.created_at ? new Date(r.created_at).toLocaleDateString() : "—"}
                    </span>
                  </td>
                  <td>
                    <button
                      type="button"
                      className="admin-action-btn primary"
                      onClick={() => setSelectedReport(r)}
                    >
                      View Audit
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={10} style={{ textAlign: "center", padding: "30px", color: "#64748b" }}>
                  No resume analysis audits found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Audit Detail Modal */}
      {selectedReport && (
        <div className="admin-modal-overlay" onClick={() => setSelectedReport(null)}>
          <div className="admin-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <span className="section-kicker">AUDIT RECORD #{selectedReport.id}</span>
                <h3>{selectedReport.filename}</h3>
                <p>Candidate: {selectedReport.candidate_name} ({selectedReport.candidate_email})</p>
              </div>
              <button
                type="button"
                className="close-button"
                onClick={() => setSelectedReport(null)}
              >
                ✕
              </button>
            </div>

            <div className="modal-scores-row">
              <div className="score-stat-box">
                <span>ATS Compatibility</span>
                <strong>{selectedReport.ats_score}%</strong>
              </div>
              <div className="score-stat-box">
                <span>Job Role Match</span>
                <strong>{selectedReport.job_match_percentage}%</strong>
              </div>
              <div className="score-stat-box">
                <span>Document Length</span>
                <strong>{selectedReport.pages} Page(s)</strong>
              </div>
            </div>

            <div className="modal-skills-section">
              <strong>Detected Candidate Skills:</strong>
              <div className="chips" style={{ marginTop: "6px" }}>
                {(selectedReport.detected_skills || []).map((sk) => (
                  <span key={sk} className="chip success">{sk}</span>
                ))}
              </div>
            </div>

            <div className="modal-skills-section" style={{ marginTop: "16px" }}>
              <strong>Identified Skill Gaps (Missing):</strong>
              <div className="chips" style={{ marginTop: "6px" }}>
                {(selectedReport.missing_skills || []).map((sk) => (
                  <span key={sk} className="chip warning">{sk}</span>
                ))}
              </div>
            </div>

            <div style={{ marginTop: "20px", display: "flex", justifyContent: "flex-end" }}>
              <button
                type="button"
                className="secondary-button"
                onClick={() => setSelectedReport(null)}
              >
                Close Audit
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

