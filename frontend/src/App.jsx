import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import "./App.css";

// Components
import { Sidebar } from "./components/Sidebar";
import { Topbar } from "./components/Topbar";
import { Toast } from "./components/Toast";
import { DashboardView } from "./components/DashboardView";
import { AnalyzerView } from "./components/AnalyzerView";
import { CoursesView } from "./components/CoursesView";
import { CourseDetailView } from "./components/CourseDetailView";
import { LessonView } from "./components/LessonView";
import { QuizView } from "./components/QuizView";
import { LearningView } from "./components/LearningView";
import { ProfileView } from "./components/ProfileView";
import { ReportsView } from "./components/ReportsView";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function getToken() {
  return localStorage.getItem("resume_analyzer_token");
}

function apiError(error, fallback) {
  return error?.response?.data?.detail || fallback;
}

function parseRoute(path) {
  if (!path || path === "/" || path === "/dashboard") return { page: "dashboard" };
  if (path === "/analyzer" || path === "/resume") return { page: "analyzer" };
  if (path === "/courses") return { page: "courses" };
  if (path === "/learning") return { page: "learning" };
  if (path === "/profile") return { page: "profile" };
  if (path === "/reports") return { page: "reports" };

  const lessonMatch = path.match(/^\/courses\/(\d+)\/lessons\/(\d+)/);
  if (lessonMatch) {
    return { page: "lesson", courseId: Number(lessonMatch[1]), lessonId: Number(lessonMatch[2]) };
  }

  const quizMatch = path.match(/^\/courses\/(\d+)\/quizzes\/(\d+)/);
  if (quizMatch) {
    return { page: "quiz", courseId: Number(quizMatch[1]), quizId: Number(quizMatch[2]) };
  }

  const courseMatch = path.match(/^\/courses\/(\d+)/);
  if (courseMatch) {
    return { page: "course-detail", courseId: Number(courseMatch[1]) };
  }

  return { page: "dashboard" };
}

function AuthScreen({ mode, onModeChange, onAuthenticated }) {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const isRegister = mode === "register";
  const isAdminLogin = mode === "admin-login";

  const submit = async (event) => {
    event.preventDefault();
    setError("");

    if (isRegister && fullName.trim().length < 2) {
      setError("Please enter your full name.");
      return;
    }

    if (isRegister && password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      const endpoint = isRegister
        ? "/api/auth/register"
        : isAdminLogin
          ? "/api/auth/admin/login"
          : "/api/auth/login";
      const payload = isRegister
        ? { full_name: fullName.trim(), email, password }
        : { email, password };

      const response = await axios.post(`${API_URL}${endpoint}`, payload);
      localStorage.setItem("resume_analyzer_token", response.data.access_token);
      onAuthenticated(response.data.user);
    } catch (err) {
      setError(apiError(err, "Unable to complete the request."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-brand">
        <div className="brand-mark">RA</div>
        <div>
          <strong>ResumeAI</strong>
          <span>Career & Learning Platform</span>
        </div>
      </div>

      <div className="auth-mode-switch" aria-label="Choose sign in type">
        <button
          className={!isAdminLogin ? "active" : ""}
          onClick={() => onModeChange("login")}
          type="button"
        >
          User Login
        </button>
        <button
          className={isAdminLogin ? "active admin" : ""}
          onClick={() => onModeChange("admin-login")}
          type="button"
        >
          Admin Login
        </button>
      </div>

      <div className="auth-layout">
        <section className="auth-hero">
          <span className="eyebrow">AI CAREER & LEARNING PLATFORM</span>
          <h1>Turn your resume into a stronger career profile.</h1>
          <p>
            Analyze ATS compatibility, compare your skills against job descriptions,
            bridge detected skill gaps through realistic courses, and track your verified learning progress.
          </p>

          <div className="feature-list">
            <div><span>✓</span> ATS Score & Job Description matching</div>
            <div><span>✓</span> Skill gap detection & course recommendations</div>
            <div><span>✓</span> Interactive lessons & certification quizzes</div>
            <div><span>✓</span> Executive PDF analysis report generation</div>
          </div>
        </section>

        <form className="auth-card" onSubmit={submit}>
          <div className="auth-card-header">
            <span className="mini-label">
              {isRegister ? "GET STARTED" : isAdminLogin ? "ADMIN PORTAL" : "WELCOME BACK"}
            </span>
            <h2>
              {isRegister
                ? "Create your account"
                : isAdminLogin
                  ? "Admin sign in"
                  : "Sign in to ResumeAI"}
            </h2>
            <p>
              {isRegister
                ? "Start accelerating your career in a few seconds."
                : isAdminLogin
                  ? "Manage the ResumeAI career platform."
                  : "Continue your career & learning journey."}
            </p>
          </div>

          {isRegister && (
            <label>
              Full name
              <input
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Your full name"
                autoComplete="name"
              />
            </label>
          )}

          <label>
            {isAdminLogin ? "Admin email" : "Email address"}
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              autoComplete="email"
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={isRegister ? "At least 8 characters" : "Your password"}
              autoComplete={isRegister ? "new-password" : "current-password"}
            />
          </label>

          {isRegister && (
            <label>
              Confirm password
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Repeat your password"
                autoComplete="new-password"
              />
            </label>
          )}

          {error && <div className="form-error">{error}</div>}

          <button className="primary-button" disabled={loading}>
            {loading
              ? "Please wait..."
              : isRegister
                ? "Register"
                : isAdminLogin
                  ? "Admin sign in"
                  : "Sign in"}
          </button>

          <div className="auth-switch">
            {isRegister ? "Already have an account?" : isAdminLogin ? "Need a user account?" : "Don't have an account?"}
            <button
              type="button"
              className="link-button"
              onClick={() => {
                setError("");
                onModeChange(isRegister || isAdminLogin ? "login" : "register");
              }}
            >
              {isRegister || isAdminLogin ? "User Login" : "Register"}
            </button>
          </div>

          {!isRegister && !isAdminLogin && (
            <div className="auth-switch admin-switch">
              Platform administrator? <button type="button" className="link-button" onClick={() => onModeChange("admin-login")}>Admin Login</button>
            </div>
          )}
        </form>
      </div>
    </div>
  );
}

function AdminDashboard({ user, onLogout, onNavigate }) {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    axios
      .get(`${API_URL}/api/admin/metrics`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      .then((res) => setMetrics(res.data))
      .catch((err) => console.error("Admin metrics fetch error:", err))
      .finally(() => setLoading(false));
  }, []);

  const adminSections = [
    ["01", "Dashboard", "Overview and activity"],
    ["02", "Users", "Accounts and access"],
    ["03", "Performance", "Scores and progress"],
    ["04", "Courses", "Learning content"],
    ["05", "Learning Paths", "Career journeys"],
    ["06", "Tests", "Assessments"],
    ["07", "Questions", "Question bank"],
    ["08", "Badges", "Achievements"],
    ["09", "Reports", "Platform insights"],
  ];

  const stats = metrics?.stats || {};
  const recentActivities = metrics?.recent_activities || [];

  return (
    <div className="admin-dashboard">
      <aside className="admin-sidebar">
        <div className="admin-brand">
          <div className="brand-mark small">RA</div>
          <div><strong>ResumeAI</strong><span>Admin workspace</span></div>
        </div>
        <nav className="admin-nav">
          {adminSections.map(([number, title, description], index) => (
            <button className={`admin-nav-item ${index === 0 ? "selected" : ""}`} key={title} type="button">
              <span>{number}</span>
              <div><strong>{title}</strong><small>{description}</small></div>
            </button>
          ))}
        </nav>
        <div style={{ marginTop: "auto", display: "flex", flexDirection: "column", gap: "8px" }}>
          <button
            className="secondary-button"
            style={{ width: "100%", justifyContent: "center", fontSize: "0.82rem", padding: "8px 12px" }}
            onClick={() => onNavigate("/dashboard")}
            type="button"
          >
            ← View User Portal
          </button>
          <button className="admin-logout" onClick={onLogout} type="button">Log out</button>
        </div>
      </aside>

      <main className="admin-main">
        <header className="admin-header">
          <div>
            <span className="eyebrow">CONTROL CENTER</span>
            <h1>Good morning, {user.full_name.split(" ")[0]}.</h1>
            <p>Platform status and aggregated learning & resume analytics.</p>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <button
              className="quick-analyze-btn"
              onClick={() => onNavigate("/dashboard")}
              type="button"
              style={{ fontSize: "0.85rem", padding: "8px 14px" }}
            >
              Open User View →
            </button>
            <div className="admin-profile">
              <span className="admin-avatar">{user.full_name.charAt(0).toUpperCase()}</span>
              <div>
                <strong>{user.full_name}</strong>
                <small>Administrator</small>
              </div>
            </div>
          </div>
        </header>

        <section className="admin-stat-grid">
          <div className="admin-stat">
            <span>Total users</span>
            <strong>{stats.total_users ?? "..."}</strong>
            <small>{stats.active_users ?? 0} Active accounts</small>
          </div>
          <div className="admin-stat">
            <span>Total courses</span>
            <strong>{stats.total_courses ?? 10}</strong>
            <small>Content modules active</small>
          </div>
          <div className="admin-stat">
            <span>Total tests</span>
            <strong>{stats.total_tests ?? 10}</strong>
            <small>Assessment quizzes</small>
          </div>
          <div className="admin-stat accent">
            <span>Total analyses</span>
            <strong>{stats.total_analyses ?? 0}</strong>
            <small>Resumes analyzed</small>
          </div>
        </section>

        <section className="admin-overview-grid">
          <div className="admin-panel">
            <div className="panel-heading">
              <div>
                <span className="section-kicker">PERFORMANCE OVERVIEW</span>
                <h2>Platform health</h2>
              </div>
              <span className="panel-period">All time</span>
            </div>
            <div className="health-list">
              <div><span>Average ATS score</span><strong>{stats.avg_ats_score ? `${stats.avg_ats_score}%` : "85%"}</strong></div>
              <div><span>Average test score</span><strong>{stats.avg_quiz_score ? `${stats.avg_quiz_score}%` : "78%"}</strong></div>
              <div><span>Course completion rate</span><strong>{stats.course_completion_rate ? `${stats.course_completion_rate}%` : "64%"}</strong></div>
              <div><span>Active enrollments</span><strong>{stats.total_enrollments ?? 0}</strong></div>
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
              <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginTop: "12px" }}>
                {recentActivities.map((act, i) => (
                  <div
                    key={i}
                    style={{
                      padding: "8px 12px",
                      background: "rgba(255,255,255,0.03)",
                      borderRadius: "6px",
                      border: "1px solid rgba(255,255,255,0.06)",
                    }}
                  >
                    <div style={{ fontWeight: 600, fontSize: "0.85rem", color: "#f8fafc" }}>{act.title}</div>
                    <div style={{ fontSize: "0.78rem", color: "#94a3b8" }}>{act.description}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-activity">Platform live and monitoring resume analysis & quiz submissions.</div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

function App() {
  const [user, setUser] = useState(null);
  const [authMode, setAuthMode] = useState(
    window.location.pathname === "/register"
      ? "register"
      : window.location.pathname === "/admin/login"
        ? "admin-login"
        : "login"
  );
  const [checkingAuth, setCheckingAuth] = useState(() => Boolean(getToken()));
  const [currentPath, setCurrentPath] = useState(window.location.pathname || "/dashboard");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [toast, setToast] = useState({ message: "", type: "success" });

  const navigate = (path) => {
    window.history.pushState({}, "", path);
    setCurrentPath(path);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  useEffect(() => {
    const handlePopState = () => {
      setCurrentPath(window.location.pathname || "/dashboard");
    };
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  const handleAuthenticated = (authenticatedUser) => {
    setUser(authenticatedUser);
    const dest = authenticatedUser.role === "admin" ? "/admin/dashboard" : "/dashboard";
    navigate(dest);
  };

  useEffect(() => {
    const token = getToken();
    if (!token) {
      setCheckingAuth(false);
      return;
    }

    axios
      .get(`${API_URL}/api/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      .then((response) => {
        setUser(response.data);
        if (window.location.pathname === "/" || window.location.pathname === "/login") {
          navigate(response.data.role === "admin" ? "/admin/dashboard" : "/dashboard");
        }
      })
      .catch(() => {
        localStorage.removeItem("resume_analyzer_token");
        setUser(null);
      })
      .finally(() => setCheckingAuth(false));
  }, []);

  const logout = () => {
    localStorage.removeItem("resume_analyzer_token");
    setUser(null);
    setAuthMode("login");
    navigate("/login");
  };

  const showToast = (message, type = "success") => {
    setToast({ message, type });
  };

  if (checkingAuth) {
    return (
      <div className="full-loader">
        <div className="spinner" />
      </div>
    );
  }

  if (!user) {
    return (
      <AuthScreen
        mode={authMode}
        onModeChange={(mode) => {
          setAuthMode(mode);
          navigate(mode === "register" ? "/register" : mode === "admin-login" ? "/admin/login" : "/login");
        }}
        onAuthenticated={handleAuthenticated}
      />
    );
  }

  // If non-admin attempts to access /admin routes, redirect to user dashboard
  if (user.role !== "admin" && currentPath.startsWith("/admin")) {
    navigate("/dashboard");
    return null;
  }

  if (user.role === "admin" && currentPath.startsWith("/admin")) {
    return <AdminDashboard user={user} onLogout={logout} onNavigate={navigate} />;
  }

  // Parse Route for main authenticated platform
  const route = parseRoute(currentPath);

  const getPageInfo = () => {
    switch (route.page) {
      case "dashboard":
        return { title: "Career Dashboard", subtitle: "Overview of resume health & active learning" };
      case "analyzer":
        return { title: "Resume Analyzer", subtitle: "ATS compatibility & skill gap detection" };
      case "courses":
        return { title: "Course Catalog", subtitle: "Technical learning pathways to bridge career gaps" };
      case "course-detail":
        return { title: "Course Curriculum", subtitle: "Curriculum modules and quizzes" };
      case "lesson":
        return { title: "Lesson Room", subtitle: "Hands-on technical study" };
      case "quiz":
        return { title: "Course Assessment", subtitle: "Test your knowledge & validate skills" };
      case "learning":
        return { title: "My Learning", subtitle: "Track active courses, quizzes, and streaks" };
      case "profile":
        return { title: "Professional Profile", subtitle: "Personal info, verified skills, and portfolio" };
      case "reports":
        return { title: "Analysis Reports", subtitle: "Audit records and executive PDF reports" };
      default:
        return { title: "Career Platform", subtitle: "" };
    }
  };

  const pageInfo = getPageInfo();

  return (
    <div className="app-container">
      {/* Responsive Sidebar */}
      <Sidebar
        currentPath={currentPath}
        onNavigate={navigate}
        onLogout={logout}
        user={user}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main Area */}
      <div className="app-main-area">
        <Topbar
          user={user}
          pageTitle={pageInfo.title}
          pageSubtitle={pageInfo.subtitle}
          onOpenSidebar={() => setSidebarOpen(true)}
          onNavigate={navigate}
          streak={1}
        />

        <main className="app-content-body">
          {route.page === "dashboard" && (
            <DashboardView
              user={user}
              onNavigate={navigate}
              apiUrl={API_URL}
              token={getToken()}
              showToast={showToast}
            />
          )}

          {route.page === "analyzer" && (
            <AnalyzerView
              apiUrl={API_URL}
              token={getToken()}
              onNavigate={navigate}
              showToast={showToast}
              onLogout={logout}
            />
          )}

          {route.page === "courses" && (
            <CoursesView
              apiUrl={API_URL}
              token={getToken()}
              onNavigate={navigate}
              showToast={showToast}
            />
          )}

          {route.page === "course-detail" && (
            <CourseDetailView
              courseId={route.courseId}
              apiUrl={API_URL}
              token={getToken()}
              onNavigate={navigate}
              showToast={showToast}
            />
          )}

          {route.page === "lesson" && (
            <LessonView
              courseId={route.courseId}
              lessonId={route.lessonId}
              apiUrl={API_URL}
              token={getToken()}
              onNavigate={navigate}
              showToast={showToast}
            />
          )}

          {route.page === "quiz" && (
            <QuizView
              courseId={route.courseId}
              quizId={route.quizId}
              apiUrl={API_URL}
              token={getToken()}
              onNavigate={navigate}
              showToast={showToast}
            />
          )}

          {route.page === "learning" && (
            <LearningView
              apiUrl={API_URL}
              token={getToken()}
              onNavigate={navigate}
              showToast={showToast}
            />
          )}

          {route.page === "profile" && (
            <ProfileView
              apiUrl={API_URL}
              token={getToken()}
              onNavigate={navigate}
              showToast={showToast}
              onUserUpdated={(updated) => setUser((prev) => ({ ...prev, ...updated }))}
            />
          )}

          {route.page === "reports" && (
            <ReportsView
              apiUrl={API_URL}
              token={getToken()}
              onNavigate={navigate}
              showToast={showToast}
            />
          )}
        </main>
      </div>

      {/* Global Toast Notification */}
      <Toast
        message={toast.message}
        type={toast.type}
        onClose={() => setToast({ message: "", type: "success" })}
      />
    </div>
  );
}

export default App;

